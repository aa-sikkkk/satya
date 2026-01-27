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
Input Normalization - Core Rule Engine
Handles deterministic text transformations optimized for Phi-1.5.
"""

import re
import logging
import json
import os
from typing import Dict, List, Tuple, Set
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class InputNormalizer:
    """Rule-based normalizer for educational questions."""
    
    def __init__(self, learnable_db_path: str = "satya_data/input_normalizer_phrases.json"):
        self.learnable_db_path = learnable_db_path
        self.learned_noise_phrases: Set[str] = set()
        self._load_learnable_database()
        
        # Noise removal patterns
        self.noise_patterns = self._compile_noise_patterns()
        self.fuzzy_noise_phrases = self._get_fuzzy_phrases()
        self.fuzzy_threshold = 0.85
        
        # Phi-1.5 optimizations
        self.slang_to_formal = self._get_slang_mappings()
        self.filler_words = [r"\blike\b", r"\bbasically\b", r"\bactually\b", r"\bjust\b"]
        self.conversational_starters = [r"^hey\s+", r"^hi\s+", r"^so\s+"]
        self.politeness_patterns = [r"^can you (please )?tell me ", r"^please (tell me|explain) "]
        self.abbreviations = self._get_abbreviations()
        
        # Context expansion rules
        self.context_rules = [
            (["switch", "circuit", "current", "voltage"], "electric circuit", ["switch", "circuit"]),
            (["mitochondria", "chloroplast", "nucleus"], "cell", ["mitochondria", "chloroplast"]),
        ]
        
        # Intent classification
        self.intent_patterns = {
            "WHY": [r"^why ", r"what is the reason", r"what causes"],
            "HOW": [r"^how ", r"what is the process"],
            "DESCRIBE": [r"^describe ", r"^explain ", r"what happens"],
            "DEFINE": [r"^define ", r"what does .+ mean"],
            "COMPARE": [r"difference between", r"compare ", r"versus"],
            "SOLVE": [r"^solve ", r"^calculate ", r"^find "],
        }
        self.compiled_intent_patterns = {
            intent: [re.compile(p, re.IGNORECASE) for p in patterns]
            for intent, patterns in self.intent_patterns.items()
        }
        
        # Optional POS tagger
        self.nlp = self._load_spacy()
        
        logger.info("InputNormalizer initialized")
    
    def normalize(self, raw_question: str, add_scaffolding: bool = False) -> Dict[str, any]:
        """Main normalization pipeline."""
        try:
            if not raw_question or not isinstance(raw_question, str) or len(raw_question) < 3:
                return self._fallback_result(raw_question, "Invalid input")
            
            question = raw_question.strip()
            notes = []

            question, n = self._transform_to_formal(question)
            notes.extend(n)
            
            question, n = self._remove_noise(question)
            notes.extend(n)
            
            question, n = self._expand_abbreviations(question)
            notes.extend(n)
            
            question, n = self._normalize_sentence(question)
            notes.extend(n)
            
            question, n = self._expand_context(question)
            notes.extend(n)
            
            intent = self._classify_intent(question)
            confidence = self._calculate_confidence(raw_question, question, notes)
            
            result = {"clean_question": question, "intent": intent, "confidence": confidence, "notes": notes}
            
            if add_scaffolding:
                scaffolds = {"WHY": "Explain the reason:", "HOW": "Describe the process:", 
                           "DEFINE": "Define precisely:", "SOLVE": "Solve step by step:"}
                scaffold = scaffolds.get(intent, "Explain clearly:")
                result["scaffolded_prompt"] = f"{scaffold} {question}"
            
            return result
        except Exception as e:
            logger.error(f"Normalization error: {e}")
            return self._fallback_result(raw_question, str(e))
    
    def add_noise_phrase(self, phrase: str):
        """Add learned noise phrase."""
        phrase = phrase.lower().strip()
        if phrase and phrase not in self.learned_noise_phrases:
            self.learned_noise_phrases.add(phrase)
            self._save_learnable_database()
    
    # Private Methods
    
    def _compile_noise_patterns(self) -> List[re.Pattern]:
        """Compiles exam meta-language patterns."""
        patterns = [
            r"with reference to the (figure|diagram|graph|table|passage|text) (above|below|given)",
            r"according to the (passage|text|diagram|figure)",
            r"write short notes? on",
            r"explain (in )?brief(ly)?",
            r"give reasons?",
            r"in your own words",
        ]
        return [re.compile(p, re.IGNORECASE) for p in patterns]
    
    def _get_fuzzy_phrases(self) -> List[str]:
        return ["with reference to the figure above", "according to the passage", "explain in brief"]
    
    def _get_slang_mappings(self) -> Dict[str, str]:
        return {
            r"\bgonna\b": "going to", r"\bwanna\b": "want to", r"\bcoz\b": "because",
            r"\bu\b": "you", r"\bur\b": "your", r"\bidk\b": "I do not know",
        }
    
    def _get_abbreviations(self) -> Dict[str, str]:
        return {
            r"\bEMF\b": "electromotive force", r"\bAC\b": "alternating current",
            r"\bDC\b": "direct current", r"\bDNA\b": "deoxyribonucleic acid",
        }
    
    def _load_spacy(self):
        try:
            import spacy
            return spacy.load("en_core_web_sm", disable=["ner", "textcat"])
        except:
            return None
    
    def _load_learnable_database(self):
        try:
            if os.path.exists(self.learnable_db_path):
                with open(self.learnable_db_path, 'r') as f:
                    data = json.load(f)
                    self.learned_noise_phrases = set(data.get("noise_phrases", []))
        except Exception as e:
            logger.warning(f"Could not load learned phrases: {e}")
    
    def _save_learnable_database(self):
        try:
            os.makedirs(os.path.dirname(self.learnable_db_path), exist_ok=True)
            with open(self.learnable_db_path, 'w') as f:
                json.dump({"noise_phrases": list(self.learned_noise_phrases)}, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save learned phrases: {e}")
    
    def _transform_to_formal(self, question: str) -> Tuple[str, List[str]]:
        """Removes slang and casual language."""
        notes, original = [], question
        
        for pattern in self.conversational_starters:
            question = re.sub(pattern, "", question, flags=re.IGNORECASE)
        
        for slang, formal in self.slang_to_formal.items():
            question = re.sub(slang, formal, question, flags=re.IGNORECASE)
        
        for filler in self.filler_words:
            question = re.sub(filler, "", question, flags=re.IGNORECASE)
        
        for pattern in self.politeness_patterns:
            question = re.sub(pattern, "", question, flags=re.IGNORECASE)
        
        question = re.sub(r'\s+', ' ', question).strip()
        if question != original:
            notes.append("formalized")
        return question, notes
    
    def _remove_noise(self, question: str) -> Tuple[str, List[str]]:
        """Removes exam fluff using multiple strategies."""
        notes, original = [], question
        
        for pattern in self.noise_patterns:
            if pattern.search(question):
                question = pattern.sub("", question)
                notes.append("removed_regex")
        
        for phrase in self.fuzzy_noise_phrases:
            if self._fuzzy_match(question, phrase):
                question = self._remove_fuzzy(question, phrase)
                notes.append("removed_fuzzy")
        
        for phrase in self.learned_noise_phrases:
            if phrase in question.lower():
                question = re.sub(re.escape(phrase), "", question, flags=re.IGNORECASE)
                notes.append("removed_learned")
        
        question = re.sub(r'\s+', ' ', question).strip()
        question = re.sub(r'^[,:;\-\s]+', '', question)
        return question, notes
    
    def _fuzzy_match(self, text: str, phrase: str) -> bool:
        """Checks fuzzy match using sliding window."""
        text_words, phrase_words = text.lower().split(), phrase.lower().split()
        if len(phrase_words) > len(text_words):
            return False
        
        for i in range(len(text_words) - len(phrase_words) + 1):
            window = " ".join(text_words[i:i + len(phrase_words)])
            if SequenceMatcher(None, window, phrase.lower()).ratio() >= self.fuzzy_threshold:
                return True
        return False
    
    def _remove_fuzzy(self, text: str, phrase: str) -> str:
        """Removes fuzzy-matched phrase."""
        text_words = text.split()
        phrase_words = phrase.lower().split()
        best_idx, best_sim = -1, 0.0
        
        for i in range(len(text_words) - len(phrase_words) + 1):
            window = " ".join([w.lower() for w in text_words[i:i + len(phrase_words)]])
            sim = SequenceMatcher(None, window, phrase.lower()).ratio()
            if sim > best_sim and sim >= self.fuzzy_threshold:
                best_sim, best_idx = sim, i
        
        if best_idx >= 0:
            return " ".join(text_words[:best_idx] + text_words[best_idx + len(phrase_words):])
        return text
    
    def _expand_abbreviations(self, question: str) -> Tuple[str, List[str]]:
        """Expands domain abbreviations."""
        notes = []
        for abbrev, full in self.abbreviations.items():
            if re.search(abbrev, question):
                question = re.sub(abbrev, full, question)
                notes.append("expanded_abbrev")
        return question, notes
    
    def _normalize_sentence(self, question: str) -> Tuple[str, List[str]]:
        """Fixes case and punctuation."""
        notes, original = [], question
        
        if question.isupper():
            question = question.capitalize()
            notes.append("fixed_caps")
        
        if question and question[0].islower():
            question = question[0].upper() + question[1:]
        
        starters = ["what", "why", "how", "when", "where", "who"]
        if any(question.lower().startswith(w) for w in starters) and not question.endswith("?"):
            question = question.rstrip(".!,;:") + "?"
        
        question = re.sub(r'\?+', '?', question)
        return question, notes
    
    def _expand_context(self, question: str) -> Tuple[str, List[str]]:
        """Adds implicit context for vague questions."""
        if len(question.split()) > 15:
            return question, []
        
        notes = []
        q_lower = question.lower()
        
        for triggers, context, required in self.context_rules:
            if not any(w in q_lower for w in required) or context in q_lower:
                continue
            
            match = re.search(r'(what happens)\s+(when|if)', question, re.IGNORECASE)
            if match:
                pos = match.end(1)
                question = question[:pos] + f" in a {context}" + question[pos:]
                notes.append("expanded_context")
                break
        
        return question, notes
    
    def _classify_intent(self, question: str) -> str:
        """Classifies question intent."""
        for intent, patterns in self.compiled_intent_patterns.items():
            if any(p.search(question.lower()) for p in patterns):
                return intent
        return "DESCRIBE"
    
    def _calculate_confidence(self, original: str, clean: str, notes: List[str]) -> float:
        """Calculates normalization confidence."""
        confidence = 1.0
        change_ratio = len(clean) / max(len(original), 1)
        
        if change_ratio < 0.5:
            confidence -= 0.2
        if len(notes) > 5:
            confidence -= 0.15
        elif len(notes) > 3:
            confidence -= 0.1
        
        return max(0.5, min(1.0, confidence))
    
    def _fallback_result(self, question: str, reason: str) -> Dict[str, any]:
        return {
            "clean_question": str(question) if question else "",
            "intent": "UNKNOWN",
            "confidence": 0.0,
            "notes": [f"fallback: {reason}"]
        }
