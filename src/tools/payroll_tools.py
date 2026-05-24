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


# ── Vietnam Personal Income Tax (PIT) — 7 progressive brackets ──────────────
# Based on Circular 111/2013/TT-BTC + updated 2024
# Applies to taxable income = gross - BHXH(8%) - BHYT(1.5%) - BHTN(1%) - personal deduction
_VN_PIT_BRACKETS = [
    (5_000_000, 0.05),
    (10_000_000, 0.10),
    (18_000_000, 0.15),
    (32_000_000, 0.20),
    (52_000_000, 0.25),
    (80_000_000, 0.30),
    (float("inf"), 0.35),
]
_PERSONAL_DEDUCTION_VND = 11_000_000  # Giảm trừ bản thân 11tr/tháng (2024)
_DEPENDENT_DEDUCTION_VND = 4_400_000  # Mỗi người phụ thuộc 4.4tr/tháng


def _calculate_vn_pit(taxable_income: float) -> float:
    """Calculate VN PIT using 7-bracket progressive method."""
    if taxable_income <= 0:
        return 0.0
    tax = 0.0
    prev_ceiling = 0.0
    for ceiling, rate in _VN_PIT_BRACKETS:
        if taxable_income <= prev_ceiling:
            break
        bracket_income = min(taxable_income, ceiling) - prev_ceiling
        tax += bracket_income * rate
        prev_ceiling = ceiling
    return round(tax, 0)


@tool
def calculate_vn_income_tax(
    gross_salary_vnd: float,
    dependents: int = 0,
) -> str:
    """Calculate Vietnam Personal Income Tax (Thuế TNCN) for a given gross salary.

    Uses the official 7-bracket progressive tax table (Circular 111/2013, updated 2024).
    Includes mandatory insurance deductions before tax calculation.

    Args:
        gross_salary_vnd: Total gross salary in VND (e.g. 25000000)
        dependents: Number of tax dependents (giảm trừ người phụ thuộc), default 0
    """
    # Step 1: Mandatory insurance (employee portion)
    bhxh = gross_salary_vnd * 0.08  # BHXH
    bhyt = gross_salary_vnd * 0.015  # BHYT
    bhtn = gross_salary_vnd * 0.01  # BHTN
    total_insurance = bhxh + bhyt + bhtn

    # Step 2: Total deductions before taxable income
    personal_ded = _PERSONAL_DEDUCTION_VND
    dependent_ded = dependents * _DEPENDENT_DEDUCTION_VND

    taxable = gross_salary_vnd - total_insurance - personal_ded - dependent_ded
    pit = _calculate_vn_pit(taxable)

    total_ded = total_insurance + pit
    net = gross_salary_vnd - total_ded
    effective_rate = (pit / gross_salary_vnd * 100) if gross_salary_vnd > 0 else 0

    lines = [
        f"Tinh Thue TNCN — Gross: {_fmt_vnd(gross_salary_vnd)}",
        "=" * 52,
        "KHAU TRU BAO HIEM (nhan vien):",
        f"   BHXH (8%):          {_fmt_vnd(bhxh)}",
        f"   BHYT (1.5%):        {_fmt_vnd(bhyt)}",
        f"   BHTN (1%):          {_fmt_vnd(bhtn)}",
        f"   Tong bao hiem:      {_fmt_vnd(total_insurance)}",
        "=" * 52,
        "TINH THUE TNCN:",
        f"   Thu nhap chiu thue: {_fmt_vnd(gross_salary_vnd)}",
        f"   - Bao hiem:         {_fmt_vnd(total_insurance)}",
        f"   - Giam tru ban than:{_fmt_vnd(personal_ded)}",
        f"   - Giam tru {dependents} NTT:  {_fmt_vnd(dependent_ded)}",
        f"   = Thu nhap tinh thue: {_fmt_vnd(max(taxable, 0))}",
        "=" * 52,
        f"   THUE TNCN:          {_fmt_vnd(pit)}",
        f"   (Ty le thuc te:     {effective_rate:.1f}%)",
        "=" * 52,
        f"   LUONG THUC NHAN:    {_fmt_vnd(net)}",
    ]
    return "\n".join(lines)


# ── Leave Accrual Rules ───────────────────────────────────────────────────────
@tool
def calculate_leave_accrual(employee_id: str) -> str:
    """Calculate the theoretical annual leave days an employee has accrued based on tenure.

    Leave accrual rules (Paraline policy):
    - 0–1 year tenure:  12 days/year (1.0 day/month)
    - 1–3 years tenure: 14 days/year (~1.17 days/month)
    - 3–5 years tenure: 16 days/year (~1.33 days/month)
    - 5+ years tenure:  18 days/year (1.5 days/month)

    Args:
        employee_id: Employee ID to check (e.g. EMP001)
    """
    import json as _json
    import os as _os
    from datetime import date

    emp_path = _os.path.join(
        _os.path.dirname(__file__), "..", "..", "data", "employees_data.json"
    )
    try:
        with open(emp_path, encoding="utf-8") as f:
            employees = _json.load(f).get("employees", [])
    except FileNotFoundError:
        return "Khong tim thay file du lieu nhan vien."

    emp = next(
        (e for e in employees if e["employee_id"].upper() == employee_id.upper()), None
    )
    if not emp:
        return f"Khong tim thay nhan vien {employee_id}."

    hire_date = date.fromisoformat(emp["hire_date"])
    today = date.today()
    tenure_years = (today - hire_date).days / 365.25
    months_worked = (today - hire_date).days / 30.44

    # Determine accrual rate
    if tenure_years < 1:
        annual_days = 12
        rate_label = "12 ngay/nam (< 1 nam)"
    elif tenure_years < 3:
        annual_days = 14
        rate_label = "14 ngay/nam (1-3 nam)"
    elif tenure_years < 5:
        annual_days = 16
        rate_label = "16 ngay/nam (3-5 nam)"
    else:
        annual_days = 18
        rate_label = "18 ngay/nam (5+ nam)"

    # Days accrued this year
    year_start = date(today.year, 1, 1)
    months_this_year = (today - year_start).days / 30.44
    accrued_this_year = round(annual_days / 12 * months_this_year, 1)

    current_balance = emp.get("leave_balance", 0)
    theoretical_total = round(annual_days * tenure_years, 1)

    return (
        f"Phan tich tich luy ngay phep: {emp['name']} ({employee_id})\n"
        f"   Ngay vao lam:     {emp['hire_date']}\n"
        f"   Than niem (nam):  {tenure_years:.1f} nam ({months_worked:.0f} thang)\n"
        f"   Quy tac ap dung:  {rate_label}\n"
        f"   Tich luy nam nay: {accrued_this_year} ngay (tu 01/01/{today.year})\n"
        f"   Du kien ca nam:   {annual_days} ngay\n"
        f"   So du hien tai:   {current_balance} ngay\n"
        f"   Tong ly thuyet:   {theoretical_total} ngay (toan bo than niem)\n"
        f"\nLuu y: So du thuc te co the khac do da su dung phep truoc do."
    )
