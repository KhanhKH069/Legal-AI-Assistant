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
    """Search HR Q&A and Policies knowledge base. Use this tool when the user asks any question about company policies, rules, benefits, etc."""
    try:
        from src.services.hybrid_retriever import get_hybrid_retriever

        retriever = get_hybrid_retriever()
        results = retriever.retrieve(question, top_k=3)

        if not results:
            return "No relevant information found in the HR knowledge base."

        formatted_results = []
        for i, res in enumerate(results):
            content = res["content"]
            source = res["metadata"].get("source_file", "Unknown")
            formatted_results.append(
                f"--- Result {i + 1} (Source: {source}) ---\n{content}"
            )

        return "\n\n".join(formatted_results)
    except Exception as e:
        return f"Error searching knowledge base: {e}"
