from langchain_core.tools import tool

# Mock Database
EMPLOYEE_DATA = {
    "EMP001": {
        "name": "Nguyen Van A",
        "department": "Engineering",
        "position": "Backend Developer",
        "start_date": "2023-01-15",
        "salary_level": "L3",
        "leave_balance": 12,
        "performance_rating": 4.5,
    },
    "EMP002": {
        "name": "Tran Thi B",
        "department": "HR",
        "position": "HR Specialist",
        "start_date": "2022-05-10",
        "salary_level": "L2",
        "leave_balance": 5,
        "performance_rating": 4.0,
    },
}


@tool
def get_employee_profile(employee_id: str) -> str:
    """Retrieve the basic profile information for a specific employee.

    Args:
        employee_id: The ID of the employee (e.g., EMP001, EMP002).

    Returns:
        A string containing the employee's profile information or an error message if not found.
    """
    employee_id = employee_id.upper()
    if employee_id in EMPLOYEE_DATA:
        data = EMPLOYEE_DATA[employee_id]
        return f"Employee Profile for {employee_id}:\nName: {data['name']}\nDepartment: {data['department']}\nPosition: {data['position']}\nStart Date: {data['start_date']}"
    return f"Employee with ID {employee_id} not found."


@tool
def get_leave_balance(employee_id: str) -> str:
    """Retrieve the remaining leave balance for a specific employee.

    Args:
        employee_id: The ID of the employee (e.g., EMP001, EMP002).

    Returns:
        A string containing the number of leave days remaining or an error message if not found.
    """
    employee_id = employee_id.upper()
    if employee_id in EMPLOYEE_DATA:
        days = EMPLOYEE_DATA[employee_id]["leave_balance"]
        return f"Employee {employee_id} ({EMPLOYEE_DATA[employee_id]['name']}) has {days} days of leave remaining."
    return f"Employee with ID {employee_id} not found."


@tool
def get_salary_info(employee_id: str) -> str:
    """Retrieve salary level and performance rating for a specific employee.

    Args:
        employee_id: The ID of the employee (e.g., EMP001, EMP002).

    Returns:
        A string containing salary and performance info or an error message if not found.
    """
    employee_id = employee_id.upper()
    if employee_id in EMPLOYEE_DATA:
        data = EMPLOYEE_DATA[employee_id]
        return f"Compensation Info for {employee_id}:\nSalary Level: {data['salary_level']}\nPerformance Rating: {data['performance_rating']}/5.0"
    return f"Employee with ID {employee_id} not found."
