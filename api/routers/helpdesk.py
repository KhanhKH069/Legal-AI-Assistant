"""Helpdesk API Router"""

import json
import os
from datetime import datetime
from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/helpdesk", tags=["Helpdesk"])

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "helpdesk_data.json"
)


def _load_data() -> Dict[str, Any]:
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return dict(json.load(f))
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Helpdesk data not available")


class TicketPayload(BaseModel):
    employee_id: str
    category: str
    subject: str
    description: str
    priority: str = "Medium"


@router.post("/tickets")
def create_ticket(payload: TicketPayload):
    """Create a new HR support ticket."""
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"tickets": [], "categories": [], "sla_hours": {}}

    tickets = data.get("tickets", [])
    ticket_id = f"TICK-{datetime.now().year}-{len(tickets) + 1:03d}"
    sla = data.get("sla_hours", {}).get(payload.priority, 72)

    new_ticket: Dict[str, Any] = {
        "ticket_id": ticket_id,
        "employee_id": payload.employee_id.upper(),
        "category": payload.category,
        "subject": payload.subject,
        "description": payload.description,
        "priority": payload.priority,
        "status": "Open",
        "assigned_to": "HR Team",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "resolution": None,
        "comments": [],
    }

    tickets.append(new_ticket)
    data["tickets"] = tickets

    with open(_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {
        "status": "created",
        "ticket_id": ticket_id,
        "sla_hours": sla,
        "ticket": new_ticket,
    }


@router.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    """Get a specific HR support ticket by ID."""
    data = _load_data()
    ticket = next(
        (t for t in data.get("tickets", []) if t["ticket_id"] == ticket_id), None
    )
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return ticket


@router.get("/tickets/employee/{employee_id}")
def list_employee_tickets(employee_id: str):
    """List all tickets for a specific employee."""
    data = _load_data()
    eid = employee_id.strip().upper()
    tickets = [t for t in data.get("tickets", []) if t["employee_id"] == eid]
    return {"employee_id": eid, "tickets": tickets, "total": len(tickets)}


@router.get("/categories")
def list_categories():
    """Get available ticket categories and priority levels."""
    data = _load_data()
    return {
        "categories": data.get("categories", []),
        "priority_levels": data.get("priority_levels", []),
        "sla_hours": data.get("sla_hours", {}),
    }
