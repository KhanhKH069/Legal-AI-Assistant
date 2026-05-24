"""Contracts router — Contract expiry alerts and employee contract management."""

import json
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from api.database import get_session
from api.models import Employee, User
from api.auth import get_current_user

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.get("/expiring-soon")
def get_expiring_contracts(
    days: int = 30,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get all employee contracts expiring within the given number of days."""
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403, detail="Not authorized to view company-wide contracts"
        )

    days = min(max(days, 1), 365)
    cutoff = date.today() + timedelta(days=days)
    employees = session.exec(select(Employee).where(Employee.status == "Active")).all()

    expiring = []
    expired = []

    for emp in employees:
        contract = json.loads(emp.contract_json) if emp.contract_json else {}
        end_str = contract.get("end", "")
        if not end_str:
            continue

        try:
            end_date = date.fromisoformat(end_str)
        except ValueError:
            continue

        days_left = (end_date - date.today()).days

        rec = {
            "employee_id": emp.employee_id,
            "name": emp.name,
            "position": emp.position,
            "department": emp.department,
            "contract_start": contract.get("start", ""),
            "contract_end": end_str,
            "days_remaining": days_left,
            "urgency": (
                "EXPIRED"
                if days_left < 0
                else "CRITICAL"
                if days_left <= 7
                else "WARNING"
                if days_left <= 14
                else "UPCOMING"
            ),
        }

        if days_left < 0:
            expired.append(rec)
        elif end_date <= cutoff:
            expiring.append(rec)

    expiring.sort(key=lambda x: x["days_remaining"])
    expired.sort(key=lambda x: x["days_remaining"])

    return {
        "check_date": str(date.today()),
        "cutoff_date": str(cutoff),
        "days_ahead": days,
        "expiring_count": len(expiring),
        "expired_count": len(expired),
        "expiring": expiring,
        "expired": expired,
    }


@router.get("/employee/{employee_id}")
def get_employee_contract(
    employee_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get contract details for a specific employee."""
    eid = employee_id.upper()
    if current_user.role == "employee" and current_user.employee_id != eid:
        raise HTTPException(status_code=403, detail="Not authorized")

    emp = session.exec(select(Employee).where(Employee.employee_id == eid)).first()
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {eid} not found")

    contract = json.loads(emp.contract_json) if emp.contract_json else {}
    end_str = contract.get("end", "")
    try:
        end_date = date.fromisoformat(end_str)
        days_left = (end_date - date.today()).days
    except (ValueError, TypeError):
        days_left = None

    return {
        "employee_id": emp.employee_id,
        "name": emp.name,
        "position": emp.position,
        "department": emp.department,
        "contract_start": contract.get("start", ""),
        "contract_end": end_str,
        "days_remaining": days_left,
        "status": emp.status,
    }
