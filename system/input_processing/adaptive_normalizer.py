# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
Adaptive Normalizer - Production Wrapper
Adds spell correction, logging, and learning capabilities.
"""

import logging
import json
import os
import re
import hashlib
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from system.input_processing.input_normalizer import InputNormalizer

logger = logging.getLogger(__name__)


class AdaptiveNormalizer:
    """Production wrapper with learning and spell correction."""
    
    def __init__(
        self,
        normalizer: Optional[InputNormalizer] = None,
        log_dir: str = "satya_data/normalization_logs",
        enable_spell_check: bool = True
    ):
        self.normalizer = normalizer or InputNormalizer()
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.feedback_db: List[Dict] = []
        self.feedback_file = self.log_dir / "feedback_db.jsonl"
        
        # Spell correction cache
        self.spell_cache_file = self.log_dir / "spell_cache.json"
        self.spell_cache = self._load_spell_cache()
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Grammar + spell checker 
        self.spell_checker = None
        if enable_spell_check:
            self.spell_checker = self._load_language_tool()
        
        logger.info("AdaptiveNormalizer initialized")
    
    def normalize(
        self,
        raw_question: str,
        user_id: Optional[str] = None,
        add_scaffolding: bool = False,
        enable_spell_check: bool = True
    ) -> Dict[str, any]:
        original = raw_question
        
        # Conditional spell-checking with caching
        if enable_spell_check and self.spell_checker:
            cache_key = self._get_cache_key(raw_question)
            if cache_key in self.spell_cache:
                raw_question = self.spell_cache[cache_key]["corrected"]
                self.cache_hits += 1
                logger.debug(f"Cache HIT: {cache_key[:8]}...")
            elif self._should_spell_check(raw_question):
                # Run LanguageTool only if needed
                corrected = self._correct_text(raw_question)
                if corrected != raw_question:
                    # Cache the correction
                    self.spell_cache[cache_key] = {
                        "corrected": corrected,
                        "timestamp": datetime.now().isoformat(),
                        "hit_count": 1
                    }
                    self._save_spell_cache()
                raw_question = corrected
                self.cache_misses += 1
            else:
                logger.debug(f"Spell-check SKIPPED (heuristic)")
        
        result = self.normalizer.normalize(raw_question, add_scaffolding=add_scaffolding)
        
        self._log_normalization(
            original=original,
            corrected=raw_question,
            result=result,
            user_id=user_id
        )
        
        return result
    
    def get_low_confidence_cases(self, limit: int = 100) -> List[Dict]:
        """Gets recent low-confidence cases for review."""
        review_file = self.log_dir / "low_confidence_cases.jsonl"
        if not review_file.exists():
            return []
        
        try:
            cases = []
            with open(review_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        cases.append(json.loads(line))
            return cases[-limit:]
        except Exception as e:
            logger.error(f"Could not load low-confidence cases: {e}")
            return []
    
    # Private Methods
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text."""
        normalized = text.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _load_spell_cache(self) -> Dict:
        """Load spell correction cache from disk."""
        if not self.spell_cache_file.exists():
            return {}
        
        try:
            with open(self.spell_cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            logger.info(f"Loaded spell cache: {len(cache)} entries")
            return cache
        except Exception as e:
            logger.warning(f"Could not load spell cache: {e}")
            return {}
    
    def _save_spell_cache(self):
        """Save spell correction cache to disk."""
        try:
            # LRU eviction: keep only 10,000 most recent entries
            if len(self.spell_cache) > 10000:
                sorted_cache = sorted(
                    self.spell_cache.items(),
                    key=lambda x: x[1].get("timestamp", ""),
                    reverse=True
                )
                self.spell_cache = dict(sorted_cache[:10000])
            
            with open(self.spell_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.spell_cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save spell cache: {e}")
    
    def _should_spell_check(self, text: str) -> bool:
        words = text.split()

        if len(words) < 5:
            return False
        
        if re.match(r'^[A-D]\)', text) or re.match(r'^\d+\.', text):
            return False
        
        if text.isupper():
            return False
        
        potential_typos = [
            r'\b\w*[0-9]+\w*\b',  
            r'\b\w{15,}\b',       
            r'(.)\1{3,}',     
        ]
        
        for pattern in potential_typos:
            if re.search(pattern, text):
                return True
        
        # For longer questions, we'll run spell-check
        if len(words) > 10:
            return True
        
        return False
    
    def _load_language_tool(self):
        """Load LanguageTool for offline correction."""
        try:
            import language_tool_python
            tool = language_tool_python.LanguageTool('en-US')
            logger.info("LanguageTool loaded (offline mode)")
            return tool
        except ImportError:
            logger.warning("LanguageTool not installed. Run: pip install language-tool-python")
            return None
        except Exception as e:
            logger.warning(f"Could not load LanguageTool: {e}")
            return None
    
    def _correct_text(self, text: str) -> str:
        if not self.spell_checker:
            return text
        
        try:
            import language_tool_python
            matches = self.spell_checker.check(text)
            if not matches:
                return text
            
            corrected = language_tool_python.utils.correct(text, matches)
            if corrected != text:
                logger.debug(f"Corrected: '{text}' -> '{corrected}'")
            return corrected
        except Exception as e:
            logger.debug(f"Correction error: {e}")
            return text
    
    def _log_normalization(
        self,
        original: str,
        corrected: str,
        result: Dict,
        user_id: Optional[str]
    ):
        """Log for learning."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "original": original,
            "corrected": corrected,
            "clean": result["clean_question"],
            "confidence": result["confidence"],
            "notes": result["notes"],
        }
        
        self.feedback_db.append(log_entry)
        
        if result["confidence"] < 0.7:
            self._flag_for_review(log_entry)
        
        if len(self.feedback_db) % 100 == 0:
            self._persist_feedback()
    
    def _flag_for_review(self, log_entry: Dict):
        review_file = self.log_dir / "low_confidence_cases.jsonl"
        try:
            with open(review_file, 'a', encoding='utf-8') as f:
                json.dump(log_entry, f)
                f.write('\n')
        except Exception as e:
            logger.warning(f"Could not flag for review: {e}")
    
    def _persist_feedback(self):
        try:
            with open(self.feedback_file, 'a', encoding='utf-8') as f:
                for entry in self.feedback_db:
                    json.dump(entry, f)
                    f.write('\n')
            self.feedback_db = []
            logger.debug("Persisted feedback")
        except Exception as e:
            logger.warning(f"Could not persist feedback: {e}")
