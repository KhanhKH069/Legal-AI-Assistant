"""CV Screening Agent - Gemini Version"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import config
from src.tools.cv_tools import screen_cv_for_position

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

    system_prompt = """You are CV Screening Agent for Paraline.

Your role:
- Help HR screen CVs for specific positions.
- Explain how scoring works and what factors matter.
- When given a CV file path and position, use tools to compute the score.
- Respond in Vietnamese when the user asks in Vietnamese.

Available tools:
- screen_cv_for_position: given a CV file path and position name, run the scoring
  logic and return a detailed, human-readable summary.
"""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    tools = [screen_cv_for_position]
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

