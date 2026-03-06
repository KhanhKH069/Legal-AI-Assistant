"""Attendance Tools — loads from attendance_data.json"""

import json
import os
from datetime import datetime
from langchain_core.tools import tool

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "attendance_data.json"
)


def _load_attendance_data() -> dict:
    """Load attendance data from JSON."""
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"attendance_records": {}, "leave_requests": [], "ot_policy": {}}


def _save_attendance_data(data: dict) -> None:
    """Save attendance data back to JSON."""
    with open(_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@tool
def get_attendance_record(employee_id: str) -> str:
    """Retrieve the weekly attendance record for a specific employee.

    Args:
        employee_id: The ID of the employee (e.g., EMP001, EMP002).

    Returns:
        A detailed string of the employee's attendance this week
        including check-in/out times, total hours, and OT.
    """
    data = _load_attendance_data()
    eid = employee_id.strip().upper()
    records = data.get("attendance_records", {})

    if eid not in records:
        return f"Không tìm thấy dữ liệu chấm công cho nhân viên {eid}."

    emp = records[eid]
    summary = emp["weekly_summary"]
    lines = [
        f"📋 Bảng Chấm Công Tuần {emp['week']} — {emp['name']} ({eid})",
        "-" * 50,
    ]
    for day in emp["daily_records"]:
        check_in = day["check_in"] or "—"
        check_out = day["check_out"] or "—"
        ot = f" (+{day['ot_hours']}h OT)" if day["ot_hours"] > 0 else ""
        status_icon = {"Present": "✅", "Leave": "🏖️", "Absent": "❌"}.get(
            day["status"], ""
        )
        lines.append(
            f"{status_icon} {day['day']} ({day['date']}): "
            f"{check_in} → {check_out} | {day['total_hours']}h{ot}"
        )

    lines.extend(
        [
            "-" * 50,
            "📊 Tổng kết tuần:",
            f"   • Ngày làm việc: {summary['total_working_days']}/5",
            f"   • Tổng giờ làm: {summary['total_hours']}h",
            f"   • Giờ OT: {summary['total_ot_hours']}h",
            f"   • Ngày vắng: {summary['absent_days']}",
            f"   • Ngày nghỉ phép: {summary['leave_days']}",
        ]
    )
    return "\n".join(lines)


@tool
def submit_leave_request(
    employee_id: str, leave_type: str, start_date: str, end_date: str, reason: str
) -> str:
    """Submit a leave request for an employee.

    Args:
        employee_id: The employee ID (e.g., EMP001).
        leave_type: Type of leave — 'Annual Leave', 'Sick Leave', 'Unpaid Leave', 'Maternity Leave'.
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.
        reason: The reason for the leave request.

    Returns:
        A confirmation message with the generated request ID.
    """
    data = _load_attendance_data()
    eid = employee_id.strip().upper()

    # Calculate days
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        days = (end - start).days + 1
    except ValueError:
        return "❌ Lỗi: Định dạng ngày không hợp lệ. Vui lòng dùng YYYY-MM-DD."

    # Generate request ID
    existing = data.get("leave_requests", [])
    request_id = f"LR-{datetime.now().year}-{len(existing) + 1:03d}"

    new_request = {
        "request_id": request_id,
        "employee_id": eid,
        "type": leave_type,
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
        "reason": reason,
        "status": "Pending",
        "approved_by": None,
        "submitted_at": datetime.now().isoformat(),
    }

    existing.append(new_request)
    data["leave_requests"] = existing
    _save_attendance_data(data)

    return (
        f"✅ Đã nộp đơn nghỉ phép thành công!\n"
        f"   • Mã đơn: {request_id}\n"
        f"   • Loại nghỉ: {leave_type}\n"
        f"   • Thời gian: {start_date} → {end_date} ({days} ngày)\n"
        f"   • Lý do: {reason}\n"
        f"   • Trạng thái: ⏳ Đang chờ duyệt\n"
        f"Đơn của bạn đã được gửi đến Manager để phê duyệt."
    )


@tool
def get_leave_requests(employee_id: str) -> str:
    """Get all leave requests for a specific employee.

    Args:
        employee_id: The employee ID (e.g., EMP001).

    Returns:
        A formatted list of all leave requests and their statuses.
    """
    data = _load_attendance_data()
    eid = employee_id.strip().upper()
    requests = [r for r in data.get("leave_requests", []) if r["employee_id"] == eid]

    if not requests:
        return f"Nhân viên {eid} chưa có đơn nghỉ phép nào."

    status_icons = {"Approved": "✅", "Pending": "⏳", "Rejected": "❌"}
    lines = [f"📄 Danh sách đơn nghỉ phép của {eid}:", "-" * 40]
    for r in requests:
        icon = status_icons.get(r["status"], "❓")
        lines.append(
            f"{icon} [{r['request_id']}] {r['type']}\n"
            f"   📅 {r['start_date']} → {r['end_date']} ({r['days']} ngày)\n"
            f"   💬 {r['reason']}\n"
            f"   Trạng thái: {r['status']}"
        )

    return "\n".join(lines)
