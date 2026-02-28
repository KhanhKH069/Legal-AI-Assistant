from typing import List, Optional
from pathlib import Path
import json

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from src.db import get_session
from src.db_models import Applicant


# --- helper for legacy JSON storage -------------------------------------------------

def _append_applicant_to_json(applicant: Applicant):
    """Append a new applicant record to applicants_db.json.

    This mirrors the behavior of the old Streamlit UI, so that existing
    scripts (cv_screening.py, streamlit_app.py) can continue to work without
    modification. The JSON file is kept in the project root.
    """
    db_file = Path("applicants_db.json")
    # load existing array, if any
    if db_file.exists() and db_file.stat().st_size > 0:
        try:
            with open(db_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []
    else:
        data = []

    # convert applicant object to simple dict (exclude sqlalchemy internals)
    record = {
        "name": applicant.name,
        "email": applicant.email,
        "phone": applicant.phone,
        "position": applicant.position,
        "cv_path": applicant.cv_path,
        "cv_url": applicant.cv_url,
        "status": applicant.status,
        "created_at": applicant.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }
    data.append(record)
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# -----------------------------------------------------------------------------------

router = APIRouter(prefix="/applicants", tags=["applicants"])


@router.get("/", response_model=List[Applicant])
def list_applicants(
    status: Optional[str] = None,
    position: Optional[str] = None,
):
    """List applicants with optional filters."""
    session = get_session()
    query = select(Applicant)

    if status:
        query = query.where(Applicant.status == status)
    if position:
        query = query.where(Applicant.position == position)

    return session.exec(query).all()


@router.post("/", response_model=Applicant, status_code=201)
def create_applicant(payload: Applicant):
    """Create new applicant and persist to both database and JSON file."""
    session = get_session()
    applicant = Applicant.from_orm(payload)
    session.add(applicant)
    session.commit()
    session.refresh(applicant)

    # also write to legacy JSON file for compatibility with older scripts/UI
    try:
        _append_applicant_to_json(applicant)
    except Exception as e:
        # log but don't fail the request
        import logging

        logging.warning(f"Failed to append applicant to JSON: {e}")

    # run automatic screening for the newly created applicant (non-blocking)
    try:
        from api.routers.screening import _screen_single_applicant

        try:
            _screen_single_applicant(applicant)
        except Exception as e:
            logging.warning(f"Auto-screening failed for applicant {applicant.id}: {e}")
    except ImportError:
        # if router is not importable for any reason, skip
        pass

    return applicant


@router.get("/{applicant_id}", response_model=Applicant)
def get_applicant(applicant_id: int):
    session = get_session()
    applicant = session.get(Applicant, applicant_id)
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    return applicant


@router.patch("/{applicant_id}", response_model=Applicant)
def update_applicant(applicant_id: int, payload: Applicant):
    session = get_session()
    applicant = session.get(Applicant, applicant_id)
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(applicant, field, value)

    session.add(applicant)
    session.commit()
    session.refresh(applicant)
    return applicant

