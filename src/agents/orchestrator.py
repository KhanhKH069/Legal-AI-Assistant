import logging
import operator
from typing import Annotated, Literal, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel

from src.core.llm import get_llm
from src.tools.legal_tools import search_case_law, search_statutory_law

logger = logging.getLogger(__name__)

_VALID_AGENTS = {'STATUTORY': 'statutory_agent', 'CASELAW': 'caselaw_agent'}
_MAX_ROUTING_RETRIES = 2

llm = get_llm()


class IntentRouting(BaseModel):
    """Phân loại ý định câu hỏi pháp lý."""
    intent: Literal['STATUTORY', 'CASELAW']


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str
    user_intent: str
    user_id: str
    user_info: dict
    retry_count: int


_ORCHESTRATOR_PROMPT = (
    'Bạn là bộ phân loại ý định cho hệ thống **Legal AI Assistant** — Trợ lý Pháp lý AI Việt Nam.\n\n'
    'Nhiệm vụ của bạn là đọc câu hỏi của người dùng và phân loại vào đúng một trong hai nhóm:\n\n'
    '**STATUTORY** — Câu hỏi về quy định pháp luật, điều luật, văn bản quy phạm pháp luật\n'
    'Ví dụ:\n'
    '- "Luật doanh nghiệp quy định vốn điều lệ tối thiểu là bao nhiêu?"\n'
    '- "Điều kiện để ly hôn theo pháp luật Việt Nam?"\n'
    '- "Mức xử phạt vi phạm giao thông vượt đèn đỏ?"\n'
    '- "Quyền lợi của người lao động khi bị sa thải trái luật?"\n'
    '- "Thủ tục đăng ký kết hôn theo quy định?"\n\n'
    '**CASELAW** — Câu hỏi về án lệ, vụ kiện, tranh chấp cụ thể, cách Tòa xử lý tình huống\n'
    'Ví dụ:\n'
    '- "Tòa án thường xử tranh chấp đất đai không có sổ đỏ như thế nào?"\n'
    '- "Có án lệ nào về tranh chấp hợp đồng mua bán nhà không?"\n'
    '- "Trong vụ kiện chia tài sản ly hôn, Tòa xét tới những yếu tố gì?"\n'
    '- "Tiền lệ về bồi thường tai nạn lao động?"\n'
    '- "Án lệ về hành vi lừa đảo chiếm đoạt tài sản?"\n\n'
    '**Quy tắc phân loại:**\n'
    '- Nếu câu hỏi hỏi về QUY ĐỊNH, ĐIỀU LUẬT, VĂN BẢN PHÁP LÝ → STATUTORY\n'
    '- Nếu câu hỏi hỏi về VỤ ÁN, TRANH CHẤP, CÁCH TÒA XỬ → CASELAW\n'
    '- Khi không chắc chắn, mặc định → STATUTORY'
)


def create_orchestrator():
    prompt = ChatPromptTemplate.from_messages([
        ('system', _ORCHESTRATOR_PROMPT),
        MessagesPlaceholder(variable_name='messages'),
    ])
    structured_llm = llm.with_structured_output(IntentRouting)
    return prompt | structured_llm


def orchestrator_node(state: AgentState):
    orchestrator = create_orchestrator()
    next_agent = 'statutory_agent'
    intent_str = 'STATUTORY'

    for attempt in range(1, _MAX_ROUTING_RETRIES + 1):
        try:
            result: IntentRouting = orchestrator.invoke({'messages': state['messages']})
            intent_str = result.intent
            next_agent = _VALID_AGENTS.get(intent_str, 'statutory_agent')
            break
        except Exception as e:
            logger.warning('Orchestrator attempt %d failed: %s', attempt, e)
            if attempt == _MAX_ROUTING_RETRIES:
                logger.error('Orchestrator failed after %d retries, defaulting to statutory_agent', _MAX_ROUTING_RETRIES)

    logger.info('Legal Orchestrator → %s (intent: %s)', next_agent, intent_str)
    return {
        'messages': state['messages'],
        'next': next_agent,
        'user_intent': intent_str,
        'user_id': state.get('user_id', ''),
        'user_info': state.get('user_info', {}),
        'retry_count': 0,
    }


def router(state: AgentState) -> str:
    next_step = state.get('next', 'statutory_agent')
    valid_nodes = set(_VALID_AGENTS.values()) | {'end'}
    return next_step if next_step in valid_nodes else 'statutory_agent'


def create_legal_agent_graph():
    from src.agents.caselaw_agent import caselaw_agent_node
    from src.agents.reviewer_agent import reviewer_node
    from src.agents.statutory_agent import statutory_agent_node

    workflow = StateGraph(AgentState)
    workflow.add_node('orchestrator', orchestrator_node)
    workflow.add_node('statutory_agent', statutory_agent_node)
    workflow.add_node('caselaw_agent', caselaw_agent_node)
    workflow.add_node('reviewer_node', reviewer_node)

    statutory_tools_list = [search_statutory_law]
    caselaw_tools_list = [search_case_law, search_statutory_law]
    workflow.add_node('statutory_tools', ToolNode(statutory_tools_list))
    workflow.add_node('caselaw_tools', ToolNode(caselaw_tools_list))

    workflow.set_entry_point('orchestrator')
    workflow.add_conditional_edges(
        'orchestrator',
        router,
        {'statutory_agent': 'statutory_agent', 'caselaw_agent': 'caselaw_agent', 'end': END},
    )

    def route_statutory(state: AgentState) -> str:
        messages = state.get('messages', [])
        if not messages:
            return 'reviewer_node'
        last = messages[-1]
        if hasattr(last, 'tool_calls') and last.tool_calls:
            return 'statutory_tools'
        return 'reviewer_node'

    def route_reviewer(state: AgentState) -> str:
        if state.get('next') == 'fail':
            return 'statutory_agent'
        return 'end'

    workflow.add_conditional_edges(
        'statutory_agent',
        route_statutory,
        {'statutory_tools': 'statutory_tools', 'reviewer_node': 'reviewer_node'},
    )
    workflow.add_edge('statutory_tools', 'statutory_agent')
    workflow.add_conditional_edges(
        'reviewer_node',
        route_reviewer,
        {'statutory_agent': 'statutory_agent', 'end': END},
    )

    def route_caselaw(state: AgentState) -> str:
        messages = state.get('messages', [])
        if not messages:
            return 'end'
        last = messages[-1]
        if hasattr(last, 'tool_calls') and last.tool_calls:
            return 'caselaw_tools'
        return 'end'

    workflow.add_conditional_edges(
        'caselaw_agent',
        route_caselaw,
        {'caselaw_tools': 'caselaw_tools', 'end': END},
    )
    workflow.add_edge('caselaw_tools', 'caselaw_agent')

    try:
        from langgraph.checkpoint.redis import RedisSaver
        import redis
        import os
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        pool = redis.ConnectionPool.from_url(redis_url)
        conn = redis.Redis(connection_pool=pool)
        memory = RedisSaver(conn)
        return workflow.compile(checkpointer=memory)
    except Exception as e:
        logger.warning('Redis unavailable (%s) — using MemorySaver for checkpointing', e)
        from langgraph.checkpoint.memory import MemorySaver
        return workflow.compile(checkpointer=MemorySaver())