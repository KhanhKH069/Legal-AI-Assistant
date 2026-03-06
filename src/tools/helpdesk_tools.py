"""Helpdesk Tools — HR Support Ticket Management"""

import json
import os
from datetime import datetime
from typing import Any, Dict
from langchain_core.tools import tool

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "helpdesk_data.json"
)


def _load_helpdesk_data() -> dict:
    """Load helpdesk data from JSON."""
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"tickets": [], "categories": [], "sla_hours": {}}


def _save_helpdesk_data(data: dict) -> None:
    """Save helpdesk data back to JSON."""
    with open(_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@tool
def create_hr_ticket(
    employee_id: str,
    category: str,
    subject: str,
    description: str,
    priority: str = "Medium",
) -> str:
    """Create a new HR support ticket for an employee.

    Args:
        employee_id: The employee ID requesting support (e.g., EMP001).
        category: Category — 'Equipment', 'Payroll', 'Leave',
                  'Benefits', 'Training', 'HR Policy', 'IT Support',
                  'Other'.
        subject: Short title of the issue.
        description: Detailed description of the issue or request.
        priority: Priority — 'Low', 'Medium', 'High', 'Critical'.
                  Default is 'Medium'.

    Returns:
        Confirmation with generated ticket ID.
    """
    data = _load_helpdesk_data()
    eid = employee_id.strip().upper()
    tickets = data.get("tickets", [])

    ticket_id = f"TICK-{datetime.now().year}-{len(tickets) + 1:03d}"
    sla = data.get("sla_hours", {}).get(priority, 72)

    new_ticket: Dict[str, Any] = {
        "ticket_id": ticket_id,
        "employee_id": eid,
        "category": category,
        "subject": subject,
        "description": description,
        "priority": priority,
        "status": "Open",
        "assigned_to": "HR Team",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "resolution": None,
        "comments": [],
    }

    tickets.append(new_ticket)
    data["tickets"] = tickets
    _save_helpdesk_data(data)

    priority_icons = {"Low": "🔵", "Medium": "🟡", "High": "🟠", "Critical": "🔴"}
    icon = priority_icons.get(priority, "🟡")

    return (
        f"✅ Ticket hỗ trợ HR đã được tạo thành công!\n"
        f"   🎫 Mã ticket: {ticket_id}\n"
        f"   📂 Danh mục: {category}\n"
        f"   📝 Tiêu đề: {subject}\n"
        f"   {icon} Mức độ ưu tiên: {priority}\n"
        f"   👥 Được chuyển đến: HR Team\n"
        f"   ⏰ SLA: Phản hồi trong vòng {sla} giờ\n"
        f"   Trạng thái: 🔓 Open\n"
        f"Chúng tôi sẽ liên hệ với bạn sớm nhất có thể!"
    )


@tool
def get_ticket_status(ticket_id: str) -> str:
    """Get the current status and details of an HR support ticket.

    Args:
        ticket_id: The ticket ID (e.g., TICK-2026-001).

    Returns:
        Current status, assigned team, and any comments on the ticket.
    """
    data = _load_helpdesk_data()
    ticket = next(
        (t for t in data.get("tickets", []) if t["ticket_id"] == ticket_id), None
    )

    if not ticket:
        return f"❌ Không tìm thấy ticket {ticket_id}."

    status_icons = {
        "Open": "🔓",
        "In Progress": "🔄",
        "Pending Employee": "⏳",
        "Resolved": "✅",
        "Closed": "🔒",
    }
    icon = status_icons.get(ticket["status"], "❓")

    lines = [
        f"🎫 Ticket {ticket['ticket_id']}",
        f"   📝 Tiêu đề: {ticket['subject']}",
        f"   📂 Danh mục: {ticket['category']}",
        f"   🏷️ Mức độ: {ticket['priority']}",
        f"   {icon} Trạng thái: {ticket['status']}",
        f"   👥 Được xử lý bởi: {ticket['assigned_to']}",
        f"   📅 Tạo lúc: {ticket['created_at'][:10]}",
    ]

    if ticket.get("resolution"):
        lines.append(f"   🔑 Giải pháp: {ticket['resolution']}")

    if ticket.get("comments"):
        lines.append("   💬 Cập nhật gần nhất:")
        for c in ticket["comments"][-2:]:
            lines.append(f"      [{c['author']}] {c['message']}")

    return "\n".join(lines)


@tool
def list_employee_tickets(employee_id: str) -> str:
    """List all HR support tickets for a specific employee.

    Args:
        employee_id: The employee ID (e.g., EMP001).

    Returns:
        Summary list of all tickets with their statuses.
    """
    data = _load_helpdesk_data()
    eid = employee_id.strip().upper()
    tickets = [t for t in data.get("tickets", []) if t["employee_id"] == eid]

    if not tickets:
        return f"Nhân viên {eid} chưa có ticket hỗ trợ nào."

    status_icons = {
        "Open": "🔓",
        "In Progress": "🔄",
        "Pending Employee": "⏳",
        "Resolved": "✅",
        "Closed": "🔒",
    }
    lines = [f"🎫 Danh sách ticket HR của {eid}:", "-" * 40]
    for t in tickets:
        icon = status_icons.get(t["status"], "❓")
        lines.append(
            f"{icon} [{t['ticket_id']}] {t['subject']} "
            f"({t['category']}) — {t['status']}"
        )

    return "\n".join(lines)
