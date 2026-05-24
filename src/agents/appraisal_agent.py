"""
Appraisal Agent — Paraline HR AI Agent
Handles all performance appraisal related queries via LangGraph.
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import config
from src.tools.appraisal_tools import appraisal_tools
from src.tools.skills_tools import skills_tools
from src.core.prompt_loader import get_prompt

llm = None
if not config.enable_offline_mode and config.google_api_key:
    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        google_api_key=config.google_api_key,
        temperature=config.temperature,
    )


def create_appraisal_agent():
    """Create Appraisal Agent."""
    system_prompt = get_prompt("appraisal_agent")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    all_tools = appraisal_tools + skills_tools
    llm_with_tools = llm.bind_tools(all_tools)
    return prompt | llm_with_tools


def appraisal_agent_node(state):
    """Appraisal Agent Node for LangGraph."""
    agent = create_appraisal_agent()
    response = agent.invoke({"messages": state["messages"]})
    return {
        "messages": [response],
        "next": "end",
        "user_intent": state.get("user_intent", ""),
        "user_id": state.get("user_id", ""),
        "user_info": state.get("user_info", {}),
    }
