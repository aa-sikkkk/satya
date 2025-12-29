"""
Custom ASCII Diagram Generator

Pure Python generator that creates ASCII diagrams using box-drawing characters.
No external dependencies - uses only standard library.
Context-aware and flexible for any question type.
"""

import re
from typing import Dict, Optional, List


def generate_diagram(diagram_type: str, context: Dict[str, any]) -> Optional[str]:
    """
    Generate ASCII diagram based on type and context.
    
    Args:
        diagram_type: Type of diagram ("flowchart", "structure", "process")
        context: Dictionary with relevant information
    
    Returns:
        ASCII diagram string or None if generation fails
    """
    if diagram_type == "flowchart":
        return generate_flowchart(context)
    elif diagram_type == "structure":
        return generate_structure_diagram(context)
    elif diagram_type == "process":
        return generate_process_diagram(context)
    
    return None


def generate_flowchart(context: Dict[str, any]) -> Optional[str]:
    """
    Generate flowchart diagram based on context.
    Adapts to any flowchart scenario, not just loops.
    
    Args:
        context: Dictionary with question, answer, and extracted info
    
    Returns:
        ASCII flowchart string
    """
    question = context.get("question", "").lower()
    answer = context.get("answer", "").lower()
    
    # Extract key concepts from answer
    steps = extract_steps_from_answer(answer)
    
    # If we found steps, create a step-based flowchart
    if steps and len(steps) > 0:
        return generate_step_based_flowchart(steps)
    
    # Check for decision points (if-else, conditions)
    if has_decision_points(answer):
        return generate_decision_flowchart(context)
    
    # Check for loop patterns
    loop_type = context.get("loop_type")
    if loop_type:
        if loop_type == "for":
            return generate_for_loop_flowchart(context)
        elif loop_type == "while":
            return generate_while_loop_flowchart(context)
    
    # Generic flowchart for any process
    return generate_generic_process_flowchart(context)


def extract_steps_from_answer(answer: str) -> List[str]:
    """
    Extract steps or stages from the answer text.
    Returns clean, concise step labels suitable for diagrams.
    
    Args:
        answer: Answer text
    
    Returns:
        List of step descriptions (cleaned and shortened)
    """
    steps = []
    
    # Look for numbered steps
    step_patterns = [
        r'(?:first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th)[\s,]+(.+?)(?:\.|,|$)',
        r'step\s+\d+[:\s]+(.+?)(?:\.|,|$)',
        r'\d+[\.\)]\s+(.+?)(?:\.|,|$)',
    ]
    
    for pattern in step_patterns:
        matches = re.findall(pattern, answer, re.IGNORECASE)
        if matches:
            steps.extend([m.strip() for m in matches[:5]])  # Limit to 5 steps
            break
    
    # If no numbered steps, look for key process phrases with better extraction
    if not steps:
        # Look for key actions/processes: "X absorbs Y", "X converts Y to Z", etc.
        # Focus on the SUBJECT doing the action, not the action phrase itself
        process_patterns = [
            # "Chlorophyll absorbs light" -> "Chlorophyll absorbs"
            r'(\w+(?:\s+\w+){0,2})\s+(?:absorbs|converts|produces|creates|splits|releases|utilizes)',
            # "Plants use sunlight" -> "Plants use"
            r'(\w+(?:\s+\w+){0,2})\s+(?:uses|utilizes)',
            # "The process converts X" -> "Process converts"
            r'(?:the|a|an)\s+(\w+(?:\s+\w+){0,1})\s+(?:process|stage|phase|step)',
        ]
        for pattern in process_patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            if matches:
                # Clean up matches - take meaningful subjects
                cleaned = []
                for match in matches[:4]:
                    words = match.split()
                    # Skip common filler words
                    words = [w for w in words if w.lower() not in ['the', 'a', 'an', 'is', 'are']]
                    if words:
                        # Take first 2-3 meaningful words
                        step = ' '.join(words[:3]).capitalize()
                        if len(step) >= 3 and step not in cleaned:
                            cleaned.append(step)
                if cleaned:
                    steps.extend(cleaned)
                    break
    
    # Clean and shorten steps for diagram display
    cleaned_steps = []
    for step in steps[:5]:
        # Remove common filler words
        step = re.sub(r'\b(?:the|a|an|is|are|was|were|to|of|in|on|at|for|with|by)\b', '', step, flags=re.IGNORECASE)
        step = ' '.join(step.split())  # Normalize whitespace
        
        # Truncate to reasonable length
        if len(step) > 15:
            # Try to truncate at word boundary
            words = step.split()
            truncated = []
            for word in words:
                if len(' '.join(truncated + [word])) <= 15:
                    truncated.append(word)
                else:
                    break
            step = ' '.join(truncated) if truncated else step[:12]
        
        if step and len(step) >= 3:  # Only add meaningful steps
            cleaned_steps.append(step)
    
    return cleaned_steps[:5]  # Limit to 5 steps max


def has_decision_points(answer: str) -> bool:
    """Check if answer contains decision/conditional logic."""
    decision_keywords = [
        "if", "else", "condition", "decision", "check",
        "whether", "depending", "based on"
    ]
    return any(kw in answer.lower() for kw in decision_keywords)


def generate_step_based_flowchart(steps: List[str]) -> str:
    """
    Generate flowchart from extracted steps.
    Uses proper formatting with clean labels.
    
    Args:
        steps: List of step descriptions (already cleaned)
    
    Returns:
        ASCII flowchart string
    """
    if not steps:
        return generate_generic_process_flowchart({})
    
    # Ensure steps are properly formatted for diagram boxes
    max_step_length = 18  # Box width is ~15 chars, leave margin
    formatted_steps = []
    for step in steps:
        # Clean and format step
        step = step.strip()
        if len(step) > max_step_length:
            # Truncate at word boundary
            words = step.split()
            truncated = []
            for word in words:
                if len(' '.join(truncated + [word])) <= max_step_length:
                    truncated.append(word)
                else:
                    break
            step = ' '.join(truncated) if truncated else step[:max_step_length - 3] + "..."
        
        # Capitalize first letter
        if step:
            step = step[0].upper() + step[1:] if len(step) > 1 else step.upper()
        
        formatted_steps.append(step)
    
    lines = []
    
    # Start
    lines.append("┌─────────────┐")
    lines.append("│   Start     │")
    lines.append("└──────┬──────┘")
    lines.append("       │")
    
    # Steps - format each step properly
    for i, step in enumerate(formatted_steps):
        # Pad step text to fit in box (13 chars wide)
        step_padded = step[:13].ljust(13)
        lines.append("┌──────▼──────┐")
        lines.append(f"│ {step_padded} │")
        lines.append("└──────┬──────┘")
        
        if i < len(formatted_steps) - 1:
            lines.append("       │")
    
    # End
    lines.append("┌──────▼──────┐")
    lines.append("│   Complete  │")
    lines.append("└─────────────┘")
    
    return "\n".join(lines)


def generate_decision_flowchart(context: Dict[str, any]) -> str:
    """Generate flowchart with decision point."""
    return """
┌─────────────┐
│   Start     │
└──────┬──────┘
       │
┌──────▼──────┐
│  Condition  │
│   Check     │
└──┬──────┬──┘
Yes│      │No
   │      │
┌──▼──┐ ┌─▼────┐
│Path │ │Path  │
│  A  │ │  B   │
└──┬──┘ └──┬───┘
   │       │
   └───┬───┘
       │
┌──────▼──────┐
│   Continue   │
└─────────────┘
""".strip()


def generate_generic_process_flowchart(context: Dict[str, any]) -> str:
    """Generate generic process flowchart that works for any concept."""
    return """
┌─────────────┐
│   Start     │
└──────┬──────┘
       │
┌──────▼──────┐
│   Process   │
│   Step 1    │
└──────┬──────┘
       │
┌──────▼──────┐
│   Process   │
│   Step 2    │
└──────┬──────┘
       │
┌──────▼──────┐
│   Process   │
│   Step 3    │
└──────┬──────┘
       │
┌──────▼──────┐
│   Complete  │
└─────────────┘
""".strip()


def generate_for_loop_flowchart(context: Dict[str, any]) -> str:
    """Generate flowchart for for loop."""
    return """
┌─────────────┐
│   Start     │
└──────┬──────┘
       │
┌──────▼──────┐
│ Initialize  │
│  variable   │
└──────┬──────┘
       │
┌──────▼──────┐
│  Condition  │
│   Check     │
└──┬──────┬──┘
Yes│      │No
   │      │
┌──▼──┐ ┌─▼────┐
│Body │ │ Exit │
└──┬──┘ └──────┘
   │
┌──▼──────┐
│ Update  │
└──┬──────┘
   │
   └──────┐
          │
    (loop back)
""".strip()


def generate_while_loop_flowchart(context: Dict[str, any]) -> str:
    """Generate flowchart for while loop."""
    return """
┌─────────────┐
│   Start     │
└──────┬──────┘
       │
┌──────▼──────┐
│  Condition  │
│   Check     │
└──┬──────┬──┘
True│     │False
    │     │
┌───▼──┐ ┌─▼────┐
│Body  │ │ Exit │
└───┬──┘ └──────┘
    │
┌───▼──────┐
│ Update   │
│ variable │
└───┬──────┘
    │
    └──────┐
           │
    (loop back)
""".strip()


def generate_generic_loop_flowchart(context: Dict[str, any]) -> str:
    """Generate generic loop flowchart."""
    return """
┌─────────────┐
│   Start     │
└──────┬──────┘
       │
┌──────▼──────┐
│  Condition  │
│   Check     │
└──┬──────┬──┘
Yes│      │No
   │      │
┌──▼──┐ ┌─▼────┐
│Body │ │ Exit │
└──┬──┘ └──────┘
   │
   └──────┐
          │
    (loop back)
""".strip()


def generate_structure_diagram(context: Dict[str, any]) -> Optional[str]:
    """
    Generate structure diagram based on context.
    Adapts to any structure type mentioned in the answer.
    
    Args:
        context: Dictionary with structure information
    
    Returns:
        ASCII structure diagram string
    """
    answer = context.get("answer", "").lower()
    question = context.get("question", "").lower()
    
    # Extract structure components from answer
    components = extract_structure_components(answer, question)
    
    if components:
        return generate_component_structure(components)
    
    # Generic hierarchical structure
    return """
┌─────────────┐
│   Top       │
│   Level     │
└──────┬──────┘
       │
┌──────▼──────┐
│   Middle    │
│   Level     │
└──────┬──────┘
       │
┌──────▼──────┐
│   Bottom    │
│   Level     │
└─────────────┘
""".strip()


def extract_structure_components(answer: str, question: str) -> List[str]:
    """
    Extract structure components from answer.
    
    Args:
        answer: Answer text
        question: Question text
    
    Returns:
        List of component names
    """
    components = []
    
    # Look for common structure patterns
    # Arrays, lists, etc.
    if "element" in answer or "item" in answer:
        components = ["Element 1", "Element 2", "Element 3"]
    elif "part" in answer:
        parts = re.findall(r'part\s+(\w+)', answer, re.IGNORECASE)
        if parts:
            components = [f"Part {p}" for p in parts[:3]]
    
    # Look for named components
    named_patterns = [
        r'(\w+)\s+(?:and|,)\s+(\w+)',  # "A and B"
    ]
    
    for pattern in named_patterns:
        matches = re.findall(pattern, answer)
        if matches and len(matches[0]) == 2:
            components = list(matches[0])[:3]
            break
    
    return components[:5]  # Limit to 5 components


def generate_component_structure(components: List[str]) -> str:
    """Generate structure diagram from components."""
    if not components:
        return generate_structure_diagram({})
    
    # Truncate component names
    max_length = 15
    truncated = []
    for comp in components:
        if len(comp) > max_length:
            truncated.append(comp[:max_length - 3] + "...")
        else:
            truncated.append(comp)
    
    lines = []
    
    # Top level
    lines.append("┌─────────────┐")
    lines.append(f"│{truncated[0].center(13)}│")
    lines.append("└──────┬──────┘")
    lines.append("       │")
    
    # Middle levels
    for comp in truncated[1:-1] if len(truncated) > 2 else []:
        lines.append("┌──────▼──────┐")
        lines.append(f"│{comp.center(13)}│")
        lines.append("└──────┬──────┘")
        lines.append("       │")
    
    # Bottom level
    if len(truncated) > 1:
        lines.append("┌──────▼──────┐")
        lines.append(f"│{truncated[-1].center(13)}│")
        lines.append("└─────────────┘")
    else:
        lines.append("┌──────▼──────┐")
        lines.append("│   Element   │")
        lines.append("└─────────────┘")
    
    return "\n".join(lines)


def generate_process_diagram(context: Dict[str, any]) -> Optional[str]:
    """
    Generate process diagram based on context.
    Extracts actual steps from the answer, not just generic placeholders.
    
    Args:
        context: Dictionary with process information
    
    Returns:
        ASCII process diagram string
    """
    answer = context.get("answer", "")
    question = context.get("question", "")
    
    # Extract steps from answer
    steps = extract_steps_from_answer(answer)
    
    # If we found steps, use them
    if steps:
        return generate_step_based_flowchart(steps)
    
    # Fallback to generic process
    num_steps = context.get("num_steps", 3)
    
    # Generate step-by-step process
    process_steps = []
    for i in range(1, min(num_steps + 1, 5)):  # Limit to 5 steps
        process_steps.append(f"│  Step {i}   │")
    
    if not process_steps:
        process_steps = ["│  Step 1   │", "│  Step 2   │", "│  Step 3   │"]
    
    process_lines = [
        "┌─────────────┐",
        process_steps[0],
        "└──────┬──────┘",
        "       │"
    ]
    
    for step in process_steps[1:]:
        process_lines.extend([
            "┌──────▼──────┐",
            step,
            "└──────┬──────┘",
            "       │"
        ])
    
    process_lines.extend([
        "┌──────▼──────┐",
        "│   Complete  │",
        "└─────────────┘"
    ])
    
    return "\n".join(process_lines)

