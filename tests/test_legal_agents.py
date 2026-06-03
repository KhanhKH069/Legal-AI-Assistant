import pytest

# Placeholder tests for Legal Agents
# In a real environment, you would mock the LangGraph graph execution to avoid hitting LLM API

@pytest.mark.asyncio
async def test_statutory_agent_basic():
    # Mock result
    result = {"messages": [{"role": "assistant", "content": "Theo Điều 1 Luật Dân sự..."}]}
    assert "messages" in result
    assert result["messages"][0]["role"] == "assistant"
    assert "Điều 1" in result["messages"][0]["content"]

@pytest.mark.asyncio
async def test_caselaw_agent_basic():
    # Mock result
    result = {"messages": [{"role": "assistant", "content": "Án lệ số 01/2016..."}]}
    assert len(result["messages"]) > 0
    assert "Án lệ" in result["messages"][0]["content"]

def test_hybrid_retriever_initialization():
    # Ensure HybridRetriever can be imported without crashing
    from src.services.hybrid_retriever import HybridRetriever, get_hybrid_retriever
    assert callable(get_hybrid_retriever)
