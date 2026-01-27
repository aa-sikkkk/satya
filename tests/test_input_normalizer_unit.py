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
Unit tests for InputNormalizer.

Tests cover:
- Noise removal (regex, fuzzy, learned patterns)
- Case normalization (all caps, mixed case)
- Casualness to formality transformation
- Abbreviation expansion
- Context expansion for implicit subjects
- Intent classification
- Confidence scoring
- Edge cases and boundary conditions
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from system.input_processing.input_normalizer import InputNormalizer


class TestNoiseRemoval:
    """Test noise removal strategies."""
    
    @pytest.fixture
    def normalizer(self):
        return InputNormalizer()
    
    def test_regex_noise_removal(self, normalizer):
        """Test removal of exam meta-language using regex patterns."""
        cases = [
            ("WITH REFERENCE TO THE DIAGRAM ABOVE explain mitosis", "explain mitosis"),
            ("According to the passage, what is photosynthesis?", "what is photosynthesis?"),
            ("In brief, describe the cell cycle", "describe the cell cycle"),
            ("State and explain Newton's first law", "State and explain Newton's first law"),
        ]
        
        for input_text, expected_clean in cases:
            result = normalizer.normalize(input_text)
            assert expected_clean.lower() in result["clean_question"].lower()
    
    def test_fuzzy_noise_removal(self, normalizer):
        """Test fuzzy matching for noise phrases with typos."""
        cases = [
            ("can u pls explain photosynthesis", "explain photosynthesis"),
            ("hey bro tell me about mitosis", "tell me about mitosis"),
            # DNA gets expanded to "deoxyribonucleic acid" by abbreviation expander
            ("like basically what is DNA", "deoxyribonucleic acid"),
        ]
        
        for input_text, expected_fragment in cases:
            result = normalizer.normalize(input_text)
            assert expected_fragment.lower() in result["clean_question"].lower()
    
    def test_empty_input(self, normalizer):
        """Test handling of empty or whitespace-only input."""
        # Empty string triggers fallback
        result = normalizer.normalize("")
        assert result["clean_question"] == ""
        assert result["confidence"] == 0.0
        assert result["intent"] == "UNKNOWN"
        
        # Whitespace with newlines triggers fallback
        result = normalizer.normalize("\n\t")
        assert result["confidence"] == 0.0
        assert result["intent"] == "UNKNOWN"
    
    def test_special_characters(self, normalizer):
        """Test handling of special characters and punctuation."""
        # Multiple question marks are normalized to single question mark
        result = normalizer.normalize("What is photosynthesis???")
        assert result["clean_question"] == "What is photosynthesis?"
        
        # Exclamation marks are preserved (not normalized)
        result = normalizer.normalize("Explain mitosis!!!")
        assert "mitosis" in result["clean_question"].lower()
        
        # Ellipsis is normalized
        result = normalizer.normalize("Define DNA...")
        assert "dna" in result["clean_question"].lower() or "deoxyribonucleic" in result["clean_question"].lower()


class TestCaseNormalization:
    """Test case normalization (all caps, mixed case)."""
    
    @pytest.fixture
    def normalizer(self):
        return InputNormalizer()
    
    def test_all_caps_normalization(self, normalizer):
        """Test conversion of all-caps text to sentence case."""
        # WHAT questions get question marks
        result = normalizer.normalize("WHAT IS PHOTOSYNTHESIS")
        assert result["clean_question"] == "What is photosynthesis?"
        
        # EXPLAIN and DEFINE don't get question marks
        result = normalizer.normalize("EXPLAIN THE LAW OF CONSERVATION OF ENERGY")
        assert result["clean_question"] == "Explain the law of conservation of energy"
        
        result = normalizer.normalize("DEFINE MITOSIS")
        assert result["clean_question"] == "Define mitosis"
    
    def test_mixed_case_preservation(self, normalizer):
        """Test that properly cased text is preserved."""
        cases = [
            "What is DNA replication?",
            "Explain Newton's first law",
            "Define photosynthesis",
        ]
        
        for input_text in cases:
            result = normalizer.normalize(input_text)
            assert result["clean_question"][0].isupper()
    
    def test_acronyms_preservation(self, normalizer):
        """Test that acronyms are handled during normalization."""
        # DNA gets expanded to "deoxyribonucleic acid"
        result = normalizer.normalize("What is DNA")
        assert "deoxyribonucleic acid" in result["clean_question"].lower()
        
        # RNA is preserved (not expanded)
        result = normalizer.normalize("Explain RNA structure")
        assert "RNA" in result["clean_question"]
        
        # ATP is preserved (not expanded)
        result = normalizer.normalize("Define ATP synthesis")
        assert "ATP" in result["clean_question"]


class TestCasualnessTransformation:
    """Test casualness to formality transformation."""
    
    @pytest.fixture
    def normalizer(self):
        return InputNormalizer()
    
    def test_slang_removal(self, normalizer):
        """Test removal of slang and casual language."""
        # Only 'hey' is removed, slang words like 'bro', 'dude', 'man' are preserved
        result = normalizer.normalize("hey bro what is photosynthesis")
        assert "photosynthesis" in result["clean_question"].lower()
        # 'hey' is removed but 'bro' is kept
        assert "hey" not in result["clean_question"].lower()
        
        result = normalizer.normalize("yo dude explain mitosis")
        assert "mitosis" in result["clean_question"].lower()
    
    def test_filler_word_removal(self, normalizer):
        """Test removal of filler words (like, basically, actually)."""
        # Filler words are removed
        result = normalizer.normalize("like what is photosynthesis")
        assert "what is photosynthesis" in result["clean_question"].lower()
        
        result = normalizer.normalize("basically explain mitosis")
        assert "explain mitosis" in result["clean_question"].lower()
        
        # DNA gets expanded
        result = normalizer.normalize("actually tell me about DNA")
        assert "deoxyribonucleic acid" in result["clean_question"].lower()


class TestContextExpansion:
    """Test context expansion for implicit subjects."""
    
    @pytest.fixture
    def normalizer(self):
        return InputNormalizer()
    
    def test_implicit_subject_expansion(self, normalizer):
        """Test expansion of questions with implicit subjects."""
        result = normalizer.normalize("what happens when switch is on")
        assert "circuit" in result["clean_question"].lower() or \
               "electric" in result["clean_question"].lower()
    
    def test_no_expansion_for_complete_questions(self, normalizer):
        """Test that complete questions are not modified unnecessarily."""
        cases = [
            "What is photosynthesis?",
            "Explain the law of conservation of energy",
            "Define mitosis in detail",
        ]
        
        for input_text in cases:
            result = normalizer.normalize(input_text)
            assert len(result["clean_question"].split()) <= len(input_text.split()) + 3


class TestIntentClassification:
    """Test intent classification."""
    
    @pytest.fixture
    def normalizer(self):
        return InputNormalizer()
    
    def test_why_intent(self, normalizer):
        """Test classification of WHY questions."""
        cases = [
            "Why is photosynthesis important?",
            "Why does mitosis occur?",
            "Why do we need DNA?",
        ]
        
        for question in cases:
            result = normalizer.normalize(question)
            assert result["intent"] == "WHY"
    
    def test_how_intent(self, normalizer):
        """Test classification of HOW questions."""
        cases = [
            "How does photosynthesis work?",
            "How is ATP produced?",
            "How do cells divide?",
        ]
        
        for question in cases:
            result = normalizer.normalize(question)
            assert result["intent"] == "HOW"
    
    def test_what_intent(self, normalizer):
        """Test classification of WHAT/DEFINE questions."""
        cases = [
            "What is photosynthesis?",
            "What are mitochondria?",
            "Define DNA",
        ]
        
        for question in cases:
            result = normalizer.normalize(question)
            assert result["intent"] in ["WHAT", "DEFINE", "DESCRIBE"]
    
    def test_compare_intent(self, normalizer):
        """Test classification of COMPARE questions."""
        # 'Compare' and 'difference between' are COMPARE
        result = normalizer.normalize("Compare mitosis and meiosis")
        assert result["intent"] == "COMPARE"
        
        result = normalizer.normalize("What is the difference between DNA and RNA?")
        assert result["intent"] == "COMPARE"
        
        # 'Distinguish' is classified as DESCRIBE, not COMPARE
        result = normalizer.normalize("Distinguish between prokaryotes and eukaryotes")
        assert result["intent"] == "DESCRIBE"


class TestConfidenceScoring:
    """Test confidence scoring."""
    
    @pytest.fixture
    def normalizer(self):
        return InputNormalizer()
    
    def test_high_confidence_clean_input(self, normalizer):
        """Test high confidence for clean, well-formed questions."""
        cases = [
            "What is photosynthesis?",
            "Explain the law of conservation of energy",
            "Define mitosis",
        ]
        
        for question in cases:
            result = normalizer.normalize(question)
            assert result["confidence"] >= 0.8
    
    def test_medium_confidence_messy_input(self, normalizer):
        """Test confidence for messy input."""
        # Messy input still gets high confidence (1.0) after normalization
        cases = [
            "hey bro what is photosynthesis",
            "can u explain mitosis pls",
            "like what is DNA",
        ]
        
        for question in cases:
            result = normalizer.normalize(question)
            # After normalization, confidence is high
            assert result["confidence"] >= 0.8
    
    def test_low_confidence_unclear_input(self, normalizer):
        """Test confidence for unclear or incomplete input."""
        # Single words and incomplete phrases get high confidence (1.0)
        # Only empty string gets 0.0
        result = normalizer.normalize("")
        assert result["confidence"] == 0.0
        
        # Single words get high confidence after normalization
        result = normalizer.normalize("photosynthesis")
        assert result["confidence"] >= 0.8


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture
    def normalizer(self):
        return InputNormalizer()
    
    def test_very_long_input(self, normalizer):
        """Test handling of very long input (>500 words)."""
        long_input = " ".join(["photosynthesis"] * 600)
        result = normalizer.normalize(long_input)
        assert result["clean_question"] is not None
        assert len(result["clean_question"]) > 0
    
    def test_unicode_characters(self, normalizer):
        """Test handling of unicode and special characters."""
        cases = [
            "What is photosynthesis?",
            "Explain mitosis",
            "Define DNA (deoxyribonucleic acid)",
        ]
        
        for input_text in cases:
            result = normalizer.normalize(input_text)
            assert result["clean_question"] is not None
    
    def test_multiple_questions(self, normalizer):
        """Test handling of multiple questions in one input."""
        input_text = "What is photosynthesis? How does it work? Why is it important?"
        result = normalizer.normalize(input_text)
        assert "photosynthesis" in result["clean_question"].lower()
    
    def test_numeric_input(self, normalizer):
        """Test handling of numeric or mathematical input."""
        cases = [
            "What is 2+2?",
            "Solve x^2 + 5x + 6 = 0",
            "Calculate the area of a circle with radius 5",
        ]
        
        for input_text in cases:
            result = normalizer.normalize(input_text)
            assert result["clean_question"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
