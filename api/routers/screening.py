from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from cv_screening import score_cv
from src.db import get_session
from src.db_models import Applicant, ScreeningResult

router = APIRouter(prefix="/screening", tags=["screening"])


def _screen_single_applicant(applicant: Applicant) -> ScreeningResult:
    """Run scoring for a single applicant and persist result."""
    if not applicant.cv_path:
        raise HTTPException(
            status_code=400,
            detail=f"Applicant {applicant.id} has no cv_path stored.",
        )

    result = score_cv(applicant.cv_path, applicant.position)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    session = get_session()

    screening = ScreeningResult(
        applicant_id=applicant.id,
        position=result["position"],
        total_score=result["total_score"],
        max_score=result["max_score"],
        percentage=result["percentage"],
        recommendation=result["recommendation"],
        status=result["status"],
        action=result["action"],
        breakdown=result["breakdown"],
        min_score=result["min_score"],
    )

    # Persist result and update applicant status
    applicant.status = "SCREENED"
    session.add(screening)
    session.add(applicant)
    session.commit()
    session.refresh(screening)
    return screening


@router.post("/run")
def run_screening(applicant_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Run CV screening.
    - If applicant_id is provided, screen that applicant only.
    - Otherwise, screen all applicants with status NEW and a stored cv_path.
    """
    session = get_session()

    if applicant_id is not None:
        applicant = session.get(Applicant, applicant_id)
        if not applicant:
            raise HTTPException(status_code=404, detail="Applicant not found")

        screening = _screen_single_applicant(applicant)
        return {
            "count": 1,
            "results": [screening],
        }

    # Batch mode: all NEW applicants with cv_path
    query = select(Applicant).where(
        Applicant.status == "NEW",
        Applicant.cv_path.is_not(None),
    )
    applicants = session.exec(query).all()

    results: List[ScreeningResult] = []
    for app in applicants:
        try:
            results.append(_screen_single_applicant(app))
        except HTTPException:
            # Skip invalid CVs but continue others
            continue

    return {
        "count": len(results),
        "results": results,
    }


@router.get("/results", response_model=List[ScreeningResult])
def list_results(
    position: Optional[str] = None,
    recommendation: Optional[str] = None,
):
    session = get_session()
    query = select(ScreeningResult)

    if position:
        query = query.where(ScreeningResult.position == position)
    if recommendation:
        query = query.where(ScreeningResult.recommendation == recommendation)

    return session.exec(query).all()


@router.get("/results/{result_id}", response_model=ScreeningResult)
def get_result(result_id: int):
    session = get_session()
    result = session.get(ScreeningResult, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Screening result not found")
    return result

