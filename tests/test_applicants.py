from fastapi.testclient import TestClient


def get_auth_token(client: TestClient) -> str:
    res = client.post(
        "/auth/login", data={"username": "admin_test", "password": "testpass"}
    )
    return res.json()["access_token"]


def test_list_applicants_unauthorized(client: TestClient):
    response = client.get("/applicants/")
    assert response.status_code == 401


def test_list_applicants_authorized(client: TestClient):
    token = get_auth_token(client)
    response = client.get("/applicants/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_applicant_public(client: TestClient):
    # POST should be public
    payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "0987654321",
        "position": "Frontend Developer",
    }
    response = client.post("/applicants/", json=payload)
    assert response.status_code == 201
    assert response.json()["name"] == "Jane Doe"
    assert response.json()["position"] == "Frontend Developer"
