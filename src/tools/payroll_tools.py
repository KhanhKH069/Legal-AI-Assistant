"""Payroll Tools — loads from payroll_data.json, uses LLMMathChain for calculations."""

import json
import os
from langchain_core.tools import tool

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "payroll_data.json"
)


def _load_payroll_data() -> dict:
    """Load payroll data from JSON."""
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"payroll_records": {}, "payroll_config": {}}


def _fmt_vnd(amount: float) -> str:
    return f"{amount:,.0f} ₫"


@tool
def get_payroll_record(employee_id: str, month: str = "") -> str:
    """Retrieve the payroll record for a specific employee for a given month.

    Uses the payroll data to show base salary, OT pay, bonuses, deductions,
    and net salary. If month is not provided, returns the latest month.

    Args:
        employee_id: The employee ID (e.g., EMP001).
        month: The month in YYYY-MM format (e.g., 2026-03). Leave empty for latest.

    Returns:
        A detailed formatted payroll breakdown for the employee.
    """
    data = _load_payroll_data()
    eid = employee_id.strip().upper()
    record = data.get("payroll_records", {}).get(eid)

    if not record:
        return f"❌ Không tìm thấy dữ liệu lương cho nhân viên {eid}."

    history = record.get("salary_history", [])
    if not history:
        return f"❌ Nhân viên {eid} chưa có dữ liệu lương."

    if month:
        entry = next((s for s in history if s["month"] == month), None)
        if not entry:
            return f"❌ Không có dữ liệu lương cho {eid} trong tháng {month}."
    else:
        entry = history[-1]  # Latest month

    status_icon = "✅" if entry["status"] == "Paid" else "⏳"

    lines = [
        f"💰 Bảng Lương — {record['name']} ({eid})",
        f"   {record['department']} | {record['position']}",
        f"   📅 {entry['month_label']}  {status_icon} {entry['status']}",
        "─" * 52,
        "📋 CHI TIẾT CÔNG:",
        f"   • Ngày công chuẩn:    {entry['working_days']} ngày",
        f"   • Ngày thực tế làm:   {entry['days_worked']} ngày",
        f"   • Ngày nghỉ phép:     {entry['leave_days']} ngày",
        f"   • Ngày vắng:          {entry['absent_days']} ngày",
        f"   • Giờ OT:             {entry['ot_hours']} giờ (x{entry['ot_rate']})",
        "─" * 52,
        "💵 CÁC KHOẢN THU NHẬP:",
        f"   • Lương cơ bản:       {_fmt_vnd(entry['base_salary'])}",
        f"   • Phụ cấp OT:         {_fmt_vnd(entry['ot_pay'])}",
        f"   • Thưởng KPI:         {_fmt_vnd(entry['kpi_bonus'])}",
        f"   • Thưởng khác:        {_fmt_vnd(entry['other_bonus'])}",
        f"   ➤ Tổng gross:         {_fmt_vnd(entry['gross_salary'])}",
        "─" * 52,
        "📉 CÁC KHOẢN KHẤU TRỪ:",
        f"   • BHXH (8%):          {_fmt_vnd(entry['social_insurance'])}",
        f"   • BHYT (1.5%):        {_fmt_vnd(entry['health_insurance'])}",
        f"   • BHTN (1%):          {_fmt_vnd(entry['unemployment_insurance'])}",
        f"   • Thuế TNCN:          {_fmt_vnd(entry['income_tax'])}",
        f"   ➤ Tổng khấu trừ:      {_fmt_vnd(entry['total_deductions'])}",
        "─" * 52,
        f"🏦 LƯƠNG THỰC NHẬN:    {_fmt_vnd(entry['net_salary'])}",
        f"   💳 Ngày thanh toán:   {entry['payment_date']}",
    ]
    return "\n".join(lines)


@tool
def get_payroll_history(employee_id: str) -> str:
    """Get a summary of payroll history (last 3 months) for an employee.

    Args:
        employee_id: The employee ID (e.g., EMP001).

    Returns:
        A summary table of the last 3 months of payroll data.
    """
    data = _load_payroll_data()
    eid = employee_id.strip().upper()
    record = data.get("payroll_records", {}).get(eid)

    if not record:
        return f"❌ Không tìm thấy dữ liệu lương cho nhân viên {eid}."

    history = record.get("salary_history", [])
    if not history:
        return f"❌ Nhân viên {eid} chưa có dữ liệu lương."

    lines = [
        f"📊 Lịch Sử Lương — {record['name']} ({eid})",
        f"   {record['department']} | {record['position']}",
        "─" * 60,
        f"{'Tháng':<18} {'Gross':>15} {'Khấu trừ':>14} {'Thực nhận':>14}",
        "─" * 60,
    ]

    for entry in history:
        status_icon = "✅" if entry["status"] == "Paid" else "⏳"
        lines.append(
            f"{status_icon} {entry['month_label']:<16} "
            f"{_fmt_vnd(entry['gross_salary']):>15} "
            f"{_fmt_vnd(entry['total_deductions']):>14} "
            f"{_fmt_vnd(entry['net_salary']):>14}"
        )

    if len(history) >= 2:
        last = history[-1]["net_salary"]
        prev = history[-2]["net_salary"]
        diff = last - prev
        sign = "+" if diff >= 0 else ""
        lines.extend(["─" * 60, f"   📈 So với tháng trước: {sign}{_fmt_vnd(diff)}"])

    avg = sum(e["net_salary"] for e in history) / len(history)
    lines.append(f"   📊 Lương thực nhận TB: {_fmt_vnd(avg)}/tháng")

    return "\n".join(lines)
