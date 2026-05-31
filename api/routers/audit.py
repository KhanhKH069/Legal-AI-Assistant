"""Audit Log Router — admin-only endpoint to query the AuditLog table."""

from datetime import datetime, UTC
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select

from api.database import get_session
from api.models import AuditLog, User
from api.auth import get_current_user

router = APIRouter(prefix="/audit", tags=["Audit"])


# ── Helper ────────────────────────────────────────────────────────────────────


def log_action(
    session: Session,
    actor_id: str,
    action: str,
    target: str = "",
    detail: str = "",
):
    """Convenience helper — call from any router to append an audit entry.

    Usage::

        from api.routers.audit import log_action
        log_action(session, current_user.employee_id, "VIEW_SALARY", "EMP042")
        session.commit()  # caller must commit
    """
    session.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            target=target,
            detail=detail,
            timestamp=datetime.now(UTC).isoformat(),
        )
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.get("/logs")
def get_audit_logs(
    actor_id: Optional[str] = None,
    action: Optional[str] = None,
    target: Optional[str] = None,
    date_from: Optional[str] = None,  # YYYY-MM-DD
    date_to: Optional[str] = None,  # YYYY-MM-DD
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=500),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Retrieve audit logs. Admin only.

    Filters (all optional):
    - actor_id  : who performed the action (e.g. EMP001)
    - action    : action type (e.g. VIEW_SALARY, APPROVE_LEAVE)
    - target    : target entity (e.g. EMP042)
    - date_from : earliest timestamp (YYYY-MM-DD)
    - date_to   : latest timestamp  (YYYY-MM-DD)
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view audit logs")

    query = select(AuditLog).order_by(AuditLog.timestamp.desc())
    logs = session.exec(query).all()

    # Filter in Python (SQLite text column — avoids complex SQL LIKE)
    filtered = []
    for log in logs:
        if actor_id and actor_id.upper() not in log.actor_id.upper():
            continue
        if action and action.upper() not in log.action.upper():
            continue
        if target and target.upper() not in log.target.upper():
            continue
        if date_from and log.timestamp < date_from:
            continue
        if date_to and log.timestamp > date_to + "T23:59:59":
            continue
        filtered.append(
            {
                "id": log.id,
                "actor_id": log.actor_id,
                "action": log.action,
                "target": log.target,
                "detail": log.detail,
                "timestamp": log.timestamp,
            }
        )

    total = len(filtered)
    start = (page - 1) * size
    return {
        "total": total,
        "page": page,
        "size": size,
        "logs": filtered[start : start + size],
    }


@router.get("/logs/summary")
def get_audit_summary(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Return a count breakdown of actions by type. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view audit logs")

    logs = session.exec(select(AuditLog)).all()
    counts: dict = {}
    for log in logs:
        counts[log.action] = counts.get(log.action, 0) + 1

    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return {
        "total_entries": len(logs),
        "by_action": [{"action": a, "count": c} for a, c in sorted_counts],
    }
