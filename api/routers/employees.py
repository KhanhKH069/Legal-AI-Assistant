"""Employee router — serves employee list and per-employee monthly info from SQLite.

RBAC rules enforced:
- admin / manager : full access including salary_vnd and contract details
- employee        : salary_vnd and contract redacted for OTHER employees;
                    own profile is fully visible
"""

import json
from datetime import datetime, UTC
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select

from api.database import get_session
from api.models import Employee, User, AuditLog
from api.auth import get_current_user

router = APIRouter(prefix="/employees", tags=["employees"])

_SENSITIVE_FIELDS = {"salary_vnd", "contract"}


def _salary_level(salary: float) -> str:
    if salary < 13_000_000:
        return "L1"
    elif salary < 18_000_000:
        return "L2"
    elif salary < 25_000_000:
        return "L3"
    elif salary < 35_000_000:
        return "L4"
    return "L5"


def _log(session: Session, actor_id: str, action: str, target: str, detail: str = ""):
    session.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            target=target,
            detail=detail,
            timestamp=datetime.now(UTC).isoformat(),
        )
    )


def _redact(emp_dict: dict) -> dict:
    """Remove sensitive salary/contract fields for non-privileged viewers."""
    emp_dict["salary_vnd"] = None
    emp_dict["contract"] = {}
    return emp_dict


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("")
def list_employees(
    search: Optional[str] = None,
    page: int = 1,
    size: int = 50,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Return list of active employees. Supports ?search=, ?page=, ?size=."""
    query = select(Employee).where(Employee.status == "Active")
    employees = session.exec(query).all()

    result = []
    for r in employees:
        if (
            search
            and search.lower() not in r.name.lower()
            and search.lower() not in r.employee_id.lower()
        ):
            continue
        result.append(
            {
                "employee_id": r.employee_id,
                "name": r.name,
                "department": r.department,
                "position": r.position,
            }
        )

    total = len(result)
    start = (page - 1) * size
    return {
        "total": total,
        "page": page,
        "size": size,
        "employees": result[start : start + size],
    }


@router.get("/all-profiles")
def get_all_profiles(
    department: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    size: int = 50,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Return full employee profiles from database.

    Salary and contract info are redacted for `employee` role users
    (they may only see their own full details via /{id}/profile).
    """
    query = select(Employee)
    if department:
        query = query.where(Employee.department == department)
    if status:
        query = query.where(Employee.status == status)

    employees = session.exec(query).all()

    result = []
    is_privileged = current_user.role in ("admin", "manager")

    for e in employees:
        if search:
            s = search.lower()
            if s not in e.name.lower() and s not in e.employee_id.lower():
                continue

        emp_dict = e.model_dump()
        emp_dict["skills"] = json.loads(e.skills_json) if e.skills_json else []
        emp_dict["contract"] = json.loads(e.contract_json) if e.contract_json else {}

        # RBAC: employees see redacted data for everyone except themselves
        if not is_privileged and e.employee_id != current_user.employee_id:
            _redact(emp_dict)

        result.append(emp_dict)

    total = len(result)
    start = (page - 1) * size

    # Log access for privileged users viewing all salary data
    if is_privileged:
        _log(
            session,
            current_user.employee_id or current_user.username,
            "VIEW_ALL_PROFILES",
            "ALL",
            f"role={current_user.role}, dept={department}, count={total}",
        )
        session.commit()

    return {
        "employees": result[start : start + size],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/{employee_id}/profile")
def get_employee_profile_full(
    employee_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Return full profile for a single employee (with skills, contract, org info)."""
    emp = session.exec(
        select(Employee).where(Employee.employee_id == employee_id.upper())
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")

    emp_dict = emp.model_dump()
    emp_dict["skills"] = json.loads(emp.skills_json) if emp.skills_json else []
    emp_dict["contract"] = json.loads(emp.contract_json) if emp.contract_json else {}

    # Enrich with manager name
    if emp.manager_id:
        manager = session.exec(
            select(Employee).where(Employee.employee_id == emp.manager_id)
        ).first()
        emp_dict["manager_name"] = manager.name if manager else None
        emp_dict["manager_position"] = manager.position if manager else None

    # RBAC: redact sensitive info if not authorized
    is_own = current_user.employee_id == emp.employee_id
    is_privileged = current_user.role in ("admin", "manager")
    if not is_own and not is_privileged:
        _redact(emp_dict)

    # Audit log for privileged salary access
    if is_privileged and not is_own:
        _log(
            session,
            current_user.employee_id or current_user.username,
            "VIEW_SALARY",
            emp.employee_id,
            f"viewer_role={current_user.role}",
        )
        session.commit()

    return emp_dict


@router.get("/{employee_id}/monthly")
def get_monthly_info(
    employee_id: str,
    month: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Return employee monthly snapshot. month format: YYYY-MM (default = current month)."""
    eid = employee_id.upper()

    # RBAC check
    if current_user.role == "employee" and current_user.employee_id != eid:
        raise HTTPException(
            status_code=403, detail="Not authorized to view this employee's snapshot"
        )

    emp = session.exec(select(Employee).where(Employee.employee_id == eid)).first()
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")

    now = datetime.now()
    target_month = month or now.strftime("%Y-%m")
    try:
        month_dt = datetime.strptime(target_month, "%Y-%m")
    except ValueError:
        raise HTTPException(status_code=400, detail="month must be YYYY-MM")

    month_label = month_dt.strftime("%B %Y")

    import calendar

    _, days_in_month = calendar.monthrange(month_dt.year, month_dt.month)
    working_days = sum(
        1
        for d in range(1, days_in_month + 1)
        if datetime(month_dt.year, month_dt.month, d).weekday() < 5
    )

    return {
        "employee_id": emp.employee_id,
        "name": emp.name,
        "department": emp.department,
        "position": emp.position,
        "hire_date": emp.hire_date,
        "status": emp.status,
        "salary_level": _salary_level(float(emp.salary_vnd)),
        "performance_rating": float(emp.performance_rating),
        "leave_balance": int(emp.leave_balance),
        "month": target_month,
        "month_label": month_label,
        "working_days_in_month": working_days,
        "days_worked": working_days,
        "leave_taken_this_month": 0,
    }


from api.models import PayrollRecord, Appraisal, LeaveRequest, Ticket


@router.get("/me/metrics")
def get_my_metrics(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Lấy số liệu cá nhân của nhân viên đang đăng nhập"""
    if not current_user.employee_id:
        raise HTTPException(status_code=400, detail="User is not linked to an employee")

    emp = session.exec(
        select(Employee).where(Employee.employee_id == current_user.employee_id)
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee record not found")

    # Get latest payroll
    payroll = session.exec(
        select(PayrollRecord)
        .where(PayrollRecord.employee_id == emp.employee_id)
        .order_by(PayrollRecord.month.desc())
    ).first()

    # Get latest appraisal
    appraisal = session.exec(
        select(Appraisal)
        .where(Appraisal.employee_id == emp.employee_id)
        .order_by(Appraisal.period.desc())
    ).first()

    # Get pending leaves count
    pending_leaves = len(
        session.exec(
            select(LeaveRequest)
            .where(LeaveRequest.employee_id == emp.employee_id)
            .where(LeaveRequest.status == "Pending")
        ).all()
    )

    # Get open tickets count
    open_tickets = len(
        session.exec(
            select(Ticket)
            .where(Ticket.employee_id == emp.employee_id)
            .where(Ticket.status == "Open")
        ).all()
    )

    return {
        "employee": {
            "name": emp.name,
            "department": emp.department,
            "position": emp.position,
            "level": emp.level,
            "base_salary": emp.salary_vnd,
            "leave_balance": emp.leave_balance,
            "performance_rating": emp.performance_rating,
        },
        "latest_payroll": payroll.model_dump() if payroll else None,
        "latest_appraisal": appraisal.model_dump() if appraisal else None,
        "pending_leaves": pending_leaves,
        "open_tickets": open_tickets,
    }
