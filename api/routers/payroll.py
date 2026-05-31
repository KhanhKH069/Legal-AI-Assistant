"""Payroll API Router — with pagination on summary endpoint."""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from api.database import get_session
from api.models import PayrollRecord, Employee, User, AuditLog
from api.auth import get_current_user
from datetime import datetime, UTC

router = APIRouter(prefix="/payroll", tags=["Payroll"])


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


@router.get("/{employee_id}")
def get_payroll_history(
    employee_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get full payroll history for an employee (all months)."""
    eid = employee_id.strip().upper()

    # RBAC check
    if current_user.role == "employee" and current_user.employee_id != eid:
        raise HTTPException(
            status_code=403, detail="Not authorized to view this record"
        )

    emp = session.exec(select(Employee).where(Employee.employee_id == eid)).first()
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {eid} not found")

    records = session.exec(
        select(PayrollRecord)
        .where(PayrollRecord.employee_id == eid)
        .order_by(PayrollRecord.month)
    ).all()

    if not records:
        raise HTTPException(status_code=404, detail=f"No payroll record for {eid}")

    # Audit log for managers/admins viewing others' payroll
    if current_user.role in ("admin", "manager") and current_user.employee_id != eid:
        _log(
            session,
            current_user.employee_id or current_user.username,
            "VIEW_PAYROLL_HISTORY",
            eid,
            f"viewer_role={current_user.role}",
        )
        session.commit()

    return {
        "employee_id": eid,
        "name": emp.name,
        "department": emp.department,
        "position": emp.position,
        "salary_history": [r.dict() for r in records],
    }


@router.get("/{employee_id}/month/{month}")
def get_payroll_month(
    employee_id: str,
    month: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get payroll for a specific month. month format: YYYY-MM"""
    eid = employee_id.strip().upper()

    # RBAC check
    if current_user.role == "employee" and current_user.employee_id != eid:
        raise HTTPException(status_code=403, detail="Not authorized")

    emp = session.exec(select(Employee).where(Employee.employee_id == eid)).first()
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {eid} not found")

    record = session.exec(
        select(PayrollRecord).where(
            PayrollRecord.employee_id == eid,
            PayrollRecord.month == month,
        )
    ).first()

    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"No payroll data for {eid} in month {month}",
        )

    return {
        "employee_id": eid,
        "name": emp.name,
        "department": emp.department,
        "position": emp.position,
        "payroll": record.dict(),
    }


@router.get("/summary/all")
def get_payroll_summary(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get payroll summary for all employees (latest month). Admin/Manager only. Supports pagination."""
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403, detail="Only admins or managers can view payroll summaries"
        )

    latest_month_record = session.exec(
        select(PayrollRecord).order_by(PayrollRecord.month.desc())
    ).first()
    if not latest_month_record:
        return {
            "month": "",
            "total_employees": 0,
            "total_payroll": 0,
            "page": page,
            "size": size,
            "employees": [],
        }

    latest_month = latest_month_record.month
    records = session.exec(
        select(PayrollRecord).where(PayrollRecord.month == latest_month)
    ).all()

    summary = []
    total_payroll = 0.0
    for r in records:
        emp = session.exec(
            select(Employee).where(Employee.employee_id == r.employee_id)
        ).first()
        if not emp:
            continue
        summary.append(
            {
                "employee_id": r.employee_id,
                "name": emp.name,
                "department": emp.department,
                "position": emp.position,
                "month": r.month,
                "month_label": r.month_label,
                "base_salary": r.base_salary,
                "ot_pay": r.ot_pay,
                "kpi_bonus": r.kpi_bonus,
                "total_deductions": r.total_deductions,
                "net_salary": r.net_salary,
                "status": r.status,
            }
        )
        total_payroll += r.net_salary

    total = len(summary)
    start = (page - 1) * size

    _log(
        session,
        current_user.employee_id or current_user.username,
        "VIEW_PAYROLL_SUMMARY_ALL",
        "ALL",
        f"month={latest_month}, count={total}, role={current_user.role}",
    )
    session.commit()

    return {
        "month": latest_month,
        "total_employees": total,
        "total_payroll": total_payroll,
        "page": page,
        "size": size,
        "employees": summary[start : start + size],
    }
