"""Orchestrator Agent - Gemini Version

Routes incoming user messages to the correct specialized agent using
a Gemini LLM classifier.  Includes retry logic for ambiguous responses.
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

logger = logging.getLogger(__name__)

_VALID_AGENTS = {
    "POLICY": "policy_agent",
    "ONBOARD": "onboard_agent",
    "CV": "cv_agent",
    "ANALYTICS": "analytics_agent",
    "ATTENDANCE": "attendance_agent",
    "HELPDESK": "helpdesk_agent",
    "BENEFITS": "benefits_agent",
    "APPRAISAL": "appraisal_agent",
}
_MAX_ROUTING_RETRIES = 2

from src.agents.cv_agent import cv_agent_node
from src.agents.onboard_agent import onboard_agent_node
from src.agents.policy_agent import policy_agent_node
from src.agents.analytics_agent import query_hr_data
from src.agents.attendance_agent import attendance_agent_node
from src.agents.helpdesk_agent import helpdesk_agent_node
from src.agents.benefits_agent import benefits_agent_node
from src.core.config import config
from src.tools.cv_tools import screen_cv_for_position
from src.tools.onboard_tools import get_onboarding_checklist
from src.tools.onboard_validation_tools import verify_onboarding_document
from src.tools.document_tools import (
    list_employee_documents,
    sign_document,
    get_document_template,
    check_expiring_contracts,
)
from src.tools.policy_tools import calculate_leave_days, get_policy_info, search_hr_qa
from src.tools.employee_data_tools import (
    get_employee_profile,
    get_leave_balance,
    get_salary_info,
)
from src.tools.math_tools import calculate_math_expression
from src.tools.attendance_tools import (
    get_attendance_record,
    submit_leave_request,
    get_leave_requests,
)
from src.tools.helpdesk_tools import (
    create_hr_ticket,
    get_ticket_status,
    list_employee_tickets,
)
from src.tools.benefits_tools import (
    get_employee_benefits,
    get_benefits_catalog,
    request_benefit_change,
)
from src.tools.recruitment_tools import (
    get_recruitment_pipeline,
    create_interview_schedule,
    get_hiring_stats,
    convert_applicant_to_employee,
)
from src.tools.notification_tools import (
    get_employee_notifications,
)
from src.tools.payroll_tools import (
    get_payroll_record,
    get_payroll_history,
    calculate_vn_income_tax,
    calculate_leave_accrual,
)
from src.tools.appraisal_tools import appraisal_tools
from src.tools.skills_tools import skills_tools


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str
    user_intent: str
    user_id: str
    user_info: dict


# Initialize Gemini LLM (only if online mode with API key)
llm = None
if not config.enable_offline_mode and config.google_api_key:
    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        google_api_key=config.google_api_key,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


from src.core.prompt_loader import get_prompt


def create_orchestrator():
    """Create orchestrator agent"""
    system_prompt = get_prompt("orchestrator")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    return prompt | llm | StrOutputParser()


def _classify_intent(response_text: str) -> str:
    """Map the raw LLM classifier output to an internal agent key."""
    upper = response_text.strip().upper()

    # Check exact match first
    for keyword, agent_key in _VALID_AGENTS.items():
        if keyword == upper:
            return agent_key

    # Fallback to substring
    for keyword, agent_key in _VALID_AGENTS.items():
        if keyword in upper:
            return agent_key

    return "end"


def orchestrator_node(state: AgentState):
    """Orchestrator node — routes the user's message to the correct agent.

    Retries up to *_MAX_ROUTING_RETRIES* times when the LLM returns an
    unrecognised intent so that transient model quirks don't silently
    drop the request.
    """
    orchestrator = create_orchestrator()
    next_agent = "end"
    response_clean = ""

    for attempt in range(1, _MAX_ROUTING_RETRIES + 1):
        response = orchestrator.invoke({"messages": state["messages"]})
        response_clean = response.strip().upper()
        next_agent = _classify_intent(response_clean)
        if next_agent != "end":
            break
        logger.warning(
            "Orchestrator attempt %d/%d: unrecognised intent '%s'",
            attempt,
            _MAX_ROUTING_RETRIES,
            response_clean,
        )

    if next_agent == "end":
        logger.error(
            "Orchestrator could not classify intent after %d attempts — routing to END.",
            _MAX_ROUTING_RETRIES,
        )

    return {
        "messages": state["messages"],
        "next": next_agent,
        "user_intent": response_clean,
        "user_id": state.get("user_id", ""),
        "user_info": state.get("user_info", {}),
    }


def router(state: AgentState) -> str:
    """Conditional edge function — returns the name of the next node.

    Used by LangGraph's ``add_conditional_edges`` to dispatch the state
    to the correct agent node after orchestration.
    """
    next_step = state.get("next", "end")
    # All valid agent keys are in _VALID_AGENTS values; pass through directly.
    valid_nodes = set(_VALID_AGENTS.values()) | {"end"}
    return next_step if next_step in valid_nodes else "end"


def create_hr_agent_graph():
    """Create HR Agent Graph with LangGraph — 7 Agents"""
    workflow = StateGraph(AgentState)

    # Add nodes — original 4
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("policy_agent", policy_agent_node)
    workflow.add_node("onboard_agent", onboard_agent_node)
    workflow.add_node("cv_agent", cv_agent_node)

    # Node for Analytics (wraps its own Pandas agent)
    def analytics_agent_node(state):
        last_msg = state["messages"][-1].content
        answer = query_hr_data(last_msg)
        from langchain_core.messages import AIMessage

        return {
            "messages": [AIMessage(content=answer)],
            "next": "end",
            "user_intent": state.get("user_intent", ""),
            "user_id": state.get("user_id", ""),
            "user_info": state.get("user_info", {}),
        }

    workflow.add_node("analytics_agent", analytics_agent_node)

    # New agents — Odoo modules
    workflow.add_node("attendance_agent", attendance_agent_node)
    workflow.add_node("helpdesk_agent", helpdesk_agent_node)
    workflow.add_node("benefits_agent", benefits_agent_node)

    # Appraisal + Skills agent (Phase 2)
    if llm is not None:
        from src.agents.appraisal_agent import appraisal_agent_node

        workflow.add_node("appraisal_agent", appraisal_agent_node)
    else:

        def _appraisal_fallback(state):
            from langchain_core.messages import AIMessage

            return {
                "messages": [
                    AIMessage(content="Appraisal Agent not available in offline mode.")
                ],
                "next": "end",
                "user_intent": state.get("user_intent", ""),
                "user_id": state.get("user_id", ""),
                "user_info": state.get("user_info", {}),
            }

        workflow.add_node("appraisal_agent", _appraisal_fallback)

    # Tool nodes — original
    policy_tools = [
        get_policy_info,
        calculate_leave_days,
        search_hr_qa,
        get_employee_profile,
        get_leave_balance,
        get_salary_info,
        calculate_math_expression,
        get_payroll_record,
        get_payroll_history,
        calculate_vn_income_tax,
        calculate_leave_accrual,
    ]

    # Tool nodes — new Odoo modules
    attendance_safe_tools = [get_attendance_record, get_leave_requests]
    attendance_sensitive_tools = [submit_leave_request]
    helpdesk_tools = [create_hr_ticket, get_ticket_status, list_employee_tickets]
    benefits_tools_list = [
        get_employee_benefits,
        get_benefits_catalog,
        request_benefit_change,
    ]
    cv_tools_extended = [
        screen_cv_for_position,
        get_recruitment_pipeline,
        create_interview_schedule,
        get_hiring_stats,
        convert_applicant_to_employee,
        get_employee_notifications,
    ]
    onboard_tools_extended = [
        get_onboarding_checklist,
        search_hr_qa,
        verify_onboarding_document,
        list_employee_documents,
        sign_document,
        get_document_template,
        check_expiring_contracts,
    ]

    workflow.add_node("policy_tools", ToolNode(policy_tools))
    workflow.add_node("onboard_tools", ToolNode(onboard_tools_extended))
    workflow.add_node("cv_tools", ToolNode(cv_tools_extended))
    workflow.add_node("attendance_safe_tools", ToolNode(attendance_safe_tools))
    workflow.add_node(
        "attendance_sensitive_tools", ToolNode(attendance_sensitive_tools)
    )
    workflow.add_node("helpdesk_tools", ToolNode(helpdesk_tools))
    workflow.add_node("benefits_tools", ToolNode(benefits_tools_list))
    workflow.add_node("appraisal_tools", ToolNode(appraisal_tools + skills_tools))

    # Set entry point
    workflow.set_entry_point("orchestrator")

    # Conditional edges from orchestrator → agents
    workflow.add_conditional_edges(
        "orchestrator",
        router,
        {
            "policy_agent": "policy_agent",
            "onboard_agent": "onboard_agent",
            "cv_agent": "cv_agent",
            "analytics_agent": "analytics_agent",
            "attendance_agent": "attendance_agent",
            "helpdesk_agent": "helpdesk_agent",
            "benefits_agent": "benefits_agent",
            "appraisal_agent": "appraisal_agent",
            "end": END,
        },
    )

    from src.agents.reviewer_agent import reviewer_node

    workflow.add_node("reviewer_node", reviewer_node)

    # Debate routing for policy_agent
    def route_policy(state: AgentState) -> str:
        messages = state.get("messages", [])
        if not messages:
            return "end"
        last_msg = messages[-1]
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            return "policy_tools"
        return "reviewer_node"

    def route_reviewer(state: AgentState) -> str:
        if state.get("next") == "fail":
            return "policy_agent"
        return "end"

    workflow.add_conditional_edges(
        "policy_agent",
        route_policy,
        {"policy_tools": "policy_tools", "reviewer_node": "reviewer_node", "end": END},
    )
    workflow.add_edge("policy_tools", "policy_agent")

    workflow.add_conditional_edges(
        "reviewer_node", route_reviewer, {"policy_agent": "policy_agent", "end": END}
    )

    def route_onboard(state: AgentState) -> str:
        messages = state.get("messages", [])
        if not messages:
            return "end"
        if hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls:
            return "onboard_tools"
        return "end"

    workflow.add_conditional_edges(
        "onboard_agent", route_onboard, {"onboard_tools": "onboard_tools", "end": END}
    )
    workflow.add_edge("onboard_tools", "onboard_agent")

    def route_cv(state: AgentState) -> str:
        messages = state.get("messages", [])
        if not messages:
            return "end"
        last_msg = messages[-1]
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            return "cv_tools"
        return "end"

    workflow.add_conditional_edges(
        "cv_agent", route_cv, {"cv_tools": "cv_tools", "end": END}
    )
    workflow.add_edge("cv_tools", "cv_agent")
    workflow.add_edge("analytics_agent", END)

    # Conditional routing for attendance agent
    def route_attendance_tools(state: AgentState) -> str:
        messages = state.get("messages", [])
        if not messages:
            return "end"
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            for call in last_message.tool_calls:
                if call["name"] == "submit_leave_request":
                    return "attendance_sensitive_tools"
            return "attendance_safe_tools"
        return "end"

    workflow.add_conditional_edges(
        "attendance_agent",
        route_attendance_tools,
        {
            "attendance_safe_tools": "attendance_safe_tools",
            "attendance_sensitive_tools": "attendance_sensitive_tools",
            "end": END,
        },
    )
    workflow.add_edge("attendance_safe_tools", END)
    workflow.add_edge("attendance_sensitive_tools", END)

    def route_helpdesk(state: AgentState) -> str:
        messages = state.get("messages", [])
        if not messages:
            return "end"
        if hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls:
            return "helpdesk_tools"
        return "end"

    workflow.add_conditional_edges(
        "helpdesk_agent",
        route_helpdesk,
        {"helpdesk_tools": "helpdesk_tools", "end": END},
    )
    workflow.add_edge("helpdesk_tools", "helpdesk_agent")

    def route_benefits(state: AgentState) -> str:
        messages = state.get("messages", [])
        if not messages:
            return "end"
        if hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls:
            return "benefits_tools"
        return "end"

    workflow.add_conditional_edges(
        "benefits_agent",
        route_benefits,
        {"benefits_tools": "benefits_tools", "end": END},
    )
    workflow.add_edge("benefits_tools", "benefits_agent")

    def route_appraisal(state: AgentState) -> str:
        messages = state.get("messages", [])
        if not messages:
            return "end"
        if hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls:
            return "appraisal_tools"
        return "end"

    workflow.add_conditional_edges(
        "appraisal_agent",
        route_appraisal,
        {"appraisal_tools": "appraisal_tools", "end": END},
    )
    workflow.add_edge("appraisal_tools", "appraisal_agent")

    # Setup Checkpointer for LangGraph State Memory
    from langgraph.checkpoint.redis import RedisSaver
    import redis
    import os

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    pool = redis.ConnectionPool.from_url(redis_url)
    conn = redis.Redis(connection_pool=pool)
    memory = RedisSaver(conn)

    return workflow.compile(
        checkpointer=memory, interrupt_before=["attendance_sensitive_tools"]
    )
