"""Attendance API Router"""

import json
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/attendance", tags=["Attendance"])

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "attendance_data.json"
)


def _load_data() -> dict:
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Attendance data not available")


class LeaveRequestPayload(BaseModel):
    employee_id: str
    leave_type: str
    start_date: str
    end_date: str
    reason: str


@router.get("/{employee_id}")
def get_attendance(employee_id: str):
    """Get weekly attendance record for an employee."""
    data = _load_data()
    eid = employee_id.strip().upper()
    record = data.get("attendance_records", {}).get(eid)
    if not record:
        raise HTTPException(status_code=404, detail=f"No attendance record for {eid}")
    return {"employee_id": eid, "attendance": record}


@router.get("/{employee_id}/leave-requests")
def get_leave_requests(employee_id: str):
    """Get all leave requests for an employee."""
    data = _load_data()
    eid = employee_id.strip().upper()
    requests = [r for r in data.get("leave_requests", []) if r["employee_id"] == eid]
    return {"employee_id": eid, "leave_requests": requests, "total": len(requests)}


@router.post("/leave-request")
def submit_leave_request(payload: LeaveRequestPayload):
    """Submit a new leave request."""
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"attendance_records": {}, "leave_requests": [], "ot_policy": {}}

    existing = data.get("leave_requests", [])
    request_id = f"LR-{datetime.now().year}-{len(existing) + 1:03d}"

    start = datetime.strptime(payload.start_date, "%Y-%m-%d").date()
    end = datetime.strptime(payload.end_date, "%Y-%m-%d").date()
    days = (end - start).days + 1

    new_request = {
        "request_id": request_id,
        "employee_id": payload.employee_id.upper(),
        "type": payload.leave_type,
        "start_date": payload.start_date,
        "end_date": payload.end_date,
        "days": days,
        "reason": payload.reason,
        "status": "Pending",
        "approved_by": None,
        "submitted_at": datetime.now().isoformat(),
    }
    existing.append(new_request)
    data["leave_requests"] = existing

    with open(_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"status": "created", "request_id": request_id, "leave_request": new_request}
