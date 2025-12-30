"""
Custom ASCII Diagram Generator

Pure Python generator that creates ASCII diagrams using box-drawing characters.
No external dependencies - uses only standard library.
Fully adaptive and handles real-world edge cases with dynamic sizing.
"""

import re
from typing import Dict, Optional, List, Tuple

# Common stopwords for text processing
STOPWORDS = {
    "the", "is", "are", "a", "an", "to", "of", "and", "or", "for", "in", "on", "at", "by", "that",
    "this", "it", "as", "be", "with", "from", "into", "their", "its", "they", "them", "can", "will",
    "about", "how", "what", "why", "which", "who", "whose", "when", "where", "than", "then", "also"
}


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


def _calculate_adaptive_limits(content_length: int, num_items: int) -> Tuple[int, int]:
    """
    Calculate adaptive limits based on content size and number of items.
    Handles edge cases: very short/long content, many/few items.
    
    Args:
        content_length: Length of content text
        num_items: Number of items to display
    
    Returns:
        Tuple of (max_items, max_item_length)
    """
    # Adaptive max items based on content complexity
    if content_length < 100:
        max_items = min(num_items, 3)  # Short content: max 3 items
    elif content_length < 500:
        max_items = min(num_items, 5)  # Medium content: max 5 items
    elif content_length < 2000:
        max_items = min(num_items, 8)  # Long content: max 8 items
    else:
        max_items = min(num_items, 10)  # Very long: max 10 items
    
    # Adaptive item length based on number of items
    if num_items <= 3:
        max_item_length = 25  # Few items: can be longer
    elif num_items <= 5:
        max_item_length = 18  # Medium: moderate length
    elif num_items <= 8:
        max_item_length = 15  # Many items: shorter
    else:
        max_item_length = 12  # Very many: very short
    
    return max_items, max_item_length


def extract_steps_from_answer(answer: str) -> List[str]:
    """
    Extract steps or stages from the answer text using multiple strategies.
    Fully adaptive - handles various formats and edge cases.
    
    Args:
        answer: Answer text
    
    Returns:
        List of step descriptions (cleaned and shortened adaptively)
    """
    if not answer or len(answer.strip()) < 10:
        return []
    
    steps = []
    answer_lower = answer.lower()
    
    # Strategy 1: Numbered steps (most reliable) - multiple patterns
    numbered_patterns = [
        r'(?:^|\n)\s*(\d+)[\.\)]\s+(.+?)(?=\n\s*\d+[\.\)]|\n\n|$)',  # "1. Step text"
        r'(?:step|stage|phase|part)\s+(\d+)[:\.]\s*(.+?)(?=\n|\.|$)',  # "Step 1: text"
        r'(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|1st|2nd|3rd|4th|5th)[\s:,]+(.+?)(?=\n|\.|$)',  # "First, text"
    ]
    
    for pattern in numbered_patterns:
        matches = re.findall(pattern, answer, re.IGNORECASE | re.MULTILINE)
        if matches:
            for match in matches:
                # Handle tuple matches (number + text) or single matches
                if isinstance(match, tuple):
                    step_text = match[-1].strip()  # Take last element (the text)
                else:
                    step_text = match.strip()
                
                if step_text and len(step_text) > 3:
                    # Extract meaningful content
                    cleaned = _extract_meaningful_phrase(step_text)
                    if cleaned and cleaned not in steps:
                        steps.append(cleaned)
            
            if steps:
                break  # Found numbered steps, use them
    
    # Strategy 2: Sequential markers (then, next, after, etc.)
    if not steps:
        sequential_patterns = [
            r'(?:then|next|after|following|subsequently)[\s,]+(.+?)(?=\n|\.|,|$)',
            r'(?:finally|lastly|ultimately)[\s,]+(.+?)(?=\n|\.|$)',
        ]
        
        for pattern in sequential_patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            if matches:
                for match in matches[:10]:  # Limit to prevent too many
                    cleaned = _extract_meaningful_phrase(match.strip())
                    if cleaned and cleaned not in steps:
                        steps.append(cleaned)
                if len(steps) >= 3:  # Found enough sequential steps
                    break
    
    # Strategy 3: Action verbs indicating processes
    if not steps:
        action_patterns = [
            r'(\w+(?:\s+\w+){0,2})\s+(?:absorbs|converts|produces|creates|splits|releases|utilizes|transforms|changes|becomes)',
            r'(\w+(?:\s+\w+){0,2})\s+(?:uses|utilizes|applies|performs|executes)',
            r'(?:the|a|an)\s+(\w+(?:\s+\w+){0,1})\s+(?:process|stage|phase|step|action)',
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            if matches:
                for match in matches[:8]:
                    words = match.split()
                    words = [w for w in words if w.lower() not in STOPWORDS]
                    if words:
                        step = ' '.join(words[:4]).capitalize()
                        if len(step) >= 3 and step not in steps:
                            steps.append(step)
                if steps:
                    break
    
    # Strategy 4: Bullet points or list items
    if not steps:
        bullet_patterns = [
            r'^\s*[-•*]\s+(.+?)(?=\n|$)',  # Bullet points
            r'^\s*[○●]\s+(.+?)(?=\n|$)',  # Circle bullets
        ]
        
        for pattern in bullet_patterns:
            matches = re.findall(pattern, answer, re.MULTILINE | re.IGNORECASE)
            if matches:
                for match in matches[:10]:
                    cleaned = _extract_meaningful_phrase(match.strip())
                    if cleaned and cleaned not in steps:
                        steps.append(cleaned)
                if steps:
                    break
    
    # Adaptive cleaning and truncation
    max_items, max_length = _calculate_adaptive_limits(len(answer), len(steps))
    cleaned_steps = []
    
    for step in steps[:max_items]:
        # Remove filler words
        step = re.sub(r'\b(?:' + '|'.join(STOPWORDS) + r')\b', '', step, flags=re.IGNORECASE)
        step = ' '.join(step.split())  # Normalize whitespace
        
        # Adaptive truncation
        if len(step) > max_length:
            step = _truncate_at_word_boundary(step, max_length)
        
        if step and len(step) >= 2:  # Minimum 2 chars
            cleaned_steps.append(step)
    
    return cleaned_steps


def _extract_meaningful_phrase(text: str) -> str:
    """Extract meaningful phrase from text, removing filler words."""
    if not text:
        return ""
    
    words = text.split()
    # Take first 4-6 words, skipping stopwords
    meaningful = [w for w in words[:6] if w.lower() not in STOPWORDS and len(w) > 1]
    
    if not meaningful:
        # If all words are stopwords, take first 3 words anyway
        meaningful = words[:3]
    
    result = ' '.join(meaningful)
    return result.strip()


def _truncate_at_word_boundary(text: str, max_length: int) -> str:
    """Truncate text at word boundary, preserving meaning."""
    if len(text) <= max_length:
        return text
    
    words = text.split()
    truncated = []
    
    for word in words:
        potential = ' '.join(truncated + [word])
        if len(potential) <= max_length - 3:  # Leave room for "..."
            truncated.append(word)
        else:
            break
    
    result = ' '.join(truncated) if truncated else text[:max_length - 3]
    
    # Add ellipsis if truncated
    if len(result) < len(text):
        result += "..."
    
    return result


def has_decision_points(answer: str) -> bool:
    """Check if answer contains decision/conditional logic."""
    decision_keywords = [
        "if", "else", "condition", "decision", "check",
        "whether", "depending", "based on"
    ]
    return any(kw in answer.lower() for kw in decision_keywords)


def _calculate_box_dimensions(steps: List[str]) -> Tuple[int, int]:
    """
    Calculate adaptive box dimensions based on step content.
    Handles edge cases: very long steps, many steps, short steps.
    
    Args:
        steps: List of step texts
    
    Returns:
        Tuple of (box_width, content_width)
    """
    if not steps:
        return 15, 13  # Default
    
    # Find longest step
    max_step_len = max(len(step) for step in steps) if steps else 0
    
    # Adaptive width calculation
    if max_step_len <= 10:
        content_width = 10
        box_width = content_width + 4
    elif max_step_len <= 15:
        content_width = 15
        box_width = content_width + 4
    elif max_step_len <= 20:
        content_width = 20
        box_width = content_width + 4
    elif max_step_len <= 30:
        content_width = 30
        box_width = content_width + 4
    else:
        # Very long steps: cap at reasonable size
        content_width = 35
        box_width = content_width + 4
    
    # Adjust based on number of steps (more steps = narrower to fit)
    if len(steps) > 8:
        content_width = min(content_width, 18)
        box_width = content_width + 4
    elif len(steps) > 5:
        content_width = min(content_width, 22)
        box_width = content_width + 4
    
    return box_width, content_width


def generate_step_based_flowchart(steps: List[str]) -> str:
    """
    Generate adaptive flowchart from extracted steps.
    Box sizes adjust automatically based on content.
    
    Args:
        steps: List of step descriptions (already cleaned)
    
    Returns:
        ASCII flowchart string
    """
    if not steps:
        return _generate_minimal_flowchart()
    
    # Calculate adaptive dimensions
    box_width, content_width = _calculate_box_dimensions(steps)
    
    # Format steps with adaptive truncation
    formatted_steps = []
    for step in steps:
        step = step.strip()
        # Truncate if needed
        if len(step) > content_width:
            step = _truncate_at_word_boundary(step, content_width)
        
        # Capitalize first letter
        if step:
            step = step[0].upper() + step[1:] if len(step) > 1 else step.upper()
        
        formatted_steps.append(step)
    
    # Generate box drawing characters based on width
    top_left = "┌"
    top_right = "┐"
    bottom_left = "└"
    bottom_right = "┘"
    horizontal = "─"
    vertical = "│"
    down_arrow = "▼"
    connector = "┬"
    
    lines = []
    
    # Start box (adaptive width)
    start_label = "Start"
    start_box_width = max(len(start_label) + 2, box_width)
    lines.append(top_left + horizontal * (start_box_width - 2) + top_right)
    lines.append(vertical + start_label.center(start_box_width - 2) + vertical)
    lines.append(bottom_left + horizontal * ((start_box_width - 2) // 2) + connector + horizontal * ((start_box_width - 2) // 2) + bottom_right)
    lines.append(" " * ((start_box_width - 2) // 2) + vertical)
    
    # Steps with adaptive boxes
    for i, step in enumerate(formatted_steps):
        # Center step text in box
        step_padded = step.center(content_width)
        
        lines.append(" " * ((start_box_width - 2) // 2) + top_left + horizontal * (content_width - 2) + top_right)
        lines.append(" " * ((start_box_width - 2) // 2) + vertical + step_padded + vertical)
        lines.append(" " * ((start_box_width - 2) // 2) + bottom_left + horizontal * (content_width - 2) + bottom_right)
        
        if i < len(formatted_steps) - 1:
            lines.append(" " * ((start_box_width - 2) // 2) + vertical)
    
    # End box
    end_label = "Complete"
    end_box_width = max(len(end_label) + 2, box_width)
    lines.append(" " * ((start_box_width - 2) // 2) + top_left + horizontal * (end_box_width - 2) + top_right)
    lines.append(" " * ((start_box_width - 2) // 2) + vertical + end_label.center(end_box_width - 2) + vertical)
    lines.append(" " * ((start_box_width - 2) // 2) + bottom_left + horizontal * (end_box_width - 2) + bottom_right)
    
    return "\n".join(lines)


def _generate_minimal_flowchart() -> str:
    """Generate minimal flowchart for edge cases."""
    return """┌──────┐
│Start │
└──┬───┘
   │
┌──▼───┐
│Step 1│
└──┬───┘
   │
┌──▼───┐
│ End  │
└──────┘"""


def generate_decision_flowchart(context: Dict[str, any]) -> str:
    """
    Generate adaptive decision flowchart based on context.
    Extracts actual conditions and paths from answer.
    """
    answer = context.get("answer", "")
    conditions = context.get("conditions", [])
    
    # Extract condition text if available
    condition_text = "Condition Check"
    if conditions:
        condition_text = conditions[0]
        if len(condition_text) > 20:
            condition_text = _truncate_at_word_boundary(condition_text, 20)
    else:
        # Try to extract from answer
        cond_match = re.search(r'(?:if|when|whether)\s+([^,\.]+?)(?:,|\.|then)', answer, re.IGNORECASE)
        if cond_match:
            condition_text = cond_match.group(1).strip()
            if len(condition_text) > 20:
                condition_text = _truncate_at_word_boundary(condition_text, 20)
    
    # Extract path labels if available
    path_a = "Path A"
    path_b = "Path B"
    
    # Calculate adaptive box width
    max_label_len = max(len(condition_text), len(path_a), len(path_b), 10)
    content_width = min(max(max_label_len + 2, 12), 25)
    box_width = content_width + 4
    
    lines = []
    
    # Start
    lines.append("┌" + "─" * (box_width - 2) + "┐")
    lines.append("│" + "Start".center(box_width - 2) + "│")
    lines.append("└" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 2) + "┘")
    lines.append(" " * ((box_width - 2) // 2) + "│")
    
    # Condition box
    lines.append(" " * ((box_width - 2) // 2) + "┌" + "─" * (box_width - 2) + "┐")
    lines.append(" " * ((box_width - 2) // 2) + "│" + condition_text.center(box_width - 2) + "│")
    lines.append(" " * ((box_width - 2) // 2) + "└" + "─" * ((box_width - 2) // 4) + "┬" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 4) + "┘")
    
    # Decision branches
    indent_yes = " " * ((box_width - 2) // 2 - 2)
    indent_no = " " * ((box_width - 2) // 2 + (box_width - 2) // 2)
    
    lines.append(indent_yes + "Yes│" + " " * ((box_width - 2) // 2) + "│No")
    lines.append(indent_yes + "   │" + " " * ((box_width - 2) // 2) + "│")
    
    # Path boxes
    path_box_width = min(box_width - 4, 15)
    lines.append(indent_yes + "┌" + "─" * (path_box_width - 2) + "┐" + " " * 2 + "┌" + "─" * (path_box_width - 2) + "┐")
    lines.append(indent_yes + "│" + path_a.center(path_box_width - 2) + "│" + " " * 2 + "│" + path_b.center(path_box_width - 2) + "│")
    lines.append(indent_yes + "└" + "─" * (path_box_width - 2) + "┘" + " " * 2 + "└" + "─" * (path_box_width - 2) + "┘")
    lines.append(indent_yes + "   │" + " " * ((box_width - 2) // 2) + "│")
    lines.append(indent_yes + "   └" + "─" * ((box_width - 2) // 2) + "─" + "┘")
    lines.append(indent_yes + "     │")
    
    # Continue
    lines.append(indent_yes + "     ┌" + "─" * (box_width - 2) + "┐")
    lines.append(indent_yes + "     │" + "Continue".center(box_width - 2) + "│")
    lines.append(indent_yes + "     └" + "─" * (box_width - 2) + "┘")
    
    return "\n".join(lines)


def generate_generic_process_flowchart(context: Dict[str, any]) -> str:
    """
    Generate adaptive generic process flowchart.
    Uses context to determine number of steps and labels.
    """
    num_steps = context.get("num_steps", 3)
    answer = context.get("answer", "")
    
    # Try to extract step count from answer if not provided
    if num_steps == 3 and answer:
        step_count = len(re.findall(r'\b(?:step|stage|phase|part)\s+\d+', answer, re.IGNORECASE))
        if step_count > 0:
            num_steps = min(step_count, 6)  # Cap at 6 for readability
    
    # Adaptive step count (handle edge cases)
    num_steps = max(2, min(num_steps, 6))  # Between 2 and 6 steps
    
    # Generate steps
    steps = []
    for i in range(1, num_steps + 1):
        steps.append(f"Step {i}")
    
    return generate_step_based_flowchart(steps)


def generate_for_loop_flowchart(context: Dict[str, any]) -> str:
    """Generate adaptive flowchart for for loop."""
    variables = context.get("variables", [])
    var_name = variables[0] if variables else "item"
    
    # Adaptive box sizing
    box_width = 18
    content_width = 14
    
    lines = []
    lines.append("┌" + "─" * (box_width - 2) + "┐")
    lines.append("│" + "Start".center(box_width - 2) + "│")
    lines.append("└" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 2) + "┘")
    lines.append(" " * ((box_width - 2) // 2) + "│")
    
    init_text = f"Init {var_name[:8]}"
    lines.append(" " * ((box_width - 2) // 2) + "┌" + "─" * (box_width - 2) + "┐")
    lines.append(" " * ((box_width - 2) // 2) + "│" + init_text.center(box_width - 2) + "│")
    lines.append(" " * ((box_width - 2) // 2) + "└" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 2) + "┘")
    lines.append(" " * ((box_width - 2) // 2) + " " * ((box_width - 2) // 2) + "│")
    
    cond_text = "Check Condition"
    lines.append(" " * ((box_width - 2) // 2) + " " * ((box_width - 2) // 2) + "┌" + "─" * (box_width - 2) + "┐")
    lines.append(" " * ((box_width - 2) // 2) + " " * ((box_width - 2) // 2) + "│" + cond_text.center(box_width - 2) + "│")
    lines.append(" " * ((box_width - 2) // 2) + " " * ((box_width - 2) // 2) + "└" + "─" * ((box_width - 2) // 4) + "┬" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 4) + "┘")
    
    indent_yes = " " * ((box_width - 2) // 2) + " " * ((box_width - 2) // 2 - 1)
    lines.append(indent_yes + "Yes│" + " " * ((box_width - 2) // 2) + "│No")
    lines.append(indent_yes + "   │" + " " * ((box_width - 2) // 2) + "│")
    
    lines.append(indent_yes + "┌" + "─" * 8 + "┐" + " " * 2 + "┌" + "─" * 8 + "┐")
    lines.append(indent_yes + "│" + "Body".center(8) + "│" + " " * 2 + "│" + "Exit".center(8) + "│")
    lines.append(indent_yes + "└" + "─" * 4 + "┬" + "─" * 4 + "┘" + " " * 2 + "└" + "─" * 8 + "┘")
    lines.append(indent_yes + "   │")
    
    update_text = "Update"
    lines.append(indent_yes + "   ┌" + "─" * (box_width - 2) + "┐")
    lines.append(indent_yes + "   │" + update_text.center(box_width - 2) + "│")
    lines.append(indent_yes + "   └" + "─" * ((box_width - 2) // 2) + "┘")
    lines.append(indent_yes + "     │")
    lines.append(indent_yes + "     └───► (loop)")
    
    return "\n".join(lines)


def generate_while_loop_flowchart(context: Dict[str, any]) -> str:
    """Generate adaptive flowchart for while loop."""
    # Similar structure but condition check comes first
    box_width = 18
    
    lines = []
    lines.append("┌" + "─" * (box_width - 2) + "┐")
    lines.append("│" + "Start".center(box_width - 2) + "│")
    lines.append("└" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 2) + "┘")
    lines.append(" " * ((box_width - 2) // 2) + "│")
    
    cond_text = "Check Condition"
    lines.append(" " * ((box_width - 2) // 2) + "┌" + "─" * (box_width - 2) + "┐")
    lines.append(" " * ((box_width - 2) // 2) + "│" + cond_text.center(box_width - 2) + "│")
    lines.append(" " * ((box_width - 2) // 2) + "└" + "─" * ((box_width - 2) // 4) + "┬" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 4) + "┘")
    
    indent_true = " " * ((box_width - 2) // 2 - 1)
    lines.append(indent_true + "True│" + " " * ((box_width - 2) // 2) + "│False")
    lines.append(indent_true + "    │" + " " * ((box_width - 2) // 2) + "│")
    
    lines.append(indent_true + "┌" + "─" * 10 + "┐" + " " * 2 + "┌" + "─" * 8 + "┐")
    lines.append(indent_true + "│" + "Body".center(10) + "│" + " " * 2 + "│" + "Exit".center(8) + "│")
    lines.append(indent_true + "└" + "─" * 5 + "┬" + "─" * 5 + "┘" + " " * 2 + "└" + "─" * 8 + "┘")
    lines.append(indent_true + "    │")
    
    update_text = "Update"
    lines.append(indent_true + "    ┌" + "─" * (box_width - 2) + "┐")
    lines.append(indent_true + "    │" + update_text.center(box_width - 2) + "│")
    lines.append(indent_true + "    └" + "─" * ((box_width - 2) // 2) + "┘")
    lines.append(indent_true + "      │")
    lines.append(indent_true + "      └───► (loop)")
    
    return "\n".join(lines)


def generate_structure_diagram(context: Dict[str, any]) -> Optional[str]:
    """
    Generate adaptive structure diagram based on context.
    Fully extracts components and adapts to content.
    
    Args:
        context: Dictionary with structure information
    
    Returns:
        ASCII structure diagram string
    """
    answer = context.get("answer", "")
    question = context.get("question", "")
    components = context.get("components", [])
    
    # Extract structure components if not provided
    if not components:
        components = extract_structure_components(answer, question)
    
    # If we found components, use them
    if components:
        return generate_component_structure(components)
    
    # Fallback: try to extract from answer structure
    if answer:
        # Look for hierarchical indicators
        hierarchy_match = re.search(r'(?:top|upper|highest|main).*?(?:level|layer|tier)', answer, re.IGNORECASE)
        if hierarchy_match:
            # Try to extract 3-level hierarchy
            levels = ["Top Level", "Middle Level", "Bottom Level"]
            return generate_component_structure(levels)
    
    # Minimal fallback
    return _generate_minimal_structure()


def extract_structure_components(answer: str, question: str) -> List[str]:
    """
    Extract structure components from answer using multiple strategies.
    Fully adaptive - handles various formats and edge cases.
    
    Args:
        answer: Answer text
        question: Question text
    
    Returns:
        List of component names (adaptively limited)
    """
    if not answer:
        return []
    
    components = []
    answer_lower = answer.lower()
    combined_text = f"{question} {answer}".lower()
    
    # Strategy 1: Explicit component lists ("consists of X, Y, Z")
    component_patterns = [
        r'(?:consists|composed|made)\s+of\s+([^\.]+?)(?:\.|$)',
        r'(?:has|contains|includes|comprises)\s+([^\.]+?)(?:\.|$)',
        r'(?:components?|parts?|elements?)\s+(?:are|is|include|consist of)\s+([^\.]+?)(?:\.|$)',
    ]
    
    for pattern in component_patterns:
        matches = re.findall(pattern, answer, re.IGNORECASE)
        if matches:
            for match in matches:
                # Split by commas, semicolons, "and", "or"
                parts = re.split(r'[,;]\s*|\s+and\s+|\s+or\s+', match)
                for part in parts:
                    part = part.strip()
                    # Extract meaningful component name
                    words = part.split()
                    # Take first 2-3 meaningful words
                    meaningful = [w for w in words[:3] if w.lower() not in STOPWORDS]
                    if meaningful:
                        comp = ' '.join(meaningful).capitalize()
                        if len(comp) >= 2 and comp not in components:
                            components.append(comp)
            if components:
                break
    
    # Strategy 2: Named entities (capitalized words often indicate components)
    if not components:
        # Find capitalized phrases (likely proper nouns or important terms)
        capitalized = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', answer)
        for cap in capitalized[:10]:  # Limit to prevent too many
            if len(cap) >= 3 and cap.lower() not in STOPWORDS:
                components.append(cap)
    
    # Strategy 3: Generic component indicators
    if not components:
        generic_patterns = [
            r'(?:element|item|part|component|piece|section)\s+(\d+)',
            r'(?:first|second|third|fourth|fifth)\s+(?:component|part|element)\s+is\s+([^\.]+?)(?:\.|$)',
        ]
        
        for pattern in generic_patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            if matches:
                for match in matches[:5]:
                    if isinstance(match, tuple):
                        match = match[-1]
                    comp = str(match).strip().capitalize()
                    if comp and comp not in components:
                        components.append(comp)
                if components:
                    break
    
    # Strategy 4: Extract from question if answer doesn't have components
    if not components and question:
        # Look for "what are the parts of X" -> extract X
        question_components = re.findall(r'(?:parts?|components?|elements?)\s+of\s+(\w+)', question, re.IGNORECASE)
        if question_components:
            components.extend([c.capitalize() for c in question_components[:3]])
    
    # Adaptive limiting based on content
    max_items, _ = _calculate_adaptive_limits(len(answer), len(components))
    return components[:max_items]


def generate_component_structure(components: List[str]) -> str:
    """
    Generate adaptive structure diagram from components.
    Handles edge cases: single component, many components, long names.
    """
    if not components:
        return _generate_minimal_structure()
    
    # Calculate adaptive dimensions
    max_comp_len = max(len(comp) for comp in components) if components else 0
    content_width = max(12, min(max_comp_len + 2, 30))  # Adaptive width
    box_width = content_width + 4
    
    # Format components with adaptive truncation
    formatted = []
    for comp in components:
        if len(comp) > content_width:
            comp = _truncate_at_word_boundary(comp, content_width)
        formatted.append(comp)
    
    lines = []
    
    # Handle different structure types based on number of components
    if len(formatted) == 1:
        # Single component - simple box
        lines.append("┌" + "─" * (box_width - 2) + "┐")
        lines.append("│" + formatted[0].center(box_width - 2) + "│")
        lines.append("└" + "─" * (box_width - 2) + "┘")
    elif len(formatted) == 2:
        # Two components - parent-child
        lines.append("┌" + "─" * (box_width - 2) + "┐")
        lines.append("│" + formatted[0].center(box_width - 2) + "│")
        lines.append("└" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 2) + "┘")
        lines.append(" " * ((box_width - 2) // 2) + "│")
        lines.append(" " * ((box_width - 2) // 2) + "┌" + "─" * (box_width - 2) + "┐")
        lines.append(" " * ((box_width - 2) // 2) + "│" + formatted[1].center(box_width - 2) + "│")
        lines.append(" " * ((box_width - 2) // 2) + "└" + "─" * (box_width - 2) + "┘")
    else:
        # Multiple components - hierarchical
        # Top level
        lines.append("┌" + "─" * (box_width - 2) + "┐")
        lines.append("│" + formatted[0].center(box_width - 2) + "│")
        lines.append("└" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 2) + "┘")
        lines.append(" " * ((box_width - 2) // 2) + "│")
        
        # Middle levels
        for comp in formatted[1:-1]:
            lines.append(" " * ((box_width - 2) // 2) + "┌" + "─" * (box_width - 2) + "┐")
            lines.append(" " * ((box_width - 2) // 2) + "│" + comp.center(box_width - 2) + "│")
            lines.append(" " * ((box_width - 2) // 2) + "└" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 2) + "┘")
            lines.append(" " * ((box_width - 2) // 2) + " " * ((box_width - 2) // 2) + "│")
        
        # Bottom level
        if len(formatted) > 1:
            indent = " " * ((box_width - 2) // 2) * (len(formatted) - 1)
            lines.append(indent + "┌" + "─" * (box_width - 2) + "┐")
            lines.append(indent + "│" + formatted[-1].center(box_width - 2) + "│")
            lines.append(indent + "└" + "─" * (box_width - 2) + "┘")
    
    return "\n".join(lines)


def _generate_minimal_structure() -> str:
    """Generate minimal structure for edge cases."""
    return """┌────────┐
│Component│
└─────────┘"""


def generate_process_diagram(context: Dict[str, any]) -> Optional[str]:
    """
    Generate adaptive process diagram based on context.
    Fully extracts and adapts to actual content from answer.
    
    Args:
        context: Dictionary with process information
    
    Returns:
        ASCII process diagram string
    """
    answer = context.get("answer", "")
    question = context.get("question", "")
    
    # Extract steps from answer (adaptive extraction)
    steps = extract_steps_from_answer(answer)
    
    # If we found steps, use them (already adaptive)
    if steps:
        return generate_step_based_flowchart(steps)
    
    # Fallback: estimate steps from context
    num_steps = context.get("num_steps", 3)
    
    # Try to estimate from answer structure if num_steps is default
    if num_steps == 3 and answer:
        # Count sequential indicators
        sequential_count = len(re.findall(
            r'\b(first|second|third|fourth|fifth|sixth|then|next|after|finally)', 
            answer, re.IGNORECASE
        ))
        if sequential_count > 0:
            num_steps = min(sequential_count + 1, 6)  # +1 for initial step
    
    # Generate generic steps (adaptive count)
    num_steps = max(2, min(num_steps, 6))  # Between 2 and 6
    generic_steps = [f"Step {i}" for i in range(1, num_steps + 1)]
    
    return generate_step_based_flowchart(generic_steps)

