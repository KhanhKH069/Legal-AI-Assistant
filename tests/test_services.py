"""test_services.py — Tests for Legal AI services: hybrid retriever, config."""

import os
os.environ.setdefault("OFFLINE_MODE", "true")
os.environ.setdefault("GOOGLE_API_KEY", "test-key-placeholder")


# ── Config ────────────────────────────────────────────────────────────────────


def test_config_loads():
    from src.core.config import config
    assert config.model_name is not None
    assert isinstance(config.max_tokens, int)
    assert config.max_tokens > 0


def test_config_offline_mode_readable():
    """Config should expose enable_offline_mode as a bool attribute."""
    from src.core.config import config
    # Value depends on env - just check the attribute exists and is a bool
    assert isinstance(config.enable_offline_mode, bool)


# ── HybridRetriever ───────────────────────────────────────────────────────────


def test_hybrid_retriever_importable():
    from src.services.hybrid_retriever import HybridRetriever, get_hybrid_retriever
    assert callable(get_hybrid_retriever)
    assert HybridRetriever is not None


def test_hybrid_retriever_instantiation():
    """Retriever should instantiate without crashing even with empty DB."""
    from src.services.hybrid_retriever import HybridRetriever
    # Use a temp directory so no real DB needed
    import tempfile
    # ignore_cleanup_errors=True prevents Windows file-lock error on chroma.sqlite3
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        r = HybridRetriever(collection_name="test_col", persist_directory=tmpdir)
        assert r.collection_name == "test_col"


# ── Legal Tools ───────────────────────────────────────────────────────────────


def test_legal_tools_importable():
    from src.tools.legal_tools import search_statutory_law, search_case_law, search_legal_qa
    from langchain_core.tools import BaseTool
    # LangChain @tool creates StructuredTool (a BaseTool), not a plain callable
    assert isinstance(search_statutory_law, BaseTool)
    assert isinstance(search_case_law, BaseTool)
    assert isinstance(search_legal_qa, BaseTool)


# ── Guardrail ─────────────────────────────────────────────────────────────────


def test_guardrail_importable():
    from src.services.guardrail import guardrail_node
    assert callable(guardrail_node)


# ── Metrics ───────────────────────────────────────────────────────────────────


def test_metrics_collector():
    from src.services.metrics import get_metrics_collector
    collector = get_metrics_collector()
    assert collector is not None
    summary = collector.get_summary()
    assert isinstance(summary, dict)
    assert "total_requests" in summary
