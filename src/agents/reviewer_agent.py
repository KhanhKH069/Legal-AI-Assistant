import logging
from typing import Any, Dict, Literal, Optional

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from src.core.config import config

logger = logging.getLogger(__name__)

_REVIEWER_PROMPT = (
    'Bạn là Trưởng phòng Pháp chế, đánh giá chất lượng câu trả lời pháp lý.\n\n'
    'Câu hỏi gốc: {query}\n'
    'Câu trả lời: {draft}\n\n'
    'Hãy đánh giá câu trả lời trên. '
    'Chỉ đánh giá FAIL khi câu trả lời: bịa luật, sai điều khoản, hoặc không liên quan đến câu hỏi. '
    'Nếu câu trả lời hợp lý, đánh giá PASS.'
)


class ReviewResult(BaseModel):
    """Kết quả đánh giá chất lượng câu trả lời pháp lý."""
    status: Literal['PASS', 'FAIL']
    feedback: Optional[str] = None


def reviewer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    messages = state.get('messages', [])
    if not messages:
        return {'next': 'pass'}

    if config.enable_offline_mode:
        return {'next': 'pass'}

    user_query = ''
    for msg in messages:
        if isinstance(msg, HumanMessage) and not msg.content.startswith('Feedback từ Trưởng phòng'):
            user_query = msg.content
            break

    last_msg = messages[-1]
    if not isinstance(last_msg, AIMessage) or not last_msg.content:
        if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
            return {'next': 'pass'}
        return {'next': 'pass'}

    draft_response = last_msg.content
    retry_count = state.get('retry_count', 0)
    if retry_count >= 2:
        return {'next': 'pass', 'retry_count': retry_count}

    from src.core.llm import get_llm
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([('system', _REVIEWER_PROMPT)])
    structured_llm = llm.with_structured_output(ReviewResult)

    try:
        chain = prompt | structured_llm
        result: ReviewResult = chain.invoke({'draft': draft_response, 'query': user_query})

        if result.status == 'FAIL':
            feedback = result.feedback or 'Câu trả lời chưa đạt yêu cầu.'
            feedback_msg = HumanMessage(
                content=f'Feedback từ Trưởng phòng Pháp chế: {feedback}\nHãy viết lại câu trả lời và ghi nhớ feedback này.'
            )
            return {'messages': [feedback_msg], 'next': 'fail', 'retry_count': retry_count + 1}

        return {'next': 'pass', 'retry_count': retry_count}

    except Exception as e:
        logger.warning('Reviewer error: %s — defaulting to PASS', e)
        return {'next': 'pass', 'retry_count': retry_count}