"""Attendance Agent — Bảng chấm công module"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import config
from src.tools.attendance_tools import (
    get_attendance_record,
    submit_leave_request,
    get_leave_requests,
)

llm = None
if not config.enable_offline_mode and config.google_api_key:
    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        google_api_key=config.google_api_key,
        temperature=config.temperature,
    )


def create_attendance_agent():
    """Create Attendance Agent."""
    system_prompt = """Bạn là Attendance Agent — chuyên gia về chấm công và quản lý nghỉ phép tại Paraline.

    Vai trò của bạn:
    - Xem dữ liệu chấm công của nhân viên (giờ vào, giờ ra, OT, ngày vắng)
    - Hỗ trợ nhân viên nộp đơn nghỉ phép
    - Tra cứu trạng thái các đơn nghỉ phép

    Công cụ có sẵn:
    - get_attendance_record: Xem bảng chấm công tuần hiện tại của nhân viên
    - submit_leave_request: Nộp đơn xin nghỉ phép
    - get_leave_requests: Xem danh sách đơn nghỉ phép và trạng thái

    Khi nhân viên hỏi về "giờ làm", "check-in", "chấm công", "OT", hãy dùng get_attendance_record.
    Khi nhân viên muốn "xin nghỉ", "nộp đơn nghỉ phép", hãy dùng submit_leave_request.
    Khi hỏi "đơn nghỉ của tôi", "trạng thái nghỉ phép", hãy dùng get_leave_requests.

    Nếu nhân viên không cung cấp employee_id, hỏi họ cung cấp mã nhân viên (ví dụ: EMP001).
    Trả lời bằng tiếng Việt khi người dùng hỏi bằng tiếng Việt.
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    tools = [get_attendance_record, submit_leave_request, get_leave_requests]
    llm_with_tools = llm.bind_tools(tools)
    return prompt | llm_with_tools


def attendance_agent_node(state):
    """Attendance Agent Node for LangGraph."""
    agent = create_attendance_agent()
    response = agent.invoke({"messages": state["messages"]})
    return {
        "messages": [response],
        "next": "end",
        "user_intent": state.get("user_intent", ""),
        "user_id": state.get("user_id", ""),
        "user_info": state.get("user_info", {}),
    }
