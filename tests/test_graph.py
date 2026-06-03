"""test_graph.py — Tests for Legal AI Orchestrator routing logic."""

import pytest
from src.agents.orchestrator import _classify_intent, router, AgentState


def test_classify_intent_statutory_exact():
    assert _classify_intent("STATUTORY") == "statutory_agent"


def test_classify_intent_caselaw_exact():
    assert _classify_intent("CASELAW") == "caselaw_agent"


def test_classify_intent_statutory_substring():
    assert _classify_intent("THIS IS A STATUTORY QUESTION") == "statutory_agent"


def test_classify_intent_caselaw_substring():
    assert _classify_intent("CASELAW IS NEEDED HERE") == "caselaw_agent"


def test_classify_intent_unknown_defaults_to_statutory():
    """Legal domain always defaults to statutory_agent (not 'end')."""
    assert _classify_intent("SOMETHING UNKNOWN") == "statutory_agent"
    assert _classify_intent("") == "statutory_agent"


def test_classify_intent_case_insensitive():
    assert _classify_intent("statutory") == "statutory_agent"
    assert _classify_intent("Caselaw") == "caselaw_agent"


def test_router_valid_statutory():
    state: AgentState = {
        "messages": [],
        "next": "statutory_agent",
        "user_intent": "STATUTORY",
        "user_id": "test",
        "user_info": {},
    }
    assert router(state) == "statutory_agent"


def test_router_valid_caselaw():
    state: AgentState = {
        "messages": [],
        "next": "caselaw_agent",
        "user_intent": "CASELAW",
        "user_id": "test",
        "user_info": {},
    }
    assert router(state) == "caselaw_agent"


def test_router_invalid_agent_falls_back_to_statutory():
    """Unknown next step should fall back to statutory_agent."""
    state: AgentState = {
        "messages": [],
        "next": "invalid_agent",
        "user_intent": "UNKNOWN",
        "user_id": "test",
        "user_info": {},
    }
    assert router(state) == "statutory_agent"


def test_router_empty_next_falls_back_to_statutory():
    state: AgentState = {
        "messages": [],
        "next": "",
        "user_intent": "",
        "user_id": "test",
        "user_info": {},
    }
    assert router(state) == "statutory_agent"
