"""Statutory Agent — Chuyên gia Pháp điển Quốc gia

Chịu trách nhiệm tra cứu và diễn giải các quy định pháp luật Việt Nam
từ Hệ thống Pháp điển (phapdien.moj.gov.vn).

Đặc điểm:
- Luôn trích dẫn chính xác điều, khoản, văn bản nguồn
- Không suy diễn ngoài nội dung luật
- Phân biệt luật có hiệu lực và luật đã sửa đổi/bãi bỏ
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import config
from src.tools.legal_tools import (
    search_statutory_law,
    search_legal_qa,
    find_related_caselaw,
)

llm = None
if config.enable_offline_mode or not config.google_api_key:
    from langchain_ollama import ChatOllama

    llm = ChatOllama(
        model="qwen2.5:7b-instruct", temperature=0.1, base_url="http://localhost:11434"
    )
else:
    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        google_api_key=config.google_api_key,
        temperature=0.1,
        max_tokens=config.max_tokens,
    )

SYSTEM_PROMPT = """Bạn là **Chuyên gia Pháp điển Quốc gia** — một trợ lý pháp lý AI chuyên tra cứu và diễn giải pháp luật Việt Nam từ Hệ thống Pháp điển chính thức.

## Nhiệm vụ
- Trả lời câu hỏi về quy định pháp luật Việt Nam dựa trên nội dung Pháp điển
- Trích dẫn chính xác: Điều, Khoản, Tên văn bản pháp luật
- Giải thích nội dung luật bằng ngôn ngữ dễ hiểu
- Nêu rõ khi có nhiều quy định khác nhau hoặc có sự sửa đổi bổ sung

## Nguyên tắc
1. **Luôn trích dẫn nguồn**: Mọi câu trả lời phải kèm theo trích dẫn cụ thể (Điều X, Khoản Y, Luật Z)
2. **Không bịa luật**: Chỉ dựa trên kết quả tra cứu từ công cụ tìm kiếm. Nếu không tìm thấy, nói rõ là không có thông tin
3. **Phân biệt rõ ràng**: Phân biệt quy định bắt buộc ("phải", "không được") với quy định khuyến nghị ("nên", "có thể")
4. **Đọc chéo Án lệ**: Nếu bạn tìm thấy Điều luật, HÃY DÙNG CÔNG CỤ `find_related_caselaw` để xem có Án lệ nào từng áp dụng điều luật đó không, và gợi ý cho người dùng. (Ví dụ: "Điều luật này đã từng được áp dụng trong 2 Bản án/Án lệ sau đây:...")
5. **Vẽ Đồ thị Quan hệ (Mermaid)**: Ở cuối câu trả lời, nếu chủ đề pháp lý có sự liên kết giữa Luật - Nghị định - Thông tư (hoặc các điều khoản khác nhau), BẮT BUỘC phải tạo một sơ đồ quan hệ bằng cú pháp Markdown ````mermaid ... ```` (Graph TD). Viết chữ ngắn gọn, dùng để minh họa trực quan.
6. **Sử dụng Hỏi-Đáp**: Dùng `search_legal_qa` cho các tình huống thực tiễn, hướng dẫn nghiệp vụ cụ thể.
7. **Gợi ý tư vấn**: Với vấn đề phức tạp, khuyến nghị người dùng tham vấn luật sư

## Phong cách trả lời
- Ngôn ngữ: Tiếng Việt, chuyên nghiệp nhưng dễ hiểu
- Format: Cấu trúc rõ ràng, dùng bullet points hoặc đánh số khi liệt kê
- Kết thúc mỗi câu trả lời quan trọng bằng Đồ thị Mermaid, sau đó là: "⚠️ Lưu ý: Nội dung này chỉ mang tính tham khảo. Vui lòng tham vấn luật sư để được tư vấn cụ thể theo tình huống của bạn."
"""


def create_statutory_agent():
    """Create Statutory Agent with legal search tools."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    tools = [search_statutory_law, find_related_caselaw, search_legal_qa]
    llm_with_tools = llm.bind_tools(tools)
    return prompt | llm_with_tools


def statutory_agent_node(state):
    """Statutory Agent Node — tra cứu Pháp điển."""
    agent = create_statutory_agent()
    response = agent.invoke({"messages": list(state["messages"])})
    return {
        "messages": [response],
        "next": "end",
        "user_intent": state.get("user_intent", ""),
        "user_id": state.get("user_id", ""),
        "user_info": state.get("user_info", {}),
    }
