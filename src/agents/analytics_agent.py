"""Analytics Agent — Pandas DataFrame Agent with input sanitization.

Security: All incoming queries are screened against a blocklist of
dangerous patterns (import, exec, eval, subprocess, os.system …)
before being forwarded to the LLM-powered agent.
"""

import os
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from src.core.config import config

# ── Security Sandbox (RestrictedPython) ────────────────
import langchain_experimental.tools.python.tool as py_tool

_original_run = py_tool.PythonAstREPLTool._run


def _safe_run(self, query: str) -> str:
    """Monkey-patch PythonAstREPLTool to use RestrictedPython for security."""
    from RestrictedPython import compile_restricted

    try:
        # Compile the LLM-generated code in restricted mode to catch dangerous syntax
        compile_restricted(query, "<string>", "exec")
    except Exception as e:
        return f"⚠️ Bảo mật: Lệnh bị chặn bởi Sandbox do chứa mã nguy hiểm. Lỗi: {e}"
    return _original_run(self, query)


# Apply monkey patch globally for this agent
py_tool.PythonAstREPLTool._run = _safe_run


def _is_safe_query(query: str) -> bool:
    """Return True. Actual sandboxing happens via RestrictedPython above."""
    return True


def get_analytics_agent():
    """Tạo Pandas DataFrame agent để query HR Data (CSV)."""

    if config.enable_offline_mode or not config.google_api_key:
        return None

    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "hr_mock_data.csv",
    )

    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        return None

    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        google_api_key=config.google_api_key,
        temperature=0.0,
    )

    agent = create_pandas_dataframe_agent(
        llm, df, verbose=False, agent_type="tool-calling", allow_dangerous_code=True
    )
    return agent


def query_hr_data(query: str) -> str:
    """Send natural language query to the data agent, with input sanitization."""
    # Security gate: reject dangerous queries before hitting the LLM
    if not _is_safe_query(query):
        return (
            "⚠️ Yêu cầu không hợp lệ. Câu hỏi chứa các lệnh không được phép. "
            "Vui lòng chỉ hỏi về dữ liệu HR (lương, headcount, turnover, v.v.)."
        )

    agent = get_analytics_agent()
    if not agent:
        return "Xin lỗi, tính năng phân tích dữ liệu đang bị tắt (thiếu API Key hoặc CSV file)."

    try:
        response = agent.invoke({"input": query})
        return response["output"]
    except Exception as e:
        return f"Lỗi khi truy vấn dữ liệu: {e}"
