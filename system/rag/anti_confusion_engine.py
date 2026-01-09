"""
Anti-Confusion Engine for Satya Learning System

Implements the 5-Layer Defense System to ensure high-quality, 
curriculum-aligned answers for Nepali students.

Layers:
1. Mandatory Filtering (Subject + Grade)
2. Source Prioritization (NEB Notes > HuggingFace)
3. Context Ranking (Relevance Scoring)
4. Strict Grounding (Hallucination Prevention)
5. Source Attribution (Transparency)
"""

import logging
from typing import List, Dict, Tuple, Optional
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AntiConfusionEngine:
    """
    The brain of the retrieval system. 
    Filters, ranks, and verifies RAG context.
    """
    
    def __init__(self):
        # Prioritization weights
        self.SOURCE_PRIORITY = {
            'neb': 100,            # Highest priority: Teacher notes
            'openstax': 70,        # Standard textbooks
            'khanacademy': 65,     # Educational content
            'finemath': 60,        # Math datasets
            'gsm8k': 60,
            'scienceqa': 60,
            'default': 50
        }
        
        # Grounding thresholds
        self.MIN_CONTEXT_OVERLAP = 0.3  # Answer must overlap 30% with context keywords
        self.RELEVANCE_THRESHOLD = 0.6  # Minimum cosine similarity for valid chunk

    def calculate_priority_score(self, source_type: str) -> int:
        """Get priority score for a source type."""
        source = source_type.lower()
        if 'neb' in source:
            return self.SOURCE_PRIORITY['neb']
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
        Rank retrieval results based on 5-layer strategy.
        
        Args:
            results: List of raw results from ChromaDB
            query_text: Original user query
            
        Returns:
            Re-ranked list of best context chunks
        """
        ranked_chunks = []
        
        for res in results:
            # Extract metadata
            metadata = res.get('metadata', {})
            source = metadata.get('source', 'unknown')
            
            # Fallback to seed_data if source is unknown (Common in HuggingFace datasets)
            if (source.lower() == 'unknown' or not source) and 'seed_data' in metadata:
                source = metadata['seed_data']
                metadata['source'] = source
            
            # 3. Type Normalization (User Request: Label as General)
            current_type = metadata.get('type', 'unknown')
            if current_type == 'unknown' and source in ['openstax', 'khanacademy', 'fineweb_edu', 'finemath', 'scienceqa']:
                metadata['type'] = 'General Knowledge'
            elif current_type == 'unknown':
                 metadata['type'] = 'Supplemental'
                
            chunk_text = res.get('text', '')
            base_score = res.get('score', 0.0) # Cosine similarity
            
            # 1. Source Prioritization
            priority_score = self.calculate_priority_score(source)
            
            # 2. Context Relevance (Weighted Mix)
            # Final Score = (Similarity * 0.7) + (Priority Normalized * 0.3)
            # Priority normalized: 100 -> 1.0, 50 -> 0.5
            weighted_score = (base_score * 0.7) + ((priority_score / 100.0) * 0.3)
            
            # Boost score if grade matches exactly (reinforcement)
            if 'grade' in metadata and str(metadata['grade']) in query_text:
                weighted_score += 0.1
                
            ranked_chunks.append({
                'text': chunk_text,
                'metadata': metadata,
                'original_score': base_score,
                'final_score': weighted_score,
                'source_type': 'NEB' if priority_score == 100 else 'External'
            })
            
        # Sort by final weighted score descending
        ranked_chunks.sort(key=lambda x: x['final_score'], reverse=True)
        
        return ranked_chunks

    def validate_grounding(
        self, 
        answer: str, 
        context_chunks: List[str]
    ) -> Tuple[bool, str]:
        """
        Layer 4: Strict Grounding Check.
        
        Verifies that the answer is actually derived from the context
        to prevent hallucinations.
        
        Args:
            answer: Generated answer from LLM
            context_chunks: List of context strings provided to LLM
            
        Returns:
            (is_grounded, failure_reason)
        """
        if not answer or not context_chunks:
            return False, "No answer or context"
            
        # Combine all context
        full_context = " ".join(context_chunks).lower()
        answer_lower = answer.lower()
        
        # 1. Key Term Overlap Check
        # Extract rare words/terms from answer (simple heuristic: > 4 chars)
        answer_terms = set(re.findall(r'\b\w{5,}\b', answer_lower))
        if not answer_terms:
            return True, "Answer too short/simple to hallucinate"
            
        found_count = sum(1 for term in answer_terms if term in full_context)
        overlap_ratio = found_count / len(answer_terms)
        
        if overlap_ratio < self.MIN_CONTEXT_OVERLAP:
            logger.warning(f"⚠️ Low grounding overlap: {overlap_ratio:.2f}")
            return False, f"Low context overlap ({overlap_ratio:.0%})"
            
        # 2. Hallucination Guardrails
        # Check for phrases that indicate the model is making things up or apologizing
        forbidden_phrases = [
            "i don't have that information",
            "my knowledge cutoff",
            "unrelated to the context", 
            "based on general knowledge"
        ]
        
        for phrase in forbidden_phrases:
            if phrase in answer_lower:
                 return False, "Model admitted lack of knowledge"
                 
        return True, "Grounded"

    def resolve_conflicts(self, chunks: List[Dict]) -> List[Dict]:
        """
        Layer 5: Conflict Resolution.
        
        If NEB and External sources contradict, NEB wins.
        This function ensures NEB chunks appear first in the context window.
        """
        # Separate NEB and others
        neb_chunks = [c for c in chunks if c['source_type'] == 'NEB']
        other_chunks = [c for c in chunks if c['source_type'] != 'NEB']
        
        # Return NEB first, then others
        return neb_chunks + other_chunks

