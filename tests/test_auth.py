from fastapi.testclient import TestClient


def test_login_success(client: TestClient):
    response = client.post(
        "/auth/login", data={"username": "admin_test", "password": "testpass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "admin_test"
    assert data["user"]["role"] == "admin"


def test_login_failure(client: TestClient):
    response = client.post(
        "/auth/login", data={"username": "admin_test", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_read_users_me_success(client: TestClient):
    # First login to get token
    login_res = client.post(
        "/auth/login", data={"username": "admin_test", "password": "testpass"}
    )
    token = login_res.json()["access_token"]

    # Now request /auth/me
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "admin_test"


def test_read_users_me_unauthorized(client: TestClient):
    response = client.get("/auth/me")
    assert response.status_code == 401
