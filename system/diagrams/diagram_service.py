import logging
from typing import Optional

from .diagram_detector import should_generate_diagram, extract_context_for_diagram
from .custom_generator import generate_diagram
from .diagram_formatter import format_diagram
from .diagram_validator import validate_diagram

logger = logging.getLogger(__name__)


def generate_and_append_diagram(question: str, answer: str) -> str:
    original_answer = answer
    
    try:
        if not question or not answer or len(question.strip()) < 3 or len(answer.strip()) < 10:
            return original_answer
        
        if not should_attempt_diagram(question):
            return original_answer
        
        should_generate, diagram_type = should_generate_diagram(question, answer)
        
        if not should_generate or not diagram_type:
            return original_answer
        
        context = extract_context_for_diagram(question, answer, diagram_type)
        
        diagram = generate_diagram(diagram_type, context)
        
        if not diagram:
            logger.debug("Diagram generation returned None")
            return original_answer
        
        is_valid, error_msg = validate_diagram(diagram, context)
        if not is_valid:
            logger.debug(f"Diagram validation failed: {error_msg}")
            return original_answer
        
        formatted_diagram = format_diagram(diagram)
        
        answer_to_return = original_answer.rstrip()
        
        return f"{answer_to_return}\n\nDiagram:\n{formatted_diagram}"
    
    except Exception as e:
        logger.debug(f"Diagram generation failed: {e}", exc_info=True)
        return original_answer


def should_attempt_diagram(question: str) -> bool:
    if not question or len(question.strip()) < 3:
        return False
    
    question_lower = question.lower()
    
    import re
    
    exclusion_patterns = [
        r'\b(solve|calculate|compute|find|evaluate)\s+.*\b(equation|formula|expression|number|value)',
        r'\b(what\s+is)\s+(?!.*\b(structure|cycle|process|system|organization)\b)',
        r'\bmathematical\b',
        r'\b(add|subtract|multiply|divide|simplify)\b',
    ]
    
    for pattern in exclusion_patterns:
        if re.search(pattern, question_lower, re.IGNORECASE):
            return False
    
    process_patterns = [
        r'\b(how|what|explain|describe)\s+(do|does|is|are)\s+.*\s+(work|happen|flow|process)',
        r'\b(step|stage|phase|procedure|method|way)',
        r'\b(sequence|order|series|chain|cycle)',
    ]
    
    structure_patterns = [
        r'\b(what|how)\s+(is|are)\s+.*\s+(structure|organization|layout|form)',
        r'\b(show|display|draw|illustrate)\s+.*\s+(structure|organization)',
        r'\b(component|part|element|piece)\s+(of|in)',
    ]
    
    flowchart_patterns = [
        r'\b(how|what)\s+(do|does)\s+.*\s+(decide|choose|determine)',
        r'\b(if|when|whether|condition|decision)',
        r'\b(loop|iterate|repeat|while|for)',
    ]
    
    all_patterns = process_patterns + structure_patterns + flowchart_patterns
    return any(re.search(pattern, question_lower, re.IGNORECASE) for pattern in all_patterns)

