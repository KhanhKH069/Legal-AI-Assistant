"""Skills router — Employee skill profile management endpoints."""

import json
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session, select
from api.database import get_session
from api.models import Employee, User
from api.auth import get_current_user

router = APIRouter(prefix="/skills", tags=["skills"])


class UpdateSkillsRequest(BaseModel):
    skills_to_add: Optional[List[str]] = None
    skills_to_remove: Optional[List[str]] = None


@router.get("/employee/{employee_id}")
def get_employee_skills(
    employee_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get the skill profile of a specific employee."""
    emp = session.exec(
        select(Employee).where(Employee.employee_id == employee_id.upper())
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")

    skills = json.loads(emp.skills_json) if emp.skills_json else []

    return {
        "employee_id": emp.employee_id,
        "name": emp.name,
        "position": emp.position,
        "level": emp.level,
        "department": emp.department,
        "skills": skills,
        "skill_count": len(skills),
    }


@router.put("/employee/{employee_id}")
def update_employee_skills(
    employee_id: str,
    req: UpdateSkillsRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Add or remove skills from an employee's profile."""
    eid = employee_id.upper()

    # RBAC: Only self, manager, or admin can update skills
    if current_user.role == "employee" and current_user.employee_id != eid:
        raise HTTPException(
            status_code=403, detail="Not authorized to update skills for this employee"
        )

    emp = session.exec(select(Employee).where(Employee.employee_id == eid)).first()
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")

    current = set(json.loads(emp.skills_json) if emp.skills_json else [])
    added = []
    removed = []

    if req.skills_to_add:
        for s in req.skills_to_add:
            if s not in current:
                current.add(s)
                added.append(s)

    if req.skills_to_remove:
        for s in req.skills_to_remove:
            if s in current:
                current.discard(s)
                removed.append(s)

    new_skills = sorted(list(current))
    emp.skills_json = json.dumps(new_skills)
    session.add(emp)
    session.commit()

    return {
        "employee_id": employee_id,
        "skills": new_skills,
        "added": added,
        "removed": removed,
        "total_skills": len(new_skills),
    }


@router.get("/search")
def search_by_skill(
    skill: str,
    department: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Search for employees with a specific skill."""
    query = select(Employee).where(Employee.status == "Active")
    if department:
        query = query.where(Employee.department == department)

    employees = session.exec(query).all()

    matches = []
    search_term = skill.lower()

    for emp in employees:
        emp_skills = [
            s.lower() for s in (json.loads(emp.skills_json) if emp.skills_json else [])
        ]
        if search_term in emp_skills or any(search_term in s for s in emp_skills):
            matches.append(
                {
                    "employee_id": emp.employee_id,
                    "name": emp.name,
                    "position": emp.position,
                    "department": emp.department,
                    "skills": json.loads(emp.skills_json) if emp.skills_json else [],
                }
            )

    return {"skill": skill, "matches": matches, "total": len(matches)}


@router.get("/department/{department}")
def get_department_skills(
    department: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get skill distribution summary for a department."""
    employees = session.exec(
        select(Employee).where(
            Employee.department == department, Employee.status == "Active"
        )
    ).all()

    if not employees:
        raise HTTPException(
            status_code=404, detail=f"No active employees in '{department}'"
        )

    skill_count: dict = {}
    for emp in employees:
        skills = json.loads(emp.skills_json) if emp.skills_json else []
        for s in skills:
            skill_count[s] = skill_count.get(s, 0) + 1

    top_skills = sorted(skill_count.items(), key=lambda x: x[1], reverse=True)

    return {
        "department": department,
        "employee_count": len(employees),
        "unique_skills": len(skill_count),
        "top_skills": [{"skill": s, "count": c} for s, c in top_skills[:15]],
    }


@router.get("/gap/{employee_id}")
def get_skill_gap(
    employee_id: str,
    target_position: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Analyze skill gap for an employee vs. their position requirements."""
    # Anyone can check skill gaps (useful for team planning)
    _JOB_SKILLS: dict = {
        "Backend Developer": [
            "Python",
            "FastAPI",
            "PostgreSQL",
            "Docker",
            "REST API",
            "Git",
        ],
        "Frontend Developer": ["TypeScript", "React", "CSS", "Git", "REST API"],
        "AI Engineer": ["Python", "PyTorch", "LangChain", "Docker", "REST API"],
        "DevOps Engineer": [
            "Docker",
            "Kubernetes",
            "Terraform",
            "AWS",
            "Linux",
            "CI/CD",
        ],
        "QA Engineer": ["Selenium", "Postman", "Manual Testing", "Bug Tracking"],
        "HR Specialist": [
            "Talent Acquisition",
            "HRIS",
            "Labor Law Vietnam",
            "Onboarding",
        ],
        "HR Manager": ["Performance Management", "SHRM", "Compensation & Benefits"],
        "Sales Executive": ["CRM", "Negotiation", "Pipeline Management"],
        "Sales Manager": ["CRM", "B2B Sales", "Account Management"],
        "Marketing Manager": [
            "Brand Strategy",
            "Content Marketing",
            "Google Analytics",
        ],
        "Product Manager": ["Figma", "Jira", "Agile/Scrum", "Product Roadmap", "OKRs"],
        "Finance Manager": ["Excel", "SAP", "IFRS", "Financial Modeling"],
        "Engineering Manager": ["CI/CD", "Microservices", "Git", "Problem Solving"],
    }

    emp = session.exec(
        select(Employee).where(Employee.employee_id == employee_id.upper())
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")

    pos = target_position or emp.position
    required = _JOB_SKILLS.get(pos, [])

    skills = json.loads(emp.skills_json) if emp.skills_json else []
    current = set(s.lower() for s in skills)
    required_lower = set(s.lower() for s in required)

    has = required_lower & current
    missing = required_lower - current
    pct = round(len(has) / len(required_lower) * 100) if required_lower else 100

    return {
        "employee_id": employee_id,
        "name": emp.name,
        "evaluated_position": pos,
        "match_percentage": pct,
        "has_skills": sorted(list(has)),
        "missing_skills": sorted(list(missing)),
        "required_skills": sorted(list(required_lower)),
    }
