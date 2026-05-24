from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select

from src.db import get_session
from src.db_models import Applicant
from api.models import User
from api.auth import get_current_user


# -----------------------------------------------------------------------------------


router = APIRouter(prefix="/applicants", tags=["applicants"])


@router.get("/", response_model=List[Applicant])
def list_applicants(
    status: Optional[str] = None,
    position: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
):
    """List applicants with optional filters and pagination. (Protected)"""
    session = get_session()
    query = select(Applicant)

    if status:
        query = query.where(Applicant.status == status)
    if position:
        query = query.where(Applicant.position == position)

    query = query.offset(skip).limit(limit)
    return session.exec(query).all()


@router.post("/", response_model=Applicant, status_code=201)
def create_applicant(payload: Applicant):
    """Create new applicant and persist to database. (Public endpoint)"""
    session = get_session()

    # Check for duplicates (same email and position)
    duplicate_query = select(Applicant).where(
        Applicant.email == payload.email, Applicant.position == payload.position
    )
    existing = session.exec(duplicate_query).first()
    if existing:
        raise HTTPException(
            status_code=400, detail="You have already applied for this position."
        )

    applicant = Applicant.from_orm(payload)
    session.add(applicant)
    session.commit()
    session.refresh(applicant)

    # run automatic screening for the newly created applicant (non-blocking)
    try:
        from api.routers.screening import _screen_single_applicant

        try:
            _screen_single_applicant(applicant)
        except Exception as e:
            import logging

            logging.warning(f"Auto-screening failed for applicant {applicant.id}: {e}")
    except ImportError:
        # if router is not importable for any reason, skip
        pass

    return applicant


@router.get("/{applicant_id}", response_model=Applicant)
def get_applicant(applicant_id: int, current_user: User = Depends(get_current_user)):
    """Get applicant by ID. (Protected)"""
    session = get_session()
    applicant = session.get(Applicant, applicant_id)
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    return applicant


@router.patch("/{applicant_id}", response_model=Applicant)
def update_applicant(
    applicant_id: int,
    payload: Applicant,
    current_user: User = Depends(get_current_user),
):
    """Update applicant. (Protected)"""
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
