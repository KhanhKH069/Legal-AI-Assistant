"""Orchestrator Agent - Gemini Version"""

import operator
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

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
)
from src.tools.notification_tools import (
    get_employee_notifications,
)
from src.tools.payroll_tools import (
    get_payroll_record,
    get_payroll_history,
)


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


def create_orchestrator():
    """Create orchestrator agent"""
    system_prompt = """You are HR Orchestrator Agent. Analyze user intent and route to the appropriate agent.

Available agents:
- POLICY_AGENT: For HR policy questions (leave balance, salary, working hours, general HR policies)
- ONBOARD_AGENT: For onboarding (new employee checklist, CCCD/document verification, e-signature, signing contracts, document status)
- CV_AGENT: For CV screening, candidate scoring, recruitment pipeline stages, interview scheduling, hiring statistics
- ANALYTICS_AGENT: For HR data analysis, charts, department statistics, headcount, turnover rates from CSV data
- ATTENDANCE_AGENT: For attendance records, check-in/out times, OT hours, submitting/viewing leave requests (nghỉ phép)
- HELPDESK_AGENT: For creating/tracking HR support tickets (equipment, payroll issues, benefit changes, complaints)
- BENEFITS_AGENT: For employee benefits, insurance packages, meal/transport allowances, training budget, benefit changes

Respond with ONLY ONE WORD from: POLICY_AGENT, ONBOARD_AGENT, CV_AGENT, ANALYTICS_AGENT, ATTENDANCE_AGENT, HELPDESK_AGENT, BENEFITS_AGENT, or END

Examples:
- "How many leave days do I have?" → POLICY_AGENT
- "Onboarding checklist?" → ONBOARD_AGENT
- "Ký hợp đồng lao động" → ONBOARD_AGENT
- "Tài liệu nào chưa ký?" → ONBOARD_AGENT
- "Đánh giá CV này cho vị trí Backend Developer" → CV_AGENT
- "Pipeline tuyển ReactJS đến stage nào rồi?" → CV_AGENT
- "Đặt lịch phỏng vấn cho ứng viên" → CV_AGENT
- "Tỉ lệ nghỉ việc tháng này là bao nhiêu?" → ANALYTICS_AGENT
- "Tuần này tôi đã làm mấy tiếng?" → ATTENDANCE_AGENT
- "Tôi muốn nộp đơn xin nghỉ phép" → ATTENDANCE_AGENT
- "Check-in hôm nay của tôi" → ATTENDANCE_AGENT
- "Tôi muốn tạo ticket xin đổi laptop" → HELPDESK_AGENT
- "Ticket của tôi đang ở trạng thái nào?" → HELPDESK_AGENT
- "Gói bảo hiểm của tôi gồm những gì?" → BENEFITS_AGENT
- "Công ty có những phúc lợi gì?" → BENEFITS_AGENT
- "Tôi muốn đổi gói bảo hiểm" → BENEFITS_AGENT
"""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    return prompt | llm | StrOutputParser()


def orchestrator_node(state: AgentState):
    """Orchestrator node"""
    orchestrator = create_orchestrator()
    response = orchestrator.invoke({"messages": state["messages"]})

    response_clean = response.strip().upper()
    if "POLICY" in response_clean:
        next_agent = "policy_agent"
    elif "ONBOARD" in response_clean:
        next_agent = "onboard_agent"
    elif "CV" in response_clean:
        next_agent = "cv_agent"
    elif "ANALYTICS" in response_clean:
        next_agent = "analytics_agent"
    elif "ATTENDANCE" in response_clean:
        next_agent = "attendance_agent"
    elif "HELPDESK" in response_clean:
        next_agent = "helpdesk_agent"
    elif "BENEFITS" in response_clean:
        next_agent = "benefits_agent"
    else:
        next_agent = "end"

    return {
        "messages": state["messages"],
        "next": next_agent,
        "user_intent": response_clean,
        "user_id": state.get("user_id", ""),
        "user_info": state.get("user_info", {}),
    }


def router(state: AgentState):
    """Route to next agent"""
    next_step = state.get("next", "end")
    if next_step == "policy_agent":
        return "policy_agent"
    elif next_step == "onboard_agent":
        return "onboard_agent"
    elif next_step == "cv_agent":
        return "cv_agent"
    elif next_step == "analytics_agent":
        return "analytics_agent"
    elif next_step == "attendance_agent":
        return "attendance_agent"
    elif next_step == "helpdesk_agent":
        return "helpdesk_agent"
    elif next_step == "benefits_agent":
        return "benefits_agent"
    return "end"


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
    ]
    onboard_tools = [
        get_onboarding_checklist,
        search_hr_qa,
        verify_onboarding_document,
        list_employee_documents,
        sign_document,
        get_document_template,
    ]
    cv_tools = [
        screen_cv_for_position,
        get_recruitment_pipeline,
        create_interview_schedule,
        get_hiring_stats,
        get_employee_notifications,
    ]

    # Tool nodes — new Odoo modules
    attendance_tools = [get_attendance_record, submit_leave_request, get_leave_requests]
    helpdesk_tools = [create_hr_ticket, get_ticket_status, list_employee_tickets]
    benefits_tools = [
        get_employee_benefits,
        get_benefits_catalog,
        request_benefit_change,
    ]

    workflow.add_node("policy_tools", ToolNode(policy_tools))
    workflow.add_node("onboard_tools", ToolNode(onboard_tools))
    workflow.add_node("cv_tools", ToolNode(cv_tools))
    workflow.add_node("attendance_tools", ToolNode(attendance_tools))
    workflow.add_node("helpdesk_tools", ToolNode(helpdesk_tools))
    workflow.add_node("benefits_tools", ToolNode(benefits_tools))

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
            "end": END,
        },
    )

    # Agent → tool → END edges
    workflow.add_edge("policy_agent", "policy_tools")
    workflow.add_edge("policy_tools", END)
    workflow.add_edge("onboard_agent", "onboard_tools")
    workflow.add_edge("onboard_tools", END)
    workflow.add_edge("cv_agent", "cv_tools")
    workflow.add_edge("cv_tools", END)
    workflow.add_edge("analytics_agent", END)
    workflow.add_edge("attendance_agent", "attendance_tools")
    workflow.add_edge("attendance_tools", END)
    workflow.add_edge("helpdesk_agent", "helpdesk_tools")
    workflow.add_edge("helpdesk_tools", END)
    workflow.add_edge("benefits_agent", "benefits_tools")
    workflow.add_edge("benefits_tools", END)

    return workflow.compile()
