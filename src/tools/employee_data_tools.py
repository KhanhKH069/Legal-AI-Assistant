"""Employee Data Tools — loads from hr_mock_data.csv"""

import csv
import os
from functools import lru_cache

from langchain_core.tools import tool

_CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "hr_mock_data.csv"
)


def _salary_to_level(salary: float) -> str:
    """Map raw salary (USD) to an anonymised level."""
    if salary < 1300:
        return "L1"
    elif salary < 1800:
        return "L2"
    elif salary < 2500:
        return "L3"
    elif salary < 3500:
        return "L4"
    else:
        return "L5"


@lru_cache(maxsize=1)
def _load_employees() -> dict:
    """Load all employees from CSV once and cache."""
    data: dict = {}
    try:
        with open(_CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                eid = row["employee_id"].strip().upper()
                data[eid] = {
                    "name": row["name"].strip(),
                    "department": row["department"].strip(),
                    "position": row["position"].strip(),
                    "start_date": row["hire_date"].strip(),
                    "salary_level": _salary_to_level(float(row["salary"])),
                    "leave_balance": int(row["leave_balance"]),
                    "performance_rating": float(row["performance_rating"]),
                    "status": row["status"].strip(),
                }
    except FileNotFoundError:
        # Fallback to a minimal dict so tools don't crash
        data = {
            "EMP001": {
                "name": "Nguyen Van A",
                "department": "Engineering",
                "position": "Backend Developer",
                "start_date": "2023-01-15",
                "salary_level": "L3",
                "leave_balance": 12,
                "performance_rating": 4.5,
                "status": "Active",
            }
        }
    return data


def get_employee_by_id(employee_id: str) -> dict | None:
    """Return employee dict or None if not found."""
    return _load_employees().get(employee_id.strip().upper())


def list_all_employees() -> list[dict]:
    """Return list of all employees with id+name for UI dropdowns."""
    return [
        {"id": eid, "name": info["name"], "department": info["department"]}
        for eid, info in _load_employees().items()
        if info["status"] == "Active"
    ]


@tool
def get_employee_profile(employee_id: str) -> str:
    """Retrieve the basic profile information for a specific employee.

    Args:
        employee_id: The ID of the employee (e.g., EMP001, EMP002).

    Returns:
        A string containing the employee's profile information or an error message if not found.
    """
    data = get_employee_by_id(employee_id)
    if data:
        return (
            f"Employee Profile for {employee_id.upper()}:\n"
            f"Name: {data['name']}\n"
            f"Department: {data['department']}\n"
            f"Position: {data['position']}\n"
            f"Start Date: {data['start_date']}\n"
            f"Status: {data['status']}"
        )
    return f"Employee with ID {employee_id} not found."


@tool
def get_leave_balance(employee_id: str) -> str:
    """Retrieve the remaining leave balance for a specific employee.

    Args:
        employee_id: The ID of the employee (e.g., EMP001, EMP002).

    Returns:
        A string containing the number of leave days remaining or an error message if not found.
    """
    data = get_employee_by_id(employee_id)
    if data:
        return (
            f"Employee {employee_id.upper()} ({data['name']}) has "
            f"{data['leave_balance']} days of leave remaining."
        )
    return f"Employee with ID {employee_id} not found."


@tool
def get_salary_info(employee_id: str) -> str:
    """Retrieve salary level and performance rating for a specific employee.

    Args:
        employee_id: The ID of the employee (e.g., EMP001, EMP002).

    Returns:
        A string containing salary level and performance info (no raw numbers).
    """
    data = get_employee_by_id(employee_id)
    if data:
        return (
            f"Compensation Info for {employee_id.upper()}:\n"
            f"Salary Level: {data['salary_level']}\n"
            f"Performance Rating: {data['performance_rating']}/5.0"
        )
    return f"Employee with ID {employee_id} not found."
