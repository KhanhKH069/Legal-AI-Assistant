"""
personal_info_handler.py
Detects personal questions and answers them from employee data.
No LLM / Gemini API needed — works offline.
"""

import re
from src.tools.employee_data_tools import get_employee_by_id

# ---------------------------------------------------------------------------
# Keywords that signal a PERSONAL question (about "me/tôi")
# ---------------------------------------------------------------------------
_PERSONAL_KEYWORDS = [
    # Vietnamese (accented)
    r"\btôi\b",
    r"\bcủa tôi\b",
    r"\bmình\b",
    r"\bcủa mình\b",
    r"\bngày phép\b",
    r"\bphép còn\b",
    r"\bphép của\b",
    r"\blương\b",
    r"\bsalary\b",
    r"\blevel\b",
    r"\bhồ sơ\b",
    r"\bphòng ban\b",
    r"\bchức vụ\b",
    r"\bdánh giá\b",
    r"\brating\b",
    r"\bperformance\b",
    r"\bnhân viên.*\btôi\b",
    # Vietnamese (unaccented fall-backs — users without IME)
    r"\btoi\b",
    r"\bcua toi\b",
    r"\bminh\b",
    r"\bngay phep\b",
    r"\bphep con\b",
    r"\bphep cua\b",
    r"\bluong\b",
    r"\bho so\b",
    r"\bphong ban\b",
    r"\bchuc vu\b",
    r"\bdanh gia\b",
    # English
    r"\bmy leave\b",
    r"\bmy salary\b",
    r"\bmy profile\b",
    r"\bmy department\b",
    r"\bmy position\b",
    r"\bleave balance\b",
    r"\bdays off\b",
    r"\bmy rating\b",
]

_LEAVE_KEYWORDS = [
    r"\bngày phép\b",
    r"\bphép còn\b",
    r"\bleave\b",
    r"\bphép\b",
    r"\bdays off\b",
    r"\bleave balance\b",
]
_SALARY_KEYWORDS = [
    r"\blương\b",
    r"\bsalary\b",
    r"\bsalary level\b",
    r"\bmức lương\b",
    r"\bcompensation\b",
]
_PERFORMANCE_KEYWORDS = [
    r"\bdánh giá\b",
    r"\brating\b",
    r"\bperformance\b",
    r"\bkết quả.*đánh giá\b",
    r"\bperformance rating\b",
]
_PROFILE_KEYWORDS = [
    r"\bhồ sơ\b",
    r"\bprofile\b",
    r"\bthông tin\b",
    r"\bphòng ban\b",
    r"\bchức vụ\b",
    r"\bdepartment\b",
    r"\bposition\b",
    r"\bthông tin cá nhân\b",
    r"\bmy info\b",
]


def _matches_any(text: str, patterns: list[str]) -> bool:
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in patterns)


def is_personal_question(question: str) -> bool:
    """Return True if the question is asking about the user's own personal info."""
    return _matches_any(question, _PERSONAL_KEYWORDS)


def answer_personal_question(question: str, employee_id: str) -> str:
    """
    Look up employee data and return a Vietnamese-friendly answer.
    Falls back to a general profile if the topic cannot be identified.
    """
    emp = get_employee_by_id(employee_id)
    if not emp:
        return (
            f"❌ Không tìm thấy nhân viên với mã **{employee_id}**. "
            "Vui lòng kiểm tra lại mã nhân viên."
        )

    name = emp["name"]
    q = question.lower()

    # Leave balance
    if _matches_any(q, _LEAVE_KEYWORDS):
        days = emp["leave_balance"]
        emoji = "🟢" if days >= 10 else ("🟡" if days >= 5 else "🔴")
        return (
            f"📅 **Số ngày phép còn lại của {name}:**\n\n"
            f"{emoji} **{days} ngày** phép còn khả dụng trong năm nay."
        )

    # Salary level
    if _matches_any(q, _SALARY_KEYWORDS):
        level = emp["salary_level"]
        level_desc = {
            "L1": "Junior / Entry",
            "L2": "Junior+",
            "L3": "Mid-level",
            "L4": "Senior",
            "L5": "Lead / Principal",
        }.get(level, level)
        return (
            f"💼 **Thông tin lương của {name}:**\n\n"
            f"• **Salary Level:** {level} ({level_desc})\n"
            f"• **Performance Rating:** {emp['performance_rating']}/5.0 ⭐\n\n"
            f"_Để biết thêm chi tiết về thang lương, vui lòng liên hệ HR: hr@paraline.com.vn_"
        )

    # Performance rating
    if _matches_any(q, _PERFORMANCE_KEYWORDS):
        rating = emp["performance_rating"]
        stars = "⭐" * round(rating)
        return (
            f"📊 **Kết quả đánh giá của {name}:**\n\n"
            f"• **Rating:** {rating}/5.0  {stars}"
        )

    # General profile (default)
    return (
        f"👤 **Thông tin cá nhân của {name} ({employee_id.upper()}):**\n\n"
        f"• **Họ tên:** {name}\n"
        f"• **Phòng ban:** {emp['department']}\n"
        f"• **Chức vụ:** {emp['position']}\n"
        f"• **Ngày vào làm:** {emp['start_date']}\n"
        f"• **Salary Level:** {emp['salary_level']}\n"
        f"• **Performance Rating:** {emp['performance_rating']}/5.0 ⭐\n"
        f"• **Ngày phép còn lại:** {emp['leave_balance']} ngày"
    )
