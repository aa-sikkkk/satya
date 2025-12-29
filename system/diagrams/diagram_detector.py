"""
Diagram Type Detector

Analyzes questions and answers to determine if a diagram would help
and what type of diagram is needed.
"""

import re
import logging
from typing import Tuple, Optional, Dict

logger = logging.getLogger(__name__)


def should_generate_diagram(question: str, answer: str) -> Tuple[bool, Optional[str]]:
    """
    Determine if diagram should be generated and what type.
    
    Args:
        question: Student's question
        answer: Generated answer from Phi model
    
    Returns:
        (should_generate, diagram_type) where diagram_type is:
        - "flowchart" for loops, processes, algorithms
        - "structure" for data structures, hierarchies
        - "process" for step-by-step procedures
        - None if no diagram needed
    """
    if not question or not answer:
        return False, None
    
    question_lower = question.lower()
    answer_lower = answer.lower()
    
    # Keywords that indicate flowchart would help
    flowchart_keywords = [
        "how does", "how do", "how is", "how can",
        "explain the process", "explain the flow",
        "what happens", "what is the flow",
        "how does it work", "how do they work",
        "loop", "iteration", "iterate",
        "if else", "if-else", "conditional",
        "decision", "branch"
    ]
    
    # Keywords that indicate structure diagram would help
    structure_keywords = [
        "what is the structure", "show the structure",
        "how is it organized", "what does it look like",
        "data structure", "array", "list", "tree",
        "hierarchy", "organization"
    ]
    
    # Keywords that indicate process diagram would help
    process_keywords = [
        "steps", "procedure", "algorithm", "method",
        "step by step", "step-by-step",
        "sequence", "order", "process"
    ]
    
    # Check for flowchart indicators
    if any(kw in question_lower for kw in flowchart_keywords):
        # Additional check: if answer mentions loops, it's definitely a flowchart
        if any(term in answer_lower for term in ["loop", "iterate", "condition", "while", "for"]):
            return True, "flowchart"
        return True, "flowchart"
    
    # Check for structure indicators
    if any(kw in question_lower for kw in structure_keywords):
        return True, "structure"
    
    # Check for process indicators
    if any(kw in question_lower for kw in process_keywords):
        return True, "process"
    
    return False, None


def extract_context_for_diagram(question: str, answer: str, diagram_type: str) -> Dict[str, any]:
    """
    Extract context needed for diagram generation.
    
    Args:
        question: Student's question
        answer: Generated answer from Phi model
        diagram_type: Type of diagram to generate
    
    Returns:
        Dictionary with relevant information (variable names, conditions, etc.)
    """
    context = {
        "question": question,
        "answer": answer,
        "diagram_type": diagram_type
    }
    
    # Extract variable names from answer (common patterns)
    variable_patterns = [
        r'\b([a-z_][a-z0-9_]*)\s*=',  # Python variable assignment
        r'for\s+(\w+)\s+in',  # For loop variable
        r'while\s+(\w+)',  # While loop variable
    ]
    
    variables = set()
    for pattern in variable_patterns:
        matches = re.findall(pattern, answer, re.IGNORECASE)
        variables.update(matches)
    
    if variables:
        context["variables"] = list(variables)[:3]  # Limit to 3 most common
    
    # Extract loop types
    if "for loop" in answer.lower() or "for" in answer.lower():
        context["loop_type"] = "for"
    elif "while loop" in answer.lower() or "while" in answer.lower():
        context["loop_type"] = "while"
    
    # Extract condition mentions
    if "condition" in answer.lower():
        context["has_condition"] = True
    
    # Extract step mentions for process diagrams
    if diagram_type == "process":
        step_pattern = r'step\s+(\d+)'
        steps = re.findall(step_pattern, answer, re.IGNORECASE)
        if steps:
            context["num_steps"] = len(steps)
    
    return context

