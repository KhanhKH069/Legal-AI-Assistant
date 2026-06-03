from typing import Dict, List
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from src.tools.legal_tools import search_statutory_law
from src.core.llm import get_llm

class ContractReviewState(TypedDict):
    contract_text: str
    extracted_clauses: List[str]
    analysis_results: List[Dict[str, str]]
    final_report: str

def parse_contract(state: ContractReviewState) -> ContractReviewState:
    llm = get_llm()
    prompt = f"Bạn là một chuyên gia pháp lý. Hãy trích xuất các điều khoản quan trọng từ bản hợp đồng sau đây để phân tích rủi ro. Trả về mỗi điều khoản trên một dòng, bắt đầu bằng dấu gạch ngang (-).\n\nHợp đồng:\n{state['contract_text'][:10000]}"
    response = llm.invoke([HumanMessage(content=prompt)])
    lines = response.content.split('\n')
    clauses = [line.strip('- ').strip() for line in lines if line.strip().startswith('-')]
    return {'extracted_clauses': clauses}

def analyze_clauses(state: ContractReviewState) -> ContractReviewState:
    results = []
    for clause in state['extracted_clauses'][:5]:
        search_result = search_statutory_law(clause, top_k=3)
        llm = get_llm()
        eval_prompt = f'Bạn là một Luật sư Thẩm định. Hãy đánh giá xem điều khoản hợp đồng sau có vi phạm các quy định pháp luật được cung cấp hay không. Nếu có rủi ro, hãy giải thích rõ.\n\nĐiều khoản Hợp đồng:\n{clause}\n\nCăn cứ Pháp luật:\n{search_result}'
        response = llm.invoke([SystemMessage(content='Bạn là Luật sư cực kỳ cẩn thận. Chỉ ra rủi ro nếu có căn cứ rõ ràng, không bịa đặt luật.'), HumanMessage(content=eval_prompt)])
        results.append({'clause': clause, 'analysis': response.content})
    return {'analysis_results': results}

def generate_report(state: ContractReviewState) -> ContractReviewState:
    report = '# Báo cáo Thẩm định Hợp đồng\n\n'
    if not state.get('analysis_results'):
        report += 'Không có vấn đề rủi ro pháp lý nào được phát hiện trong các điều khoản chính.'
        return {'final_report': report}
    for i, res in enumerate(state['analysis_results'], 1):
        report += f"### {i}. Điều khoản:\n_{res['clause']}_\n\n"
        report += f"**Đánh giá Pháp lý:**\n{res['analysis']}\n\n"
        report += '---\n'
    return {'final_report': report}

def build_contract_reviewer_graph() -> StateGraph:
    workflow = StateGraph(ContractReviewState)
    workflow.add_node('parse', parse_contract)
    workflow.add_node('analyze', analyze_clauses)
    workflow.add_node('report', generate_report)
    workflow.add_edge(START, 'parse')
    workflow.add_edge('parse', 'analyze')
    workflow.add_edge('analyze', 'report')
    workflow.add_edge('report', END)
    return workflow.compile()

def run_contract_review(text: str) -> str:
    graph = build_contract_reviewer_graph()
    initial_state = {'contract_text': text, 'extracted_clauses': [], 'analysis_results': [], 'final_report': ''}
    result = graph.invoke(initial_state)
    return result['final_report']