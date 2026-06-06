import logging
from functools import lru_cache
from typing import Dict, Any

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.tools.legal_tools import search_statutory_law, search_legal_qa, find_related_caselaw

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    'Bạn là **Chuyên gia Pháp điển Quốc gia** — một trợ lý pháp lý AI chuyên tra cứu và diễn giải pháp luật Việt Nam từ Hệ thống Pháp điển chính thức.\n\n'
    '- Trả lời câu hỏi về quy định pháp luật Việt Nam dựa trên nội dung Pháp điển\n'
    '- Trích dẫn chính xác: Điều, Khoản, Tên văn bản pháp luật\n'
    '- Giải thích nội dung luật bằng ngôn ngữ dễ hiểu\n'
    '- Nêu rõ khi có nhiều quy định khác nhau hoặc có sự sửa đổi bổ sung\n\n'
    '1. **Luôn trích dẫn nguồn**: Mọi câu trả lời phải kèm theo trích dẫn cụ thể (Điều X, Khoản Y, Luật Z)\n'
    '2. **Không bịa luật**: Chỉ dựa trên kết quả tra cứu từ công cụ tìm kiếm. Nếu không tìm thấy, nói rõ là không có thông tin\n'
    '3. **Phân biệt rõ ràng**: Phân biệt quy định bắt buộc ("phải", "không được") với quy định khuyến nghị ("nên", "có thể")\n'
    '4. **Đọc chéo Án lệ**: Nếu bạn tìm thấy Điều luật, HÃY DÙNG CÔNG CỤ `find_related_caselaw` để xem có Án lệ nào từng áp dụng điều luật đó không, và gợi ý cho người dùng.\n'
    '5. **Vẽ Đồ thị Quan hệ (Mermaid)**: Ở cuối câu trả lời, nếu chủ đề pháp lý có sự liên kết giữa Luật - Nghị định - Thông tư, BẮT BUỘC phải tạo một sơ đồ quan hệ bằng cú pháp Markdown ```mermaid ... ``` (Graph TD).\n'
    '6. **Sử dụng Hỏi-Đáp**: Dùng `search_legal_qa` cho các tình huống thực tiễn, hướng dẫn nghiệp vụ cụ thể.\n'
    '7. **Gợi ý tư vấn**: Với vấn đề phức tạp, khuyến nghị người dùng tham vấn luật sư\n\n'
    '- Ngôn ngữ: Tiếng Việt, chuyên nghiệp nhưng dễ hiểu\n'
    '- Format: Cấu trúc rõ ràng, dùng bullet points hoặc đánh số khi liệt kê\n'
    '- Kết thúc mỗi câu trả lời quan trọng bằng Đồ thị Mermaid, sau đó là: '
    '"⚠️ Lưu ý: Nội dung này chỉ mang tính tham khảo. Vui lòng tham vấn luật sư để được tư vấn cụ thể theo tình huống của bạn."\n'
)


@lru_cache(maxsize=1)
def _get_llm():
    """Lazy, cached LLM initialization to avoid crash-at-import-time."""
    from src.core.llm import get_llm
    return get_llm()


def create_statutory_agent():
    prompt = ChatPromptTemplate.from_messages([
        ('system', SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name='messages'),
    ])
    tools = [search_statutory_law, find_related_caselaw, search_legal_qa]
    llm_with_tools = _get_llm().bind_tools(tools)
    return prompt | llm_with_tools


def statutory_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = create_statutory_agent()
    response = agent.invoke({'messages': list(state['messages'])})
    return {
        'messages': [response],
        'next': 'end',
        'user_intent': state.get('user_intent', ''),
        'user_id': state.get('user_id', ''),
        'user_info': state.get('user_info', {}),
        'retry_count': state.get('retry_count', 0),
    }