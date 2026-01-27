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
Anti-Confusion Engine for Satya Learning System

5-Layer Defense System for high-quality, curriculum-aligned answers.

Layers:
1. Mandatory Filtering (Subject + Grade)
2. Source Prioritization (NEB Notes > HuggingFace)
3. Context Ranking (Relevance Scoring)
4. Strict Grounding (Hallucination Prevention)
5. Source Attribution (Transparency)
"""

import logging
from typing import List, Dict, Tuple
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AntiConfusionEngine:
    """
    Filters, ranks, and verifies RAG context.
    Ensures quality answers for educational use.
    """
    
    def __init__(self):
        # Source priority weights
        self.SOURCE_PRIORITY = {
            'neb': 100,            # Highest: Teacher notes
            'openstax': 70,        # Standard textbooks
            'khanacademy': 65,     # Educational content
            'finemath': 60,        # Math datasets
            'gsm8k': 60,
            'scienceqa': 60,
            'default': 50
        }
        
        # Grounding thresholds
        self.MIN_CONTEXT_OVERLAP = 0.3  # 30% keyword overlap minimum
        self.RELEVANCE_THRESHOLD = 0.6  # Minimum similarity

    def calculate_priority_score(self, source_type: str) -> int:
        if not source_type:
            return self.SOURCE_PRIORITY['default']
        
        source = source_type.lower()
        
        # Checks for NEB first (highest priority)
        if 'neb' in source:
            return self.SOURCE_PRIORITY['neb']
        
        # Checks other sources
        for key, score in self.SOURCE_PRIORITY.items():
            if key in source:
                return score
        
        return self.SOURCE_PRIORITY['default']

    def rank_results(
        self, 
        results: List[Dict], 
        query_text: str
    ) -> List[Dict]:
        if not results:
            return []
        
        ranked_chunks = []
        
        for res in results:
            metadata = res.get('metadata', {})
            source = metadata.get('source', 'unknown')
            
            if (source.lower() == 'unknown' or not source) and 'seed_data' in metadata:
                source = metadata['seed_data']
                metadata['source'] = source
            
            current_type = metadata.get('type', 'unknown')
            if current_type == 'unknown':
                if source in ['openstax', 'khanacademy', 'fineweb_edu', 'finemath', 'scienceqa']:
                    metadata['type'] = 'General Knowledge'
                else:
                    metadata['type'] = 'Supplemental'
                
            chunk_text = res.get('text', '')
            base_score = res.get('score', 0.0)  # Cosine similarity
            
            if not chunk_text or len(chunk_text.strip()) < 10:
                continue
            
            priority_score = self.calculate_priority_score(source)
            
            weighted_score = (base_score * 0.7) + ((priority_score / 100.0) * 0.3)
            
            if 'grade' in metadata:
                grade_str = str(metadata['grade'])
                if grade_str in query_text or f"grade {grade_str}" in query_text.lower():
                    weighted_score += 0.1
                
            ranked_chunks.append({
                'text': chunk_text,
                'metadata': metadata,
                'original_score': base_score,
                'final_score': weighted_score,
                'source_type': 'NEB' if priority_score == 100 else 'External'
            })
            
        ranked_chunks.sort(key=lambda x: x['final_score'], reverse=True)
        
        return ranked_chunks

    def validate_grounding(
        self, 
        answer: str, 
        context_chunks: List[str]
    ) -> Tuple[bool, str]:
        """
        Layer 4: Verify answer is grounded in context.
        Prevents hallucinations.
        
        Args:
            answer: Generated answer
            context_chunks: Context provided to LLM
            
        Returns:
            (is_grounded, reason)
        """
        if not answer or not context_chunks:
            return False, "No answer or context"
        
        # Skips validation for very short answers
        if len(answer.split()) < 5:
            return True, "Answer too short to validate"
            
        full_context = " ".join(context_chunks).lower()
        answer_lower = answer.lower()
        
        answer_terms = set(re.findall(r'\b\w{5,}\b', answer_lower))
        
        if not answer_terms:
            return True, "No key terms to validate"
            
        found_count = sum(1 for term in answer_terms if term in full_context)
        overlap_ratio = found_count / len(answer_terms) if answer_terms else 0
        
        if overlap_ratio < self.MIN_CONTEXT_OVERLAP:
            logger.warning(f"Low grounding: {overlap_ratio:.2%}")
            return False, f"Low context overlap ({overlap_ratio:.0%})"
            
        forbidden_phrases = [
            "i don't have that information",
            "my knowledge cutoff",
            "unrelated to the context", 
            "based on general knowledge",
            "i couldn't find",
            "not mentioned in the context"
        ]
        
        for phrase in forbidden_phrases:
            if phrase in answer_lower:
                return False, "Model admitted lack of knowledge"
                 
        return True, "Grounded"

    def resolve_conflicts(self, chunks: List[Dict]) -> List[Dict]:
        if not chunks:
            return []
        
        neb_chunks = [c for c in chunks if c.get('source_type') == 'NEB']
        other_chunks = [c for c in chunks if c.get('source_type') != 'NEB']
        
        return neb_chunks + other_chunks
    
    def filter_low_quality(self, chunks: List[Dict], min_score: float = 0.35) -> List[Dict]:
        return [c for c in chunks if c.get('final_score', 0) >= min_score]