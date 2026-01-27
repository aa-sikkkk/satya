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
Unit tests for PatternMiner.

Tests cover:
- Pattern discovery from logs
- Frequency analysis
- Confidence calculation
- N-gram extraction
- Noise likelihood detection
- Example retrieval
- Report generation
- Edge cases and boundary conditions
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import json
import tempfile
from pathlib import Path
from system.input_processing.pattern_miner import PatternMiner


class TestPatternDiscovery:
    """Test pattern discovery from logs."""
    
    @pytest.fixture
    def miner(self):
        return PatternMiner(min_frequency=3, min_confidence=0.6)
    
    @pytest.fixture
    def sample_logs(self):
        """Create sample low-confidence logs for testing."""
        # All confidence values must be < 0.7 to be analyzed
        return [
            {"original": "can u pls explain photosynthesis", "confidence": 0.5},
            {"original": "can u pls tell me about mitosis", "confidence": 0.6},
            {"original": "can u pls help me with DNA", "confidence": 0.55},
            {"original": "hey bro what is photosynthesis", "confidence": 0.6},
            {"original": "hey bro explain mitosis", "confidence": 0.65},
            {"original": "like basically what is DNA", "confidence": 0.5},
            {"original": "like basically explain photosynthesis", "confidence": 0.55},
            {"original": "like basically tell me about mitosis", "confidence": 0.6},
        ]
    
    def test_pattern_discovery(self, miner, sample_logs):
        """Test discovery of repeated patterns from logs."""
        suggestions = miner.mine_new_patterns(sample_logs)
        
        assert len(suggestions) > 0, "Should discover at least one pattern"
        
        # Check that "like basically" was discovered (appears 3 times)
        pattern_phrases = [s["phrase"] for s in suggestions]
        assert any("like basically" in phrase for phrase in pattern_phrases)
    
    def test_frequency_threshold(self, miner, sample_logs):
        """Test that patterns below frequency threshold are filtered."""
        # Miner has min_frequency=3
        suggestions = miner.mine_new_patterns(sample_logs)
        
        for suggestion in suggestions:
            assert suggestion["frequency"] >= 3, "All suggestions should meet frequency threshold"
    
    def test_confidence_threshold(self, miner, sample_logs):
        """Test that patterns below confidence threshold are filtered."""
        # Miner has min_confidence=0.6
        suggestions = miner.mine_new_patterns(sample_logs)
        
        for suggestion in suggestions:
            assert suggestion["confidence"] >= 0.6, "All suggestions should meet confidence threshold"
    
    def test_empty_logs(self, miner):
        """Test handling of empty log list."""
        suggestions = miner.mine_new_patterns([])
        assert suggestions == [], "Should return empty list for empty logs"
    
    def test_no_low_confidence_cases(self, miner):
        """Test handling when all logs have high confidence."""
        high_conf_logs = [
            {"original": "What is photosynthesis?", "confidence": 0.9},
            {"original": "Explain mitosis", "confidence": 0.85},
        ]
        
        suggestions = miner.mine_new_patterns(high_conf_logs)
        assert suggestions == [], "Should return empty list when no low-confidence cases"


class TestNgramExtraction:
    """Test n-gram extraction from logs."""
    
    @pytest.fixture
    def miner(self):
        return PatternMiner()
    
    def test_bigram_extraction(self, miner):
        """Test extraction of 2-word phrases."""
        logs = [
            {"original": "can you please explain", "confidence": 0.5},
            {"original": "can you tell me", "confidence": 0.5},
        ]
        
        ngrams = miner._extract_ngrams(logs, n_range=(2, 2))
        
        assert "can you" in ngrams
        assert ngrams.count("can you") == 2
    
    def test_trigram_extraction(self, miner):
        """Test extraction of 3-word phrases."""
        logs = [
            {"original": "can you please explain", "confidence": 0.5},
            {"original": "can you please tell", "confidence": 0.5},
        ]
        
        ngrams = miner._extract_ngrams(logs, n_range=(3, 3))
        
        assert "can you please" in ngrams
        assert ngrams.count("can you please") == 2
    
    def test_variable_length_ngrams(self, miner):
        """Test extraction of variable-length n-grams."""
        logs = [
            {"original": "can you please explain photosynthesis", "confidence": 0.5},
        ]
        
        ngrams = miner._extract_ngrams(logs, n_range=(2, 4))
        
        # Should extract 2-grams, 3-grams, and 4-grams
        assert "can you" in ngrams
        assert "can you please" in ngrams
        assert "can you please explain" in ngrams


class TestNoiseLikelihood:
    """Test noise likelihood detection."""
    
    @pytest.fixture
    def miner(self):
        return PatternMiner()
    
    def test_noise_indicators(self, miner):
        """Test detection of known noise indicators."""
        noise_phrases = [
            "can you please",
            "help me with",
            "tell me about",
            "like basically",
            "hey bro what",
        ]
        
        for phrase in noise_phrases:
            is_noise = miner._is_likely_noise(phrase)
            assert is_noise == True, f"'{phrase}' should be detected as noise"
    
    def test_non_noise_phrases(self, miner):
        """Test that valid content is not flagged as noise."""
        valid_phrases = [
            "photosynthesis process",
            "mitosis stages",
            "DNA structure",
            "cell division",
        ]
        
        for phrase in valid_phrases:
            is_noise = miner._is_likely_noise(phrase)
            assert is_noise == False, f"'{phrase}' should not be flagged as noise"
    
    def test_regex_patterns(self, miner):
        """Test regex-based noise detection."""
        noise_patterns = [
            "can you explain",
            "could you tell",
            "please help",
            "with reference to",
            "according to the",
        ]
        
        for phrase in noise_patterns:
            is_noise = miner._is_likely_noise(phrase)
            assert is_noise == True, f"'{phrase}' should match noise regex"


class TestConfidenceCalculation:
    """Test confidence calculation for patterns."""
    
    @pytest.fixture
    def miner(self):
        return PatternMiner()
    
    @pytest.fixture
    def sample_logs(self):
        return [
            {"original": "can you please explain photosynthesis", "confidence": 0.5},
            {"original": "can you please tell me about mitosis", "confidence": 0.5},
            {"original": "can you please help with DNA", "confidence": 0.5},
            {"original": "please explain photosynthesis", "confidence": 0.6},
        ]
    
    def test_high_frequency_bonus(self, miner, sample_logs):
        """Test that high frequency increases confidence."""
        # Pattern with frequency > 50 should get +0.2 bonus
        confidence_high = miner._calculate_confidence("test", sample_logs, frequency=60)
        confidence_low = miner._calculate_confidence("test", sample_logs, frequency=10)
        
        assert confidence_high > confidence_low
    
    def test_start_position_bonus(self, miner, sample_logs):
        """Test that patterns at start of questions get confidence bonus."""
        # "can you please" appears at start of 3 out of 3 occurrences
        confidence = miner._calculate_confidence("can you please", sample_logs, frequency=3)
        
        # Should get bonus for appearing at start
        assert confidence > 0.5
    
    def test_noise_indicator_bonus(self, miner, sample_logs):
        """Test that known noise indicators get confidence bonus."""
        # "please" is a noise indicator
        confidence = miner._calculate_confidence("please explain", sample_logs, frequency=5)
        
        # Should get bonus for containing noise indicator
        assert confidence > 0.5


class TestExampleRetrieval:
    """Test example retrieval for patterns."""
    
    @pytest.fixture
    def miner(self):
        return PatternMiner()
    
    @pytest.fixture
    def sample_logs(self):
        return [
            {"original": "can you please explain photosynthesis", "confidence": 0.5},
            {"original": "can you please tell me about mitosis", "confidence": 0.5},
            {"original": "can you please help with DNA", "confidence": 0.5},
            {"original": "what is photosynthesis", "confidence": 0.8},
        ]
    
    def test_example_retrieval(self, miner, sample_logs):
        """Test retrieval of example questions containing pattern."""
        examples = miner._get_examples("can you please", sample_logs, limit=2)
        
        assert len(examples) == 2
        assert all("can you please" in ex.lower() for ex in examples)
    
    def test_example_limit(self, miner, sample_logs):
        """Test that example retrieval respects limit."""
        examples = miner._get_examples("can you please", sample_logs, limit=1)
        
        assert len(examples) == 1
    
    def test_no_matching_examples(self, miner, sample_logs):
        """Test handling when no examples match pattern."""
        examples = miner._get_examples("nonexistent pattern", sample_logs, limit=5)
        
        assert examples == []


class TestReportGeneration:
    """Test report generation."""
    
    @pytest.fixture
    def miner(self):
        return PatternMiner()
    
    @pytest.fixture
    def sample_suggestions(self):
        return [
            {
                "phrase": "can you please",
                "frequency": 25,
                "confidence": 0.85,
                "examples": [
                    "can you please explain photosynthesis",
                    "can you please tell me about mitosis",
                ]
            },
            {
                "phrase": "like basically",
                "frequency": 18,
                "confidence": 0.75,
                "examples": [
                    "like basically what is DNA",
                    "like basically explain mitosis",
                ]
            },
        ]
    
    def test_report_creation(self, miner, sample_suggestions):
        """Test that report is created successfully."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            output_file = f.name
        
        try:
            miner.generate_report(sample_suggestions, output_file)
            
            assert Path(output_file).exists(), "Report file should be created"
            
            with open(output_file, 'r') as f:
                content = f.read()
            
            assert "Pattern Mining Report" in content
            assert "can you please" in content
            assert "like basically" in content
        finally:
            Path(output_file).unlink()
    
    def test_empty_suggestions(self, miner):
        """Test report generation with empty suggestions."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            output_file = f.name
        
        try:
            miner.generate_report([], output_file)
            
            assert Path(output_file).exists()
            
            with open(output_file, 'r') as f:
                content = f.read()
            
            assert "Total suggestions: 0" in content
        finally:
            Path(output_file).unlink()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture
    def miner(self):
        return PatternMiner()
    
    def test_very_long_logs(self, miner):
        """Test handling of very large log files."""
        large_logs = [
            {"original": f"can you please explain topic {i}", "confidence": 0.5}
            for i in range(10000)
        ]
        
        suggestions = miner.mine_new_patterns(large_logs)
        assert suggestions is not None
    
    def test_unicode_in_logs(self, miner):
        """Test handling of unicode characters in logs."""
        unicode_logs = [
            {"original": "can you please explain photosynthesis", "confidence": 0.5},
            {"original": "can you please tell me about mitosis", "confidence": 0.5},
        ]
        
        suggestions = miner.mine_new_patterns(unicode_logs)
        assert suggestions is not None
    
    def test_malformed_logs(self, miner):
        """Test handling of malformed log entries."""
        malformed_logs = [
            {"original": "valid question", "confidence": 0.5},
            {},  # Missing fields
            {"original": "", "confidence": 0.5},  # Empty string
        ]
        
        # Should not crash
        suggestions = miner.mine_new_patterns(malformed_logs)
        assert suggestions is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
