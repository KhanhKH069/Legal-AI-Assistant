"""Helpdesk Agent — HR Support Ticket module"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import config
from src.tools.helpdesk_tools import (
    create_hr_ticket,
    get_ticket_status,
    list_employee_tickets,
)

llm = None
if not config.enable_offline_mode and config.google_api_key:
    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        google_api_key=config.google_api_key,
        temperature=config.temperature,
    )


from src.core.prompt_loader import get_prompt


def create_helpdesk_agent():
    """Create Helpdesk Agent."""
    system_prompt = get_prompt("helpdesk_agent")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    tools = [create_hr_ticket, get_ticket_status, list_employee_tickets]
    llm_with_tools = llm.bind_tools(tools)
    return prompt | llm_with_tools


def helpdesk_agent_node(state):
    """Helpdesk Agent Node for LangGraph."""
    agent = create_helpdesk_agent()
    response = agent.invoke({"messages": state["messages"]})
    return {
        "messages": [response],
        "next": "end",
        "user_intent": state.get("user_intent", ""),
        "user_id": state.get("user_id", ""),
        "user_info": state.get("user_info", {}),
    }
