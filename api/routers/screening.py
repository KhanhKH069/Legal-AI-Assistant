"""Screening API Router — JSON-backed, no SQLite dependency"""

import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/screening", tags=["screening"])

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
RESULTS_FILE = os.path.join(DATA_DIR, "screening_results.json")
RECRUITMENT_FILE = os.path.join(DATA_DIR, "recruitment_data.json")


def _load_results() -> List[Dict]:
    if not os.path.exists(RESULTS_FILE):
        return []
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_results(results: List[Dict]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def _load_recruitment() -> Dict:
    if not os.path.exists(RECRUITMENT_FILE):
        return {}
    with open(RECRUITMENT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _next_id(results: List[Dict]) -> int:
    return max((r.get("id", 0) for r in results), default=0) + 1


@router.post("/run")
def run_screening(applicant_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Simulate running CV screening based on recruitment pipeline data.
    Generates screening results from candidates in 'CV Screening' stage.
    """
    recruitment = _load_recruitment()
    existing = _load_results()
    existing_ids = {r.get("applicant_id") for r in existing}

    new_results: List[Dict] = []
    counter = _next_id(existing)

    import random
    from datetime import datetime

    pipelines = recruitment.get("pipelines", {})
    for position, pipeline in pipelines.items():
        stages = pipeline.get("pipeline_stages", {})
        # Combine all candidates to screen (those with a score)
        for stage_name, candidates in stages.items():
            for candidate in candidates:
                cid = hash(candidate.get("candidate_id", "")) % 100000
                if applicant_id is not None and cid != applicant_id:
                    continue
                if cid in existing_ids:
                    continue
                score = candidate.get("score")
                if score is None:
                    score = random.randint(40, 95)

                min_score = 60
                percentage = score
                if percentage >= min_score + 20:
                    recommendation = "STRONG_PASS"
                    action = "Schedule interview ASAP"
                elif percentage >= min_score:
                    recommendation = "PASS"
                    action = "Schedule interview"
                elif percentage >= min_score - 10:
                    recommendation = "MAYBE"
                    action = "Review manually"
                else:
                    recommendation = "REJECT"
                    action = "Send rejection email"

                result = {
                    "id": counter,
                    "applicant_id": cid,
                    "applicant_name": candidate.get("name", "Unknown"),
                    "position": position,
                    "total_score": score,
                    "max_score": 100,
                    "percentage": percentage,
                    "recommendation": recommendation,
                    "status": stage_name,
                    "action": action,
                    "breakdown": {
                        "required_skills": {
                            "found": [],
                            "percentage": score * 0.4,
                            "points": score * 0.3,
                        },
                        "preferred_skills": {
                            "found": [],
                            "percentage": score * 0.3,
                            "points": score * 0.2,
                        },
                        "experience": {
                            "years_found": 2,
                            "years_required": 2,
                            "points": score * 0.25,
                        },
                        "education": {"relevant": True, "points": score * 0.15},
                        "certifications": {"found": [], "points": 0},
                    },
                    "min_score": min_score,
                    "created_at": datetime.now().isoformat(),
                }
                new_results.append(result)
                existing_ids.add(cid)
                counter += 1

    if new_results:
        _save_results(existing + new_results)

    return {"count": len(new_results), "results": new_results}


@router.get("/results")
def list_results(
    position: Optional[str] = None,
    recommendation: Optional[str] = None,
) -> List[Dict]:
    results = _load_results()
    if position:
        results = [r for r in results if r.get("position") == position]
    if recommendation:
        results = [r for r in results if r.get("recommendation") == recommendation]
    return results


@router.get("/results/{result_id}")
def get_result(result_id: int) -> Dict:
    results = _load_results()
    for r in results:
        if r.get("id") == result_id:
            return r
    raise HTTPException(status_code=404, detail="Screening result not found")
