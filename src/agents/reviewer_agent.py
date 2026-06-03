import json
from typing import Dict, Any
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from src.core.config import config
_REVIEWER_PROMPT = 'Bạn là Trưởng phòng Pháp chế, đánh giá chất lượng câu trả lời pháp lý.\n\nCâu hỏi gốc: {query}\nCâu trả lời: {draft}\n\nHãy đánh giá và trả về JSON:\n{{"status": "PASS" hoặc "FAIL", "feedback": "lý do nếu FAIL"}}\n\nChỉ FAIL khi câu trả lời: bịa luật, sai điều khoản, hoặc không liên quan đến câu hỏi.\n'

def reviewer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    messages = state.get('messages', [])
    if not messages:
        return {'next': 'pass'}
    if config.enable_offline_mode:
        return {'next': 'pass'}
    user_query = ''
    for msg in messages:
        if isinstance(msg, HumanMessage) and (not msg.content.startswith('Feedback từ Trưởng phòng')):
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
    system_prompt_template = _REVIEWER_PROMPT
    prompt = ChatPromptTemplate.from_messages([('system', system_prompt_template)])
    try:
        chain = prompt | llm
        result = chain.invoke({'draft': draft_response, 'query': user_query})
        content = result.content.strip()
        if content.startswith('```json'):
            content = content[7:-3].strip()
        elif content.startswith('```'):
            content = content[3:-3].strip()
        data = json.loads(content)
        if data.get('status') == 'FAIL':
            feedback = data.get('feedback', 'Câu trả lời chưa đạt yêu cầu.')
            feedback_msg = HumanMessage(content=f'Feedback từ Trưởng phòng Pháp chế: {feedback}\nHãy viết lại câu trả lời và ghi nhớ feedback này.')
            return {'messages': [feedback_msg], 'next': 'fail', 'retry_count': retry_count + 1}
        return {'next': 'pass', 'retry_count': retry_count}
    except Exception as e:
        print(f'Reviewer Error: {e}')
        return {'next': 'pass', 'retry_count': retry_count}