"""CV Screening Agent - Gemini Version (with Recruitment CRM & Interview Scheduling)"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import config
from src.tools.cv_tools import screen_cv_for_position, get_job_requirements
from src.tools.recruitment_tools import (
    get_recruitment_pipeline,
    create_interview_schedule,
    get_hiring_stats,
)
from src.tools.notification_tools import send_internal_notification

# Initialize Gemini LLM (only when online)
llm = None
if not config.enable_offline_mode and config.google_api_key:
    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        google_api_key=config.google_api_key,
        temperature=config.temperature,
    )


from src.core.prompt_loader import get_prompt


def create_cv_agent():
    """Create CV Screening Agent.

    This agent focuses on questions about CV scoring, matching candidates to positions,
    and interpreting screening results. It can call tools to actually run the scoring
    logic on stored CV files.
    """

    system_prompt = get_prompt("cv_agent")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    tools = [
        screen_cv_for_position,
        get_recruitment_pipeline,
        create_interview_schedule,
        get_hiring_stats,
        send_internal_notification,
        get_job_requirements,
    ]
    llm_with_tools = llm.bind_tools(tools)
    return prompt | llm_with_tools


def cv_agent_node(state):
    """CV Screening Agent node for LangGraph."""
    agent = create_cv_agent()
    response = agent.invoke({"messages": state["messages"]})
    return {
        "messages": [response],
        "next": "end",
        "user_intent": state.get("user_intent", ""),
        "user_id": state.get("user_id", ""),
        "user_info": state.get("user_info", {}),
    }
