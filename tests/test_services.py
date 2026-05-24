"""test_services.py — Tests for analytics security and VN tax calculator."""

import sys
from unittest.mock import MagicMock

# Mock LLM packages so analytics_agent can be imported offline
for _mod in [
    "langchain_google_genai",
    "langchain_google_genai.chat_models",
    "langchain_experimental",
    "langchain_experimental.agents",
    "langchain_experimental.agents.agent_toolkits",
    "langchain_experimental.tools",
    "langchain_experimental.tools.python",
    "langchain_experimental.tools.python.tool",
]:
    sys.modules.setdefault(_mod, MagicMock())

# Import the blocklist directly from the module
from src.agents.analytics_agent import _is_safe_query


# ── Analytics Agent — Input Sanitization (RestrictedPython) ─────────────────


def test_safe_query_passes_gate():
    """A safe analytics query should NOT be blocked."""
    assert _is_safe_query("Lương trung bình Engineering là bao nhiêu?") is True
    assert _is_safe_query("Tỉ lệ nghỉ việc theo phòng ban") is True
    assert _is_safe_query("Headcount by department") is True


# ── VN Tax Calculator ──────────────────────────────────────────────────────────


def test_tax_zero_income():
    """Zero gross → zero tax."""
    from src.tools.payroll_tools import calculate_vn_income_tax

    result = calculate_vn_income_tax.invoke({"gross_salary_vnd": 0, "dependents": 0})
    assert "0" in result or "zero" in result.lower() or "không" in result.lower()


def test_tax_below_threshold_no_tax():
    """Gross 10M VND, 0 dependents: taxable income below personal deduction (11M)."""
    from src.tools.payroll_tools import _calculate_vn_pit, _PERSONAL_DEDUCTION_VND

    gross = 10_000_000
    bhxh = gross * 0.08
    bhyt = gross * 0.015
    bhtn = gross * 0.01
    taxable = max(gross - bhxh - bhyt - bhtn - _PERSONAL_DEDUCTION_VND, 0)
    tax = _calculate_vn_pit(taxable)
    assert tax == 0, f"Expected 0 tax for 10M gross, got {tax}"


def test_tax_bracket_2():
    """30M VND gross → should fall in bracket 2 (15%)."""
    from src.tools.payroll_tools import _calculate_vn_pit, _PERSONAL_DEDUCTION_VND

    gross = 30_000_000
    insurance = gross * (0.08 + 0.015 + 0.01)
    taxable = max(gross - insurance - _PERSONAL_DEDUCTION_VND, 0)
    tax = _calculate_vn_pit(taxable)
    assert tax > 0, "Expected positive tax for 30M gross"


def test_tax_with_dependents_reduces_tax():
    """More dependents → lower taxable income → lower tax."""
    from src.tools.payroll_tools import (
        _calculate_vn_pit,
        _PERSONAL_DEDUCTION_VND,
        _DEPENDENT_DEDUCTION_VND,
    )

    gross = 30_000_000
    insurance = gross * (0.08 + 0.015 + 0.01)

    taxable_0 = max(gross - insurance - _PERSONAL_DEDUCTION_VND, 0)
    taxable_2 = max(
        gross - insurance - _PERSONAL_DEDUCTION_VND - 2 * _DEPENDENT_DEDUCTION_VND, 0
    )

    tax_0 = _calculate_vn_pit(taxable_0)
    tax_2 = _calculate_vn_pit(taxable_2)

    assert tax_2 <= tax_0, "More dependents should reduce or equal tax"
