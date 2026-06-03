import os
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, select, create_engine
from sqlmodel.pool import StaticPool

os.environ.setdefault("OFFLINE_MODE", "true")
os.environ.setdefault("GOOGLE_API_KEY", "test-key-placeholder")

# Override the engine to in-memory BEFORE importing api modules
_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

import api.database as _db_module
_db_module.engine = _test_engine

# Also patch the engine used inside chat router helper functions
import api.routers.chat as _chat_module  # noqa: E402 - must be after engine patch

from api.main import app
from src.core.config import config
from api.models import ConversationMessage

# Ensure DB is created for tests
SQLModel.metadata.create_all(_test_engine)


@pytest.fixture(autouse=True)
def setup_teardown():
    # Clear test db before each test
    with Session(_test_engine) as session:
        for msg in session.exec(select(ConversationMessage)).all():
            session.delete(msg)
        session.commit()
    yield
    # Clear test db after each test
    with Session(_test_engine) as session:
        for msg in session.exec(select(ConversationMessage)).all():
            session.delete(msg)
        session.commit()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def mock_graph(client):
    """Mock the graph invoke method to avoid real LLM calls (and 429 errors).
    Depends on `client` fixture to run AFTER TestClient's lifespan.
    """
    from langchain_core.messages import AIMessage
    
    class MockGraph:
        def invoke(self, state, config=None):
            msgs = state.get("messages", [])
            msgs.append(AIMessage(content="Mocked legal response"))
            return {
                "messages": msgs,
                "user_intent": "STATUTORY",
                "next": "end",
                "user_id": state.get("user_id"),
            }
            
    from api.main import app as _app
    original_graph = getattr(_app.state, "graph", None)
    _app.state.graph = MockGraph()
    yield
    _app.state.graph = original_graph




def test_chat_returns_success(client):
    """Legal AI chat endpoint should return a structured response."""
    response = client.post("/chat", json={"user_id": "test_user_1", "message": "Luật dân sự quy định gì?"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "response" in data
    assert data["user_id"] == "test_user_1"


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


def test_guest_chat_responds(client):
    """Guest chat endpoint should exist and return a valid response structure."""
    response = client.post(
        "/chat/guest", json={"message": "Câu hỏi pháp luật", "session_id": "guest_123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["agent_name"] == "Legal Assistant"
    assert data["session_id"] == "guest_123"
    assert "response" in data
