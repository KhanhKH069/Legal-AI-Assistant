"""Benefits Tools — Employee Benefits & Subscription Management"""

import json
import os
from langchain_core.tools import tool

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "benefits_data.json"
)


def _load_benefits_data() -> dict:
    """Load benefits data from JSON."""
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"benefits_catalog": {}, "employee_benefits": {}}


def _save_benefits_data(data: dict) -> None:
    """Save benefits data back to JSON."""
    with open(_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@tool
def get_employee_benefits(employee_id: str) -> str:
    """Retrieve the current benefits and subscriptions for a specific employee.

    Args:
        employee_id: The employee ID (e.g., EMP001).

    Returns:
        A detailed summary of all active benefits for the employee.
    """
    data = _load_benefits_data()
    eid = employee_id.strip().upper()

    emp_benefits = data.get("employee_benefits", {}).get(eid)
    if not emp_benefits:
        return f"Không tìm thấy thông tin phúc lợi cho nhân viên {eid}."

    catalog = data.get("benefits_catalog", {})
    health_pkg = emp_benefits.get("health_insurance_package", "N/A")
    health_info = (
        catalog.get("health_insurance", {}).get("packages", {}).get(health_pkg, {})
    )
    coverage_list = ", ".join(health_info.get("coverage", []))
    max_cov = health_info.get("max_annual_coverage", 0)

    transport_tier = emp_benefits.get("transportation_allowance_tier", "N/A")
    transport_amt = (
        catalog.get("transportation_allowance", {})
        .get("tiers", {})
        .get(transport_tier, 0)
    )

    meal_per_day = catalog.get("meal_allowance", {}).get("amount_per_day", 40000)

    training_used = emp_benefits.get("training_budget_used", 0)
    training_remaining = emp_benefits.get("training_budget_remaining", 0)

    lines = [
        f"🎁 Phúc Lợi Của Nhân Viên {eid}",
        "=" * 45,
        f"🏥 Bảo hiểm sức khỏe: Gói {health_pkg}",
        f"   Phạm vi bảo hiểm: {coverage_list}",
        f"   Mức bảo hiểm tối đa: {max_cov:,.0f}đ/năm",
        f"🍱 Phụ cấp ăn trưa: {meal_per_day:,}đ/ngày",
        f"🚌 Phụ cấp đi lại: {transport_amt:,}đ/tháng (cự ly {transport_tier})",
        f"📚 Ngân sách đào tạo: {training_used:,}/{training_used + training_remaining:,}đ đã dùng ({training_remaining:,}đ còn lại)",
        f"💻 Phụ cấp WFH: {'✅ Có' if emp_benefits.get('wfh_allowance') else '❌ Chưa đăng ký'}",
        f"🏥 Khám sức khỏe định kỳ: {'✅ Đã khám' if emp_benefits.get('annual_checkup_done') else '⏳ Chưa khám năm nay'}",
    ]

    pending = emp_benefits.get("benefit_changes_pending", [])
    if pending:
        lines.append("\n⏳ Yêu cầu thay đổi đang chờ duyệt:")
        for p in pending:
            lines.append(f"   • {p['type']}: {p['from']} → {p['to']} ({p['status']})")

    return "\n".join(lines)


@tool
def get_benefits_catalog() -> str:
    """Get the complete catalog of all available employee benefits and packages at the company.

    Returns:
        A formatted list of all benefit options, packages, and amounts.
    """
    data = _load_benefits_data()
    catalog = data.get("benefits_catalog", {})

    lines = ["📋 Danh Mục Phúc Lợi Công Ty", "=" * 45]

    # Health Insurance
    hi = catalog.get("health_insurance", {})
    lines.append("\n🏥 Bảo Hiểm Sức Khỏe:")
    for pkg_name, pkg_info in hi.get("packages", {}).items():
        lines.append(
            f"   [{pkg_name}] Công ty: {pkg_info['monthly_cost_company']:,}đ/tháng | "
            f"Nhân viên: {pkg_info['monthly_cost_employee']:,}đ/tháng | "
            f"Bảo hiểm tối đa: {pkg_info['max_annual_coverage']:,.0f}đ"
        )

    # Meal
    meal = catalog.get("meal_allowance", {})
    lines.append(
        f"\n🍱 Phụ Cấp Ăn Trưa: {meal.get('amount_per_day', 0):,}đ/ngày ({meal.get('payment', '')})"
    )

    # Transport
    transport = catalog.get("transportation_allowance", {})
    lines.append("\n🚌 Phụ Cấp Đi Lại:")
    for tier, amount in transport.get("tiers", {}).items():
        lines.append(f"   Cự ly {tier}: {amount:,}đ/tháng")

    # Training
    training = catalog.get("training_budget", {})
    lines.append(
        f"\n📚 Ngân Sách Đào Tạo: {training.get('annual_amount', 0):,}đ/năm "
        f"(từ tháng thứ {training.get('eligible_after_months', 6)})"
    )

    # WFH
    wfh = catalog.get("wfh_allowance", {})
    lines.append(
        f"\n💻 Phụ Cấp WFH: {wfh.get('amount_per_month', 0):,}đ/tháng "
        f"(từ tháng thứ {wfh.get('eligible_after_months', 3)})"
    )

    # Birthday
    bday = catalog.get("birthday_bonus", {})
    lines.append(
        f"\n🎂 Thưởng Sinh Nhật: {bday.get('amount', 0):,}đ + {bday.get('additional', '')}"
    )

    # Health Checkup
    checkup = catalog.get("annual_health_checkup", {})
    lines.append(
        f"\n🏥 Khám Sức Khỏe Định Kỳ: {checkup.get('frequency', '')} | "
        f"Giá trị: {checkup.get('value', 0):,}đ | Tại: {checkup.get('clinic', '')}"
    )

    return "\n".join(lines)


@tool
def request_benefit_change(
    employee_id: str, benefit_type: str, requested_change: str
) -> str:
    """Submit a request to change or adjust an employee's benefit package.

    Args:
        employee_id: The employee ID (e.g., EMP001).
        benefit_type: Type of benefit to change — 'health_insurance', 'wfh_allowance', 'transportation_allowance'.
        requested_change: Description of the desired change (e.g., 'Upgrade from Basic to Standard').

    Returns:
        Confirmation message of the benefit change request.
    """
    data = _load_benefits_data()
    eid = employee_id.strip().upper()

    emp_benefits = data.get("employee_benefits", {})
    if eid not in emp_benefits:
        return f"Không tìm thấy thông tin nhân viên {eid}."

    request_entry = {
        "type": benefit_type,
        "requested_change": requested_change,
        "status": "Pending Approval",
    }
    emp_benefits[eid].setdefault("benefit_changes_pending", []).append(request_entry)
    data["employee_benefits"] = emp_benefits
    _save_benefits_data(data)

    return (
        f"✅ Yêu cầu thay đổi phúc lợi đã được ghi nhận!\n"
        f"   👤 Nhân viên: {eid}\n"
        f"   🎁 Loại phúc lợi: {benefit_type}\n"
        f"   📝 Thay đổi yêu cầu: {requested_change}\n"
        f"   ⏳ Trạng thái: Đang chờ HR phê duyệt\n"
        f"HR sẽ xem xét và phản hồi trong vòng 3 ngày làm việc."
    )
