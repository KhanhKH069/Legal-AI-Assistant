"""Payroll API Router"""

import json
import os
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/payroll", tags=["Payroll"])

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "payroll_data.json"
)


def _load_data() -> dict:
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Payroll data not available")


def _fmt_vnd(amount: int) -> str:
    return f"{amount:,.0f} ₫"


@router.get("/{employee_id}")
def get_payroll_history(employee_id: str):
    """Get full payroll history for an employee (all months)."""
    data = _load_data()
    eid = employee_id.strip().upper()
    record = data.get("payroll_records", {}).get(eid)
    if not record:
        raise HTTPException(status_code=404, detail=f"No payroll record for {eid}")
    return {
        "employee_id": eid,
        "name": record["name"],
        "department": record["department"],
        "position": record["position"],
        "salary_history": record["salary_history"],
    }


@router.get("/{employee_id}/month/{month}")
def get_payroll_month(employee_id: str, month: str):
    """
    Get payroll for a specific month.
    month format: YYYY-MM
    """
    data = _load_data()
    eid = employee_id.strip().upper()
    record = data.get("payroll_records", {}).get(eid)
    if not record:
        raise HTTPException(status_code=404, detail=f"No payroll record for {eid}")

    entry = next((s for s in record["salary_history"] if s["month"] == month), None)
    if not entry:
        raise HTTPException(
            status_code=404,
            detail=f"No payroll data for {eid} in month {month}",
        )

    return {
        "employee_id": eid,
        "name": record["name"],
        "department": record["department"],
        "position": record["position"],
        "payroll": entry,
    }


@router.get("/summary/all")
def get_payroll_summary():
    """Get payroll summary for all employees (latest month). For HR Dashboard."""
    data = _load_data()
    records = data.get("payroll_records", {})
    summary = []
    for eid, rec in records.items():
        history = rec.get("salary_history", [])
        if not history:
            continue
        latest = history[-1]
        summary.append(
            {
                "employee_id": eid,
                "name": rec["name"],
                "department": rec["department"],
                "position": rec["position"],
                "month": latest["month"],
                "month_label": latest["month_label"],
                "base_salary": latest["base_salary"],
                "ot_pay": latest["ot_pay"],
                "kpi_bonus": latest["kpi_bonus"],
                "total_deductions": latest["total_deductions"],
                "net_salary": latest["net_salary"],
                "status": latest["status"],
            }
        )
    total_payroll = sum(s["net_salary"] for s in summary)
    return {
        "month": summary[0]["month"] if summary else "",
        "total_employees": len(summary),
        "total_payroll": total_payroll,
        "employees": summary,
    }
