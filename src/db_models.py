from datetime import datetime
from typing import Any, Dict, Optional

from sqlmodel import JSON, Column, Field, SQLModel


class Applicant(SQLModel, table=True):
    __tablename__ = "applicants"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str
    phone: str
    position: str
    cv_url: Optional[str] = None
    cv_path: Optional[str] = None
    status: str = Field(default="NEW", description="NEW/SCREENED/INTERVIEW/REJECTED/HIRED")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScreeningResult(SQLModel, table=True):
    __tablename__ = "screening_results"

    id: Optional[int] = Field(default=None, primary_key=True)
    applicant_id: int = Field(foreign_key="applicants.id")
    position: str
    total_score: float
    max_score: float
    percentage: float
    recommendation: str
    status: str
    action: str
    breakdown: Dict[str, Any] = Field(sa_column=Column(JSON))
    min_score: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JobRequirement(SQLModel, table=True):
    __tablename__ = "job_requirements"

    id: Optional[int] = Field(default=None, primary_key=True)
    position: str
    required_skills: Dict[str, Any] = Field(
        sa_column=Column(JSON), description="List or structured required skills"
    )
    preferred_skills: Dict[str, Any] = Field(
        sa_column=Column(JSON), description="List or structured preferred skills"
    )
    min_experience_years: int = 0
    education_keywords: Dict[str, Any] = Field(
        sa_column=Column(JSON), description="Keywords for education matching"
    )
    certifications: Dict[str, Any] = Field(
        sa_column=Column(JSON), description="Preferred certifications"
    )
    min_score: float = 60.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

