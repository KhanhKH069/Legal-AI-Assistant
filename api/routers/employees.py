"""Employee router — serves employee list and per-employee monthly info."""

import csv
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/employees", tags=["employees"])

_CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "hr_mock_data.csv"
)


def _load_csv() -> list[dict]:
    rows = []
    try:
        with open(_CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append({k: v.strip() for k, v in row.items()})
    except FileNotFoundError:
        pass
    return rows


def _salary_level(salary: float) -> str:
    if salary < 1300:
        return "L1"
    elif salary < 1800:
        return "L2"
    elif salary < 2500:
        return "L3"
    elif salary < 3500:
        return "L4"
    return "L5"


@router.get("")
def list_employees(search: Optional[str] = None):
    """Return list of active employees. Optional ?search= to filter by name."""
    rows = _load_csv()
    result = []
    for r in rows:
        if r.get("status", "Active") != "Active":
            continue
        if search and search.lower() not in r["name"].lower():
            continue
        result.append(
            {
                "employee_id": r["employee_id"],
                "name": r["name"],
                "department": r["department"],
                "position": r["position"],
            }
        )
    return result


@router.get("/{employee_id}/monthly")
def get_monthly_info(employee_id: str, month: Optional[str] = None):
    """
    Return employee monthly snapshot.
    month format: YYYY-MM (default = current month).
    """
    rows = _load_csv()
    emp = next(
        (r for r in rows if r["employee_id"].upper() == employee_id.upper()),
        None,
    )
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")

    now = datetime.now()
    target_month = month or now.strftime("%Y-%m")
    try:
        month_dt = datetime.strptime(target_month, "%Y-%m")
    except ValueError:
        raise HTTPException(status_code=400, detail="month must be YYYY-MM")

    month_label = month_dt.strftime("%B %Y")  # e.g. "March 2026"

    # Compute working days in that month (Mon–Fri)
    import calendar

    _, days_in_month = calendar.monthrange(month_dt.year, month_dt.month)
    working_days = sum(
        1
        for d in range(1, days_in_month + 1)
        if datetime(month_dt.year, month_dt.month, d).weekday() < 5
    )

    return {
        "employee_id": emp["employee_id"],
        "name": emp["name"],
        "department": emp["department"],
        "position": emp["position"],
        "hire_date": emp["hire_date"],
        "status": emp["status"],
        "salary_level": _salary_level(float(emp["salary"])),
        "performance_rating": float(emp["performance_rating"]),
        "leave_balance": int(emp["leave_balance"]),
        "month": target_month,
        "month_label": month_label,
        "working_days_in_month": working_days,
        # Assume employee worked all working days (no leave taken this month for demo)
        "days_worked": working_days,
        "leave_taken_this_month": 0,
    }
