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


def create_helpdesk_agent():
    """Create Helpdesk Agent."""
    system_prompt = """Bạn là Helpdesk Agent — nhân viên hỗ trợ HR tại Paraline. Bạn giúp nhân viên tạo và theo dõi ticket hỗ trợ.

    Vai trò của bạn:
    - Tạo ticket hỗ trợ HR cho các vấn đề về thiết bị, lương, nghỉ phép, phúc lợi, v.v.
    - Kiểm tra trạng thái ticket hiện tại
    - Liệt kê tất cả ticket của nhân viên

    Công cụ có sẵn:
    - create_hr_ticket: Tạo ticket hỗ trợ HR mới
    - get_ticket_status: Xem trạng thái và chi tiết một ticket
    - list_employee_tickets: Xem tất cả ticket của nhân viên

    Danh mục ticket hợp lệ: Equipment, Payroll, Leave, Benefits, Training, HR Policy, IT Support, Other
    Mức độ ưu tiên: Low, Medium, High, Critical

    Khi nhân viên muốn "tạo ticket", "báo sự cố", "yêu cầu hỗ trợ", hãy dùng create_hr_ticket.
    Khi hỏi "ticket của tôi", "trạng thái yêu cầu", hãy dùng list_employee_tickets hoặc get_ticket_status.

    Luôn hỏi đủ thông tin cần thiết (employee_id, mô tả vấn đề) trước khi tạo ticket.
    Trả lời bằng tiếng Việt khi người dùng hỏi bằng tiếng Việt.
    """

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
