from typing import Optional
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    role: str = Field(default="employee")  # admin, manager, employee
    employee_id: Optional[str] = Field(default=None)


class Employee(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: str = Field(unique=True, index=True)
    name: str
    gender: str = Field(default="N/A")
    department: str
    position: str
    level: str = Field(default="Junior")
    email: str = Field(default="")
    phone: str = Field(default="")
    hire_date: str
    status: str = Field(default="Active")
    manager_id: Optional[str] = Field(default=None)
    salary_vnd: float = Field(default=0.0)
    leave_balance: float = Field(default=0.0)
    performance_rating: float = Field(default=3.0)
    address: str = Field(default="")
    education: str = Field(default="")
    skills_json: str = Field(default="[]")
    contract_json: str = Field(default="{}")


class LeaveRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    request_id: str = Field(unique=True, index=True)
    employee_id: str = Field(index=True)
    type: str
    start_date: str
    end_date: str
    days: int
    reason: str
    status: str = Field(default="Pending")
    approved_by: Optional[str] = Field(default=None)
    submitted_at: str


class Appraisal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    appraisal_id: str = Field(unique=True, index=True)
    employee_id: str = Field(index=True)
    period: str
    type: str
    status: str = Field(default="Pending")
    self_evaluation_json: str = Field(default="null")
    manager_feedback_json: str = Field(default="null")
    final_score: Optional[float] = Field(default=None)
    rating_label: Optional[str] = Field(default=None)
    created_at: str


class PayrollRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: str = Field(index=True)
    month: str  # e.g. 2026-03
    month_label: str
    working_days: int
    days_worked: int
    leave_days: int
    absent_days: int
    base_salary: float
    ot_hours: float
    ot_rate: float
    ot_pay: float
    kpi_bonus: float
    other_bonus: float
    gross_salary: float
    social_insurance: float
    health_insurance: float
    unemployment_insurance: float
    income_tax: float
    total_deductions: float
    net_salary: float
    status: str = Field(default="Pending")
    payment_date: Optional[str] = Field(default=None)


class Ticket(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticket_id: str = Field(unique=True, index=True)
    employee_id: str = Field(index=True)
    category: str
    subject: str
    description: str
    priority: str
    status: str = Field(default="Open")
    created_at: str
    resolved_at: Optional[str] = Field(default=None)
    comments_json: str = Field(default="[]")


class AttendanceRecord(SQLModel, table=True):
    """Daily check-in/check-out record — replaces attendance_data.json reads."""

    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: str = Field(index=True)
    date: str = Field(index=True)  # YYYY-MM-DD
    day_of_week: str = Field(default="")  # Monday, Tuesday, ...
    week: str = Field(default="")  # YYYY-Www
    check_in: Optional[str] = Field(default=None)  # HH:MM
    check_out: Optional[str] = Field(default=None)  # HH:MM
    total_hours: float = Field(default=0.0)
    ot_hours: float = Field(default=0.0)
    status: str = Field(default="Present")  # Present | Absent | Leave | Weekend


class ConversationMessage(SQLModel, table=True):
    """Persisted chat message — replaces in-memory conversation_history dict."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    role: str  # "user" | "assistant"
    content: str
    timestamp: str  # ISO datetime string


class AuditLog(SQLModel, table=True):
    """Audit trail for sensitive HR actions (view salary, approve leave, etc.)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    actor_id: str = Field(index=True)  # who performed the action
    action: str  # e.g. "VIEW_SALARY", "APPROVE_LEAVE"
    target: str = Field(default="")  # e.g. "EMP042"
    detail: str = Field(default="")  # extra context
    timestamp: str = Field(index=True)  # ISO datetime string
