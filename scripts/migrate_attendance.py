"""migrate_attendance.py

Migrate attendance_data.json → SQLite AttendanceRecord table.
Also creates any new tables (ConversationMessage, AuditLog) added to models.py.

Run once after updating models.py:
    python scripts/migrate_attendance.py
"""

import json
import os
import sys

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database import engine, create_db_and_tables
from api.models import AttendanceRecord
from sqlmodel import Session, select

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "attendance_data.json"
)


def run_migration():
    print("=" * 60)
    print("Paraline HR — Attendance Migration Script")
    print("=" * 60)

    # Step 1: Create all new tables
    print("\n[1/3] Creating new database tables...")
    create_db_and_tables()
    print("      ✅ Tables created (AttendanceRecord, ConversationMessage, AuditLog)")

    # Step 2: Load JSON source
    print("\n[2/3] Loading attendance_data.json...")
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"      ❌ File not found: {DATA_PATH}")
        return

    records = data.get("attendance_records", {})
    print(f"      ✅ Found {len(records)} employees in JSON")

    # Step 3: Insert into SQLite (skip if already exists)
    print("\n[3/3] Inserting attendance records into SQLite...")
    inserted = 0
    skipped = 0

    with Session(engine) as session:
        for emp_id, rec in records.items():
            week = rec.get("week", "2026-W10")
            for day in rec.get("daily_records", []):
                date_str = day.get("date")
                # Check if already exists
                existing = session.exec(
                    select(AttendanceRecord).where(
                        AttendanceRecord.employee_id == emp_id,
                        AttendanceRecord.date == date_str,
                    )
                ).first()
                if existing:
                    skipped += 1
                    continue

                ar = AttendanceRecord(
                    employee_id=emp_id,
                    date=date_str,
                    day_of_week=day.get("day", ""),
                    week=week,
                    check_in=day.get("check_in"),
                    check_out=day.get("check_out"),
                    total_hours=float(day.get("total_hours") or 0),
                    ot_hours=float(day.get("ot_hours") or 0),
                    status=day.get("status", "Present"),
                )
                session.add(ar)
                inserted += 1

        session.commit()

    print(f"      ✅ Inserted {inserted} records | Skipped (already exist): {skipped}")

    print("\n" + "=" * 60)
    print("Migration completed successfully! ✅")
    print("=" * 60)


if __name__ == "__main__":
    run_migration()
