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
    Quick adaptive check if question type typically needs a diagram.
    Uses semantic patterns instead of hardcoded keywords.
    
    Args:
        question: Student's question
    
    Returns:
        True if diagram might be helpful, False otherwise
    """
    if not question or len(question.strip()) < 3:
        return False
    
    question_lower = question.lower()
    
    # Use semantic patterns instead of hardcoded keywords
    import re
    
    # Process/flow patterns
    process_patterns = [
        r'\b(how|what|explain|describe)\s+(do|does|is|are)\s+.*\s+(work|happen|flow|process)',
        r'\b(step|stage|phase|procedure|method|way)',
        r'\b(sequence|order|series|chain|cycle)',
    ]
    
    # Structure patterns
    structure_patterns = [
        r'\b(what|how)\s+(is|are)\s+.*\s+(structure|organization|layout|form)',
        r'\b(show|display|draw|illustrate)\s+.*\s+(structure|organization)',
        r'\b(component|part|element|piece)\s+(of|in)',
    ]
    
    # Flowchart/decision patterns
    flowchart_patterns = [
        r'\b(how|what)\s+(do|does)\s+.*\s+(decide|choose|determine)',
        r'\b(if|when|whether|condition|decision)',
        r'\b(loop|iterate|repeat|while|for)',
    ]
    
    # Check if any pattern matches
    all_patterns = process_patterns + structure_patterns + flowchart_patterns
    return any(re.search(pattern, question_lower, re.IGNORECASE) for pattern in all_patterns)

