"""Legal Orchestrator — Router cho Legal AI Assistant

Phân loại ý định người dùng và định tuyến đến Agent phù hợp:
  - STATUTORY : Câu hỏi về điều luật, quy định pháp lý → statutory_agent
  - CASELAW   : Câu hỏi về án lệ, vụ án, tranh chấp cụ thể → caselaw_agent
"""

import logging
import operator
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from src.core.config import config
from src.tools.legal_tools import search_statutory_law, search_case_law

logger = logging.getLogger(__name__)

_VALID_AGENTS = {
    "STATUTORY": "statutory_agent",
    "CASELAW": "caselaw_agent",
}
_MAX_ROUTING_RETRIES = 2

llm = None
if config.enable_offline_mode or not config.google_api_key:
    from langchain_ollama import ChatOllama

    llm = ChatOllama(
        model="qwen2.5:7b-instruct", temperature=0.0, base_url="http://localhost:11434"
    )
else:
    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        google_api_key=config.google_api_key,
        temperature=0.0,
        max_tokens=config.max_tokens,
    )


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str
    user_intent: str
    user_id: str
    user_info: dict


_ORCHESTRATOR_PROMPT = """Bạn là bộ phân loại ý định cho hệ thống **Legal AI Assistant** — Trợ lý Pháp lý AI Việt Nam.

Nhiệm vụ của bạn là đọc câu hỏi của người dùng và trả về ĐÚNG MỘT từ khóa sau:

**STATUTORY** — Câu hỏi về quy định pháp luật, điều luật, văn bản quy phạm pháp luật
Ví dụ:
- "Luật doanh nghiệp quy định vốn điều lệ tối thiểu là bao nhiêu?"
- "Điều kiện để ly hôn theo pháp luật Việt Nam?"
- "Mức xử phạt vi phạm giao thông vượt đèn đỏ?"
- "Quyền lợi của người lao động khi bị sa thải trái luật?"
- "Thủ tục đăng ký kết hôn theo quy định?"

**CASELAW** — Câu hỏi về án lệ, vụ kiện, tranh chấp cụ thể, cách Tòa xử lý tình huống
Ví dụ:
- "Tòa án thường xử tranh chấp đất đai không có sổ đỏ như thế nào?"
- "Có án lệ nào về tranh chấp hợp đồng mua bán nhà không?"
- "Trong vụ kiện chia tài sản ly hôn, Tòa xét tới những yếu tố gì?"
- "Tiền lệ về bồi thường tai nạn lao động?"
- "Án lệ về hành vi lừa đảo chiếm đoạt tài sản?"

**Quy tắc phân loại:**
- Nếu câu hỏi hỏi về QUY ĐỊNH, ĐIỀU LUẬT, VĂN BẢN PHÁP LÝ → STATUTORY
- Nếu câu hỏi hỏi về VỤ ÁN, TRANH CHẤP, CÁCH TÒA XỬ → CASELAW
- Khi không chắc chắn, mặc định → STATUTORY

Chỉ trả về đúng một từ: STATUTORY hoặc CASELAW. Không giải thích, không thêm gì khác."""


def create_orchestrator():
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _ORCHESTRATOR_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    return prompt | llm | StrOutputParser()


def _classify_intent(response_text: str) -> str:
    upper = response_text.strip().upper()
    for keyword, agent_key in _VALID_AGENTS.items():
        if keyword == upper:
            return agent_key
    for keyword, agent_key in _VALID_AGENTS.items():
        if keyword in upper:
            return agent_key
    return "statutory_agent"  # Default fallback for legal domain


def orchestrator_node(state: AgentState):
    """Route user message to STATUTORY or CASELAW agent."""
    orchestrator = create_orchestrator()
    next_agent = "statutory_agent"
    response_clean = ""

    for attempt in range(1, _MAX_ROUTING_RETRIES + 1):
        response = orchestrator.invoke({"messages": state["messages"]})
        response_clean = response.strip().upper()
        next_agent = _classify_intent(response_clean)
        if next_agent != "end":
            break
        logger.warning(
            "Orchestrator attempt %d: unrecognised intent '%s'", attempt, response_clean
        )

    logger.info("Legal Orchestrator → %s (intent: %s)", next_agent, response_clean)

    return {
        "messages": state["messages"],
        "next": next_agent,
        "user_intent": response_clean,
        "user_id": state.get("user_id", ""),
        "user_info": state.get("user_info", {}),
    }


def router(state: AgentState) -> str:
    next_step = state.get("next", "statutory_agent")
    valid_nodes = set(_VALID_AGENTS.values()) | {"end"}
    return next_step if next_step in valid_nodes else "statutory_agent"


def create_legal_agent_graph():
    """Create Legal AI Agent Graph with LangGraph — 2 Specialist Agents."""
    from src.agents.statutory_agent import statutory_agent_node
    from src.agents.caselaw_agent import caselaw_agent_node
    from src.agents.reviewer_agent import reviewer_node

    workflow = StateGraph(AgentState)

    # Nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("statutory_agent", statutory_agent_node)
    workflow.add_node("caselaw_agent", caselaw_agent_node)
    workflow.add_node("reviewer_node", reviewer_node)

    # Tool nodes
    statutory_tools_list = [search_statutory_law]
    caselaw_tools_list = [search_case_law, search_statutory_law]

    workflow.add_node("statutory_tools", ToolNode(statutory_tools_list))
    workflow.add_node("caselaw_tools", ToolNode(caselaw_tools_list))

    # Entry
    workflow.set_entry_point("orchestrator")

    # Orchestrator routing
    workflow.add_conditional_edges(
        "orchestrator",
        router,
        {
            "statutory_agent": "statutory_agent",
            "caselaw_agent": "caselaw_agent",
            "end": END,
        },
    )

    # Statutory agent routing: tool calls → statutory_tools → reviewer
    def route_statutory(state: AgentState) -> str:
        messages = state.get("messages", [])
        if not messages:
            return "reviewer_node"
        last = messages[-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "statutory_tools"
        return "reviewer_node"

    def route_reviewer(state: AgentState) -> str:
        if state.get("next") == "fail":
            return "statutory_agent"
        return "end"

    workflow.add_conditional_edges(
        "statutory_agent",
        route_statutory,
        {"statutory_tools": "statutory_tools", "reviewer_node": "reviewer_node"},
    )
    workflow.add_edge("statutory_tools", "statutory_agent")

    workflow.add_conditional_edges(
        "reviewer_node",
        route_reviewer,
        {"statutory_agent": "statutory_agent", "end": END},
    )

    # Caselaw agent routing: tool calls → caselaw_tools → end
    def route_caselaw(state: AgentState) -> str:
        messages = state.get("messages", [])
        if not messages:
            return "end"
        last = messages[-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "caselaw_tools"
        return "end"

    workflow.add_conditional_edges(
        "caselaw_agent",
        route_caselaw,
        {"caselaw_tools": "caselaw_tools", "end": END},
    )
    workflow.add_edge("caselaw_tools", "caselaw_agent")

    # Checkpointer
    try:
        from langgraph.checkpoint.redis import RedisSaver
        import redis
        import os

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        pool = redis.ConnectionPool.from_url(redis_url)
        conn = redis.Redis(connection_pool=pool)
        memory = RedisSaver(conn)
        return workflow.compile(checkpointer=memory)
    except Exception as e:
        logger.warning(
            "Redis unavailable (%s) — using MemorySaver for checkpointing", e
        )
        from langgraph.checkpoint.memory import MemorySaver

        return workflow.compile(checkpointer=MemorySaver())
