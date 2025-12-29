"""
Diagram Service Layer

Main service that coordinates diagram detection and generation.
Handles errors gracefully and ensures non-blocking operation.
"""

import logging
from typing import Optional

from .diagram_detector import should_generate_diagram, extract_context_for_diagram
from .custom_generator import generate_diagram
from .diagram_formatter import format_diagram
from .diagram_validator import validate_diagram

logger = logging.getLogger(__name__)


def generate_and_append_diagram(question: str, answer: str) -> str:
    """
    Generate diagram if needed and append to answer.
    
    This function is designed to be fast (<50ms) and non-blocking.
    If any step fails, it gracefully returns the original answer.
    
    Args:
        question: Student's question
        answer: Generated answer from Phi model
    
    Returns:
        Answer with diagram appended (or original answer if generation fails)
    """
    try:
        # Step 1: Detect if diagram needed (fast check)
        should_generate, diagram_type = should_generate_diagram(question, answer)
        
        if not should_generate or not diagram_type:
            return answer
        
        # Step 2: Extract context from question/answer
        context = extract_context_for_diagram(question, answer, diagram_type)
        
        # Step 3: Generate diagram
        diagram = generate_diagram(diagram_type, context)
        
        if not diagram:
            logger.debug("Diagram generation returned None")
            return answer
        
        # Step 4: Validate diagram
        is_valid, error_msg = validate_diagram(diagram)
        if not is_valid:
            logger.debug(f"Diagram validation failed: {error_msg}")
            return answer
        
        # Step 5: Format diagram (lightweight cleanup)
        formatted_diagram = format_diagram(diagram)
        
        # Step 6: Append to answer
        return f"{answer}\n\nDiagram:\n{formatted_diagram}"
    
    except Exception as e:
        # Graceful fallback: return original answer on any error
        logger.debug(f"Diagram generation failed: {e}", exc_info=True)
        return answer


def should_attempt_diagram(question: str) -> bool:
    """
    Quick check if question type typically needs a diagram.
    Used for early filtering to avoid unnecessary processing.
    
    Args:
        question: Student's question
    
    Returns:
        True if diagram might be helpful, False otherwise
    """
    if not question:
        return False
    
    question_lower = question.lower()
    
    # Quick keyword check
    diagram_keywords = [
        "how does", "how do", "how is", "how can",
        "explain the process", "explain the flow",
        "what happens", "what is the flow",
        "steps", "procedure", "algorithm",
        "structure", "loop", "iteration"
    ]
    
    return any(kw in question_lower for kw in diagram_keywords)

