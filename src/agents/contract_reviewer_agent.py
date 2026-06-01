from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

from src.core.config import config
from src.tools.legal_tools import search_statutory_law


def get_llm():
    if config.enable_offline_mode or not config.google_api_key:
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model="qwen2.5:7b-instruct",
            temperature=0.1,
            base_url="http://localhost:11434",
        )
    else:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=config.model_name,
            google_api_key=config.google_api_key,
            temperature=0.1,
            max_tokens=config.max_tokens,
        )


class ContractReviewState(TypedDict):
    contract_text: str
    extracted_clauses: List[str]
    analysis_results: List[Dict[str, str]]
    final_report: str


def parse_contract(state: ContractReviewState) -> ContractReviewState:
    """Uses LLM to chunk the contract into major clauses for analysis."""
    llm = get_llm()
    prompt = (
        "Bạn là một chuyên gia pháp lý. Hãy trích xuất các điều khoản quan trọng "
        "từ bản hợp đồng sau đây để phân tích rủi ro. "
        "Trả về mỗi điều khoản trên một dòng, bắt đầu bằng dấu gạch ngang (-).\n\n"
        f"Hợp đồng:\n{state['contract_text'][:10000]}"  # Limit to 10k chars for safety
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    lines = response.content.split("\n")
    clauses = [
        line.strip("- ").strip() for line in lines if line.strip().startswith("-")
    ]

    return {"extracted_clauses": clauses}


def analyze_clauses(state: ContractReviewState) -> ContractReviewState:
    """Checks each clause against Statutory law using the search tool."""
    results = []

    # Analyze top 5 most important clauses to save time/tokens
    for clause in state["extracted_clauses"][:5]:
        # Search for laws related to this clause
        search_result = search_statutory_law(clause, top_k=3)

        # Ask LLM to evaluate the clause against the found laws
        llm = get_llm()
        eval_prompt = (
            "Bạn là một Luật sư Thẩm định. Hãy đánh giá xem điều khoản hợp đồng sau có "
            "vi phạm các quy định pháp luật được cung cấp hay không. "
            "Nếu có rủi ro, hãy giải thích rõ.\n\n"
            f"Điều khoản Hợp đồng:\n{clause}\n\n"
            f"Căn cứ Pháp luật:\n{search_result}"
        )
        response = llm.invoke(
            [
                SystemMessage(
                    content="Bạn là Luật sư cực kỳ cẩn thận. Chỉ ra rủi ro nếu có căn cứ rõ ràng, không bịa đặt luật."
                ),
                HumanMessage(content=eval_prompt),
            ]
        )

        results.append({"clause": clause, "analysis": response.content})

    return {"analysis_results": results}


def generate_report(state: ContractReviewState) -> ContractReviewState:
    """Summarizes the findings into a markdown report."""
    report = "# Báo cáo Thẩm định Hợp đồng\n\n"

    if not state.get("analysis_results"):
        report += "Không có vấn đề rủi ro pháp lý nào được phát hiện trong các điều khoản chính."
        return {"final_report": report}

    for i, res in enumerate(state["analysis_results"], 1):
        report += f"### {i}. Điều khoản:\n_{res['clause']}_\n\n"
        report += f"**Đánh giá Pháp lý:**\n{res['analysis']}\n\n"
        report += "---\n"

    return {"final_report": report}


def build_contract_reviewer_graph() -> StateGraph:
    workflow = StateGraph(ContractReviewState)

    workflow.add_node("parse", parse_contract)
    workflow.add_node("analyze", analyze_clauses)
    workflow.add_node("report", generate_report)

    workflow.add_edge(START, "parse")
    workflow.add_edge("parse", "analyze")
    workflow.add_edge("analyze", "report")
    workflow.add_edge("report", END)

    return workflow.compile()


def run_contract_review(text: str) -> str:
    """Helper function to execute the graph."""
    graph = build_contract_reviewer_graph()
    initial_state = {
        "contract_text": text,
        "extracted_clauses": [],
        "analysis_results": [],
        "final_report": "",
    }
    result = graph.invoke(initial_state)
    return result["final_report"]
