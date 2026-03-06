"""Benefits API Router"""

import json
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/benefits", tags=["Benefits"])

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "benefits_data.json"
)


def _load_data() -> dict:
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Benefits data not available")


class BenefitChangePayload(BaseModel):
    employee_id: str
    benefit_type: str
    requested_change: str


@router.get("/catalog")
def get_catalog():
    """Get the full company benefits catalog."""
    data = _load_data()
    return {"benefits_catalog": data.get("benefits_catalog", {})}


@router.get("/{employee_id}")
def get_employee_benefits(employee_id: str):
    """Get current benefits for a specific employee."""
    data = _load_data()
    eid = employee_id.strip().upper()
    emp_benefits = data.get("employee_benefits", {}).get(eid)
    if not emp_benefits:
        raise HTTPException(
            status_code=404, detail=f"No benefits record for employee {eid}"
        )
    return {"employee_id": eid, "benefits": emp_benefits}


@router.post("/change-request")
def request_benefit_change(payload: BenefitChangePayload):
    """Submit a request to change an employee's benefit package."""
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Benefits data not available")

    eid = payload.employee_id.strip().upper()
    emp_benefits = data.get("employee_benefits", {})

    if eid not in emp_benefits:
        raise HTTPException(status_code=404, detail=f"Employee {eid} not found")

    change_entry = {
        "type": payload.benefit_type,
        "requested_change": payload.requested_change,
        "status": "Pending Approval",
        "submitted_at": datetime.now().isoformat(),
    }
    emp_benefits[eid].setdefault("benefit_changes_pending", []).append(change_entry)
    data["employee_benefits"] = emp_benefits

    with open(_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {
        "status": "submitted",
        "employee_id": eid,
        "change_request": change_entry,
        "message": "HR will review and respond within 3 business days.",
    }
