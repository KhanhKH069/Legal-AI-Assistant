"""Attendance API Router — backed by SQLite AttendanceRecord table."""

import json
import os
from datetime import datetime, date, UTC
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from api.database import get_session
from api.models import AttendanceRecord, LeaveRequest, Employee, User, AuditLog
from api.auth import get_current_user

router = APIRouter(prefix="/attendance", tags=["Attendance"])

# ── Helpers ──────────────────────────────────────────────────────────────────

_STANDARD_WORK_HOURS = 9.0  # hours per day (08:00–17:00)


def _hours_between(check_in: str, check_out: str) -> float:
    """Calculate hours between two HH:MM strings."""
    try:
        fmt = "%H:%M"
        ci = datetime.strptime(check_in, fmt)
        co = datetime.strptime(check_out, fmt)
        diff = (co - ci).seconds / 3600
        return round(diff, 2)
    except Exception:
        return 0.0


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


# ── Payloads ──────────────────────────────────────────────────────────────────


class LeaveRequestPayload(BaseModel):
    employee_id: str
    leave_type: str
    start_date: str
    end_date: str
    reason: str


class CheckInPayload(BaseModel):
    check_in_time: Optional[str] = None  # HH:MM, defaults to now


class CheckOutPayload(BaseModel):
    check_out_time: Optional[str] = None  # HH:MM, defaults to now


class LeaveApprovalPayload(BaseModel):
    action: str  # "approve" | "reject"
    comment: Optional[str] = None


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.get("/{employee_id}")
def get_attendance(
    employee_id: str,
    week: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get attendance records for an employee (latest week or specific YYYY-Www)."""
    eid = employee_id.strip().upper()

    # RBAC check
    if current_user.role == "employee" and current_user.employee_id != eid:
        raise HTTPException(
            status_code=403, detail="Not authorized to view this record"
        )

    query = select(AttendanceRecord).where(AttendanceRecord.employee_id == eid)
    if week:
        query = query.where(AttendanceRecord.week == week)

    records = session.exec(query.order_by(AttendanceRecord.date)).all()

    # If no DB records yet, fall back to JSON (backward compatibility)
    if not records:
        _data_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "attendance_data.json"
        )
        try:
            with open(_data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            record = data.get("attendance_records", {}).get(eid)
            if record:
                return {
                    "employee_id": eid,
                    "source": "json_fallback",
                    "attendance": record,
                }
        except FileNotFoundError:
            pass
        raise HTTPException(status_code=404, detail=f"No attendance record for {eid}")

    daily = [
        {
            "date": r.date,
            "day": r.day_of_week,
            "week": r.week,
            "check_in": r.check_in,
            "check_out": r.check_out,
            "total_hours": r.total_hours,
            "ot_hours": r.ot_hours,
            "status": r.status,
        }
        for r in records
    ]
    total_hours = sum(r.total_hours for r in records)
    total_ot = sum(r.ot_hours for r in records)
    present_days = sum(1 for r in records if r.status == "Present")

    emp = session.exec(select(Employee).where(Employee.employee_id == eid)).first()
    emp_name = emp.name if emp else "Unknown"
    current_week = week or datetime.now().strftime("%Y-W%W")

    return {
        "employee_id": eid,
        "source": "sqlite",
        "attendance": {
            "name": emp_name,
            "week": current_week,
            "daily_records": daily,
            "weekly_summary": {
                "total_working_days": present_days,
                "total_hours": round(total_hours, 2),
                "total_ot_hours": round(total_ot, 2),
                "absent_days": sum(1 for r in records if r.status == "Absent"),
                "leave_days": sum(1 for r in records if r.status == "Leave"),
            },
        },
    }


@router.post("/{employee_id}/check-in")
def check_in(
    employee_id: str,
    payload: CheckInPayload,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Record a check-in for today. Employees can only check in for themselves."""
    eid = employee_id.strip().upper()
    if current_user.role == "employee" and current_user.employee_id != eid:
        raise HTTPException(status_code=403, detail="Can only check in for yourself")

    emp = session.exec(select(Employee).where(Employee.employee_id == eid)).first()
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {eid} not found")

    today = date.today().isoformat()
    existing = session.exec(
        select(AttendanceRecord).where(
            AttendanceRecord.employee_id == eid,
            AttendanceRecord.date == today,
        )
    ).first()
    if existing and existing.check_in:
        raise HTTPException(
            status_code=409, detail=f"Already checked in at {existing.check_in}"
        )

    now_time = payload.check_in_time or datetime.now().strftime("%H:%M")
    week_str = datetime.now().strftime("%Y-W%W")
    day_name = datetime.now().strftime("%A")

    if existing:
        existing.check_in = now_time
        session.add(existing)
    else:
        session.add(
            AttendanceRecord(
                employee_id=eid,
                date=today,
                day_of_week=day_name,
                week=week_str,
                check_in=now_time,
                status="Present",
            )
        )

    _log(
        session,
        current_user.employee_id or current_user.username,
        "CHECK_IN",
        eid,
        f"at {now_time}",
    )
    session.commit()
    return {
        "status": "checked_in",
        "employee_id": eid,
        "date": today,
        "check_in": now_time,
    }


@router.post("/{employee_id}/check-out")
def check_out(
    employee_id: str,
    payload: CheckOutPayload,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Record a check-out for today and compute total/OT hours."""
    eid = employee_id.strip().upper()
    if current_user.role == "employee" and current_user.employee_id != eid:
        raise HTTPException(status_code=403, detail="Can only check out for yourself")

    today = date.today().isoformat()
    record = session.exec(
        select(AttendanceRecord).where(
            AttendanceRecord.employee_id == eid,
            AttendanceRecord.date == today,
        )
    ).first()
    if not record:
        raise HTTPException(
            status_code=404,
            detail="No check-in found for today. Please check in first.",
        )
    if record.check_out:
        raise HTTPException(
            status_code=409, detail=f"Already checked out at {record.check_out}"
        )

    now_time = payload.check_out_time or datetime.now().strftime("%H:%M")
    total = _hours_between(record.check_in or "08:00", now_time)
    ot = max(round(total - _STANDARD_WORK_HOURS, 2), 0.0)

    record.check_out = now_time
    record.total_hours = total
    record.ot_hours = ot
    session.add(record)
    _log(
        session,
        current_user.employee_id or current_user.username,
        "CHECK_OUT",
        eid,
        f"at {now_time}, OT={ot}h",
    )
    session.commit()

    return {
        "status": "checked_out",
        "employee_id": eid,
        "date": today,
        "check_in": record.check_in,
        "check_out": now_time,
        "total_hours": total,
        "ot_hours": ot,
    }


@router.get("/{employee_id}/leave-requests")
def get_leave_requests(
    employee_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get all leave requests for an employee from DB."""
    if (
        current_user.role == "employee"
        and current_user.employee_id != employee_id.upper()
    ):
        raise HTTPException(status_code=403, detail="Not authorized")

    eid = employee_id.strip().upper()
    requests = session.exec(
        select(LeaveRequest).where(LeaveRequest.employee_id == eid)
    ).all()
    return {"employee_id": eid, "leave_requests": requests, "total": len(requests)}


@router.post("/leave-request")
def submit_leave_request(
    payload: LeaveRequestPayload,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Submit a new leave request to DB."""
    eid = payload.employee_id.upper()
    if current_user.role == "employee" and current_user.employee_id != eid:
        raise HTTPException(status_code=403, detail="Can only submit for yourself")

    count = len(session.exec(select(LeaveRequest)).all())
    request_id = f"LR-{datetime.now().year}-{count + 1:03d}"

    start = datetime.strptime(payload.start_date, "%Y-%m-%d").date()
    end = datetime.strptime(payload.end_date, "%Y-%m-%d").date()
    days = (end - start).days + 1

    new_request = LeaveRequest(
        request_id=request_id,
        employee_id=eid,
        type=payload.leave_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        days=days,
        reason=payload.reason,
        status="Pending",
        submitted_at=datetime.now().isoformat(),
    )
    session.add(new_request)
    _log(
        session,
        current_user.employee_id or current_user.username,
        "SUBMIT_LEAVE",
        eid,
        f"{payload.leave_type} {payload.start_date}→{payload.end_date}",
    )
    session.commit()
    session.refresh(new_request)
    return {"status": "created", "request_id": request_id, "leave_request": new_request}


@router.put("/leave-request/{request_id}/approve")
def approve_leave_request(
    request_id: str,
    payload: LeaveApprovalPayload,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Approve or reject a leave request. Managers and admins only."""
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403, detail="Only managers or admins can approve leave requests"
        )

    action = payload.action.lower()
    if action not in ["approve", "reject"]:
        raise HTTPException(
            status_code=400, detail="action must be 'approve' or 'reject'"
        )

    lr = session.exec(
        select(LeaveRequest).where(LeaveRequest.request_id == request_id)
    ).first()
    if not lr:
        raise HTTPException(
            status_code=404, detail=f"Leave request {request_id} not found"
        )
    if lr.status != "Pending":
        raise HTTPException(
            status_code=409, detail=f"Leave request is already {lr.status}"
        )

    lr.status = "Approved" if action == "approve" else "Rejected"
    lr.approved_by = current_user.employee_id or current_user.username
    session.add(lr)

    # If approved, deduct leave balance from Employee
    if action == "approve":
        emp = session.exec(
            select(Employee).where(Employee.employee_id == lr.employee_id)
        ).first()
        if emp:
            emp.leave_balance = max(emp.leave_balance - lr.days, 0)
            session.add(emp)

    _log(
        session,
        current_user.employee_id or current_user.username,
        "APPROVE_LEAVE" if action == "approve" else "REJECT_LEAVE",
        lr.employee_id,
        f"Request {request_id} | {lr.days} days",
    )
    session.commit()

    return {
        "status": lr.status,
        "request_id": request_id,
        "employee_id": lr.employee_id,
        "approved_by": lr.approved_by,
        "leave_balance_remaining": None,
    }
