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
        """Get priority score for a source type."""
        if not source_type:
            return self.SOURCE_PRIORITY['default']
        
        source = source_type.lower()
        
        # Check for NEB first (highest priority)
        if 'neb' in source:
            return self.SOURCE_PRIORITY['neb']
        
        # Check other sources
        for key, score in self.SOURCE_PRIORITY.items():
            if key in source:
                return score
        
        return self.SOURCE_PRIORITY['default']

    def rank_results(
        self, 
        results: List[Dict], 
        query_text: str
    ) -> List[Dict]:
        """
        Rank retrieval results using 5-layer strategy.
        
        Args:
            results: Raw results from ChromaDB
            query_text: Original query
            
        Returns:
            Re-ranked context chunks
        """
        if not results:
            return []
        
        ranked_chunks = []
        
        for res in results:
            # Extract metadata
            metadata = res.get('metadata', {})
            source = metadata.get('source', 'unknown')
            
            # Fallback to seed_data if source unknown
            if (source.lower() == 'unknown' or not source) and 'seed_data' in metadata:
                source = metadata['seed_data']
                metadata['source'] = source
            
            # Type normalization
            current_type = metadata.get('type', 'unknown')
            if current_type == 'unknown':
                if source in ['openstax', 'khanacademy', 'fineweb_edu', 'finemath', 'scienceqa']:
                    metadata['type'] = 'General Knowledge'
                else:
                    metadata['type'] = 'Supplemental'
                
            chunk_text = res.get('text', '')
            base_score = res.get('score', 0.0)  # Cosine similarity
            
            # Skip empty chunks
            if not chunk_text or len(chunk_text.strip()) < 10:
                continue
            
            # Source prioritization
            priority_score = self.calculate_priority_score(source)
            
            # Weighted score: 70% similarity + 30% priority
            # Priority normalized: 100 -> 1.0, 50 -> 0.5
            weighted_score = (base_score * 0.7) + ((priority_score / 100.0) * 0.3)
            
            # Boost if grade matches
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
            
        # Sort by final score (highest first)
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
        
        # Skip validation for very short answers
        if len(answer.split()) < 5:
            return True, "Answer too short to validate"
            
        # Combine context
        full_context = " ".join(context_chunks).lower()
        answer_lower = answer.lower()
        
        # Extract key terms (words > 4 chars)
        answer_terms = set(re.findall(r'\b\w{5,}\b', answer_lower))
        
        if not answer_terms:
            return True, "No key terms to validate"
            
        # Count terms found in context
        found_count = sum(1 for term in answer_terms if term in full_context)
        overlap_ratio = found_count / len(answer_terms) if answer_terms else 0
        
        if overlap_ratio < self.MIN_CONTEXT_OVERLAP:
            logger.warning(f"⚠️ Low grounding: {overlap_ratio:.2%}")
            return False, f"Low context overlap ({overlap_ratio:.0%})"
            
        # Check for hallucination indicators
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
        """
        Layer 5: Conflict resolution.
        NEB sources always appear first.
        
        Args:
            chunks: Ranked chunks
            
        Returns:
            Chunks with NEB first
        """
        if not chunks:
            return []
        
        # Separate NEB and others
        neb_chunks = [c for c in chunks if c.get('source_type') == 'NEB']
        other_chunks = [c for c in chunks if c.get('source_type') != 'NEB']
        
        # NEB first, then others (both already sorted by score)
        return neb_chunks + other_chunks
    
    def filter_low_quality(self, chunks: List[Dict], min_score: float = 0.35) -> List[Dict]:
        """
        Remove low-quality chunks that won't help answer.
        
        Args:
            chunks: Ranked chunks
            min_score: Minimum final_score threshold
            
        Returns:
            Filtered chunks
        """
        return [c for c in chunks if c.get('final_score', 0) >= min_score]