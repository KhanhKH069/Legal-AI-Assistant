"""Helpdesk API Router — with ticket status update endpoint."""

import json
from datetime import datetime, UTC
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from api.database import get_session
from api.models import Ticket, User, AuditLog
from api.auth import get_current_user

router = APIRouter(prefix="/helpdesk", tags=["Helpdesk"])

CATEGORIES = [
    "Hardware/Equipment",
    "Software/IT Access",
    "Payroll/Tax",
    "Benefits/Insurance",
    "General HR Query",
]
PRIORITY_LEVELS = ["Low", "Medium", "High", "Critical"]
SLA_HOURS = {"Low": 72, "Medium": 48, "High": 24, "Critical": 4}
VALID_STATUSES = ["Open", "In Progress", "Resolved", "Closed", "Cancelled"]


def _log(session: Session, actor_id: str, action: str, target: str, detail: str = ""):
    session.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            target=target,
            detail=detail,
            timestamp=datetime.now(UTC).isoformat(),
        )
    )


# ── Payloads ──────────────────────────────────────────────────────────────────


class TicketPayload(BaseModel):
    employee_id: str
    category: str
    subject: str
    description: str
    priority: str = "Medium"


class TicketStatusPayload(BaseModel):
    status: str
    comment: Optional[str] = None


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.post("/tickets")
def create_ticket(
    payload: TicketPayload,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new HR support ticket."""
    if (
        current_user.role == "employee"
        and current_user.employee_id != payload.employee_id.upper()
    ):
        raise HTTPException(
            status_code=403, detail="Can only create tickets for yourself"
        )

    count = len(session.exec(select(Ticket)).all())
    ticket_id = f"TICK-{datetime.now().year}-{count + 1:03d}"
    sla = SLA_HOURS.get(payload.priority, 72)

    new_ticket = Ticket(
        ticket_id=ticket_id,
        employee_id=payload.employee_id.upper(),
        category=payload.category,
        subject=payload.subject,
        description=payload.description,
        priority=payload.priority,
        status="Open",
        created_at=datetime.now().isoformat(),
        comments_json="[]",
    )
    session.add(new_ticket)
    session.commit()
    session.refresh(new_ticket)

    return {
        "status": "created",
        "ticket_id": ticket_id,
        "sla_hours": sla,
        "ticket": new_ticket.model_dump(),
    }


@router.get("/tickets/{ticket_id}")
def get_ticket(
    ticket_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a specific HR support ticket by ID."""
    ticket = session.exec(select(Ticket).where(Ticket.ticket_id == ticket_id)).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    if (
        current_user.role == "employee"
        and current_user.employee_id != ticket.employee_id
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to view this ticket"
        )

    t_dict = ticket.model_dump()
    t_dict["comments"] = (
        json.loads(ticket.comments_json) if ticket.comments_json else []
    )
    return t_dict


@router.get("/tickets/employee/{employee_id}")
def list_employee_tickets(
    employee_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List all tickets for a specific employee."""
    eid = employee_id.strip().upper()

    if current_user.role == "employee" and current_user.employee_id != eid:
        raise HTTPException(status_code=403, detail="Not authorized")

    tickets = session.exec(select(Ticket).where(Ticket.employee_id == eid)).all()
    res = []
    for t in tickets:
        t_dict = t.model_dump()
        t_dict["comments"] = json.loads(t.comments_json) if t.comments_json else []
        res.append(t_dict)

    return {"employee_id": eid, "tickets": res, "total": len(res)}


@router.put("/tickets/{ticket_id}/status")
def update_ticket_status(
    ticket_id: str,
    payload: TicketStatusPayload,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update ticket status and optionally add a resolution comment. Admin/Manager only."""
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403, detail="Only admins or managers can update ticket status"
        )

    if payload.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}",
        )

    ticket = session.exec(select(Ticket).where(Ticket.ticket_id == ticket_id)).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    old_status = ticket.status
    ticket.status = payload.status

    if payload.status in ("Resolved", "Closed"):
        ticket.resolved_at = datetime.now().isoformat()

    # Append comment if provided
    if payload.comment:
        comments = json.loads(ticket.comments_json) if ticket.comments_json else []
        comments.append(
            {
                "by": current_user.employee_id or current_user.username,
                "role": current_user.role,
                "text": payload.comment,
                "timestamp": datetime.now().isoformat(),
            }
        )
        ticket.comments_json = json.dumps(comments, ensure_ascii=False)

    session.add(ticket)
    _log(
        session,
        current_user.employee_id or current_user.username,
        "UPDATE_TICKET_STATUS",
        ticket_id,
        f"{old_status} → {payload.status}",
    )
    session.commit()
    session.refresh(ticket)

    t_dict = ticket.model_dump() if hasattr(ticket, "model_dump") else ticket.dict()
    t_dict["comments"] = (
        json.loads(ticket.comments_json) if ticket.comments_json else []
    )
    return {"status": "updated", "ticket": t_dict}


@router.get("/categories")
def list_categories():
    """Get available ticket categories and priority levels."""
    return {
        "categories": CATEGORIES,
        "priority_levels": PRIORITY_LEVELS,
        "sla_hours": SLA_HOURS,
    }
