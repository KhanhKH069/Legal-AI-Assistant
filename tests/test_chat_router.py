import pytest
from fastapi.testclient import TestClient
from api.main import app
from src.core.config import config
from sqlmodel import Session, SQLModel, select
from api.database import engine
from api.models import ConversationMessage

# Ensure DB is created for tests
SQLModel.metadata.create_all(engine)


@pytest.fixture(autouse=True)
def setup_teardown():
    # Clear test db before each test
    with Session(engine) as session:
        for msg in session.exec(select(ConversationMessage)).all():
            session.delete(msg)
        session.commit()
    yield
    # Clear test db after each test
    with Session(engine) as session:
        for msg in session.exec(select(ConversationMessage)).all():
            session.delete(msg)
        session.commit()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_chat_offline_mode(client, monkeypatch):
    # Ensure offline mode is active
    monkeypatch.setattr(config, "enable_offline_mode", True)

    response = client.post("/chat", json={"user_id": "test_user_1", "message": "hello"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["intent"] == "OFFLINE"
    assert "response" in data


def test_get_chat_history(client):
    # Create some dummy history by hitting offline chat
    client.post("/chat", json={"user_id": "test_history", "message": "hello"})

    response = client.get("/chat/history/test_history")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "test_history"
    assert data["message_count"] == 2  # 1 user msg, 1 assistant msg
    assert len(data["messages"]) == 2
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][0]["content"] == "hello"
    assert data["messages"][1]["role"] == "assistant"


def test_clear_chat_history(client):
    # Create dummy history
    client.post("/chat", json={"user_id": "test_clear", "message": "hello"})

    # Clear it
    response = client.delete("/chat/history/test_clear")
    assert response.status_code == 200
    assert response.json()["status"] == "cleared"

    # Verify it is empty
    history = client.get("/chat/history/test_clear")
    assert history.json()["message_count"] == 0


def test_guest_chat_offline(client, monkeypatch):
    monkeypatch.setattr(config, "enable_offline_mode", True)

    # Guest graph might not be initialized if not loaded, so mock it for safety
    app.state.guest_graph = None

    response = client.post(
        "/chat/guest", json={"message": "Tôi muốn ứng tuyển", "session_id": "guest_123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["agent_name"] == "Recruitment Assistant"
    assert data["session_id"] == "guest_123"
    assert "response" in data
