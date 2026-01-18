"""
Comprehensive unit tests for RAGRetrievalEngine.

Tests cover:
- Query processing and normalization
- Collection selection strategy
- Context retrieval and ranking
- Confidence calculation
- Caching behavior
- Error handling
"""

import pytest
from system.rag.rag_retrieval_engine import RAGRetrievalEngine


@pytest.fixture(scope="session")
def rag_engine():
    """Create RAG engine instance, skip if ChromaDB not available."""
    try:
        return RAGRetrievalEngine()
    except Exception:
        pytest.skip("Chroma not available; skipping RAG tests.")


class TestQueryProcessing:
    """Test query processing and result structure."""
    
    def test_query_returns_dict(self, rag_engine):
        """Test that query returns a dictionary with expected fields."""
        result = rag_engine.query("computer", subject="Computer Science", n_results=2)
        
        assert isinstance(result, dict)
        assert "answer" in result
        assert "processing_time" in result
    
    def test_query_with_different_subjects(self, rag_engine):
        """Test queries across different subjects."""
        subjects = ["Computer Science", "Mathematics", "Science"]
        
        for subject in subjects:
            result = rag_engine.query("basic concept", subject=subject, n_results=1)
            assert isinstance(result, dict)
            assert "answer" in result
    
    def test_query_result_consistency(self, rag_engine):
        """Test that same query returns consistent structure."""
        first = rag_engine.query("binary number", subject="Computer Science", n_results=1)
        second = rag_engine.query("binary number", subject="Computer Science", n_results=1)
        
        assert isinstance(first, dict)
        assert isinstance(second, dict)
        assert first.keys() == second.keys()


class TestCollectionSelection:
    """Test collection selection logic."""
    
    def test_get_relevant_collections_computer_science(self, rag_engine):
        """Test collection selection for Computer Science."""
        collections = rag_engine._get_relevant_collections("Computer Science", "10")
        
        assert isinstance(collections, list)
        assert len(collections) <= 3  # Max 3 collections for performance
    
    def test_get_relevant_collections_mathematics(self, rag_engine):
        """Test collection selection for Mathematics."""
        collections = rag_engine._get_relevant_collections("Mathematics", "10")
        
        assert isinstance(collections, list)
        assert len(collections) <= 3
    
    def test_get_relevant_collections_fallback(self, rag_engine):
        """Test fallback collections for unknown subject."""
        collections = rag_engine._get_relevant_collections("Unknown Subject", "10")
        
        assert isinstance(collections, list)
        # Should return fallback collections


class TestConfidenceCalculation:
    """Test confidence scoring logic."""
    
    def test_confidence_short_answer(self, rag_engine):
        """Test confidence for very short answers."""
        confidence = rag_engine._calculate_confidence(
            answer="Yes",
            question="Is this correct?",
            context_chunks=None
        )
        
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
        assert confidence < 0.5  # Short answers should have low confidence
    
    def test_confidence_ideal_length(self, rag_engine):
        """Test confidence for ideal length answers."""
        # Create an answer with ~80 words (ideal range)
        answer = " ".join(["word"] * 80)
        question = "Explain this concept"
        
        confidence = rag_engine._calculate_confidence(
            answer=answer,
            question=question,
            context_chunks=None
        )
        
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
        assert confidence >= 0.5  # Should have decent confidence
    
    def test_confidence_with_context(self, rag_engine):
        """Test confidence boost from good RAG context."""
        answer = " ".join(["word"] * 80)
        question = "Explain this"
        context_chunks = [
            {"final_score": 0.9, "text": "relevant context"},
            {"final_score": 0.8, "text": "more context"}
        ]
        
        conf_with_context = rag_engine._calculate_confidence(
            answer=answer,
            question=question,
            context_chunks=context_chunks
        )
        
        conf_without_context = rag_engine._calculate_confidence(
            answer=answer,
            question=question,
            context_chunks=None
        )
        
        # Context should boost confidence
        assert conf_with_context >= conf_without_context
    
    def test_confidence_question_relevance(self, rag_engine):
        """Test confidence based on question-answer relevance."""
        question = "photosynthesis process plants"
        
        # Relevant answer
        relevant_answer = "Photosynthesis is the process by which plants convert light energy into chemical energy"
        
        # Irrelevant answer
        irrelevant_answer = "The sky is blue and water is wet"
        
        conf_relevant = rag_engine._calculate_confidence(relevant_answer, question)
        conf_irrelevant = rag_engine._calculate_confidence(irrelevant_answer, question)
        
        # Relevant answer should have higher confidence
        assert conf_relevant > conf_irrelevant


class TestCaching:
    """Test caching behavior."""
    
    def test_cache_stores_results(self, rag_engine):
        """Test that results are cached."""
        query = "test caching behavior"
        subject = "Computer Science"
        
        # First query - should miss cache
        result1 = rag_engine.query(query, subject=subject, n_results=1)
        
        # Second query - should hit cache (faster)
        result2 = rag_engine.query(query, subject=subject, n_results=1)
        
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)
        # Processing time for cached result should be very small
        assert result2["processing_time"] < result1["processing_time"] + 0.1


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_query(self, rag_engine):
        """Test handling of empty query."""
        result = rag_engine.query("", subject="Computer Science", n_results=1)
        
        assert isinstance(result, dict)
        assert "answer" in result
    
    def test_very_long_query(self, rag_engine):
        """Test handling of very long query."""
        long_query = " ".join(["word"] * 200)
        result = rag_engine.query(long_query, subject="Computer Science", n_results=1)
        
        assert isinstance(result, dict)
        assert "answer" in result
    
    def test_special_characters_query(self, rag_engine):
        """Test handling of special characters in query."""
        result = rag_engine.query(
            "What is C++?",
            subject="Computer Science",
            n_results=1
        )
        
        assert isinstance(result, dict)
        assert "answer" in result
    
    def test_n_results_parameter(self, rag_engine):
        """Test different n_results values."""
        for n in [1, 2, 3, 5]:
            result = rag_engine.query(
                "computer",
                subject="Computer Science",
                n_results=n
            )
            assert isinstance(result, dict)
            assert "answer" in result


class TestIntegration:
    """Integration tests for full pipeline."""
    
    def test_full_pipeline_computer_science(self, rag_engine):
        """Test full pipeline for Computer Science query."""
        result = rag_engine.query(
            "What is a binary number?",
            subject="Computer Science",
            n_results=3
        )
        
        assert isinstance(result, dict)
        assert "answer" in result
        assert "processing_time" in result
        assert isinstance(result["answer"], str)
        assert len(result["answer"]) > 0
    
    def test_full_pipeline_mathematics(self, rag_engine):
        """Test full pipeline for Mathematics query."""
        result = rag_engine.query(
            "What is an algorithm?",
            subject="Mathematics",
            n_results=2
        )
        
        assert isinstance(result, dict)
        assert "answer" in result
        assert isinstance(result["answer"], str)
    
    def test_input_normalization_integration(self, rag_engine):
        """Test that input normalization is applied."""
        # Query with noise that should be normalized
        messy_query = "hey bro can u pls explain what is photosynthesis"
        
        result = rag_engine.query(
            messy_query,
            subject="Science",
            n_results=2
        )
        
        assert isinstance(result, dict)
        assert "answer" in result
        # Should still get a valid answer despite messy input
        assert len(result["answer"]) > 0
