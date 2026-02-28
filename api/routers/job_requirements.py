from typing import List

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from src.db import get_session
from src.db_models import JobRequirement

router = APIRouter(prefix="/job-requirements", tags=["job-requirements"])


@router.get("/", response_model=List[JobRequirement])
def list_job_requirements():
    session = get_session()
    query = select(JobRequirement)
    return session.exec(query).all()


@router.post("/", response_model=JobRequirement, status_code=201)
def create_job_requirement(payload: JobRequirement):
    session = get_session()
    jr = JobRequirement.from_orm(payload)
    session.add(jr)
    session.commit()
    session.refresh(jr)
    return jr


@router.get("/{jr_id}", response_model=JobRequirement)
def get_job_requirement(jr_id: int):
    session = get_session()
    jr = session.get(JobRequirement, jr_id)
    if not jr:
        raise HTTPException(status_code=404, detail="Job requirement not found")
    return jr


@router.put("/{jr_id}", response_model=JobRequirement)
def update_job_requirement(jr_id: int, payload: JobRequirement):
    session = get_session()
    jr = session.get(JobRequirement, jr_id)
    if not jr:
        raise HTTPException(status_code=404, detail="Job requirement not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(jr, field, value)

    session.add(jr)
    session.commit()
    session.refresh(jr)
    return jr

