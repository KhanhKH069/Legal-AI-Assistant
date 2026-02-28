"""Onboard Agent - Gemini Version"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import config
from src.tools.onboard_tools import get_onboarding_checklist
from src.tools.policy_tools import search_hr_qa

# Initialize LLM (only when required)
llm = None
if not config.enable_offline_mode and config.google_api_key:
    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        google_api_key=config.google_api_key,
        temperature=config.temperature,
    )

def create_onboard_agent():
    """Create Onboard Agent"""
    system_prompt = """You are Onboard Agent - onboarding specialist using Gemini AI.
    
    Your role:
    - Help new employees with onboarding
    - Provide checklists and guidance
    - Answer onboarding questions
    - Be friendly and supportive
    
    Available tools:
    - get_onboarding_checklist: Get phase checklists
    - search_hr_qa: Search Q&A database
    
    Respond in Vietnamese when user asks in Vietnamese.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    tools = [get_onboarding_checklist, search_hr_qa]
    llm_with_tools = llm.bind_tools(tools)
    return prompt | llm_with_tools

def onboard_agent_node(state):
    """Onboard Agent Node"""
    agent = create_onboard_agent()
    response = agent.invoke({"messages": state["messages"]})
    return {
        "messages": [response],
        "next": "end",
        "user_intent": state.get("user_intent", ""),
        "user_id": state.get("user_id", ""),
        "user_info": state.get("user_info", {})
    }
