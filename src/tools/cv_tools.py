"""CV Screening Tools for multi-agent system."""

from langchain_core.tools import tool

from cv_screening import score_cv


@tool
def screen_cv_for_position(cv_path: str, position: str) -> str:
    """Score a CV file for a specific position and return a readable summary.

    - cv_path: Absolute or project-relative path to the CV file (PDF/DOCX).
    - position: Position name that exists in job_requirements_config.json.
    """
    result = score_cv(cv_path=cv_path, position=position)

    if "error" in result:
        return f"CV screening error: {result['error']}"

    lines = [
        f"📄 CV screening result for position: {result['position']}",
        f"🔢 Total score: {result['total_score']}/{result['max_score']} ({result['percentage']}%)",
        f"📝 Recommendation: {result['recommendation']} - {result['status']}",
        f"➡ Action: {result['action']}",
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

    return "\n".join(lines)

