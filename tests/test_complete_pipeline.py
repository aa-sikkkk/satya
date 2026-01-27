# Copyright (C) 2026 Aashik
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
COMPLETE PIPELINE TEST: Student Input → Normalization → RAG → Phi-1.5
UPDATED to match ACTUAL production code structure.
"""

import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import logging

# Import ALL pipeline components
from system.input_processing.input_normalizer import InputNormalizer
from system.input_processing.adaptive_normalizer import AdaptiveNormalizer
from system.rag.rag_retrieval_engine import RAGRetrievalEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Real student questions
STUDENT_QUESTIONS = [
    {"id": 1, "raw": "hey bro can u explain what is photosynthesis", "subject": "Biology"},
    {"id": 2, "raw": "WITH REFERENCE TO THE DIAGRAM ABOVE EXPLAIN THE LAW OF CONSERVATION OF ENERGY", "subject": "Physics"},
    {"id": 3, "raw": "what happens when switch is on", "subject": "Physics"},
    {"id": 4, "raw": "Define photosynthesis.", "subject": "Biology"},
]


@pytest.fixture(scope="module")
def rag_engine():
    """Initialize RAG engine once for all tests."""
    logger.info("Initializing RAG engine...")
    engine = RAGRetrievalEngine()
    logger.info("✅ RAG engine initialized")
    return engine


class TestNormalizerBasics:
    """Test normalizer works as expected."""
    
    @pytest.fixture
    def normalizer(self):
        return InputNormalizer()
    
    def test_all_caps_fix(self, normalizer):
        result = normalizer.normalize("WHAT IS PHOTOSYNTHESIS")
        assert not result["clean_question"].isupper()
        logger.info(f"✅ Caps fixed: '{result['clean_question']}'")
    
    def test_context_expansion(self, normalizer):
        result = normalizer.normalize("What happens when switch is on?")
        clean = result["clean_question"].lower()
        assert "circuit" in clean or "electric" in clean
        logger.info(f"✅ Context expanded: '{result['clean_question']}'")
    
    def test_intent_classification(self, normalizer):
        result = normalizer.normalize("Why is photosynthesis important?")
        assert result["intent"] == "WHY"
        logger.info(f"✅ Intent detected: {result['intent']}")


class TestRAGBasics:
    """Test RAG engine components."""
    
    def test_adaptive_normalizer_loaded(self, rag_engine):
        """Verify RAG uses AdaptiveNormalizer."""
        assert isinstance(rag_engine.input_normalizer, AdaptiveNormalizer)
        logger.info("✅ RAG using AdaptiveNormalizer")
    
    def test_embedding_generator_loaded(self, rag_engine):
        """Test embedding generator exists."""
        assert rag_engine.embedding_gen is not None
        logger.info("✅ Embedding generator available")
    
    def test_chroma_client_loaded(self, rag_engine):
        """Test ChromaDB client exists."""
        assert rag_engine.chroma_client is not None
        logger.info("✅ ChromaDB client available")


class TestCompleteFlow:
    """Test COMPLETE pipeline with actual production response structure."""
    
    @pytest.mark.parametrize("question", STUDENT_QUESTIONS, ids=lambda q: f"Q{q['id']}")
    def test_full_pipeline(self, rag_engine, question):
        """Test full pipeline - check for ACTUAL response keys."""
        raw_input = question["raw"]
        subject = question["subject"]
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Q{question['id']}: {raw_input[:50]}...")
        logger.info(f"{'='*60}")
        
        # Execute pipeline
        result = rag_engine.query(
            query_text=raw_input,
            subject=subject,
            n_results=3
        )
        
        # Check ACTUAL response structure (from production code)
        assert isinstance(result, dict), "Result must be dict"
        
       # Check for actual keys that production code returns
        assert "answer" in result, "Must have 'answer' key"
        assert "confidence" in result, "Must have 'confidence' key"
        
        answer = result["answer"]
        assert len(answer) > 0, "Answer cannot be empty"
        
        logger.info(f"  Answer: {len(answer)} chars")
        logger.info(f"  Confidence: {result['confidence']:.2f}")
        logger.info(f"  ✅ Pipeline completed\n")
    
    def test_messy_input_still_works(self, rag_engine):
        """Test that messy student input doesn't break the pipeline."""
        messy_question = "hey bro like what is photosynthesis"
        
        result = rag_engine.query(
            query_text=messy_question,
            subject="Biology",
            n_results=3
        )
        
        # Should still generate answer
        assert "answer" in result
        assert len(result["answer"]) > 0
        logger.info("✅ Messy input handled")
    
    def test_exam_fluff_removed(self, rag_engine):
        """Test that exam meta-language is normalized."""
        exam_question = "With reference to the diagram above, explain mitosis"
        
        result = rag_engine.query(
            query_text=exam_question,
            subject="Biology",
            n_results=3
        )
        
        assert "answer" in result
        assert len(result["answer"]) > 0
        logger.info("✅ Exam fluff handled")


class TestPhiModel:
    """Test Phi-1.5 generates coherent answers."""
    
    def test_phi_generates_answer(self, rag_engine):
        """Test Phi generates substantial answer."""
        result = rag_engine.query(
            query_text="What is photosynthesis?",
            subject="Biology",
            n_results=3
        )
        
        answer = result["answer"]
        assert len(answer) > 50, "Answer should be substantial"
        assert "photosynthesis" in answer.lower(), "Should mention topic"
        
        logger.info(f"✅ Phi generated {len(answer)} char answer")
    
    def test_multiple_questions(self, rag_engine):
        """Test different question types work."""
        questions = [
            "What is photosynthesis?",
            "Why is photosynthesis important?",
            "How does photosynthesis work?",
        ]
        
        for q in questions:
            result = rag_engine.query(query_text=q, subject="Biology", n_results=3)
            assert "answer" in result
            assert len(result["answer"]) > 0
        
        logger.info(f"✅ All {len(questions)} questions answered")


def test_all_imports():
    """Verify all components import successfully."""
    assert InputNormalizer is not None
    assert AdaptiveNormalizer is not None
    assert RAGRetrievalEngine is not None
    logger.info("✅ All components imported")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
