import pytest
from src.agents.orchestrator import _classify_intent, router, AgentState


def test_classify_intent_exact_match():
    assert _classify_intent("POLICY") == "policy_agent"
    assert _classify_intent("CV") == "cv_agent"
    assert _classify_intent("ATTENDANCE") == "attendance_agent"


def test_classify_intent_substring_match():
    assert _classify_intent("USE THE POLICY AGENT PLEASE") == "policy_agent"
    assert _classify_intent("ANALYTICS IS WHAT I NEED") == "analytics_agent"


def test_classify_intent_unknown():
    assert _classify_intent("SOMETHING ELSE") == "end"
    assert _classify_intent("") == "end"


def test_router_valid_agent():
    state: AgentState = {
        "messages": [],
        "next": "policy_agent",
        "user_intent": "POLICY",
        "user_id": "test",
        "user_info": {},
    }
    assert router(state) == "policy_agent"

    state["next"] = "attendance_agent"
    assert router(state) == "attendance_agent"


def test_router_invalid_agent():
    state: AgentState = {
        "messages": [],
        "next": "invalid_agent",
        "user_intent": "INVALID",
        "user_id": "test",
        "user_info": {},
    }
    assert router(state) == "end"

    state["next"] = ""
    assert router(state) == "end"
