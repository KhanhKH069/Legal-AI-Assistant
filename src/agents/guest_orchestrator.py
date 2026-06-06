import logging
import operator
from typing import Annotated, Literal, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel

from src.agents.caselaw_agent import caselaw_agent_node
from src.agents.statutory_agent import statutory_agent_node
from src.core.llm import get_llm
from src.tools.legal_tools import search_case_law, search_statutory_law

logger = logging.getLogger(__name__)

llm = get_llm()


class GuestIntentRouting(BaseModel):
    """Phân loại ý định cho người dùng vãng lai."""
    intent: Literal['STATUTORY', 'CASELAW']


class GuestLegalState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str
    user_intent: str
    session_id: str


_GUEST_ORCHESTRATOR_PROMPT = (
    'Bạn là bộ phân loại ý định cho Legal AI Assistant dành cho người dùng vãng lai.\n\n'
    'Phân loại câu hỏi vào một trong hai nhóm:\n\n'
    '**STATUTORY** — Tra cứu quy định pháp luật, điều luật, văn bản pháp quy\n'
    '**CASELAW** — Tra cứu án lệ, bản án, cách Tòa giải quyết tranh chấp'
)


def create_guest_orchestrator():
    prompt = ChatPromptTemplate.from_messages([
        ('system', _GUEST_ORCHESTRATOR_PROMPT),
        MessagesPlaceholder(variable_name='messages'),
    ])
    structured_llm = llm.with_structured_output(GuestIntentRouting)
    return prompt | structured_llm


def guest_orchestrator_node(state: GuestLegalState):
    orchestrator = create_guest_orchestrator()
    intent_str = 'STATUTORY'
    next_agent = 'statutory_agent'
    try:
        result: GuestIntentRouting = orchestrator.invoke({'messages': state['messages']})
        intent_str = result.intent
        next_agent = 'caselaw_agent' if intent_str == 'CASELAW' else 'statutory_agent'
    except Exception as e:
        logger.warning('Guest orchestrator failed: %s — defaulting to statutory_agent', e)

    logger.info('Guest Orchestrator → %s (intent: %s)', next_agent, intent_str)
    return {
        'messages': state['messages'],
        'next': next_agent,
        'user_intent': intent_str,
        'session_id': state.get('session_id', 'guest'),
    }


def guest_router(state: GuestLegalState) -> str:
    return state.get('next', 'statutory_agent')


def create_guest_agent_graph():
    if llm is None:
        return None

    workflow = StateGraph(GuestLegalState)

    def guest_statutory_node(state: GuestLegalState):
        from src.agents.orchestrator import AgentState
        adapted: AgentState = {
            'messages': state['messages'],
            'next': '',
            'user_intent': state.get('user_intent', ''),
            'user_id': state.get('session_id', 'guest'),
            'user_info': {'role': 'guest'},
            'retry_count': 0,
        }
        result = statutory_agent_node(adapted)
        return {
            'messages': result.get('messages', []),
            'next': 'end',
            'user_intent': state.get('user_intent', ''),
            'session_id': state.get('session_id', 'guest'),
        }

    def guest_caselaw_node(state: GuestLegalState):
        from src.agents.orchestrator import AgentState
        adapted: AgentState = {
            'messages': state['messages'],
            'next': '',
            'user_intent': state.get('user_intent', ''),
            'user_id': state.get('session_id', 'guest'),
            'user_info': {'role': 'guest'},
            'retry_count': 0,
        }
        result = caselaw_agent_node(adapted)
        return {
            'messages': result.get('messages', []),
            'next': 'end',
            'user_intent': state.get('user_intent', ''),
            'session_id': state.get('session_id', 'guest'),
        }

    workflow.add_node('guest_orchestrator', guest_orchestrator_node)
    workflow.add_node('statutory_agent', guest_statutory_node)
    workflow.add_node('caselaw_agent', guest_caselaw_node)
    workflow.add_node('statutory_tools', ToolNode([search_statutory_law]))
    workflow.add_node('caselaw_tools', ToolNode([search_case_law, search_statutory_law]))

    workflow.set_entry_point('guest_orchestrator')
    workflow.add_conditional_edges(
        'guest_orchestrator',
        guest_router,
        {'statutory_agent': 'statutory_agent', 'caselaw_agent': 'caselaw_agent'},
    )

    def route_statutory(state):
        msgs = state.get('messages', [])
        if msgs and hasattr(msgs[-1], 'tool_calls') and msgs[-1].tool_calls:
            return 'statutory_tools'
        return 'end'

    def route_caselaw(state):
        msgs = state.get('messages', [])
        if msgs and hasattr(msgs[-1], 'tool_calls') and msgs[-1].tool_calls:
            return 'caselaw_tools'
        return 'end'

    workflow.add_conditional_edges(
        'statutory_agent', route_statutory, {'statutory_tools': 'statutory_tools', 'end': END}
    )
    workflow.add_edge('statutory_tools', 'statutory_agent')
    workflow.add_conditional_edges(
        'caselaw_agent', route_caselaw, {'caselaw_tools': 'caselaw_tools', 'end': END}
    )
    workflow.add_edge('caselaw_tools', 'caselaw_agent')

    return workflow.compile()