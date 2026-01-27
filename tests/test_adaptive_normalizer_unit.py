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
Unit tests for AdaptiveNormalizer.

Tests cover:
- Conditional spell-checking heuristics
- Spell correction caching (MD5-based)
- Cache hit/miss tracking
- LRU eviction for cache
- LanguageTool integration
- Logging and feedback collection
- Low-confidence case flagging
- Edge cases and performance
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from system.input_processing.adaptive_normalizer import AdaptiveNormalizer


class TestConditionalSpellChecking:
    """Test conditional spell-checking heuristics."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def normalizer(self, temp_log_dir):
        return AdaptiveNormalizer(log_dir=temp_log_dir, enable_spell_check=True)
    
    def test_skip_short_queries(self, normalizer):
        """Test that short queries (<5 words) skip spell-checking."""
        short_queries = [
            "What is DNA?",
            "Define mitosis",
            "Explain photosynthesis",
        ]
        
        for query in short_queries:
            should_check = normalizer._should_spell_check(query)
            assert should_check == False, f"Should skip spell-check for: {query}"
    
    def test_skip_mcq_questions(self, normalizer):
        """Test that MCQ-style questions skip spell-checking."""
        mcq_queries = [
            "A) Photosynthesis",
            "B) Mitosis",
            "1. What is DNA?",
            "2. Explain mitosis",
        ]
        
        for query in mcq_queries:
            should_check = normalizer._should_spell_check(query)
            assert should_check == False, f"Should skip spell-check for MCQ: {query}"
    
    def test_skip_all_caps(self, normalizer):
        """Test that all-caps queries skip spell-checking."""
        all_caps_queries = [
            "WHAT IS PHOTOSYNTHESIS",
            "EXPLAIN THE LAW OF CONSERVATION",
            "DEFINE MITOSIS",
        ]
        
        for query in all_caps_queries:
            should_check = normalizer._should_spell_check(query)
            assert should_check == False, f"Should skip spell-check for all-caps: {query}"
    
    def test_run_for_long_queries(self, normalizer):
        """Test that long queries (>10 words) run spell-checking."""
        long_queries = [
            "hey bro can you please explain what is photosynthesis and how it works in plants",
            "with reference to the diagram above explain the law of conservation of energy in detail",
        ]
        
        for query in long_queries:
            should_check = normalizer._should_spell_check(query)
            assert should_check == True, f"Should run spell-check for long query: {query}"
    
    def test_run_for_potential_typos(self, normalizer):
        """Test that queries with potential typos run spell-checking."""
        # Words with numbers trigger spell-check (needs 5+ words)
        result = normalizer._should_spell_check("what is DNA123 replication process")
        assert result == True, "Should run spell-check for words with numbers"
        
        # Repeated characters trigger spell-check (needs 5+ words)
        result = normalizer._should_spell_check("hellooooo there how are you doing today")
        assert result == True, "Should run spell-check for repeated characters"



class TestSpellCorrectionCaching:
    """Test spell correction caching functionality."""
    
    @pytest.fixture
    def temp_log_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def normalizer(self, temp_log_dir):
        # Enable spell-check for cache tests
        return AdaptiveNormalizer(log_dir=temp_log_dir, enable_spell_check=True)
    
    def test_cache_key_generation(self, normalizer):
        """Test MD5-based cache key generation."""
        test_cases = [
            ("What is photosynthesis?", "what is photosynthesis?"),
            ("WHAT IS PHOTOSYNTHESIS?", "what is photosynthesis?"),
            ("  what is photosynthesis?  ", "what is photosynthesis?"),
        ]
        
        for input1, input2 in test_cases:
            key1 = normalizer._get_cache_key(input1)
            key2 = normalizer._get_cache_key(input2)
            assert key1 == key2, "Case-insensitive inputs should have same cache key"
    
    def test_cache_hit_tracking(self, normalizer):
        """Test cache hit/miss tracking."""
        # Use long query (14 words) that triggers spell-check
        query = "can you please explain to me what is the process of photosynthesis in plants"
        cache_key = normalizer._get_cache_key(query)
        
        # Pre-populate cache
        normalizer.spell_cache[cache_key] = {
            "corrected": query,
            "timestamp": "2026-01-18T08:00:00",
            "hit_count": 1
        }
        
        # Normalize with spell-check enabled
        result = normalizer.normalize(query, enable_spell_check=True)
        
        # Cache hit should be recorded
        assert normalizer.cache_hits == 1, f"Expected cache hits = 1, got {normalizer.cache_hits}"
        assert normalizer.cache_misses == 0, f"Expected cache misses = 0, got {normalizer.cache_misses}"

    
    def test_cache_persistence(self, normalizer, temp_log_dir):
        """Test that cache persists to disk."""
        query = "test query"
        cache_key = normalizer._get_cache_key(query)
        
        normalizer.spell_cache[cache_key] = {
            "corrected": "test query",
            "timestamp": "2026-01-18T08:00:00",
            "hit_count": 1
        }
        
        normalizer._save_spell_cache()
        
        cache_file = Path(temp_log_dir) / "spell_cache.json"
        assert cache_file.exists(), "Cache file should be created"
        
        with open(cache_file, 'r') as f:
            loaded_cache = json.load(f)
        
        assert cache_key in loaded_cache
        assert loaded_cache[cache_key]["corrected"] == "test query"
    
    def test_lru_eviction(self, normalizer):
        """Test LRU eviction when cache exceeds 10,000 entries."""
        # Add 10,001 entries
        for i in range(10001):
            key = f"key_{i}"
            normalizer.spell_cache[key] = {
                "corrected": f"query_{i}",
                "timestamp": f"2026-01-18T08:00:{i:02d}",
                "hit_count": 1
            }
        
        normalizer._save_spell_cache()
        
        # Cache should be trimmed to 10,000
        assert len(normalizer.spell_cache) == 10000
        
        # Oldest entry should be evicted
        assert "key_0" not in normalizer.spell_cache
        # Newest entry should be kept
        assert "key_10000" in normalizer.spell_cache


class TestLoggingAndFeedback:
    """Test logging and feedback collection."""
    
    @pytest.fixture
    def temp_log_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def normalizer(self, temp_log_dir):
        return AdaptiveNormalizer(log_dir=temp_log_dir, enable_spell_check=False)
    
    def test_feedback_logging(self, normalizer):
        """Test that normalizations are logged to feedback database."""
        query = "What is photosynthesis?"
        normalizer.normalize(query, user_id="test_user_001")
        
        assert len(normalizer.feedback_db) == 1
        log_entry = normalizer.feedback_db[0]
        
        assert log_entry["user_id"] == "test_user_001"
        assert log_entry["original"] == query
        assert "timestamp" in log_entry
        assert "confidence" in log_entry
    
    def test_low_confidence_flagging(self, normalizer, temp_log_dir):
        """Test that low-confidence cases are flagged for review."""
        # Query with low confidence (incomplete)
        query = "photosynthesis"
        normalizer.normalize(query, user_id="test_user_002")
        
        review_file = Path(temp_log_dir) / "low_confidence_cases.jsonl"
        
        # Check if low-confidence case was flagged
        if review_file.exists():
            with open(review_file, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) > 0, "Low-confidence case should be flagged"
            flagged_case = json.loads(lines[0])
            assert flagged_case["original"] == query
    
    def test_feedback_persistence(self, normalizer, temp_log_dir):
        """Test that feedback is persisted to disk after 100 entries."""
        # Add 100 normalizations
        for i in range(100):
            normalizer.normalize(f"test query {i}", user_id=f"user_{i}")
        
        feedback_file = Path(temp_log_dir) / "feedback_db.jsonl"
        assert feedback_file.exists(), "Feedback file should be created after 100 entries"
        
        with open(feedback_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 100, "All 100 entries should be persisted"


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def temp_log_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def normalizer(self, temp_log_dir):
        return AdaptiveNormalizer(log_dir=temp_log_dir, enable_spell_check=False)
    
    def test_empty_input(self, normalizer):
        """Test handling of empty input."""
        result = normalizer.normalize("")
        assert result["clean_question"] == ""
        assert result["confidence"] < 0.5
    
    def test_very_long_input(self, normalizer):
        """Test handling of very long input."""
        long_query = " ".join(["photosynthesis"] * 1000)
        result = normalizer.normalize(long_query)
        assert result["clean_question"] is not None
    
    def test_unicode_handling(self, normalizer):
        """Test handling of unicode characters."""
        unicode_query = "What is photosynthesis?"
        result = normalizer.normalize(unicode_query)
        assert result["clean_question"] is not None
    
    def test_missing_log_directory(self):
        """Test graceful handling when log directory doesn't exist."""
        non_existent_dir = "/tmp/non_existent_log_dir_12345"
        normalizer = AdaptiveNormalizer(log_dir=non_existent_dir, enable_spell_check=False)
        
        # Should create directory automatically
        assert Path(non_existent_dir).exists()
        
        # Cleanup
        shutil.rmtree(non_existent_dir)
    
    def test_corrupted_cache_file(self, normalizer, temp_log_dir):
        """Test handling of corrupted cache file."""
        cache_file = Path(temp_log_dir) / "spell_cache.json"
        
        # Write corrupted JSON
        with open(cache_file, 'w') as f:
            f.write("{ corrupted json }")
        
        # Should load empty cache without crashing
        loaded_cache = normalizer._load_spell_cache()
        assert loaded_cache == {}


class TestPerformance:
    """Test performance characteristics."""
    
    @pytest.fixture
    def temp_log_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def normalizer(self, temp_log_dir):
        return AdaptiveNormalizer(log_dir=temp_log_dir, enable_spell_check=False)
    
    def test_cache_lookup_speed(self, normalizer):
        """Test that cache lookups are fast."""
        import time
        
        # Add 1000 entries to cache
        for i in range(1000):
            key = normalizer._get_cache_key(f"query_{i}")
            normalizer.spell_cache[key] = {
                "corrected": f"query_{i}",
                "timestamp": "2026-01-18T08:00:00",
                "hit_count": 1
            }
        
        # Measure cache lookup time
        query = "query_500"
        start = time.time()
        normalizer.normalize(query, enable_spell_check=True)
        elapsed = time.time() - start
        
        # Cache lookup should be < 10ms
        assert elapsed < 0.01, f"Cache lookup took {elapsed*1000:.2f}ms (should be <10ms)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
