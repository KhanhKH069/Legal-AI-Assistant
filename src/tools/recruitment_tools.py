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
    candidate_email: str,
    position: str,
    interview_date: str,
    interview_time: str,
    interview_type: str,
    interviewer: str,
) -> str:
    """Schedule an interview for a candidate, generate a Google Meet link, and send invitation email.

    Args:
        candidate_name: Full name of the candidate.
        candidate_email: Email address of the candidate.
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
        "candidate_email": candidate_email,
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

    # Send real email
    try:
        from src.tools.email_calendar_tools import draft_interview_email
        from src.core.email_service import get_email_service
        
        email_body = draft_interview_email(
            candidate_name=candidate_name,
            position=position,
            interview_time=f"{interview_time} ngày {interview_date}",
            meet_link=meet_link
        )
        email_svc = get_email_service()
        subject = f"Thư Mời Phỏng Vấn - Vị trí {position} tại Paraline Software"
        email_svc.send_email(to_email=candidate_email, subject=subject, body_text=email_body)
        email_status = f"✅ Đã gửi email mời phỏng vấn tới {candidate_email}"
    except Exception as e:
        email_status = f"❌ Không thể gửi email: {e}"

    return (
        f"✅ Lịch phỏng vấn đã được tạo thành công!\n"
        f"   🆔 Mã lịch: {schedule_id}\n"
        f"   👤 Ứng viên: {candidate_name} ({candidate_email})\n"
        f"   💼 Vị trí: {position}\n"
        f"   📋 Loại phỏng vấn: {interview_type}\n"
        f"   📅 Ngày: {interview_date} lúc {interview_time}\n"
        f"   👥 Người phỏng vấn: {interviewer}\n"
        f"   🔗 Google Meet: {meet_link}\n"
        f"{email_status}"
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


@tool
def convert_applicant_to_employee(
    applicant_id: str,
    position: str,
    department: str,
    start_date: str,
    salary_vnd: int,
) -> str:
    """Convert a hired applicant into a new employee record and trigger onboarding.
    Use this after an applicant has been marked HIRED in the recruitment pipeline.

    Args:
        applicant_id: Applicant/candidate ID (e.g. CAND-001)
        position: Job position the candidate was hired for
        department: Department the new employee will join
        start_date: Official start date in YYYY-MM-DD format
        salary_vnd: Agreed monthly salary in VND (e.g. 25000000)
    """
    import json
    import os as _os

    emp_path = _os.path.join(
        _os.path.dirname(__file__), "..", "..", "data", "employees_data.json"
    )
    try:
        with open(emp_path, encoding="utf-8") as f:
            emp_data = json.load(f)
    except FileNotFoundError:
        emp_data = {"employees": [], "total": 0}

    existing_ids = [e["employee_id"] for e in emp_data["employees"]]
    # Generate next EMP ID
    nums = [int(e[3:]) for e in existing_ids if e.startswith("EMP") and e[3:].isdigit()]
    new_num = max(nums) + 1 if nums else 101
    new_emp_id = f"EMP{new_num:03d}"

    # Generate onboarding checklist
    onboarding_checklist = [
        {"task": "Ky hop dong lao dong", "due": "Day 1", "status": "Pending"},
        {"task": "Ky NDA", "due": "Day 1", "status": "Pending"},
        {"task": "Dang ky BHXH/BHYT", "due": "Week 1", "status": "Pending"},
        {"task": "Dang ky tai khoan ngan hang", "due": "Week 1", "status": "Pending"},
        {"task": "Nhan thiet bi lam viec", "due": "Day 1", "status": "Pending"},
        {"task": "Tao tai khoan he thong IT", "due": "Day 1", "status": "Pending"},
        {"task": "Tham quan van phong & gap team", "due": "Day 1", "status": "Pending"},
        {"task": "Training quy trinh noi bo", "due": "Week 2", "status": "Pending"},
        {"task": "Review 30-day checklist", "due": "Month 1", "status": "Pending"},
    ]

    new_employee = {
        "employee_id": new_emp_id,
        "name": f"New Employee (from {applicant_id})",
        "gender": "M",
        "department": department,
        "position": position,
        "level": "Junior",
        "email": f"{new_emp_id.lower()}@paraline.vn",
        "phone": "",
        "hire_date": start_date,
        "status": "Active",
        "manager_id": None,
        "salary_vnd": salary_vnd,
        "leave_balance": 12,
        "performance_rating": 0.0,
        "skills": [],
        "contract": {
            "start": start_date,
            "end": str(
                __import__("datetime")
                .date.fromisoformat(start_date)
                .replace(
                    year=__import__("datetime").date.fromisoformat(start_date).year + 1
                )
            ),
        },
        "address": "",
        "emergency_contact": {},
        "education": "",
        "source_applicant_id": applicant_id,
        "onboarding_checklist": onboarding_checklist,
    }

    emp_data["employees"].append(new_employee)
    emp_data["total"] = len(emp_data["employees"])

    with open(emp_path, "w", encoding="utf-8") as f:
        json.dump(emp_data, f, ensure_ascii=False, indent=2)

    checklist_summary = "\n".join(
        f"  - {item['task']} ({item['due']})" for item in onboarding_checklist
    )

    new_email = f"{new_emp_id.lower()}@paraline.vn"
    
    # Send onboarding email
    try:
        from src.core.email_service import get_email_service
        email_svc = get_email_service()
        subject = f"Chào Mừng Gia Nhập Paraline Software - Thông tin Onboarding"
        body = f"""
Kính gửi {new_employee['name']},

Chào mừng bạn đã chính thức gia nhập Paraline Software với vị trí {position} (Phòng {department}).
Mã nhân viên của bạn là: {new_emp_id}.
Mức lương cơ bản: {salary_vnd:,} VND.
Ngày bắt đầu làm việc: {start_date}.

Dưới đây là danh sách Onboarding Checklist bạn cần hoàn thành:
{checklist_summary}

Vui lòng liên hệ HR nếu bạn cần hỗ trợ thêm thông tin.

Trân trọng,
HR Team
Paraline Software
        """.strip()
        
        # Here we mock sending to the internal email, but realistically we would send 
        # to the applicant's personal email. For this demo, we just print/send to new_email.
        email_svc.send_email(to_email=new_email, subject=subject, body_text=body)
        email_status = f"✅ Đã gửi email chào mừng & onboarding tới {new_email}"
    except Exception as e:
        email_status = f"❌ Không thể gửi email onboarding: {e}"

    return (
        f"Chuyen doi ung vien thanh nhan vien thanh cong!\n"
        f"- Ma nhan vien moi: {new_emp_id}\n"
        f"- Vi tri: {position} | Phong ban: {department}\n"
        f"- Ngay bat dau: {start_date}\n"
        f"- Luong co ban: {salary_vnd:,} VND/thang\n\n"
        f"Onboarding checklist da duoc tao tu dong ({len(onboarding_checklist)} tasks):\n"
        f"{checklist_summary}\n\n"
        f"{email_status}"
    )
