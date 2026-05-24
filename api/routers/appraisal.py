"""Appraisal router — CRUD for performance appraisals."""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session, select
from api.database import get_session
from api.models import Appraisal, Employee, User
from api.auth import get_current_user

router = APIRouter(prefix="/appraisal", tags=["appraisal"])


class CreateAppraisalRequest(BaseModel):
    employee_id: str
    period: str
    appraisal_type: str = "Annual"


class SelfEvalRequest(BaseModel):
    score: float
    achievements: str
    challenges: str
    goals_next: str


class ManagerFeedbackRequest(BaseModel):
    manager_id: str
    score: float
    strengths: str
    improvements: str


def _check_appraisal_read_access(
    current_user: User, employee_id: str, session: Session
) -> bool:
    if current_user.role in ["admin", "manager"]:
        return True
    return current_user.employee_id == employee_id.upper()


@router.get("")
def list_appraisals(
    employee_id: Optional[str] = None,
    department: Optional[str] = None,
    status: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List all appraisals with optional filters."""
    query = select(Appraisal)

    if employee_id:
        if not _check_appraisal_read_access(current_user, employee_id, session):
            raise HTTPException(status_code=403, detail="Not authorized")
        query = query.where(Appraisal.employee_id == employee_id.upper())
    elif current_user.role == "employee":
        # Force filter to only their own if they are just an employee querying all
        query = query.where(Appraisal.employee_id == current_user.employee_id)

    if status:
        query = query.where(Appraisal.status == status)

    appraisals = session.exec(query).all()

    records = []
    for app in appraisals:
        emp = session.exec(
            select(Employee).where(Employee.employee_id == app.employee_id)
        ).first()
        if department and emp and emp.department.lower() != department.lower():
            continue

        app_dict = app.dict()
        app_dict["employee_name"] = emp.name if emp else f"Employee {app.employee_id}"
        app_dict["department"] = emp.department if emp else "Unknown"
        app_dict["self_evaluation"] = (
            json.loads(app.self_evaluation_json) if app.self_evaluation_json else None
        )
        app_dict["manager_feedback"] = (
            json.loads(app.manager_feedback_json) if app.manager_feedback_json else None
        )
        records.append(app_dict)

    return {"appraisals": records, "total": len(records)}


@router.get("/employee/{employee_id}")
def get_employee_appraisals(
    employee_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get all appraisals for a specific employee."""
    eid = employee_id.upper()
    if not _check_appraisal_read_access(current_user, eid, session):
        raise HTTPException(status_code=403, detail="Not authorized")

    appraisals = session.exec(
        select(Appraisal).where(Appraisal.employee_id == eid)
    ).all()
    if not appraisals:
        raise HTTPException(status_code=404, detail=f"No appraisals found for {eid}")

    records = []
    for app in appraisals:
        app_dict = app.dict()
        app_dict["self_evaluation"] = (
            json.loads(app.self_evaluation_json) if app.self_evaluation_json else None
        )
        app_dict["manager_feedback"] = (
            json.loads(app.manager_feedback_json) if app.manager_feedback_json else None
        )
        records.append(app_dict)

    return {"employee_id": eid, "appraisals": records, "total": len(records)}


@router.get("/pending")
def get_pending_appraisals(
    department: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get all pending or in-progress appraisals."""
    if current_user.role == "employee":
        raise HTTPException(status_code=403, detail="Not authorized")

    query = select(Appraisal).where(Appraisal.status.in_(["Pending", "In Progress"]))
    appraisals = session.exec(query).all()

    records = []
    for app in appraisals:
        emp = session.exec(
            select(Employee).where(Employee.employee_id == app.employee_id)
        ).first()
        if department and emp and emp.department.lower() != department.lower():
            continue

        app_dict = app.dict()
        app_dict["employee_name"] = emp.name if emp else f"Employee {app.employee_id}"
        app_dict["department"] = emp.department if emp else "Unknown"
        app_dict["self_evaluation"] = (
            json.loads(app.self_evaluation_json) if app.self_evaluation_json else None
        )
        app_dict["manager_feedback"] = (
            json.loads(app.manager_feedback_json) if app.manager_feedback_json else None
        )
        records.append(app_dict)

    return {"appraisals": records, "total": len(records)}


@router.post("")
def create_appraisal(
    req: CreateAppraisalRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new appraisal record for an employee."""
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403, detail="Only managers or HR can create appraisals"
        )

    appraisal_id = f"APR-{req.period}-{req.employee_id.upper()}"
    existing = session.exec(
        select(Appraisal).where(Appraisal.appraisal_id == appraisal_id)
    ).first()
    if existing:
        raise HTTPException(
            status_code=409, detail=f"Appraisal {appraisal_id} already exists"
        )

    new_app = Appraisal(
        appraisal_id=appraisal_id,
        employee_id=req.employee_id.upper(),
        period=req.period,
        type=req.appraisal_type,
        status="Pending",
        created_at=datetime.now().isoformat(),
    )
    session.add(new_app)
    session.commit()
    session.refresh(new_app)

    app_dict = new_app.dict()
    app_dict["self_evaluation"] = None
    app_dict["manager_feedback"] = None
    return app_dict


@router.put("/{appraisal_id}/self-evaluation")
def submit_self_evaluation(
    appraisal_id: str,
    req: SelfEvalRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Submit self-evaluation for an appraisal."""
    app = session.exec(
        select(Appraisal).where(Appraisal.appraisal_id == appraisal_id)
    ).first()
    if not app:
        raise HTTPException(
            status_code=404, detail=f"Appraisal {appraisal_id} not found"
        )

    if current_user.role == "employee" and current_user.employee_id != app.employee_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not (1.0 <= req.score <= 5.0):
        raise HTTPException(status_code=400, detail="Score must be between 1.0 and 5.0")

    eval_data = {
        "score": req.score,
        "achievements": req.achievements,
        "challenges": req.challenges,
        "goals_next": req.goals_next,
        "submitted_at": datetime.now().isoformat(),
    }
    app.self_evaluation_json = json.dumps(eval_data)
    app.status = "In Progress"

    session.add(app)
    session.commit()
    session.refresh(app)

    app_dict = app.dict()
    app_dict["self_evaluation"] = eval_data
    app_dict["manager_feedback"] = (
        json.loads(app.manager_feedback_json) if app.manager_feedback_json else None
    )
    return app_dict


@router.put("/{appraisal_id}/manager-feedback")
def submit_manager_feedback(
    appraisal_id: str,
    req: ManagerFeedbackRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Submit manager feedback and finalize the appraisal."""
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    app = session.exec(
        select(Appraisal).where(Appraisal.appraisal_id == appraisal_id)
    ).first()
    if not app:
        raise HTTPException(
            status_code=404, detail=f"Appraisal {appraisal_id} not found"
        )

    if not (1.0 <= req.score <= 5.0):
        raise HTTPException(status_code=400, detail="Score must be between 1.0 and 5.0")

    feedback_data = {
        "score": req.score,
        "strengths": req.strengths,
        "improvements": req.improvements,
        "manager_id": req.manager_id,
        "submitted_at": datetime.now().isoformat(),
    }
    app.manager_feedback_json = json.dumps(feedback_data)

    self_eval = (
        json.loads(app.self_evaluation_json)
        if app.self_evaluation_json and app.self_evaluation_json != "null"
        else {}
    )
    self_score = self_eval.get("score", req.score) if self_eval else req.score

    final = round(self_score * 0.3 + req.score * 0.7, 1)

    label = (
        "Xuat sac"
        if final >= 4.5
        else "Tot"
        if final >= 4.0
        else "Dat yeu cau"
        if final >= 3.0
        else "Can cai thien"
    )

    app.final_score = final
    app.rating_label = label
    app.status = "Completed"

    # Update employee's global rating
    emp = session.exec(
        select(Employee).where(Employee.employee_id == app.employee_id)
    ).first()
    if emp:
        emp.performance_rating = final
        session.add(emp)

    session.add(app)
    session.commit()
    session.refresh(app)

    app_dict = app.dict()
    app_dict["self_evaluation"] = self_eval
    app_dict["manager_feedback"] = feedback_data
    return app_dict
