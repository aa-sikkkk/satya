"""
RAG Helper Utilities
Simplified.
"""

import logging
import time
from typing import Optional, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

logger = logging.getLogger(__name__)


def should_use_rag(question: str) -> bool:
    """
    Quick check if question benefits from RAG.
    Skips RAG for general questions Phi can handle.
    
    Args:
        question: Student's question
        
    Returns:
        True if RAG might help, False to skip
    """
    if not question or len(question.strip()) < 5:
        return False
    
    question_lower = question.lower().strip()
    
    # Skip for greetings/general
    general_patterns = [
        "hello", "hi", "hey", "thanks", "thank you", "what can you",
        "who are you", "what is your name", "help me", "can you help"
    ]
    if any(pattern in question_lower for pattern in general_patterns):
        return False
    
    if len(question.split()) < 4:
        curriculum_terms = [
            "function", "variable", "class", "method", "algorithm",
            "syntax", "loop", "array", "string", "integer",
            "grammar", "sentence", "paragraph", "essay",
            "equation", "formula", "theorem", "proof"
        ]
        if not any(term in question_lower for term in curriculum_terms):
            return False
    

    curriculum_indicators = [
        "what is", "how does", "explain", "define", "describe",
        "chapter", "lesson", "topic", "concept", "subject"
    ]
    
    if any(indicator in question_lower for indicator in curriculum_indicators):
        return True
    
    return len(question.split()) > 10


def get_context_with_timeout(
    rag_engine,
    question: str,
    subject: str,
    grade: str,
    timeout_seconds: float = 2.0
) -> Tuple[str, str]:
    """
    Get RAG context with timeout.
    
    Args:
        rag_engine: RAGRetrievalEngine instance
        question: Question text
        subject: Subject filter
        grade: Grade filter
        timeout_seconds: Max wait time
        
    Returns:
        (context_string, source_info)
    """
    if not rag_engine:
        return "", "AI Knowledge"
    
    if not should_use_rag(question):
        return "", "AI Knowledge"
    
    try:
        result_container = [None]
        error_container = [None]
        
        def do_query():
            try:
                res = rag_engine.query(
                    query_text=question,
                    subject=subject,
                    grade=grade,
                    n_results=3
                )
                result_container[0] = res
            except Exception as e:
                error_container[0] = e
        
        thread = threading.Thread(target=do_query)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout_seconds)
        
        
        if thread.is_alive():
            logger.debug(f"RAG timeout after {timeout_seconds}s")
            return "", "AI Knowledge (timeout)"
        
        if error_container[0]:
            logger.debug(f"RAG error: {error_container[0]}")
            return "", "AI Knowledge (error)"
        
        result = result_container[0]
        if not result:
            return "", "AI Knowledge"
        
        
        context_texts = result.get('context_used', [])
        if context_texts:
            context = "\n\n".join(context_texts[:2])  # Max 2 chunks
            context = context[:600]  # Limit size
            return context, "RAG Context"
        
        return "", "AI Knowledge"
        
    except Exception as e:
        logger.debug(f"RAG retrieval failed: {e}")
        return "", "AI Knowledge"


def validate_context_relevance(question: str, context: str) -> bool:
    """
    Check if context is relevant to question.
    
    Args:
        question: Original question
        context: RAG context
        
    Returns:
        True if relevant
    """
    if not context or len(context.strip()) < 20:
        return False
    
    question_lower = question.lower()
    context_lower = context.lower()
    question_words = set(word for word in question_lower.split() if len(word) > 3)
    

    overlap_count = sum(1 for word in question_words if word in context_lower)
    if overlap_count >= 2:
        return True
    
   
    long_words = [w for w in question_words if len(w) > 5]
    if any(word in context_lower for word in long_words):
        return True
    
    return False


# Import threading for timeout
import threading