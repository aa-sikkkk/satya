import pytest

from system.rag.rag_retrieval_engine import RAGRetrievalEngine


@pytest.fixture(scope="session")
def rag_engine():
    try:
        return RAGRetrievalEngine()
    except Exception:
        pytest.skip("Chroma not available; skipping RAG tests.")


def test_rag_returns_dict(rag_engine):
    result = rag_engine.retrieve_relevant_content("computer", max_results=2)
    assert isinstance(result, dict)
    assert "query" in result


def test_rag_cache_hit(rag_engine):
    first = rag_engine.retrieve_relevant_content("binary number", max_results=1)
    second = rag_engine.retrieve_relevant_content("binary number", max_results=1)
    assert first == second

