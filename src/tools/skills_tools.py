"""
Skills Management Tools — Paraline HR AI Agent
Provides: search by skill, skill gap analysis, update employee skills,
           get employee skill profile.
"""

import json
import os
from typing import Any

from langchain_core.tools import tool

_EMP_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "employees_data.json"
)


def _load_employees() -> list[dict]:
    try:
        with open(_EMP_PATH, encoding="utf-8") as f:
            return json.load(f).get("employees", [])
    except FileNotFoundError:
        return []


def _save_employees(employees: list[dict]) -> None:
    with open(_EMP_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {"employees": employees, "total": len(employees)},
            f,
            ensure_ascii=False,
            indent=2,
        )


# ── Job skill requirements (used for gap analysis) ────────────────────────────
_JOB_SKILLS: dict[str, list[str]] = {
    "Backend Developer": [
        "Python",
        "FastAPI",
        "PostgreSQL",
        "Docker",
        "REST API",
        "Git",
    ],
    "Frontend Developer": ["TypeScript", "React", "CSS", "Git", "REST API"],
    "Full-stack Developer": ["Python", "React", "PostgreSQL", "Docker", "Git"],
    "AI Engineer": ["Python", "PyTorch", "LangChain", "Docker", "REST API"],
    "DevOps Engineer": ["Docker", "Kubernetes", "Terraform", "AWS", "Linux", "CI/CD"],
    "QA Engineer": ["Selenium", "Postman", "Manual Testing", "Bug Tracking"],
    "HR Specialist": ["Talent Acquisition", "HRIS", "Labor Law Vietnam", "Onboarding"],
    "HR Manager": [
        "Performance Management",
        "SHRM",
        "Compensation & Benefits",
        "Labor Law Vietnam",
    ],
    "Sales Executive": ["CRM", "Negotiation", "Pipeline Management", "Cold Calling"],
    "Sales Manager": ["CRM", "B2B Sales", "Pipeline Management", "Account Management"],
    "Marketing Manager": [
        "Brand Strategy",
        "Content Marketing",
        "Google Analytics",
        "SEO",
    ],
    "Product Manager": ["Figma", "Jira", "Agile/Scrum", "Product Roadmap", "OKRs"],
    "Finance Manager": ["Excel", "SAP", "IFRS", "Financial Modeling", "Budgeting"],
    "Engineering Manager": ["CI/CD", "Microservices", "Git", "Problem Solving"],
    "Recruiter": ["Talent Acquisition", "HRIS", "Communication", "Onboarding"],
}


@tool
def get_employee_skills(employee_id: str) -> str:
    """Get the full skill profile of an employee by their ID.

    Args:
        employee_id: Employee ID (e.g. EMP001)
    """
    employees = _load_employees()
    emp = next(
        (e for e in employees if e["employee_id"].upper() == employee_id.upper()), None
    )
    if not emp:
        return f"Không tìm thấy nhân viên {employee_id}."

    skills = emp.get("skills", [])
    level = emp.get("level", "N/A")
    return (
        f"**Hồ sơ kỹ năng — {emp['name']} ({employee_id})**\n"
        f"- Chức vụ: {emp['position']} | Cấp bậc: {level}\n"
        f"- Phòng ban: {emp['department']}\n"
        f"- Kỹ năng ({len(skills)}): {', '.join(skills)}"
    )


@tool
def search_employees_by_skill(skill: str, department: str = "") -> str:
    """Search for employees who have a specific skill. Optionally filter by department.

    Args:
        skill: Skill name to search for (e.g. 'Python', 'Docker', 'CRM')
        department: Optional department filter (e.g. 'Engineering')
    """
    employees = _load_employees()
    matches = []
    for emp in employees:
        if emp.get("status") != "Active":
            continue
        if department and emp.get("department", "").lower() != department.lower():
            continue
        emp_skills = [s.lower() for s in emp.get("skills", [])]
        if skill.lower() in emp_skills or any(skill.lower() in s for s in emp_skills):
            matches.append(emp)

    if not matches:
        return f"Không tìm thấy nhân viên nào có kỹ năng '{skill}'" + (
            f" trong phòng {department}." if department else "."
        )

    lines = [f"Tìm thấy **{len(matches)} nhân viên** có kỹ năng '{skill}':\n"]
    for m in matches[:15]:  # cap at 15 results
        lines.append(
            f"- {m['employee_id']} | {m['name']} | {m['position']} | {m['department']}"
        )
    if len(matches) > 15:
        lines.append(f"... và {len(matches) - 15} người khác.")
    return "\n".join(lines)


@tool
def get_skill_gap(employee_id: str, target_position: str = "") -> str:
    """Analyze skill gap between an employee's current skills and required skills for a position.
    If no target_position given, uses their current position.

    Args:
        employee_id: Employee ID (e.g. EMP001)
        target_position: Target job position to compare against (optional)
    """
    employees = _load_employees()
    emp = next(
        (e for e in employees if e["employee_id"].upper() == employee_id.upper()), None
    )
    if not emp:
        return f"Không tìm thấy nhân viên {employee_id}."

    pos = target_position or emp["position"]
    required = _JOB_SKILLS.get(pos)
    if not required:
        return (
            f"Chưa có dữ liệu yêu cầu kỹ năng cho vị trí '{pos}'. "
            f"Các vị trí được hỗ trợ: {', '.join(_JOB_SKILLS.keys())}"
        )

    current = set(s.lower() for s in emp.get("skills", []))
    required_lower = set(s.lower() for s in required)

    has = required_lower & current
    missing = required_lower - current

    pct = round(len(has) / len(required_lower) * 100) if required_lower else 0

    lines = [
        f"**Phân tích Skill Gap — {emp['name']} ({employee_id})**",
        f"Vị trí đánh giá: **{pos}**",
        f"Mức độ đáp ứng: **{pct}%** ({len(has)}/{len(required_lower)} kỹ năng)\n",
        f"Kỹ năng ĐÃ CÓ: {', '.join(sorted(has)) or 'Chưa có'}",
        f"Kỹ năng CAN THIET THEM: {', '.join(sorted(missing)) or 'Khong con thiếu!'}",
    ]
    if missing:
        lines.append(
            "\nGoi y: Nen dao tao them cac ky nang con thieu de dat yeu cau vi tri."
        )
    return "\n".join(lines)


@tool
def update_employee_skills(
    employee_id: str, skills_to_add: str = "", skills_to_remove: str = ""
) -> str:
    """Update an employee's skill list. Can add and/or remove skills.

    Args:
        employee_id: Employee ID (e.g. EMP001)
        skills_to_add: Comma-separated skills to add (e.g. 'Python, Docker')
        skills_to_remove: Comma-separated skills to remove (e.g. 'Java')
    """
    employees = _load_employees()
    idx = next(
        (
            i
            for i, e in enumerate(employees)
            if e["employee_id"].upper() == employee_id.upper()
        ),
        None,
    )
    if idx is None:
        return f"Không tìm thấy nhân viên {employee_id}."

    emp = employees[idx]
    current = set(emp.get("skills", []))

    added = []
    removed = []

    if skills_to_add:
        new_skills = [s.strip() for s in skills_to_add.split(",") if s.strip()]
        for s in new_skills:
            if s not in current:
                current.add(s)
                added.append(s)

    if skills_to_remove:
        rm_skills = [s.strip() for s in skills_to_remove.split(",") if s.strip()]
        for s in rm_skills:
            if s in current:
                current.discard(s)
                removed.append(s)

    employees[idx]["skills"] = sorted(current)
    _save_employees(employees)

    parts = []
    if added:
        parts.append(f"Thêm: {', '.join(added)}")
    if removed:
        parts.append(f"Xóa: {', '.join(removed)}")
    if not parts:
        parts = ["Không có thay đổi."]

    return (
        f"Cap nhat ky nang cho {emp['name']} ({employee_id}) thanh cong.\n"
        + " | ".join(parts)
        + f"\nTong so ky nang hien tai: {len(current)}"
    )


@tool
def get_department_skills_summary(department: str) -> str:
    """Get a summary of all skills available across a department.

    Args:
        department: Department name (e.g. 'Engineering', 'HR', 'Sales')
    """
    employees = _load_employees()
    dept_employees = [
        e
        for e in employees
        if e.get("department", "").lower() == department.lower()
        and e.get("status") == "Active"
    ]
    if not dept_employees:
        return f"Không tìm thấy nhân viên active trong phòng ban '{department}'."

    skill_count: dict[str, int] = {}
    for emp in dept_employees:
        for skill in emp.get("skills", []):
            skill_count[skill] = skill_count.get(skill, 0) + 1

    top = sorted(skill_count.items(), key=lambda x: x[1], reverse=True)[:12]

    lines = [
        f"**Tổng hợp kỹ năng — Phòng {department}**",
        f"Tổng nhân viên active: {len(dept_employees)}\n",
        "Top kỹ năng phổ biến nhất:",
    ]
    for skill, cnt in top:
        bar = "█" * cnt + "░" * max(0, 10 - cnt)
        lines.append(f"  {skill:<30} {bar} ({cnt} người)")
    return "\n".join(lines)


# Export list for agent binding
skills_tools: list[Any] = [
    get_employee_skills,
    search_employees_by_skill,
    get_skill_gap,
    update_employee_skills,
    get_department_skills_summary,
]
