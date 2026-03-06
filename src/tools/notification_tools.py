"""Notification Tools — Internal HR announcements and notifications"""

import json
import os
from datetime import datetime
from langchain_core.tools import tool

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "notifications_data.json"
)


def _load_notification_data() -> dict:
    """Load notification data from JSON."""
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"notifications": [], "hr_announcements": []}


def _save_notification_data(data: dict) -> None:
    """Save notification data back to JSON."""
    with open(_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@tool
def get_employee_notifications(employee_id: str) -> str:
    """Retrieve unread notifications and HR announcements for a specific employee.

    Args:
        employee_id: The employee ID (e.g., EMP001).

    Returns:
        A list of the employee's notifications including unread system messages and HR announcements.
    """
    data = _load_notification_data()
    eid = employee_id.strip().upper()

    # Personal + broadcast notifications
    notifs = [
        n
        for n in data.get("notifications", [])
        if n["recipient_id"] == eid or n["recipient_id"] == "ALL"
    ]

    if not notifs:
        return f"✅ {eid} không có thông báo mới nào."

    type_icons = {
        "Leave Approval": "🏖️",
        "Ticket Update": "🎫",
        "Announcement": "📢",
        "Payroll": "💰",
        "Benefits": "🎁",
    }

    unread = [n for n in notifs if not n.get("is_read")]
    read = [n for n in notifs if n.get("is_read")]

    lines = [f"🔔 Thông Báo của {eid}", "=" * 45]

    if unread:
        lines.append(f"\n🔴 Chưa đọc ({len(unread)}):")
        for n in unread:
            icon = type_icons.get(n["type"], "📌")
            created = n["created_at"][:10]
            lines.append(f"   {icon} [{created}] {n['title']}\n      {n['message']}")

    if read:
        lines.append(f"\n✅ Đã đọc ({len(read)}):")
        for n in read[:2]:  # Show last 2 read
            icon = type_icons.get(n["type"], "📌")
            created = n["created_at"][:10]
            lines.append(f"   {icon} [{created}] {n['title']}")

    return "\n".join(lines)


@tool
def send_internal_notification(
    employee_id: str, title: str, message: str, notification_type: str = "Announcement"
) -> str:
    """Send an internal HR notification to a specific employee.

    Args:
        employee_id: Target employee ID, or 'ALL' to broadcast to everyone.
        title: Short notification title.
        message: Full notification message content.
        notification_type: Type — 'Leave Approval', 'Ticket Update', 'Announcement', 'Payroll', 'Benefits'.

    Returns:
        Confirmation that the notification was sent.
    """
    data = _load_notification_data()
    notifs = data.get("notifications", [])

    notif_id = f"NOTIF-{len(notifs) + 1:03d}"
    new_notif = {
        "notification_id": notif_id,
        "recipient_id": employee_id.strip().upper() if employee_id != "ALL" else "ALL",
        "type": notification_type,
        "title": title,
        "message": message,
        "channel": "system",
        "is_read": False,
        "created_at": datetime.now().isoformat(),
    }

    notifs.append(new_notif)
    data["notifications"] = notifs
    _save_notification_data(data)

    recipient_text = (
        "tất cả nhân viên" if employee_id.upper() == "ALL" else employee_id.upper()
    )
    return (
        f"✅ Thông báo đã được gửi thành công!\n"
        f"   🆔 Mã thông báo: {notif_id}\n"
        f"   📢 Gửi đến: {recipient_text}\n"
        f"   📋 Tiêu đề: {title}\n"
        f"   🏷️ Loại: {notification_type}\n"
        f"   📅 Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )


@tool
def get_hr_announcements() -> str:
    """Get the latest HR announcements for all employees.

    Returns:
        List of recent official HR announcements with date and content.
    """
    data = _load_notification_data()
    announcements = data.get("hr_announcements", [])

    if not announcements:
        return "Hiện tại không có thông báo HR nào."

    lines = ["📢 Thông Báo Chính Thức Từ HR", "=" * 45]
    for ann in reversed(announcements):  # Newest first
        pub_date = ann.get("published_at", "")[:10]
        dept = ann.get("department", "All")
        lines.extend(
            [
                f"\n📌 [{pub_date}] {ann['title']}",
                f"   👥 Đối tượng: {dept}",
                f"   📝 {ann['content']}",
                f"   — {ann.get('published_by', 'HR')}",
            ]
        )

    return "\n".join(lines)
