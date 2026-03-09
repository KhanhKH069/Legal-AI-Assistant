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

                # Generate Mock Technical Assessment Questions
                interview_questions = []
                if recommendation in ["STRONG_PASS", "PASS", "MAYBE"]:
                    p_lower = position.lower()
                    if "react" in p_lower or "frontend" in p_lower:
                        interview_questions = [
                            "Bạn có thể giải thích cơ chế hoạt động của Virtual DOM trong React?",
                            "Kinh nghiệm tối ưu hóa hiệu suất ứng dụng web (performance optimization)?",
                            "Sự khác biệt giữa SSR và SSG trong Next.js là gì?",
                        ]
                    elif (
                        "python" in p_lower or "backend" in p_lower or "data" in p_lower
                    ):
                        interview_questions = [
                            "Sự khác biệt lớn nhất giữa asyncio và multi-threading trong Python là gì?",
                            "Làm thế nào để bạn scale một hệ thống API chịu tải lớn?",
                            "Kinh nghiệm xử lý transaction an toàn trong SQL Database?",
                        ]
                    else:
                        interview_questions = [
                            "Dự án nào khiến bạn tự hào nhất và vì sao?",
                            "Kinh nghiệm giải quyết xung đột ý kiến với các thành viên trong team?",
                            "Bạn áp dụng mô hình thiết kế (Design Pattern) nào nhiều nhất?",
                        ]

                # Generate AI Draft Email for Feedback/Follow-up
                c_name = candidate.get("name", "Bạn")
                if recommendation in ["STRONG_PASS", "PASS"]:
                    draft_email = (
                        f"Kính gửi {c_name},\n\n"
                        f"Chúng tôi rất ấn tượng với CV của bạn cho vị trí {position} tại Paraline. "
                        "HR team muốn mời bạn tham gia buổi phỏng vấn chuyên môn (Technical Interview) "
                        "trong tuần này. Vui lòng cho biết thời gian khả thi của bạn.\n\n"
                        "Trân trọng,\nParaline AI Recruitment Team"
                    )
                elif recommendation == "MAYBE":
                    draft_email = (
                        f"Kính gửi {c_name},\n\n"
                        f"Cảm ơn bạn đã ứng tuyển vị trí {position}. "
                        "Để bộ phận tuyển dụng hiểu rõ hơn về kỹ năng của bạn, chúng tôi muốn mời bạn hoàn thành "
                        "một bài đánh giá năng lực ngắn trước khi xếp lịch phỏng vấn. Vui lòng kiểm tra link bài test bên dưới.\n\n"
                        "Trân trọng,\nParaline AI Recruitment Team"
                    )
                else:
                    draft_email = (
                        f"Kính gửi {c_name},\n\n"
                        f"Cảm ơn bạn đã quan tâm và ứng tuyển cho vị trí {position}. "
                        "Dù hồ sơ của bạn rất thú vị, tuy nhiên ở thời điểm hiện tại, chúng tôi đang ưu tiên "
                        "các ứng viên có kinh nghiệm phù hợp hơn với định hướng của dự án. Chúng tôi sẽ lưu thông tin "
                        "của bạn vào Talent Pool cho các cơ hội trong tương lai.\n\n"
                        "Trân trọng,\nParaline AI Recruitment Team"
                    )

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
                    "interview_questions": interview_questions,
                    "draft_email": draft_email,
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
