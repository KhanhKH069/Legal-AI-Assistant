"""Benefits Agent — Employee Benefits & Subscriptions module"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import config
from src.tools.benefits_tools import (
    get_employee_benefits,
    get_benefits_catalog,
    request_benefit_change,
)

llm = None
if not config.enable_offline_mode and config.google_api_key:
    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        google_api_key=config.google_api_key,
        temperature=config.temperature,
    )


def create_benefits_agent():
    """Create Benefits Agent."""
    system_prompt = """Bạn là Benefits Agent — chuyên gia phúc lợi nhân viên tại Paraline.

    Vai trò của bạn:
    - Giải thích chi tiết các gói phúc lợi, bảo hiểm, phụ cấp của công ty
    - Tra cứu phúc lợi hiện tại của một nhân viên cụ thể
    - Hỗ trợ nhân viên đăng ký thay đổi gói phúc lợi

    Công cụ có sẵn:
    - get_employee_benefits: Xem phúc lợi hiện tại của một nhân viên
    - get_benefits_catalog: Xem toàn bộ danh mục phúc lợi công ty
    - request_benefit_change: Nộp yêu cầu thay đổi gói phúc lợi

    Khi nhân viên hỏi về "bảo hiểm", "phụ cấp", "phúc lợi của tôi", hãy dùng get_employee_benefits.
    Khi hỏi "các gói bảo hiểm", "công ty có những phúc lợi gì", hãy dùng get_benefits_catalog.
    Khi muốn "đổi gói", "đăng ký thêm", hãy dùng request_benefit_change.

    Trả lời bằng tiếng Việt khi người dùng hỏi bằng tiếng Việt.
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    tools = [get_employee_benefits, get_benefits_catalog, request_benefit_change]
    llm_with_tools = llm.bind_tools(tools)
    return prompt | llm_with_tools


def benefits_agent_node(state):
    """Benefits Agent Node for LangGraph."""
    agent = create_benefits_agent()
    response = agent.invoke({"messages": state["messages"]})
    return {
        "messages": [response],
        "next": "end",
        "user_intent": state.get("user_intent", ""),
        "user_id": state.get("user_id", ""),
        "user_info": state.get("user_info", {}),
    }
