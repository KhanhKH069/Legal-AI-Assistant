"""Policy Agent Tools"""
from langchain_core.tools import tool

from src.data.policies import HR_POLICIES


@tool
def get_policy_info(policy_type: str) -> str:
    """Get HR policy information"""
    policy = HR_POLICIES.get(policy_type.lower())
    if policy:
        return f"Policy {policy_type}:\n{policy}"
    return f"Policy not found. Available: {', '.join(HR_POLICIES.keys())}"

@tool  
def calculate_leave_days(employment_type: str, work_months: int) -> str:
    """Calculate leave days"""
    base_days = 12 if employment_type.lower() == "full_time" else 6
    earned_days = (base_days / 12) * min(work_months, 12)
    return f"{employment_type} - {work_months} months = {earned_days:.1f} days"

@tool
def search_hr_qa(question: str) -> str:
    """Search HR Q&A"""
    return "Q&A search functionality"
