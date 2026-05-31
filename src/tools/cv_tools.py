"""CV Screening Tools for multi-agent system."""

from langchain_core.tools import tool

from src.celery_app import score_single_cv_task
from celery.result import AsyncResult


@tool
def screen_cv_for_position(cv_path: str, position: str) -> str:
    """Start scoring a CV file for a specific position in the background.

    - cv_path: Absolute or project-relative path to the CV file (PDF/DOCX).
    - position: Position name that exists in job_requirements_config.json.

    Returns a Task ID. You MUST give this Task ID to the user and tell them to wait or ask you to check the status later.
    """
    task = score_single_cv_task.delay(cv_path, position)
    return f"Đã bắt đầu chấm CV dưới nền. Task ID: {task.id}. Vui lòng nói với người dùng: 'Tôi đã đưa CV vào hệ thống chấm điểm ngầm. Quá trình này có thể mất vài phút. Bạn có thể hỏi tôi tiến độ bằng cách cung cấp Task ID: {task.id}'"


@tool
def check_screening_status(task_id: str) -> str:
    """Check the status or result of a background CV screening task.

    - task_id: The Task ID returned by screen_cv_for_position.
    """
    res = AsyncResult(task_id)
    if not res.ready():
        state = res.state
        if state == "PROGRESS":
            meta = res.info or {}
            msg = meta.get("message", "Đang xử lý...")
            pct = meta.get("percent", 0)
            return f"Task vẫn đang chạy ({state}). Tiến độ: {pct}% - {msg}"
        return f"Task hiện tại đang ở trạng thái: {state}. Vui lòng thử lại sau."

    result = res.result
    if isinstance(result, Exception):
        return f"Lỗi xảy ra trong quá trình chấm CV: {str(result)}"

    if isinstance(result, dict) and "error" in result:
        return f"Lỗi chấm CV: {result['error']}"

    if not isinstance(result, dict):
        return f"Kết quả không hợp lệ: {result}"

    lines = [
        f" CV screening result for position: {result.get('position')}",
        f" Total score: {result.get('total_score')}/{result.get('max_score')} ({result.get('percentage')}%)",
        f" Recommendation: {result.get('recommendation')} - {result.get('status')}",
        f" Action: {result.get('action')}",
        "",
        "Breakdown:",
    ]

    breakdown = result.get("breakdown", {})
    req = breakdown.get("required_skills", {})
    pref = breakdown.get("preferred_skills", {})
    exp = breakdown.get("experience", {})
    edu = breakdown.get("education", {})
    cert = breakdown.get("certifications", {})

    lines.append(
        f"- Required skills: {req.get('points', 0):.1f}/30 "
        f"({req.get('percentage', 0):.0f}% match)"
    )
    lines.append(
        f"- Preferred skills: {pref.get('points', 0):.1f}/20 "
        f"({pref.get('percentage', 0):.0f}% match)"
    )
    lines.append(
        f"- Experience: {exp.get('points', 0)}/25 "
        f"({exp.get('years_found', 0)} years vs required {exp.get('years_required', 0)})"
    )
    lines.append(f"- Education: {edu.get('points', 0)}/15")
    lines.append(f"- Certifications: {cert.get('points', 0)}/10")

    # Add raw extracted sections for LLM to read
    if result.get("raw_skills"):
        lines.append(f"\n[Extracted Skills Section]\n{result.get('raw_skills')}")
    if result.get("raw_projects"):
        lines.append(f"\n[Extracted Projects Section]\n{result.get('raw_projects')}")

    return "\n".join(lines)


@tool
def get_job_requirements(position: str) -> str:
    """Get the job requirements for a specific position (e.g. 'Frontend Developer - Junior').

    Returns the required skills, preferred skills, experience years, education, etc.
    """
    import json
    import os

    config_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "job_requirements_config.json"
    )
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        return f"Cannot load job requirements: {e}"

    # Match position
    reqs = None
    for k, v in config.items():
        if position.lower() in k.lower() or k.lower() in position.lower():
            reqs = v
            break

    if not reqs:
        # Show some available positions
        available = ", ".join(list(config.keys())[:5]) + "..."
        return f"Không tìm thấy yêu cầu cho vị trí '{position}'. Các vị trí hiện có ví dụ: {available}"

    lines = [f"### Yêu cầu cho vị trí: {position}"]

    req_skills = reqs.get("required_skills", {})
    if req_skills.get("keywords"):
        lines.append("**Kỹ năng bắt buộc:** " + ", ".join(req_skills["keywords"]))

    pref_skills = reqs.get("preferred_skills", {})
    if pref_skills.get("keywords"):
        lines.append("**Kỹ năng ưu tiên:** " + ", ".join(pref_skills["keywords"]))

    exp = reqs.get("experience", {})
    if exp.get("years"):
        lines.append(f"**Kinh nghiệm:** Ít nhất {exp['years']} năm")

    edu = reqs.get("education", {})
    if edu.get("keywords"):
        lines.append("**Học vấn:** " + ", ".join(edu["keywords"]))

    cert = reqs.get("certifications", {})
    if cert.get("keywords"):
        lines.append("**Chứng chỉ:** " + ", ".join(cert["keywords"]))

    return "\n".join(lines)
