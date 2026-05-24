"""test_integration.py — FastAPI integration tests using TestClient + in-memory SQLite.

All tests run fully offline (no API key, no external services).
Uses a separate in-memory SQLite DB to avoid polluting the real data/paraline.db.
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

os.environ.setdefault("OFFLINE_MODE", "true")
os.environ.setdefault("GOOGLE_API_KEY", "test-key-placeholder")

# ── In-memory DB setup ────────────────────────────────────────────────────────


@pytest.fixture(name="test_engine", scope="session")
def test_engine_fixture():
    # Import all models here so they are registered with SQLModel.metadata
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="client", scope="session")
def client_fixture(test_engine):
    """Spin up the FastAPI app with the in-memory test DB."""
    from api import database as db_module

    # Override the engine so all routers use our test DB
    db_module.engine = test_engine

    from api.main import app
    from api.models import User, Employee
    from api.auth import get_password_hash

    # Seed minimal test data
    with Session(test_engine) as session:
        # Admin user
        session.add(
            User(
                username="admin",
                hashed_password=get_password_hash("Admin@2026"),
                role="admin",
                employee_id="EMP001",
            )
        )
        # Employee user
        session.add(
            User(
                username="EMP002",
                hashed_password=get_password_hash("Paraline@2026"),
                role="employee",
                employee_id="EMP002",
            )
        )
        # Two employees
        session.add(
            Employee(
                employee_id="EMP001",
                name="Nguyen Van Admin",
                department="Engineering",
                position="CEO",
                hire_date="2020-01-01",
                salary_vnd=50_000_000,
                leave_balance=14,
            )
        )
        session.add(
            Employee(
                employee_id="EMP002",
                name="Tran Thi B",
                department="HR",
                position="HR Specialist",
                hire_date="2022-05-01",
                salary_vnd=20_000_000,
                leave_balance=12,
            )
        )
        session.commit()

    with TestClient(app) as c:
        yield c


# ── Auth helpers ──────────────────────────────────────────────────────────────


def _login(client, username: str, password: str) -> str:
    """Return JWT access token."""
    resp = client.post("/auth/login", data={"username": username, "password": password})
    assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
    return resp.json()["access_token"]


# ── /health ───────────────────────────────────────────────────────────────────


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "agents" in body


# ── Auth ──────────────────────────────────────────────────────────────────────


def test_login_success(client):
    token = _login(client, "admin", "Admin@2026")
    assert len(token) > 10


def test_login_wrong_password(client):
    resp = client.post("/auth/login", data={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


def test_get_me(client):
    token = _login(client, "admin", "Admin@2026")
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "admin"


# ── RBAC: Employees ───────────────────────────────────────────────────────────


def test_employee_cannot_view_others_salary_in_all_profiles(client):
    """Employee role must get salary_vnd=null for other employees."""
    token = _login(client, "EMP002", "Paraline@2026")
    resp = client.get(
        "/employees/all-profiles", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    employees = resp.json()["employees"]
    for emp in employees:
        if emp["employee_id"] != "EMP002":
            assert (
                emp["salary_vnd"] is None
            ), f"Employee {emp['employee_id']} salary should be redacted for EMP002"


def test_admin_can_view_salary_in_all_profiles(client):
    """Admin must see full salary data."""
    token = _login(client, "admin", "Admin@2026")
    resp = client.get(
        "/employees/all-profiles", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    employees = resp.json()["employees"]
    salaries = [e["salary_vnd"] for e in employees]
    assert any(
        s is not None for s in salaries
    ), "Admin should see at least one non-null salary"


def test_unauthenticated_request_returns_401(client):
    resp = client.get("/employees/all-profiles")
    assert resp.status_code == 401


# ── Attendance ────────────────────────────────────────────────────────────────


def test_employee_cannot_view_others_attendance(client):
    token = _login(client, "EMP002", "Paraline@2026")
    # EMP002 trying to access EMP001's attendance
    resp = client.get(
        "/attendance/EMP001", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


# ── Leave Requests ────────────────────────────────────────────────────────────


def test_submit_leave_request(client):
    token = _login(client, "EMP002", "Paraline@2026")
    resp = client.post(
        "/attendance/leave-request",
        json={
            "employee_id": "EMP002",
            "leave_type": "Annual Leave",
            "start_date": "2026-06-10",
            "end_date": "2026-06-12",
            "reason": "Family trip",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "created"
    assert "LR-" in body["request_id"]


def test_employee_cannot_submit_for_others(client):
    token = _login(client, "EMP002", "Paraline@2026")
    resp = client.post(
        "/attendance/leave-request",
        json={
            "employee_id": "EMP001",  # trying to submit for EMP001
            "leave_type": "Annual Leave",
            "start_date": "2026-07-01",
            "end_date": "2026-07-01",
            "reason": "Unauthorized",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_employee_cannot_approve_leave(client):
    """Employees must not be able to approve leave requests."""
    token = _login(client, "EMP002", "Paraline@2026")
    resp = client.put(
        "/attendance/leave-request/LR-2026-001/approve",
        json={"action": "approve"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_admin_can_approve_leave(client):
    """Create a leave request and have admin approve it."""
    emp2_token = _login(client, "EMP002", "Paraline@2026")
    # Create
    create_resp = client.post(
        "/attendance/leave-request",
        json={
            "employee_id": "EMP002",
            "leave_type": "Sick Leave",
            "start_date": "2026-08-01",
            "end_date": "2026-08-02",
            "reason": "Flu",
        },
        headers={"Authorization": f"Bearer {emp2_token}"},
    )
    assert create_resp.status_code == 200
    request_id = create_resp.json()["request_id"]

    # Approve
    admin_token = _login(client, "admin", "Admin@2026")
    approve_resp = client.put(
        f"/attendance/leave-request/{request_id}/approve",
        json={"action": "approve", "comment": "Approved. Get well soon!"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "Approved"


# ── Helpdesk Ticket ───────────────────────────────────────────────────────────


def test_create_and_update_ticket(client):
    emp2_token = _login(client, "EMP002", "Paraline@2026")
    # Create ticket
    create_resp = client.post(
        "/helpdesk/tickets",
        json={
            "employee_id": "EMP002",
            "category": "Hardware/Equipment",
            "subject": "Need a new keyboard",
            "description": "Old keyboard is broken",
            "priority": "Medium",
        },
        headers={"Authorization": f"Bearer {emp2_token}"},
    )
    assert create_resp.status_code == 200
    ticket_id = create_resp.json()["ticket_id"]

    # Admin updates status
    admin_token = _login(client, "admin", "Admin@2026")
    update_resp = client.put(
        f"/helpdesk/tickets/{ticket_id}/status",
        json={"status": "In Progress", "comment": "Ordered a new keyboard"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["ticket"]["status"] == "In Progress"


def test_employee_cannot_update_ticket_status(client):
    emp2_token = _login(client, "EMP002", "Paraline@2026")
    resp = client.put(
        "/helpdesk/tickets/TICK-2026-001/status",
        json={"status": "Closed"},
        headers={"Authorization": f"Bearer {emp2_token}"},
    )
    assert resp.status_code == 403


# ── Audit Logs ────────────────────────────────────────────────────────────────


def test_audit_logs_admin_access(client):
    token = _login(client, "admin", "Admin@2026")
    resp = client.get("/audit/logs", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert "logs" in resp.json()


def test_audit_logs_employee_forbidden(client):
    token = _login(client, "EMP002", "Paraline@2026")
    resp = client.get("/audit/logs", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
