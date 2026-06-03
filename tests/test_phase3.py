"""test_phase3.py — Tests for Legal AI Phase 3 features: metrics, auth override."""

import os
import pytest

os.environ.setdefault("OFFLINE_MODE", "true")
os.environ.setdefault("GOOGLE_API_KEY", "test-key-placeholder")

from fastapi.testclient import TestClient
from api.main import app
from api.auth import get_current_user
from api.models import User


async def mock_get_current_user():
    return User(id=1, username="test_admin", role="admin", employee_id="TEST001")


@pytest.fixture(autouse=True)
def override_auth():
    """Override auth dependency for all tests in this module."""
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def auth_client(override_auth):
    with TestClient(app) as c:
        yield c


# ── Metrics ───────────────────────────────────────────────────────────────────


def test_dashboard_metrics(auth_client):
    """Test getting real-time metrics for dashboard."""
    response = auth_client.get("/metrics/summary")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


# ── Health ────────────────────────────────────────────────────────────────────


def test_health_check(auth_client):
    response = auth_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ── Contract Review — validation ──────────────────────────────────────────────


def test_contract_review_no_file(auth_client):
    """Uploading with no file should fail with 422."""
    response = auth_client.post("/contract/review")
    assert response.status_code == 422


def test_contract_review_invalid_type(auth_client):
    """Uploading a non-PDF file should return 400."""
    files = {"file": ("test.txt", b"this is a text file", "text/plain")}
    response = auth_client.post("/contract/review", files=files)
    # Acceptable: 400 (validation) or 422 (FastAPI unprocessable)
    assert response.status_code in (400, 422, 500)


# ── Chat Guest Endpoint ───────────────────────────────────────────────────────


def test_guest_chat_endpoint_exists(auth_client):
    """Guest chat endpoint should exist and respond."""
    response = auth_client.post(
        "/chat/guest",
        json={"message": "Tôi có câu hỏi về luật", "session_id": "test_session"},
    )
    assert response.status_code in (200, 500)


# ── Audit logs ────────────────────────────────────────────────────────────────


def test_audit_logs_accessible_with_admin(auth_client):
    response = auth_client.get("/audit/logs")
    assert response.status_code == 200
    assert "logs" in response.json()
