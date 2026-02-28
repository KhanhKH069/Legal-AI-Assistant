"""Policy Agent - Gemini Version"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import config
from src.tools.policy_tools import calculate_leave_days, get_policy_info, search_hr_qa

# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(
    model=config.model_name,
    google_api_key=config.google_api_key,
    temperature=config.temperature
)

def create_policy_agent():
    """Create Policy Agent"""
    system_prompt = """You are Policy Agent - HR policy expert using Gemini AI.
    
    Your role:
    - Answer HR policy questions
    - Provide clear, accurate information
    - Use tools to get data
    - Be professional and helpful
    
    Available tools:
    - get_policy_info: Get HR policy details
    - calculate_leave_days: Calculate leave entitlement
    - search_hr_qa: Search Q&A database
    
    Respond in Vietnamese when user asks in Vietnamese.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    tools = [get_policy_info, calculate_leave_days, search_hr_qa]
    llm_with_tools = llm.bind_tools(tools)
    return prompt | llm_with_tools

def policy_agent_node(state):
    """Policy Agent Node"""
    agent = create_policy_agent()
    response = agent.invoke({"messages": state["messages"]})
    return {
        "messages": [response],
        "next": "end",
        "user_intent": state.get("user_intent", ""),
        "user_id": state.get("user_id", ""),
        "user_info": state.get("user_info", {})
    }
