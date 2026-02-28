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
from src.core.config import config
from src.tools.cv_tools import screen_cv_for_position
from src.tools.onboard_tools import get_onboarding_checklist
from src.tools.policy_tools import calculate_leave_days, get_policy_info, search_hr_qa


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
        max_tokens=config.max_tokens
    )

def create_orchestrator():
    """Create orchestrator agent"""
    system_prompt = """You are HR Orchestrator Agent. Analyze user intent and route to the appropriate agent.

Available agents:
- POLICY_AGENT: For HR policy questions (leave, salary, benefits, working hours)
- ONBOARD_AGENT: For onboarding questions (new employee, checklist, documents)
- CV_AGENT: For CV screening, CV scoring, and questions about how suitable a candidate is for a position

Respond with ONLY ONE WORD: POLICY_AGENT, ONBOARD_AGENT, CV_AGENT or END

Examples:
- "How many leave days?" → POLICY_AGENT
- "Onboarding checklist?" → ONBOARD_AGENT
- "New employee documents?" → ONBOARD_AGENT
- "Salary policy?" → POLICY_AGENT
- "Đánh giá CV này cho vị trí Backend Developer" → CV_AGENT
- "CV này đạt bao nhiêu điểm cho Software Engineer?" → CV_AGENT
"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
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
    else:
        next_agent = "end"
    
    return {
        "messages": state["messages"],
        "next": next_agent,
        "user_intent": response_clean,
        "user_id": state.get("user_id", ""),
        "user_info": state.get("user_info", {})
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
    return "end"

def create_hr_agent_graph():
    """Create HR Agent Graph with LangGraph"""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("policy_agent", policy_agent_node)
    workflow.add_node("onboard_agent", onboard_agent_node)
    workflow.add_node("cv_agent", cv_agent_node)
    
    # Tool nodes
    policy_tools = [get_policy_info, calculate_leave_days, search_hr_qa]
    onboard_tools = [get_onboarding_checklist, search_hr_qa]
    cv_tools = [screen_cv_for_position]
    
    workflow.add_node("policy_tools", ToolNode(policy_tools))
    workflow.add_node("onboard_tools", ToolNode(onboard_tools))
    workflow.add_node("cv_tools", ToolNode(cv_tools))
    
    # Set entry point
    workflow.set_entry_point("orchestrator")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "orchestrator",
        router,
        {
            "policy_agent": "policy_agent",
            "onboard_agent": "onboard_agent",
            "cv_agent": "cv_agent",
            "end": END
        }
    )
    
    # Edges for agents
    workflow.add_edge("policy_agent", "policy_tools")
    workflow.add_edge("policy_tools", END)
    workflow.add_edge("onboard_agent", "onboard_tools")
    workflow.add_edge("onboard_tools", END)
    workflow.add_edge("cv_agent", "cv_tools")
    workflow.add_edge("cv_tools", END)
    
    return workflow.compile()
