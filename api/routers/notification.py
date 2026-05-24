"""Notification API Router — with mark-as-read and unread count endpoints."""

import json
import os
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from api.models import User
from api.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "notifications_data.json"
)


def _load_data() -> dict:
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"notifications": [], "hr_announcements": []}


def _save_data(data: dict):
    with open(_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Payloads ──────────────────────────────────────────────────────────────────


class BroadcastPayload(BaseModel):
    title: str
    content: str
    department: str = "All"
    published_by: str = "HR Team"


class NotificationPayload(BaseModel):
    recipient_id: str
    title: str
    message: str
    notification_type: str = "Announcement"


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.get("/{employee_id}")
def get_employee_notifications(
    employee_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get all notifications for a specific employee (personal + broadcast)."""
    eid = employee_id.strip().upper()
    if current_user.role == "employee" and current_user.employee_id != eid:
        raise HTTPException(status_code=403, detail="Not authorized")

    data = _load_data()
    notifs = [
        n
        for n in data.get("notifications", [])
        if n["recipient_id"] == eid or n["recipient_id"] == "ALL"
    ]
    unread = [n for n in notifs if not n.get("is_read")]
    return {
        "employee_id": eid,
        "total": len(notifs),
        "unread": len(unread),
        "notifications": notifs,
    }


@router.get("/{employee_id}/unread-count")
def get_unread_count(
    employee_id: str,
    current_user: User = Depends(get_current_user),
):
    """Fast endpoint — returns only unread notification count. For navbar badge."""
    eid = employee_id.strip().upper()
    if current_user.role == "employee" and current_user.employee_id != eid:
        raise HTTPException(status_code=403, detail="Not authorized")

    data = _load_data()
    unread = sum(
        1
        for n in data.get("notifications", [])
        if (n["recipient_id"] == eid or n["recipient_id"] == "ALL")
        and not n.get("is_read")
    )
    return {"employee_id": eid, "unread_count": unread}


@router.put("/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
):
    """Mark a notification as read. Employees can only mark their own."""
    data = _load_data()
    notifs = data.get("notifications", [])

    for n in notifs:
        if n.get("notification_id") == notification_id:
            # RBAC: employee can only mark notifications addressed to them
            if current_user.role == "employee":
                recipient = n.get("recipient_id", "")
                if recipient not in (current_user.employee_id, "ALL"):
                    raise HTTPException(status_code=403, detail="Not authorized")
            n["is_read"] = True
            n["read_at"] = datetime.now().isoformat()
            data["notifications"] = notifs
            _save_data(data)
            return {"status": "marked_read", "notification_id": notification_id}

    raise HTTPException(
        status_code=404, detail=f"Notification {notification_id} not found"
    )


@router.post("/send")
def send_notification(
    payload: NotificationPayload,
    current_user: User = Depends(get_current_user),
):
    """Send an internal notification to an employee. Admin/Manager only."""
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403, detail="Only HR/Managers can send notifications"
        )

    data = _load_data()
    notifs = data.get("notifications", [])
    notif_id = f"NOTIF-{len(notifs) + 1:03d}"

    new_notif = {
        "notification_id": notif_id,
        "recipient_id": payload.recipient_id.upper(),
        "type": payload.notification_type,
        "title": payload.title,
        "message": payload.message,
        "channel": "system",
        "is_read": False,
        "created_at": datetime.now().isoformat(),
    }
    notifs.append(new_notif)
    data["notifications"] = notifs
    _save_data(data)
    return {"status": "sent", "notification_id": notif_id, "notification": new_notif}


@router.post("/broadcast")
def broadcast_announcement(
    payload: BroadcastPayload,
    current_user: User = Depends(get_current_user),
):
    """Publish an HR announcement to all employees or a specific department. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="Only HR Admin can broadcast announcements"
        )

    data = _load_data()
    announcements = data.get("hr_announcements", [])
    ann_id = f"ANN-{len(announcements) + 1:03d}"

    new_ann = {
        "announcement_id": ann_id,
        "title": payload.title,
        "content": payload.content,
        "department": payload.department,
        "published_by": payload.published_by,
        "published_at": datetime.now().isoformat(),
    }
    announcements.append(new_ann)
    data["hr_announcements"] = announcements
    _save_data(data)
    return {"status": "published", "announcement_id": ann_id, "announcement": new_ann}


@router.get("/announcements/all")
def get_announcements(current_user: User = Depends(get_current_user)):
    """Get all official HR announcements (all authenticated users)."""
    data = _load_data()
    announcements = sorted(
        data.get("hr_announcements", []),
        key=lambda x: x.get("published_at", ""),
        reverse=True,
    )
    return {"announcements": announcements, "total": len(announcements)}
