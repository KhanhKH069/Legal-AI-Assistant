"""CV Screening Agent - Gemini Version (with Recruitment CRM & Interview Scheduling)"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import config
from src.tools.cv_tools import screen_cv_for_position
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


def create_cv_agent():
    """Create CV Screening Agent.

    This agent focuses on questions about CV scoring, matching candidates to positions,
    and interpreting screening results. It can call tools to actually run the scoring
    logic on stored CV files.
    """

    system_prompt = """You are CV Screening Agent for Paraline — HR's recruitment specialist.

Your role:
- Help HR screen and score CVs for specific positions.
- View and manage the recruitment pipeline (candidate stages).
- Schedule interviews and generate Google Meet links.
- Provide overall hiring statistics.
- Respond in Vietnamese when the user asks in Vietnamese.

Available tools:
- screen_cv_for_position: Score a CV for a specific position.
- get_recruitment_pipeline: View the recruitment funnel by stage for a position (e.g., 'ReactJS Developer').
- create_interview_schedule: Schedule an interview with date, time, type, and interviewer.
- get_hiring_stats: Get overall recruitment statistics across all open positions.
- send_internal_notification: Notify a candidate or HR team member about an update.

Routing guide:
- 'pipeline', 'tuyển dụng đến stage nào', 'ứng viên đang ở đâu' → get_recruitment_pipeline
- 'đặt lịch phỏng vấn', 'lên lịch phỏng vấn', 'tạo Google Meet' → create_interview_schedule
- 'thống kê tuyển dụng', 'tỉ lệ convert', 'hiring stats' → get_hiring_stats
"""

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
