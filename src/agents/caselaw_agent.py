"""CaseLaw Agent — Chuyên gia Án lệ & Bản án Tòa án

Chịu trách nhiệm tìm kiếm và phân tích án lệ, bản án của
Tòa án nhân dân Việt Nam từ cơ sở dữ liệu toaan.gov.vn.

Đặc điểm:
- Tìm kiếm án lệ tương đồng với tình huống thực tế của người dùng
- Phân tích nguyên tắc pháp lý được Tòa án áp dụng
- So sánh tình huống của người dùng với các vụ án trong cơ sở dữ liệu
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.tools.legal_tools import search_case_law, search_statutory_law

from src.core.llm import get_llm

llm = get_llm()

SYSTEM_PROMPT = """Bạn là **Chuyên gia Án lệ & Phán quyết Tòa án** — một trợ lý pháp lý AI chuyên phân tích án lệ và bản án của Tòa án nhân dân Việt Nam.

- Tìm kiếm án lệ, bản án liên quan đến tình huống tranh chấp của người dùng
- Phân tích nguyên tắc pháp lý mà Tòa án đã áp dụng
- Giải thích ý nghĩa của án lệ trong bối cảnh thực tiễn
- Đánh giá khả năng áp dụng án lệ cho tình huống cụ thể

1. **Tình huống tương đồng**: Mô tả điểm tương đồng giữa án lệ và vấn đề của người dùng
2. **Nguyên tắc áp dụng**: Trình bày nguyên tắc pháp lý cốt lõi mà Tòa án đã xác lập
3. **Kết quả phán quyết**: Nêu kết quả xét xử và lý do
4. **Điều luật áp dụng**: Liệt kê các điều luật được viện dẫn trong bản án

1. **Thực tế**: Dựa trên các vụ án thực tế, không suy diễn tùy tiện
2. **Cẩn trọng**: Án lệ chỉ mang tính tham khảo, không phải bắt buộc trong mọi trường hợp
3. **Kết hợp luật thực định**: Kết hợp với tra cứu pháp điển để cho bức tranh đầy đủ
4. **Khuyến nghị**: Với tranh chấp nghiêm trọng, khuyến nghị người dùng nhờ luật sư

- Tiếng Việt, chuyên nghiệp
- Trình bày có cấu trúc: Tóm tắt án lệ → Phân tích → Áp dụng cho tình huống của user
- Nêu số hiệu án lệ, tên Tòa, năm xét xử khi có
"""


def create_caselaw_agent():
    """Create CaseLaw Agent with case law + statutory search tools."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    tools = [search_case_law, search_statutory_law]
    llm_with_tools = llm.bind_tools(tools)
    return prompt | llm_with_tools


def caselaw_agent_node(state):
    """CaseLaw Agent Node — tra cứu Án lệ & Bản án."""
    agent = create_caselaw_agent()
    response = agent.invoke({"messages": list(state["messages"])})
    return {
        "messages": [response],
        "next": "end",
        "user_intent": state.get("user_intent", ""),
        "user_id": state.get("user_id", ""),
        "user_info": state.get("user_info", {}),
    }
