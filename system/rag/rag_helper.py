"""
RAG Helper Utilities

Non-blocking RAG retrieval with timeout and smart skipping.
Optimized for fast answer generation while still benefiting from RAG when available.
"""

import logging
import threading
import time
from typing import Optional, Dict, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

logger = logging.getLogger(__name__)


def should_use_rag(question: str) -> bool:
    """
    Quick check if question is likely to benefit from RAG.
    Skips RAG for general/conversational questions that Phi can handle well.
    
    Args:
        question: Student's question
        
    Returns:
        True if RAG might help, False to skip RAG and use Phi's knowledge
    """
    if not question or len(question.strip()) < 5:
        return False
    
    question_lower = question.lower().strip()
    
    # Skip RAG for very general questions
    general_patterns = [
        "hello", "hi", "hey", "thanks", "thank you", "what can you",
        "who are you", "what is your name", "help me", "can you help"
    ]
    if any(pattern in question_lower for pattern in general_patterns):
        return False
    
    # Skip RAG for very short questions (likely general knowledge)
    if len(question.split()) < 4:
        # Unless it contains curriculum-specific terms
        curriculum_terms = [
            "function", "variable", "class", "method", "algorithm",
            "syntax", "loop", "array", "string", "integer",
            "grammar", "sentence", "paragraph", "essay",
            "equation", "formula", "theorem", "proof"
        ]
        if not any(term in question_lower for term in curriculum_terms):
            return False
    
    # Use RAG for curriculum-specific questions
    curriculum_indicators = [
        "what is", "how does", "explain", "define", "describe",
        "chapter", "lesson", "topic", "concept", "subject"
    ]
    
    # If question has curriculum indicators, likely needs RAG
    if any(indicator in question_lower for indicator in curriculum_indicators):
        return True
    
    # Default: use RAG for questions longer than 10 words (likely specific)
    return len(question.split()) > 10


def retrieve_rag_with_timeout(
    rag_engine,
    question: str,
    timeout_seconds: float = 2.0,
    max_results: int = 2
) -> Optional[Dict]:
    """
    Retrieve RAG content with timeout to prevent blocking.
    
    Args:
        rag_engine: RAGRetrievalEngine instance
        question: Search query
        timeout_seconds: Maximum time to wait (default 2 seconds)
        max_results: Maximum results to return
        
    Returns:
        RAG results dict or None if timeout/error
    """
    if not rag_engine:
        return None
    
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                rag_engine.retrieve_relevant_content,
                question,
                max_results
            )
            return future.result(timeout=timeout_seconds)
    except FuturesTimeoutError:
        logger.debug(f"RAG retrieval timed out after {timeout_seconds}s for: {question[:50]}")
        return None
    except Exception as e:
        logger.debug(f"RAG retrieval error: {e}")
        return None


def validate_rag_relevance(question: str, rag_results: Dict) -> Tuple[bool, Optional[str]]:
    """
    Validate if RAG results are actually relevant to the question.
    
    Args:
        question: Original question
        rag_results: RAG retrieval results
        
    Returns:
        (is_relevant, context_string) - context_string is None if not relevant
    """
    if not rag_results or not rag_results.get('chunks'):
        return False, None
    
    question_lower = question.lower()
    question_words = set(word for word in question_lower.split() if len(word) > 3)
    
    chunks = rag_results['chunks'][:2]
    relevant_chunks = []
    
    for chunk in chunks:
        chunk_content = chunk.get('content', '').lower()
        chunk_words = set(word for word in chunk_content.split() if len(word) > 3)
        
        # Check word overlap
        overlap = len(question_words.intersection(chunk_words))
        
        # Require at least 2 meaningful word overlaps OR one long word match
        if overlap >= 2 or any(word in chunk_content for word in question_words if len(word) > 5):
            relevant_chunks.append(chunk)
    
    if not relevant_chunks:
        return False, None
    
    # Combine relevant chunks
    context = "\n\n".join([ch['content'] for ch in relevant_chunks])
    context = context[:600]  # Limit context size
    
    return True, context


def get_context_non_blocking(
    rag_engine,
    question: str,
    content_manager=None,
    timeout_seconds: float = 2.0
) -> Tuple[Optional[str], str]:
    """
    Get context for answer generation using non-blocking RAG.
    Always returns quickly - either with RAG context, structured content, or general knowledge.
    
    Strategy:
    1. Quick check if RAG is worth trying
    2. Start RAG in parallel (with timeout)
    3. Return RAG context if available
    4. Fallback to structured content (fast, concise - helps generation speed)
    5. Final fallback to general knowledge
    
    Args:
        rag_engine: RAGRetrievalEngine instance (can be None)
        question: Student's question
        content_manager: ContentManager for structured content fallback
        timeout_seconds: RAG timeout (default 2 seconds)
        
    Returns:
        (context, source_info) - context is None if using general knowledge
    """
    # Quick check: should we even try RAG?
    if not should_use_rag(question):
        return "", "AI General Knowledge"
    
    # Try RAG with SHORT timeout (1 second max - don't wait long)
    # If RAG takes >1s, skip it and use structured content instead
    rag_results = None
    if rag_engine:
        try:
            rag_results = retrieve_rag_with_timeout(
                rag_engine,
                question,
                timeout_seconds=1.0,  # Reduced from 2.0 - faster fallback
                max_results=2
            )
        except Exception as e:
            logger.debug(f"RAG retrieval exception: {e}")
            rag_results = None
    
    # Validate and use RAG if relevant (only if it returned quickly)
    if rag_results and rag_results.get('chunks'):
        is_relevant, rag_context = validate_rag_relevance(question, rag_results)
        if is_relevant and rag_context:
            # RAG succeeded quickly - use RAG context
            logger.debug(f"RAG found relevant content for: {question[:50]}")
            return rag_context, "RAG-enhanced content"
        else:
            logger.debug(f"RAG results not relevant for: {question[:50]}")
    elif rag_results and rag_results.get('error'):
        logger.debug(f"RAG error: {rag_results.get('error')}")
    
    # Fallback 1: Try structured content (fast, concise context helps generation speed)
    # This is faster than waiting for slow RAG
    if content_manager:
        try:
            # Quick search with limited results for fast generation
            relevant = content_manager.search_content(question, max_results=1)
            if relevant and relevant[0].get('summary'):
                # Limit to 250 chars to keep prompt short and fast
                return relevant[0]['summary'][:250], "Structured content"
        except Exception as e:
            logger.debug(f"Structured content search failed: {e}")
    
    # Fallback 2: General knowledge
    # Return empty context - Phi model will use its own knowledge based on system prompt
    return "", "AI General Knowledge"

