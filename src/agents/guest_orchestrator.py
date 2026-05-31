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
from src.core.prompt_loader import get_prompt
from src.agents.cv_agent import cv_agent_node
from src.tools.cv_tools import (
    screen_cv_for_position,
    get_recruitment_pipeline,
    get_hiring_stats,
    get_job_requirements,
)

logger = logging.getLogger(__name__)

llm = None
if not config.enable_offline_mode and config.google_api_key:
    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        google_api_key=config.google_api_key,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


class GuestState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str
    user_intent: str
    session_id: str


def create_guest_orchestrator():
    """Orchestrator for guest/applicant users (recruitment queries only)."""
    system_prompt = get_prompt("guest_orchestrator")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    return prompt | llm | StrOutputParser()


def guest_orchestrator_node(state: GuestState):
    """Route guest queries — only to RECRUITMENT or END."""
    orchestrator = create_guest_orchestrator()
    response = orchestrator.invoke({"messages": state["messages"]})
    upper = response.strip().upper()
    next_agent = "recruitment_agent" if "RECRUITMENT" in upper else "end"
    return {
        "messages": state["messages"],
        "next": next_agent,
        "user_intent": upper,
        "session_id": state.get("session_id", "guest"),
    }


def guest_router(state: GuestState) -> str:
    return state.get("next", "end")


def create_guest_agent_graph():
    """Create a limited LangGraph for guest/applicant users.

    Only the Recruitment / CV agent is available.  No personal employee
    data tools (salary, leave balance, attendance…) are included.
    """
    if llm is None:
        # Offline mode — return None; api/main.py will handle with offline_agent
        return None

    workflow = StateGraph(GuestState)

    # --- Nodes ---
    workflow.add_node("guest_orchestrator", guest_orchestrator_node)

    # Wrap cv_agent_node to use GuestState keys
    def recruitment_agent_node(state: GuestState):
        """Wrap cv_agent_node to adapt GuestState → AgentState signature."""
        from src.agents.orchestrator import AgentState

        adapted_state: AgentState = {
            "messages": state["messages"],
            "next": "",
            "user_intent": state.get("user_intent", ""),
            "user_id": state.get("session_id", "guest"),
            "user_info": {"role": "guest"},
        }
        result = cv_agent_node(adapted_state)
        return {
            "messages": result.get("messages", []),
            "next": "end",
            "user_intent": state.get("user_intent", ""),
            "session_id": state.get("session_id", "guest"),
        }

    workflow.add_node("recruitment_agent", recruitment_agent_node)

    guest_recruitment_tools = [
        screen_cv_for_position,
        get_recruitment_pipeline,
        get_hiring_stats,
        get_job_requirements,
    ]
    workflow.add_node("guest_recruitment_tools", ToolNode(guest_recruitment_tools))

    # --- Edges ---
    workflow.set_entry_point("guest_orchestrator")

    workflow.add_conditional_edges(
        "guest_orchestrator",
        guest_router,
        {
            "recruitment_agent": "recruitment_agent",
            "end": END,
        },
    )

    def route_recruitment(state: GuestState) -> str:
        messages = state.get("messages", [])
        if not messages:
            return "end"
        last_msg = messages[-1]
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            return "guest_recruitment_tools"
        return "end"

    workflow.add_conditional_edges(
        "recruitment_agent",
        route_recruitment,
        {
            "guest_recruitment_tools": "guest_recruitment_tools",
            "end": END,
        },
    )
    workflow.add_edge("guest_recruitment_tools", "recruitment_agent")

    # No checkpointer needed for stateless guest sessions
    return workflow.compile()
