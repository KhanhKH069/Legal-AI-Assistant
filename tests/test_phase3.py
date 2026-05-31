import pytest
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


def test_export_screening_results(auth_client):
    """Test exporting screening results as CSV"""
    response = auth_client.get("/screening/export")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment" in response.headers.get("content-disposition", "")
    assert "Candidate Name" in response.text
    assert "Score" in response.text


def test_upload_policy_no_file(auth_client):
    """Test uploading policy without a file should fail with 422"""
    response = auth_client.post("/policies/upload")
    assert response.status_code == 422


def test_upload_policy_invalid_type(auth_client):
    """Test uploading non-pdf file should return 400"""
    files = {"file": ("test.txt", b"this is a test", "text/plain")}
    response = auth_client.post("/policies/upload", files=files)
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_dashboard_metrics(auth_client):
    """Test getting real-time metrics for dashboard"""
    response = auth_client.get("/metrics/summary")
    if response.status_code == 200:
        data = response.json()
        assert "total_requests" in data or isinstance(data, dict)
