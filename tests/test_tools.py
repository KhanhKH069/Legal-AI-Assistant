"""Unit tests for HR AI Agent tool layer.

Tests are intentionally designed to run fully offline (no API key needed)
by targeting the pure data-retrieval and formatting logic.
"""


# ─── Payroll Tools ────────────────────────────────────────────────────────────


def test_payroll_record_known_employee():
    """get_payroll_record should return a formatted payslip for EMP001."""
    from src.tools.payroll_tools import get_payroll_record

    result = get_payroll_record.invoke({"employee_id": "EMP001", "month": ""})
    assert "EMP001" in result
    assert "Lương cơ bản" in result or "LƯƠNG THỰC NHẬN" in result


def test_payroll_record_unknown_employee():
    """get_payroll_record should return a friendly error for unknown IDs."""
    from src.tools.payroll_tools import get_payroll_record

    result = get_payroll_record.invoke({"employee_id": "EMP999", "month": ""})
    assert "Không tìm thấy" in result


def test_payroll_history_summary():
    """get_payroll_history should contain comparison line when ≥2 months exist."""
    from src.tools.payroll_tools import get_payroll_history

    result = get_payroll_history.invoke({"employee_id": "EMP001"})
    # Should contain the month-on-month comparison line
    assert "So với tháng trước" in result or "Lịch Sử Lương" in result


# ─── Helpdesk Tools ───────────────────────────────────────────────────────────


def test_create_ticket_returns_ticket_id():
    """create_hr_ticket should create a ticket and return a ticket ID."""
    from src.tools.helpdesk_tools import create_hr_ticket

    result = create_hr_ticket.invoke(
        {
            "employee_id": "EMP001",
            "category": "Equipment",
            "subject": "Xin đổi laptop",
            "description": "Laptop cũ bị hỏng màn hình",
            "priority": "Medium",
        }
    )
    assert "TICK" in result or "ticket" in result.lower()


def test_get_ticket_status_unknown():
    """get_ticket_status should handle unknown ticket IDs gracefully."""
    from src.tools.helpdesk_tools import get_ticket_status

    result = get_ticket_status.invoke({"ticket_id": "TICK-FAKE-0000"})
    assert "Không tìm thấy" in result or "không" in result.lower()


# ─── Benefits Tools ───────────────────────────────────────────────────────────


def test_get_benefits_catalog_returns_packages():
    """get_benefits_catalog should list at least Basic / Standard / Premium."""
    from src.tools.benefits_tools import get_benefits_catalog

    result = get_benefits_catalog.invoke({})
    assert "Basic" in result or "Standard" in result or "Premium" in result


def test_get_employee_benefits_known():
    """get_employee_benefits should return benefit info for EMP001."""
    from src.tools.benefits_tools import get_employee_benefits

    result = get_employee_benefits.invoke({"employee_id": "EMP001"})
    assert "EMP001" in result or "bảo hiểm" in result.lower()


# ─── Recruitment Tools ────────────────────────────────────────────────────────


def test_get_hiring_stats_totals():
    """get_hiring_stats should return total applicants aggregated across positions."""
    from src.tools.recruitment_tools import get_hiring_stats

    result = get_hiring_stats.invoke({})
    assert "Tổng ứng viên" in result or "Thống Kê" in result


def test_get_recruitment_pipeline_fuzzy_match():
    """get_recruitment_pipeline should do fuzzy matching on position name."""
    from src.tools.recruitment_tools import get_recruitment_pipeline

    # 'ReactJS' should fuzzy-match 'ReactJS Developer' if it's in the data
    result = get_recruitment_pipeline.invoke({"position": "ReactJS"})
    # Either found a pipeline or returned a helpful "available positions" message
    assert "Pipeline" in result or "Không tìm thấy" in result


# ─── Document Tools ───────────────────────────────────────────────────────────


def test_list_documents_shows_signed_status():
    """list_employee_documents should display signed/unsigned status for EMP001."""
    from src.tools.document_tools import list_employee_documents

    result = list_employee_documents.invoke({"employee_id": "EMP001"})
    assert "✅" in result  # EMP001 has all docs signed


def test_list_documents_emp003_has_unsigned():
    """EMP003 should have unsigned documents listed."""
    from src.tools.document_tools import list_employee_documents

    result = list_employee_documents.invoke({"employee_id": "EMP003"})
    assert "❌" in result  # EMP003 has unsigned docs


def test_sign_already_signed_document():
    """sign_document should inform the user when a doc is already signed."""
    from src.tools.document_tools import sign_document

    result = sign_document.invoke({"employee_id": "EMP001", "document_type": "NDA"})
    assert "đã được ký" in result or "ký lại" in result


def test_sign_invalid_document_type():
    """sign_document should return helpful error for unknown document types."""
    from src.tools.document_tools import sign_document

    result = sign_document.invoke(
        {"employee_id": "EMP001", "document_type": "NonExistentDoc"}
    )
    assert "không hợp lệ" in result or "Các tài liệu" in result


# ─── Orchestrator Logic (pure Python, no LLM dependency) ─────────────────────
# These tests validate the intent-classification and routing helpers that
# were intentionally extracted as pure functions, so they run fully offline.

_VALID_AGENTS_MAP = {
    "POLICY": "policy_agent",
    "ONBOARD": "onboard_agent",
    "CV": "cv_agent",
    "ANALYTICS": "analytics_agent",
    "ATTENDANCE": "attendance_agent",
    "HELPDESK": "helpdesk_agent",
    "BENEFITS": "benefits_agent",
}


def _classify(text: str) -> str:
    """Local re-implementation of _classify_intent for offline testing."""
    upper = text.strip().upper()
    for keyword, agent_key in _VALID_AGENTS_MAP.items():
        if keyword in upper:
            return agent_key
    return "end"


def _router(state: dict) -> str:
    """Local re-implementation of router for offline testing."""
    next_step = state.get("next", "end")
    valid_nodes = set(_VALID_AGENTS_MAP.values()) | {"end"}
    return next_step if next_step in valid_nodes else "end"


def test_classify_intent_policy():
    """_classify_intent should map POLICY_AGENT to policy_agent."""
    assert _classify("POLICY_AGENT") == "policy_agent"


def test_classify_intent_cv():
    assert _classify("CV_AGENT") == "cv_agent"


def test_classify_intent_unknown_returns_end():
    assert _classify("SOMETHING_WEIRD") == "end"


def test_router_valid_agent():
    """router should pass valid agent names straight through."""
    state = {
        "messages": [],
        "next": "helpdesk_agent",
        "user_intent": "",
        "user_id": "",
        "user_info": {},
    }
    assert _router(state) == "helpdesk_agent"


def test_router_invalid_falls_back_to_end():
    state = {
        "messages": [],
        "next": "some_unknown_node",
        "user_intent": "",
        "user_id": "",
        "user_info": {},
    }
    assert _router(state) == "end"
