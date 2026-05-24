"""Onboard Agent - Gemini Version (with E-Signature & Document Management)"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import config
from src.tools.onboard_tools import get_onboarding_checklist
from src.tools.policy_tools import search_hr_qa
from src.tools.onboard_validation_tools import verify_onboarding_document
from src.tools.document_tools import (
    list_employee_documents,
    sign_document,
    get_document_template,
)

# Initialize LLM (only when required)
llm = None
if not config.enable_offline_mode and config.google_api_key:
    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        google_api_key=config.google_api_key,
        temperature=config.temperature,
    )


from src.core.prompt_loader import get_prompt


def create_onboard_agent():
    """Create Onboard Agent with E-Signature & Document Management"""
    system_prompt = get_prompt("onboard_agent")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    tools = [
        get_onboarding_checklist,
        search_hr_qa,
        verify_onboarding_document,
        list_employee_documents,
        sign_document,
        get_document_template,
    ]
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
        "user_info": state.get("user_info", {}),
    }
