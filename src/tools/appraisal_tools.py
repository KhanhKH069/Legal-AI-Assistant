"""
Performance Appraisal Tools — Paraline HR AI Agent
Provides: create appraisal, submit self-evaluation, submit manager feedback,
           get appraisal history, get pending appraisals.
"""

import json
import os
from datetime import datetime
from typing import Any

from langchain_core.tools import tool

_APR_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "appraisal_data.json"
)
_EMP_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "employees_data.json"
)


def _load_appraisals() -> dict:
    try:
        with open(_APR_PATH, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"appraisals": [], "total": 0}


def _save_appraisals(data: dict) -> None:
    with open(_APR_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_employees() -> list[dict]:
    try:
        with open(_EMP_PATH, encoding="utf-8") as f:
            return json.load(f).get("employees", [])
    except FileNotFoundError:
        return []


@tool
def get_appraisal_history(employee_id: str) -> str:
    """Get all past and current appraisals for an employee.

    Args:
        employee_id: Employee ID (e.g. EMP001)
    """
    data = _load_appraisals()
    records = [
        a for a in data["appraisals"] if a["employee_id"].upper() == employee_id.upper()
    ]

    if not records:
        return f"Chưa có hồ sơ đánh giá nào cho nhân viên {employee_id}."

    lines = [f"**Lịch sử Appraisal — {records[0]['employee_name']} ({employee_id})**\n"]
    for r in records:
        score_str = (
            f"Điểm cuối: {r['final_score']}" if r.get("final_score") else "Chưa có điểm"
        )
        lines.append(
            f"- [{r['status']}] {r['appraisal_id']} | {r['period']} | {r['type']} | {score_str}"
        )
        if r.get("rating_label"):
            lines[-1] += f" → {r['rating_label']}"
    return "\n".join(lines)


@tool
def create_appraisal(
    employee_id: str, period: str, appraisal_type: str = "Annual"
) -> str:
    """Create a new performance appraisal record for an employee.

    Args:
        employee_id: Employee ID (e.g. EMP001)
        period: Appraisal period (e.g. '2026-H1', '2026-Annual')
        appraisal_type: Type of appraisal - 'Annual', 'Semi-annual', or 'Probation'
    """
    data = _load_appraisals()
    employees = _load_employees()

    emp = next(
        (e for e in employees if e["employee_id"].upper() == employee_id.upper()), None
    )
    if not emp:
        return f"Không tìm thấy nhân viên {employee_id}."

    appraisal_id = f"APR-{period}-{employee_id.upper()}"
    existing = next(
        (a for a in data["appraisals"] if a["appraisal_id"] == appraisal_id), None
    )
    if existing:
        return f"Appraisal {appraisal_id} đã tồn tại (Status: {existing['status']})."

    new_record = {
        "appraisal_id": appraisal_id,
        "employee_id": employee_id.upper(),
        "employee_name": emp["name"],
        "department": emp["department"],
        "position": emp["position"],
        "manager_id": emp.get("manager_id"),
        "period": period,
        "type": appraisal_type,
        "status": "Pending",
        "self_evaluation": None,
        "manager_feedback": None,
        "final_score": None,
        "rating_label": None,
        "created_at": datetime.now().isoformat(),
    }
    data["appraisals"].append(new_record)
    data["total"] = len(data["appraisals"])
    _save_appraisals(data)

    return (
        f"Da tao Appraisal thanh cong!\n"
        f"- ID: {appraisal_id}\n"
        f"- Nhan vien: {emp['name']} | {emp['position']}\n"
        f"- Loai: {appraisal_type} | Ky: {period}\n"
        f"- Trang thai: Pending (cho nhan vien tu danh gia)"
    )


@tool
def submit_self_evaluation(
    employee_id: str,
    period: str,
    score: float,
    achievements: str,
    challenges: str,
    goals_next: str,
) -> str:
    """Submit self-evaluation for a performance appraisal.

    Args:
        employee_id: Employee ID (e.g. EMP001)
        period: Appraisal period (e.g. '2026-H1')
        score: Self-score from 1.0 to 5.0
        achievements: Key achievements this period
        challenges: Challenges faced
        goals_next: Goals for next period
    """
    if not (1.0 <= score <= 5.0):
        return "Diem tu danh gia phai trong khoang 1.0 den 5.0."

    data = _load_appraisals()
    appraisal_id = f"APR-{period}-{employee_id.upper()}"
    record = next(
        (a for a in data["appraisals"] if a["appraisal_id"] == appraisal_id), None
    )

    if not record:
        return (
            f"Khong tim thay appraisal {appraisal_id}. "
            f"Vui long tao appraisal truoc bang create_appraisal."
        )

    record["self_evaluation"] = {
        "score": score,
        "achievements": achievements,
        "challenges": challenges,
        "goals_next": goals_next,
        "submitted_at": datetime.now().isoformat(),
    }
    record["status"] = "In Progress"
    data["total"] = len(data["appraisals"])
    _save_appraisals(data)

    return (
        f"Tu danh gia da nop thanh cong!\n"
        f"- Appraisal: {appraisal_id}\n"
        f"- Diem tu danh gia: {score}/5.0\n"
        f"- Trang thai: In Progress (cho quan ly phan hoi)"
    )


@tool
def submit_manager_feedback(
    appraisal_id: str, manager_id: str, score: float, strengths: str, improvements: str
) -> str:
    """Submit manager feedback and finalize a performance appraisal.
    Final score = 30% self-evaluation + 70% manager score.

    Args:
        appraisal_id: Full appraisal ID (e.g. APR-2026-H1-EMP001)
        manager_id: Manager's employee ID
        score: Manager score from 1.0 to 5.0
        strengths: Employee's key strengths
        improvements: Areas for improvement
    """
    if not (1.0 <= score <= 5.0):
        return "Diem quan ly phai trong khoang 1.0 den 5.0."

    data = _load_appraisals()
    record = next(
        (a for a in data["appraisals"] if a["appraisal_id"] == appraisal_id), None
    )

    if not record:
        return f"Khong tim thay appraisal '{appraisal_id}'."
    if record["status"] == "Completed":
        return f"Appraisal {appraisal_id} da Completed roi."

    record["manager_feedback"] = {
        "score": score,
        "strengths": strengths,
        "improvements": improvements,
        "manager_id": manager_id,
        "submitted_at": datetime.now().isoformat(),
    }

    # Calculate final score
    self_score = record.get("self_evaluation", {})
    self_s = self_score.get("score", score) if self_score else score
    final = round(self_s * 0.3 + score * 0.7, 1)

    label = (
        "Xuat sac"
        if final >= 4.5
        else "Tot"
        if final >= 4.0
        else "Dat yeu cau"
        if final >= 3.0
        else "Can cai thien"
    )

    record["final_score"] = final
    record["rating_label"] = label
    record["status"] = "Completed"
    data["total"] = len(data["appraisals"])
    _save_appraisals(data)

    return (
        f"Appraisal hoan thanh!\n"
        f"- ID: {appraisal_id}\n"
        f"- Diem quan ly: {score}/5.0\n"
        f"- Diem cuoi (30% self + 70% manager): {final}/5.0\n"
        f"- Xep loai: {label}"
    )


@tool
def get_pending_appraisals(department: str = "") -> str:
    """Get all pending or in-progress appraisals. Optionally filter by department.

    Args:
        department: Optional department filter (e.g. 'Engineering')
    """
    data = _load_appraisals()
    pending = [
        a
        for a in data["appraisals"]
        if a["status"] in ("Pending", "In Progress")
        and (not department or a.get("department", "").lower() == department.lower())
    ]

    if not pending:
        return "Khong co appraisal nao dang cho xu ly" + (
            f" trong phong {department}." if department else "."
        )

    lines = [f"**Appraisals chua hoan thanh** ({len(pending)} records):\n"]
    for a in pending:
        lines.append(
            f"- [{a['status']:11}] {a['appraisal_id']:30} | "
            f"{a['employee_name']:20} | {a['department']}"
        )
    return "\n".join(lines)


# Export list for agent binding
appraisal_tools: list[Any] = [
    get_appraisal_history,
    create_appraisal,
    submit_self_evaluation,
    submit_manager_feedback,
    get_pending_appraisals,
]
