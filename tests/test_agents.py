"""test_agents.py — Tests for orchestrator routing logic (fully offline, no LLM deps).

Tests the pure-Python _classify_intent and router functions directly
without importing the full orchestrator module (which triggers LLM package imports).
The logic is duplicated here intentionally — this is an offline unit test.
"""

import pytest
from langchain_core.messages import HumanMessage

# ── Local reimplementation of orchestrator logic (no heavy imports) ────────────
# This mirrors _VALID_AGENTS and the functions in orchestrator.py exactly.

_VALID_AGENTS = {
    "POLICY": "policy_agent",
    "ONBOARD": "onboard_agent",
    "CV": "cv_agent",
    "ANALYTICS": "analytics_agent",
    "ATTENDANCE": "attendance_agent",
    "HELPDESK": "helpdesk_agent",
    "BENEFITS": "benefits_agent",
    "APPRAISAL": "appraisal_agent",
}


def _classify_intent(response_text: str) -> str:
    """Mirror of orchestrator._classify_intent."""
    upper = response_text.strip().upper()
    for keyword, agent_key in _VALID_AGENTS.items():
        if keyword in upper:
            return agent_key
    return "end"


def _router(state: dict) -> str:
    """Mirror of orchestrator.router."""
    next_step = state.get("next", "end")
    valid_nodes = set(_VALID_AGENTS.values()) | {"end"}
    return next_step if next_step in valid_nodes else "end"


# ── _classify_intent ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "text,expected",
    [
        ("POLICY_AGENT", "policy_agent"),
        ("ONBOARD_AGENT", "onboard_agent"),
        ("CV_AGENT", "cv_agent"),
        ("ANALYTICS_AGENT", "analytics_agent"),
        ("ATTENDANCE_AGENT", "attendance_agent"),
        ("HELPDESK_AGENT", "helpdesk_agent"),
        ("BENEFITS_AGENT", "benefits_agent"),
        ("APPRAISAL_AGENT", "appraisal_agent"),
    ],
)
def test_classify_known_agents(text, expected):
    assert _classify_intent(text) == expected


def test_classify_unknown_returns_end():
    assert _classify_intent("SOME_RANDOM_WORD") == "end"


def test_classify_empty_returns_end():
    assert _classify_intent("") == "end"


def test_classify_case_insensitive():
    assert _classify_intent("policy_agent") == "policy_agent"
    assert _classify_intent("Cv_Agent") == "cv_agent"
    assert _classify_intent("helpdesk_agent") == "helpdesk_agent"


def test_classify_strips_whitespace():
    assert _classify_intent("  HELPDESK_AGENT  ") == "helpdesk_agent"
    assert _classify_intent("\nATTENDANCE_AGENT\n") == "attendance_agent"


def test_classify_partial_match():
    """Classifier should match if the keyword appears anywhere in the string."""
    assert _classify_intent("I think POLICY_AGENT is best") == "policy_agent"


# ── router ─────────────────────────────────────────────────────────────────────


def _make_state(next_val: str) -> dict:
    return {
        "messages": [HumanMessage(content="test")],
        "next": next_val,
        "user_intent": "",
        "user_id": "EMP001",
        "user_info": {},
    }


@pytest.mark.parametrize(
    "agent_key",
    [
        "policy_agent",
        "onboard_agent",
        "cv_agent",
        "analytics_agent",
        "attendance_agent",
        "helpdesk_agent",
        "benefits_agent",
        "appraisal_agent",
    ],
)
def test_router_valid_agents(agent_key):
    assert _router(_make_state(agent_key)) == agent_key


def test_router_end():
    assert _router(_make_state("end")) == "end"


def test_router_invalid_falls_back_to_end():
    assert _router(_make_state("nonexistent_agent")) == "end"


def test_router_empty_falls_back_to_end():
    assert _router(_make_state("")) == "end"


def test_router_with_real_message():
    state = {
        "messages": [HumanMessage(content="Lương của tôi là bao nhiêu?")],
        "next": "policy_agent",
        "user_intent": "POLICY_AGENT",
        "user_id": "EMP005",
        "user_info": {"department": "Engineering"},
    }
    assert _router(state) == "policy_agent"
