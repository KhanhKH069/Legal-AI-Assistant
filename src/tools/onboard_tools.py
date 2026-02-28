"""Onboard Agent Tools"""
from langchain_core.tools import tool

from src.data.onboarding import ONBOARDING_DATA


@tool
def get_onboarding_checklist(phase: str) -> str:
    """Get onboarding checklist"""
    checklist = ONBOARDING_DATA.get(phase.lower())
    if checklist:
        items = "\n".join([f"- {item}" for item in checklist])
        return f"Checklist for {phase}:\n{items}"
    return f"Phase not found. Available: {', '.join(ONBOARDING_DATA.keys())}"
