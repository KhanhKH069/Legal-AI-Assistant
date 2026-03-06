"""Recruitment CRM Tools — Pipeline and interview schedule management"""

import json
import os
import random
from datetime import datetime
from langchain_core.tools import tool

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "recruitment_data.json"
)


def _load_recruitment_data() -> dict:
    """Load recruitment data from JSON."""
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"pipelines": {}, "interview_schedules": []}


def _save_recruitment_data(data: dict) -> None:
    """Save recruitment data back to JSON."""
    with open(_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@tool
def get_recruitment_pipeline(position: str) -> str:
    """Get the recruitment pipeline for a specific open position, showing candidates at each stage.

    Args:
        position: The job position name (e.g., 'ReactJS Developer', 'Backend Developer').

    Returns:
        A detailed view of the recruitment funnel with candidate counts per stage.
    """
    data = _load_recruitment_data()
    pipelines = data.get("pipelines", {})

    # Fuzzy match position name
    matched_key = None
    for key in pipelines:
        if position.lower() in key.lower() or key.lower() in position.lower():
            matched_key = key
            break

    if not matched_key:
        available = ", ".join(pipelines.keys())
        return f"Không tìm thấy pipeline cho vị trí '{position}'.\nCác vị trí hiện có: {available}"

    pipeline = pipelines[matched_key]
    stats = pipeline.get("hiring_stats", {})
    stages = pipeline.get("pipeline_stages", {})

    lines = [
        f"🏢 Pipeline Tuyển Dụng: {matched_key}",
        f"📌 Số vị trí cần tuyển: {pipeline.get('open_positions', 0)}",
        "=" * 45,
    ]

    stage_icons = {
        "New Application": "📥",
        "CV Screening": "📋",
        "Technical Interview": "💻",
        "HR Interview": "🗣️",
        "Offer Extended": "📤",
        "Hired": "✅",
        "Rejected": "❌",
    }

    for stage_name, candidates in stages.items():
        icon = stage_icons.get(stage_name, "📌")
        count = len(candidates)
        lines.append(f"\n{icon} {stage_name}: {count} ứng viên")
        for c in candidates[:3]:  # Show max 3 per stage
            score_text = f" — Điểm: {c['score']}" if c.get("score") else ""
            interview_text = (
                f" (Phỏng vấn: {c['interview_date']})"
                if c.get("interview_date")
                else ""
            )
            lines.append(
                f"   • [{c['candidate_id']}] {c['name']}{score_text}{interview_text}"
            )
        if count > 3:
            lines.append(f"   ... và {count - 3} ứng viên khác")

    lines.extend(
        [
            "\n📊 Thống Kê Tổng Hợp:",
            f"   • Tổng ứng viên: {stats.get('total_applicants', 0)}",
            f"   • Đang trong pipeline: {stats.get('in_pipeline', 0)}",
            f"   • Đã tuyển: {stats.get('hired', 0)}",
            f"   • Đã loại: {stats.get('rejected', 0)}",
            f"   • Tỉ lệ chuyển đổi: {stats.get('conversion_rate', 'N/A')}",
            f"   • Thời gian tuyển trung bình: {stats.get('time_to_hire_avg_days', 'N/A')} ngày",
        ]
    )

    return "\n".join(lines)


@tool
def create_interview_schedule(
    candidate_name: str,
    position: str,
    interview_date: str,
    interview_time: str,
    interview_type: str,
    interviewer: str,
) -> str:
    """Schedule an interview for a candidate and generate a Google Meet link.

    Args:
        candidate_name: Full name of the candidate.
        position: The job position being interviewed for.
        interview_date: Date of the interview in YYYY-MM-DD format.
        interview_time: Time of the interview in HH:MM format (24h).
        interview_type: Type of interview — 'Technical Interview', 'HR Interview', 'Final Interview'.
        interviewer: Name or title of the interviewer.

    Returns:
        Interview schedule confirmation with Meet link.
    """
    data = _load_recruitment_data()
    schedules = data.get("interview_schedules", [])

    schedule_id = f"SCH-{len(schedules) + 1:03d}"
    # Generate mock Meet link
    meet_code = f"{random.choice(['abc', 'def', 'ghi', 'xyz'])}-{random.choice(['defg', 'wxyz', 'abcd'])}-{random.choice(['hij', 'mno', 'pqr'])}"
    meet_link = f"https://meet.google.com/{meet_code}"

    new_schedule = {
        "schedule_id": schedule_id,
        "candidate_name": candidate_name,
        "position": position,
        "interview_type": interview_type,
        "date": interview_date,
        "time": interview_time,
        "duration_minutes": 60,
        "interviewer": interviewer,
        "meet_link": meet_link,
        "status": "Scheduled",
        "created_at": datetime.now().isoformat(),
    }

    schedules.append(new_schedule)
    data["interview_schedules"] = schedules
    _save_recruitment_data(data)

    return (
        f"✅ Lịch phỏng vấn đã được tạo thành công!\n"
        f"   🆔 Mã lịch: {schedule_id}\n"
        f"   👤 Ứng viên: {candidate_name}\n"
        f"   💼 Vị trí: {position}\n"
        f"   📋 Loại phỏng vấn: {interview_type}\n"
        f"   📅 Ngày: {interview_date} lúc {interview_time}\n"
        f"   👥 Người phỏng vấn: {interviewer}\n"
        f"   🔗 Google Meet: {meet_link}\n"
        f"Email mời phỏng vấn sẽ được gửi tự động đến ứng viên."
    )


@tool
def get_hiring_stats() -> str:
    """Get overall hiring statistics across all open positions.

    Returns:
        A summary of recruitment performance metrics for all active positions.
    """
    data = _load_recruitment_data()
    pipelines = data.get("pipelines", {})

    total_applicants = 0
    total_hired = 0
    total_in_pipeline = 0
    total_rejected = 0

    lines = ["📊 Thống Kê Tuyển Dụng Tổng Hợp", "=" * 45]

    for position, pipeline in pipelines.items():
        stats = pipeline.get("hiring_stats", {})
        total_applicants += stats.get("total_applicants", 0)
        total_hired += stats.get("hired", 0)
        total_in_pipeline += stats.get("in_pipeline", 0)
        total_rejected += stats.get("rejected", 0)
        lines.append(
            f"\n💼 {position} (cần tuyển: {pipeline.get('open_positions', 0)}):\n"
            f"   Ứng viên: {stats.get('total_applicants', 0)} | "
            f"Pipeline: {stats.get('in_pipeline', 0)} | "
            f"Đã tuyển: {stats.get('hired', 0)} | "
            f"Tỉ lệ: {stats.get('conversion_rate', 'N/A')}"
        )

    lines.extend(
        [
            "\n" + "=" * 45,
            "🔢 Tổng Cộng:",
            f"   • Tổng ứng viên: {total_applicants}",
            f"   • Đang trong pipeline: {total_in_pipeline}",
            f"   • Đã tuyển: {total_hired}",
            f"   • Đã loại: {total_rejected}",
            f"   • Tỉ lệ tuyển dụng tổng: {(total_hired / total_applicants * 100):.1f}%"
            if total_applicants
            else "   • Tỉ lệ: N/A",
        ]
    )

    return "\n".join(lines)
