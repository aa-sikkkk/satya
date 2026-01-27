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
Extraction logic for diagram generation
"""

import re
import logging
from typing import List, Optional, Tuple, Dict, Any
from functools import lru_cache

from .diagram_constants import (
    STOPWORDS, NUMBERED_PATTERN, STEP_PREFIX_PATTERN, 
    PROCESS_LIST_PATTERN, STAGE_LIST_PATTERN,
    LEADING_NUMBERS_PATTERN, TRAILING_PUNCTUATION_PATTERN,
    COMPONENT_PATTERN_1, COMPONENT_PATTERN_2, COMPONENT_PATTERN_3,
    COMPONENT_PATTERN_1, COMPONENT_PATTERN_2, COMPONENT_PATTERN_3,
    DECISION_KEYWORDS_PATTERN,
    ITERATION_PATTERN, ITERATION_OVER_PATTERN, CYCLE_PATTERN,
    IGNORED_PREFIXES
)

BULLET_POINT_PATTERN = re.compile(r'^\s*[\-\*\u2022]\s+([^\n\.\:]{3,50})', re.MULTILINE)

logger = logging.getLogger(__name__)

class DiagramExtractor:
    """Handles extraction of entities and steps for diagrams."""
    
    @staticmethod
    def extract_steps_from_answer(answer: str, rag_chunks: Optional[List[str]] = None, llm_handler=None) -> List[str]:
        """Orchestrates extraction: LLM -> Pattern Matching -> Sentence Fallback."""
        
        # 1. Trying LLM first (High Quality)
        if llm_handler:
            llm_steps = DiagramExtractor.extract_steps_with_llm(answer, llm_handler)
            if len(llm_steps) >= 2:
                return llm_steps
        
        # 2. Try Pattern Matching on the answer itself (Fast)
        pattern_steps = DiagramExtractor._extract_via_patterns(answer)
        if len(pattern_steps) >= 2:
            return pattern_steps

        # 3. Fallback to RAG chunks
        if rag_chunks:
            rag_steps = DiagramExtractor.extract_steps_from_rag(rag_chunks)
            if len(rag_steps) >= 2:
                return rag_steps
                
        # 4. Final Fallback: Split by sentences
        return DiagramExtractor._extract_via_sentences(answer)

    @staticmethod
    def _extract_via_patterns(text: str) -> List[str]:
        """Internal helper to run regex patterns against text."""
        steps = []
        for pattern in [NUMBERED_PATTERN, STEP_PREFIX_PATTERN, BULLET_POINT_PATTERN]:
            matches = pattern.findall(text)
            for m in matches:
                val = m[1] if isinstance(m, tuple) and len(m) > 1 else (m[0] if isinstance(m, tuple) else m)
                clean = DiagramExtractor.clean_term(val)
                if clean and clean not in steps:
                    steps.append(clean)
        return steps[:8]

    @staticmethod
    def _extract_via_sentences(answer: str) -> List[str]:
        """Splits answer into logical steps based on sentence structure."""
        # Splits by punctuation but ignore abbreviations
        sentences = re.split(r'(?<!e\.g)(?<!i\.e)(?<=[.!?])\s+', answer)
        
        clean_steps = []
        for s in sentences:
            s = s.strip()
            if (len(s) > 15 and 
                not s.startswith(IGNORED_PREFIXES) and 
                not any(phrase in s for phrase in IGNORED_PREFIXES)):
                
                parts = re.split(r'[,;]', s)
                candidate = parts[0] if len(parts[0].split()) > 3 else s
                
                clean = DiagramExtractor.clean_term(candidate, max_words=10)
                if clean:
                    clean_steps.append(clean)
                    
        return clean_steps[:6]


    # TODO: NEEDS BETTER APPROACH
    @staticmethod
    def extract_steps_with_llm(answer: str, llm_handler) -> List[str]:
        """Extract steps using LLM with robust cleaning."""
        if not answer or not llm_handler or len(answer) < 20:
            return []
        
        prompt = (
            "Instruct: Provide a strictly comma-separated list of the 4 main steps "
            "in the following process. Use only 1-2 words per step. "
            "Do not include introductory text.\n"
            f"Input: {answer}\n"
            "Output:"
        )
        
        try:
            resp = llm_handler.generate_response(prompt, max_tokens=150)
            if ":" in resp: resp = resp.split(":")[-1]
            
            raw_items = re.split(r'[,|\n]', resp)
            steps = []
            for item in raw_items:
                clean = DiagramExtractor.clean_term(item, max_words=4)
                if clean and clean not in steps:
                    steps.append(clean)
            return steps if len(steps) >= 2 else []
        except Exception:
            return []

    @staticmethod
    def extract_steps_from_rag(rag_chunks: List[str]) -> List[str]:
        combined = " ".join(rag_chunks[:5])
        return DiagramExtractor._extract_via_patterns(combined)

    @staticmethod
    def extract_structure_components(answer: str, question: str, calculate_limit_callback=None) -> List[str]:
        """Extracts hierarchy parts (e.g., 'The system has a Frontend, Backend, and DB')."""
        components = []
        for pattern in [COMPONENT_PATTERN_1, COMPONENT_PATTERN_2, COMPONENT_PATTERN_3]:
            match = pattern.search(answer)
            if match:
                items = re.split(r'[,;]|\band\b', match.group(1))
                for i in items:
                    clean = DiagramExtractor.clean_term(i, max_words=3)
                    if clean and clean not in components:
                        components.append(clean)
        
        if not components:
            # Fallback: look for capitalized tech terms
            tech_terms = re.findall(r'\b[A-Z][a-z]{3,}\b', answer)
            for t in tech_terms:
                if t.lower() not in STOPWORDS and t not in components:
                    components.append(t)
                    
        return components[:8]

    @staticmethod
    def clean_term(text: str, max_words: int = 4) -> str:
        """Helper to sanitize extracted strings for ASCII display."""
        if not text: return ""
        text = LEADING_NUMBERS_PATTERN.sub('', text.strip())
        text = re.sub(r'^(the|a|an|to|your)\s+', '', text, flags=re.I)
        text = TRAILING_PUNCTUATION_PATTERN.sub('', text)
        
        words = text.split()
        if not words: return ""
        
        clean = " ".join(words[:max_words])
        if len(words) > max_words: clean += "..."
        
        return clean.strip().capitalize()

    @staticmethod
    def extract_iteration_subject(answer: str, question: str) -> str:
        combined = f"{question} {answer}".lower()
        match = ITERATION_PATTERN.search(combined) or ITERATION_OVER_PATTERN.search(combined)
        return match.group(1).capitalize() if match else "Item"

    @staticmethod
    def extract_key_process_terms(text: str) -> List[str]:
        """Quickly grab technical verbs/nouns defining the process."""
        terms = []
        # Use list patterns (consists of X, Y, Z)
        for pattern in [PROCESS_LIST_PATTERN, STAGE_LIST_PATTERN]:
            match = pattern.search(text)
            if match:
                raw_list = match.group(1)
                items = re.split(r'[,;]|\band\b', raw_list)
                for item in items:
                    clean = DiagramExtractor.clean_term(item, max_words=3)
                    if clean and clean not in terms:
                        terms.append(clean)
        return terms[:5]

    @staticmethod
    @lru_cache(maxsize=128)
    def has_decision_points(answer: str) -> bool:
        return bool(DECISION_KEYWORDS_PATTERN.search(answer))

    @staticmethod
    @lru_cache(maxsize=128)
    def is_cyclic_process(question: str, answer: str) -> bool:
        return bool(CYCLE_PATTERN.search(f"{question} {answer}"))