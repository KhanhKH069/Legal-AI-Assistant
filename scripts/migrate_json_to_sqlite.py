#!/usr/bin/env python3
"""
Migrate JSON data from data/*.json to SQLite (paraline.db)
Populates api.models
"""

import os
import sys
import json
from pathlib import Path
from passlib.context import CryptContext

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlmodel import select
from api.database import create_db_and_tables, get_session
from api.models import Employee, User, Appraisal, AttendanceRecord

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


DATA_DIR = Path("data")


def load_json(filename: str):
    path = DATA_DIR / filename
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def migrate_employees(session):
    print("Migrating Employees and Users...")
    data = load_json("employees_data.json")
    if not data or "employees" not in data:
        return

    count = 0
    default_hashed_password = get_password_hash("password123")

    for emp in data["employees"]:
        # Check if exists
        existing = session.exec(
            select(Employee).where(Employee.employee_id == emp["employee_id"])
        ).first()
        if existing:
            continue

        db_emp = Employee(
            employee_id=emp["employee_id"],
            name=emp["name"],
            gender=emp.get("gender", "N/A"),
            department=emp["department"],
            position=emp["position"],
            level=emp.get("level", "Junior"),
            email=emp.get("email", ""),
            phone=emp.get("phone", ""),
            hire_date=emp["hire_date"],
            status=emp.get("status", "Active"),
            manager_id=emp.get("manager_id"),
            salary_vnd=float(emp.get("salary_vnd", 0)),
            leave_balance=float(emp.get("leave_balance", 0)),
            performance_rating=float(emp.get("performance_rating", 3.0)),
            address=emp.get("address", ""),
            education=emp.get("education", ""),
            skills_json=json.dumps(emp.get("skills", []), ensure_ascii=False),
            contract_json=json.dumps(emp.get("contract", {}), ensure_ascii=False),
        )
        session.add(db_emp)

        # Create corresponding User
        role = "employee"
        if "Manager" in emp.get("level", "") or "Lead" in emp.get("level", ""):
            role = "manager"
        if emp.get("department") == "HR" and (
            "Manager" in emp.get("position", "")
            or "Specialist" in emp.get("position", "")
        ):
            role = "admin"

        db_user = User(
            username=emp["employee_id"],
            hashed_password=default_hashed_password,
            role=role,
            employee_id=emp["employee_id"],
        )
        session.add(db_user)

        count += 1

    session.commit()
    print(f"  -> Inserted {count} employees and users.")


def migrate_attendance(session):
    print("Migrating Attendance...")
    data = load_json("attendance_data.json")
    if not data or "attendance_records" not in data:
        return

    count = 0
    records_dict = data["attendance_records"]
    for emp_id, emp_data in records_dict.items():
        week = emp_data.get("week", "")
        if "daily_records" in emp_data:
            for rec in emp_data["daily_records"]:
                existing = session.exec(
                    select(AttendanceRecord).where(
                        AttendanceRecord.employee_id == emp_id,
                        AttendanceRecord.date == rec["date"],
                    )
                ).first()
                if existing:
                    continue

                db_rec = AttendanceRecord(
                    employee_id=emp_id,
                    date=rec["date"],
                    day_of_week=rec.get("day", ""),
                    week=week,
                    check_in=rec.get("check_in"),
                    check_out=rec.get("check_out"),
                    total_hours=float(rec.get("total_hours", 0.0)),
                    ot_hours=float(rec.get("ot_hours", 0.0)),
                    status=rec.get("status", "Present"),
                )
                session.add(db_rec)
                count += 1
    session.commit()
    print(f"  -> Inserted {count} attendance records.")


def migrate_appraisals(session):
    print("Migrating Appraisals...")
    data = load_json("appraisal_data.json")
    if not data or "appraisals" not in data:
        return

    count = 0
    for rec in data["appraisals"]:
        existing = session.exec(
            select(Appraisal).where(Appraisal.appraisal_id == rec["appraisal_id"])
        ).first()
        if existing:
            continue

        db_rec = Appraisal(
            appraisal_id=rec["appraisal_id"],
            employee_id=rec["employee_id"],
            period=rec["period"],
            type=rec.get("type", "Annual"),
            status=rec.get("status", "Pending"),
            self_evaluation_json=json.dumps(
                rec.get("self_evaluation", {}), ensure_ascii=False
            ),
            manager_feedback_json=json.dumps(
                rec.get("manager_feedback", {}), ensure_ascii=False
            ),
            final_score=rec.get("final_score"),
            rating_label=rec.get("rating_label"),
            created_at=rec.get("created_at", ""),
        )
        session.add(db_rec)
        count += 1
    session.commit()
    print(f"  -> Inserted {count} appraisal records.")


if __name__ == "__main__":
    create_db_and_tables()
    # get_session yields a session, so we use next() to get it
    session_generator = get_session()
    session = next(session_generator)
    try:
        migrate_employees(session)
        migrate_attendance(session)
        migrate_appraisals(session)
    finally:
        session.close()
    print("Migration Complete!")
