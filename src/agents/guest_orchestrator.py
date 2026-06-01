"""Guest Orchestrator — Legal AI cho người dùng vãng lai (không đăng nhập)

Người dùng vãng lai được tra cứu pháp luật tự do nhưng không có
quyền truy cập các tính năng yêu cầu tài khoản (lịch sử vụ án,
tư vấn có lưu trữ...).
"""

import logging
import operator
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from src.core.config import config
from src.tools.legal_tools import search_statutory_law, search_case_law
from src.agents.statutory_agent import statutory_agent_node
from src.agents.caselaw_agent import caselaw_agent_node

logger = logging.getLogger(__name__)

llm = None
if config.enable_offline_mode or not config.google_api_key:
    from langchain_ollama import ChatOllama

    llm = ChatOllama(
        model="qwen2.5:7b-instruct",
        temperature=0.0,
        base_url="http://localhost:11434"
    )
else:
    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        google_api_key=config.google_api_key,
        temperature=0.0,
        max_tokens=config.max_tokens,
    )


class GuestLegalState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str
    user_intent: str
    session_id: str


_GUEST_ORCHESTRATOR_PROMPT = """Bạn là bộ phân loại ý định cho Legal AI Assistant dành cho người dùng vãng lai.

Phân loại câu hỏi vào một trong hai nhóm:

**STATUTORY** — Tra cứu quy định pháp luật, điều luật, văn bản pháp quy
**CASELAW** — Tra cứu án lệ, bản án, cách Tòa giải quyết tranh chấp

Chỉ trả về đúng 1 từ: STATUTORY hoặc CASELAW"""


def create_guest_orchestrator():
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _GUEST_ORCHESTRATOR_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    return prompt | llm | StrOutputParser()


def guest_orchestrator_node(state: GuestLegalState):
    orchestrator = create_guest_orchestrator()
    response = orchestrator.invoke({"messages": state["messages"]})
    upper = response.strip().upper()
    next_agent = "caselaw_agent" if "CASELAW" in upper else "statutory_agent"
    return {
        "messages": state["messages"],
        "next": next_agent,
        "user_intent": upper,
        "session_id": state.get("session_id", "guest"),
    }


def guest_router(state: GuestLegalState) -> str:
    return state.get("next", "statutory_agent")


def create_guest_agent_graph():
    """Create a Legal AI graph for unauthenticated (guest) users."""
    if llm is None:
        return None

    workflow = StateGraph(GuestLegalState)

    # Wrap statutory_agent_node for GuestLegalState
    def guest_statutory_node(state: GuestLegalState):
        from src.agents.orchestrator import AgentState
        adapted: AgentState = {
            "messages": state["messages"],
            "next": "",
            "user_intent": state.get("user_intent", ""),
            "user_id": state.get("session_id", "guest"),
            "user_info": {"role": "guest"},
        }
        result = statutory_agent_node(adapted)
        return {
            "messages": result.get("messages", []),
            "next": "end",
            "user_intent": state.get("user_intent", ""),
            "session_id": state.get("session_id", "guest"),
        }

    # Wrap caselaw_agent_node for GuestLegalState
    def guest_caselaw_node(state: GuestLegalState):
        from src.agents.orchestrator import AgentState
        adapted: AgentState = {
            "messages": state["messages"],
            "next": "",
            "user_intent": state.get("user_intent", ""),
            "user_id": state.get("session_id", "guest"),
            "user_info": {"role": "guest"},
        }
        result = caselaw_agent_node(adapted)
        return {
            "messages": result.get("messages", []),
            "next": "end",
            "user_intent": state.get("user_intent", ""),
            "session_id": state.get("session_id", "guest"),
        }

    workflow.add_node("guest_orchestrator", guest_orchestrator_node)
    workflow.add_node("statutory_agent", guest_statutory_node)
    workflow.add_node("caselaw_agent", guest_caselaw_node)
    workflow.add_node("statutory_tools", ToolNode([search_statutory_law]))
    workflow.add_node("caselaw_tools", ToolNode([search_case_law, search_statutory_law]))

    workflow.set_entry_point("guest_orchestrator")

    workflow.add_conditional_edges(
        "guest_orchestrator",
        guest_router,
        {
            "statutory_agent": "statutory_agent",
            "caselaw_agent": "caselaw_agent",
        },
    )

    def route_statutory(state):
        msgs = state.get("messages", [])
        if msgs and hasattr(msgs[-1], "tool_calls") and msgs[-1].tool_calls:
            return "statutory_tools"
        return "end"

    def route_caselaw(state):
        msgs = state.get("messages", [])
        if msgs and hasattr(msgs[-1], "tool_calls") and msgs[-1].tool_calls:
            return "caselaw_tools"
        return "end"

    workflow.add_conditional_edges(
        "statutory_agent", route_statutory,
        {"statutory_tools": "statutory_tools", "end": END},
    )
    workflow.add_edge("statutory_tools", "statutory_agent")

    workflow.add_conditional_edges(
        "caselaw_agent", route_caselaw,
        {"caselaw_tools": "caselaw_tools", "end": END},
    )
    workflow.add_edge("caselaw_tools", "caselaw_agent")

    return workflow.compile()
