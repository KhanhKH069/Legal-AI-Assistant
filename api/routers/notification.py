"""Notification API Router"""

import json
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/notifications", tags=["Notifications"])

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "notifications_data.json"
)


def _load_data() -> dict:
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Notification data not available")


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


@router.get("/{employee_id}")
def get_employee_notifications(employee_id: str):
    """Get all notifications for a specific employee (personal + broadcast)."""
    data = _load_data()
    eid = employee_id.strip().upper()
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


@router.post("/send")
def send_notification(payload: NotificationPayload):
    """Send an internal notification to an employee."""
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"notifications": [], "hr_announcements": []}

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

    with open(_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"status": "sent", "notification_id": notif_id, "notification": new_notif}


@router.post("/broadcast")
def broadcast_announcement(payload: BroadcastPayload):
    """Publish an HR announcement to all employees or a specific department."""
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"notifications": [], "hr_announcements": []}

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

    with open(_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"status": "published", "announcement_id": ann_id, "announcement": new_ann}


@router.get("/announcements/all")
def get_announcements():
    """Get all official HR announcements."""
    data = _load_data()
    announcements = sorted(
        data.get("hr_announcements", []),
        key=lambda x: x.get("published_at", ""),
        reverse=True,
    )
    return {"announcements": announcements, "total": len(announcements)}
