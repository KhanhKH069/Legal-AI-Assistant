import logging
from functools import lru_cache
from typing import Dict, Any

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.tools.legal_tools import search_case_law, search_statutory_law

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    'Bạn là **Chuyên gia Án lệ & Phán quyết Tòa án** — một trợ lý pháp lý AI chuyên phân tích án lệ và bản án của Tòa án nhân dân Việt Nam.\n\n'
    '- Tìm kiếm án lệ, bản án liên quan đến tình huống tranh chấp của người dùng\n'
    '- Phân tích nguyên tắc pháp lý mà Tòa án đã áp dụng\n'
    '- Giải thích ý nghĩa của án lệ trong bối cảnh thực tiễn\n'
    '- Đánh giá khả năng áp dụng án lệ cho tình huống cụ thể\n\n'
    '1. **Tình huống tương đồng**: Mô tả điểm tương đồng giữa án lệ và vấn đề của người dùng\n'
    '2. **Nguyên tắc áp dụng**: Trình bày nguyên tắc pháp lý cốt lõi mà Tòa án đã xác lập\n'
    '3. **Kết quả phán quyết**: Nêu kết quả xét xử và lý do\n'
    '4. **Điều luật áp dụng**: Liệt kê các điều luật được viện dẫn trong bản án\n\n'
    '1. **Thực tế**: Dựa trên các vụ án thực tế, không suy diễn tùy tiện\n'
    '2. **Cẩn trọng**: Án lệ chỉ mang tính tham khảo, không phải bắt buộc trong mọi trường hợp\n'
    '3. **Kết hợp luật thực định**: Kết hợp với tra cứu pháp điển để cho bức tranh đầy đủ\n'
    '4. **Khuyến nghị**: Với tranh chấp nghiêm trọng, khuyến nghị người dùng nhờ luật sư\n\n'
    '- Tiếng Việt, chuyên nghiệp\n'
    '- Trình bày có cấu trúc: Tóm tắt án lệ → Phân tích → Áp dụng cho tình huống của user\n'
    '- Nêu số hiệu án lệ, tên Tòa, năm xét xử khi có\n'
)


@lru_cache(maxsize=1)
def _get_llm():
    """Lazy, cached LLM initialization to avoid crash-at-import-time."""
    from src.core.llm import get_llm
    return get_llm()


def create_caselaw_agent():
    prompt = ChatPromptTemplate.from_messages([
        ('system', SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name='messages'),
    ])
    tools = [search_case_law, search_statutory_law]
    llm_with_tools = _get_llm().bind_tools(tools)
    return prompt | llm_with_tools


def caselaw_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = create_caselaw_agent()
    response = agent.invoke({'messages': list(state['messages'])})
    return {
        'messages': [response],
        'next': 'end',
        'user_intent': state.get('user_intent', ''),
        'user_id': state.get('user_id', ''),
        'user_info': state.get('user_info', {}),
        'retry_count': state.get('retry_count', 0),
    }