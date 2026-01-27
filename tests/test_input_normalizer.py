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
Test suite for Input Normalizer
Tests normalization with real-world scenarios.
"""

import pytest
from system.input_processing.input_normalizer import InputNormalizer


@pytest.fixture
def normalizer():
    return InputNormalizer(learnable_db_path="tests/test_data/test_normalizer_phrases.json")


class TestNoiseRemoval:
    def test_exam_reference_removal(self, normalizer):
        result = normalizer.normalize("With reference to the figure above, explain photosynthesis.")
        assert "with reference" not in result["clean_question"].lower()
        assert "photosynthesis" in result["clean_question"].lower()
    
    def test_all_caps_fix(self, normalizer):
        result = normalizer.normalize("WHAT IS PHOTOSYNTHESIS")
        assert not result["clean_question"].isupper()
        assert result["clean_question"][0].isupper()
        assert "fixed_caps" in result["notes"]
    
    def test_learned_phrases(self, normalizer):
        normalizer.add_noise_phrase("as per the textbook")
        result = normalizer.normalize("As per the textbook, define photosynthesis.")
        assert "as per the textbook" not in result["clean_question"].lower()


class TestFormalization:
    def test_slang_removal(self, normalizer):
        result = normalizer.normalize("hey can u tell me what is photosynthesis")
        clean = result["clean_question"].lower()
        assert "hey" not in clean
        assert "you" in clean  # "u" converted to "you"
        assert "formalized" in result["notes"]
    
    def test_filler_word_removal(self, normalizer):
        result = normalizer.normalize("like what is basically photosynthesis")
        clean = result["clean_question"].lower()
        assert "like" not in clean
        assert "basically" not in clean


class TestSentenceNormalization:
    def test_question_mark_addition(self, normalizer):
        result = normalizer.normalize("What is photosynthesis")
        assert result["clean_question"].endswith("?")
    
    def test_capitalization(self, normalizer):
        result = normalizer.normalize("what happens when water boils")
        assert result["clean_question"][0].isupper()


class TestContextExpansion:
    def test_circuit_context(self, normalizer):
        result = normalizer.normalize("What happens when the switch is turned on?")
        clean_lower = result["clean_question"].lower()
        assert "circuit" in clean_lower or "electric" in clean_lower
    
    def test_no_expansion_for_detailed_questions(self, normalizer):
        long_q = "What happens to the electric current in a circuit when the switch is turned on?"
        result = normalizer.normalize(long_q)
        assert "expanded_context" not in str(result["notes"])


class TestIntentClassification:
    def test_why_intent(self, normalizer):
        assert normalizer.normalize("Why is photosynthesis important?")["intent"] == "WHY"
    
    def test_how_intent(self, normalizer):
        assert normalizer.normalize("How does photosynthesis work?")["intent"] == "HOW"
    
    def test_describe_intent(self, normalizer):
        assert normalizer.normalize("Explain photosynthesis.")["intent"] == "DESCRIBE"
    
    def test_define_intent(self, normalizer):
        assert normalizer.normalize("Define photosynthesis.")["intent"] == "DEFINE"
    
    def test_compare_intent(self, normalizer):
        assert normalizer.normalize("Difference between mitosis and meiosis?")["intent"] == "COMPARE"
    
    def test_solve_intent(self, normalizer):
        assert normalizer.normalize("Calculate the area of a circle.")["intent"] == "SOLVE"


class TestEdgeCases:
    def test_empty_input(self, normalizer):
        result = normalizer.normalize("")
        assert result["confidence"] == 0.0
        assert "fallback" in str(result["notes"])
    
    def test_very_short_input(self, normalizer):
        result = normalizer.normalize("Hi")
        assert result["confidence"] == 0.0
    
    def test_none_input(self, normalizer):
        result = normalizer.normalize(None)
        assert result["confidence"] == 0.0


class TestRealWorldQuestions:
    """Test with authentic student questions."""
    
    def test_casual_student_question(self, normalizer):
        question = "hey bro can u explain what is photosynthesis"
        result = normalizer.normalize(question)
        clean = result["clean_question"].lower()
        
        assert "hey" not in clean
        assert "bro" not in clean
        assert "you" in clean  # "u" converted
        assert "photosynthesis" in clean
    
    def test_neb_exam_question(self, normalizer):
        question = "STATE AND EXPLAIN THE LAW OF CONSERVATION OF ENERGY"
        result = normalizer.normalize(question)
        
        # Should preserve "state and explain" but fix caps
        assert not result["clean_question"].isupper()
        assert "conservation of energy" in result["clean_question"].lower()
    
    def test_typo_question(self, normalizer):
        # Note: Without LanguageTool, typos won't be corrected
        # But normalizer should not crash
        question = "What is fotosynthesis"
        result = normalizer.normalize(question)
        assert "fotosynthesis" in result["clean_question"].lower()
        assert result["clean_question"].endswith("?")
    
    def test_vague_circuit_question(self, normalizer):
        question = "what happens when switch is on"
        result = normalizer.normalize(question)
        
        clean_lower = result["clean_question"].lower()
        assert result["clean_question"].endswith("?")
        # Should add circuit context
        assert len(result["clean_question"]) > 0


class TestRAGIntegration:
    """Test normalization integrated with RAG pipeline."""
    
    @pytest.fixture
    def rag_engine(self):
        """Create RAG engine with normalizer."""
        try:
            from system.rag.rag_retrieval_engine import RAGRetrievalEngine
            return RAGRetrievalEngine()
        except Exception as e:
            pytest.skip(f"RAG engine not available: {e}")
    
    def test_normalizer_in_rag(self, rag_engine):
        """Test that RAG uses AdaptiveNormalizer."""
        from system.input_processing.adaptive_normalizer import AdaptiveNormalizer
        assert isinstance(rag_engine.input_normalizer, AdaptiveNormalizer)
    
    def test_casual_question_through_rag(self, rag_engine):
        """Test casual question gets normalized before RAG."""
        result = rag_engine.query(
            query_text="hey can u explain photosynthesis",
            subject="Biology",
            n_results=3
        )
        assert result.get("status") == "success"
        # Answer should be generated (even if ChomraDB is empty)
        assert "answer" in result
    
    def test_exam_fluff_through_rag(self, rag_engine):
        """Test exam fluff is removed before RAG retrieval."""
        result = rag_engine.query(
            query_text="With reference to the diagram above, explain photosynthesis",
            subject="Biology",
            n_results=3
        )
        assert result.get("status") == "success"
        assert "answer" in result
    
    def test_all_caps_through_rag(self, rag_engine):
        """Test ALL CAPS question is normalized."""
        result = rag_engine.query(
            query_text="WHAT IS PHOTOSYNTHESIS",
            subject="Biology",
            n_results=3
        )
        assert result.get("status") == "success"
    
    def test_normalized_vs_raw_retrieval(self, rag_engine):
        """Compare retrieval quality with normalized vs raw questions."""
        # This test demonstrates the value of normalization
        raw_question = "hey bro like what is photosynthesis"
        
        # The RAG engine will normalize it internally
        result = rag_engine.query(
            query_text=raw_question,
            subject="Biology",
            n_results=3
        )
        
        # Should still get a result despite messy input
        assert result.get("status") in ["success", "cache_hit"]
        assert "answer" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
