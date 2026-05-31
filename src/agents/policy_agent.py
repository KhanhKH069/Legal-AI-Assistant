"""Policy Agent - Gemini Version"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import config
from src.tools.policy_tools import calculate_leave_days, get_policy_info, search_hr_qa
from src.tools.employee_data_tools import (
    get_employee_profile,
    get_leave_balance,
    get_salary_info,
)
from src.tools.math_tools import calculate_math_expression

# Initialize Gemini LLM (only when online and key available)
llm = None
if not config.enable_offline_mode and config.google_api_key:
    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        google_api_key=config.google_api_key,
        temperature=config.temperature,
    )


from src.core.prompt_loader import get_prompt


def create_policy_agent():
    """Create Policy Agent"""
    system_prompt = get_prompt("policy_agent")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    tools = [
        get_policy_info,
        calculate_leave_days,
        search_hr_qa,
        get_employee_profile,
        get_leave_balance,
        get_salary_info,
        calculate_math_expression,
    ]
    llm_with_tools = llm.bind_tools(tools)
    return prompt | llm_with_tools


def policy_agent_node(state):
    """Policy Agent Node"""
    agent = create_policy_agent()
    
    messages = list(state["messages"])
    if state.get("user_info"):
        from langchain_core.messages import SystemMessage
        import json
        info_str = f"LƯU Ý: Đây là thông tin của nhân viên đang chat. Hãy dùng thông tin này nếu họ hỏi về cá nhân họ (lương, chức vụ, phòng ban...):\n{json.dumps(state['user_info'], ensure_ascii=False, indent=2)}"
        messages.insert(max(0, len(messages) - 1), SystemMessage(content=info_str))

    response = agent.invoke({"messages": messages})
    return {
        "messages": [response],
        "next": "end",
        "user_intent": state.get("user_intent", ""),
        "user_id": state.get("user_id", ""),
        "user_info": state.get("user_info", {}),
    }
