"""
Diagram Validator

Validates generated diagrams to ensure they are properly formatted and useful.
"""

from typing import Tuple


def validate_diagram(diagram_text: str) -> Tuple[bool, str]:
    """
    Validate diagram quality.
    
    This function performs lightweight checks to ensure the diagram
    is properly formatted and useful. Designed to be fast (<5ms).
    
    Args:
        diagram_text: Diagram text to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not diagram_text:
        return False, "Empty diagram"
    
    # Check for box-drawing characters
    box_chars = "┌┐└┘│─├┤┬┴"
    if not any(char in diagram_text for char in box_chars):
        return False, "No diagram characters detected"
    
    # Adaptive width check based on diagram size
    lines = diagram_text.split('\n')
    if not lines:
        return False, "No lines in diagram"
    
    max_width = max(len(line) for line in lines) if lines else 0
    avg_width = sum(len(line) for line in lines) / len(lines) if lines else 0
    
    # Adaptive max width: allow wider diagrams if they have more lines
    adaptive_max_width = max(80, min(150, 60 + len(lines) * 2))
    
    if max_width > adaptive_max_width:
        return False, f"Diagram too wide ({max_width} chars, max {adaptive_max_width})"
    
    # Adaptive line count: at least 2, or 1 if very compact
    min_lines = 2 if len(diagram_text) > 50 else 1
    if len(lines) < min_lines:
        return False, f"Diagram too short ({len(lines)} lines, min {min_lines})"
    
    # Adaptive box character count based on diagram size
    box_char_count = sum(1 for char in diagram_text if char in box_chars)
    min_box_chars = max(2, len(diagram_text) // 30)  # Adaptive: at least 2, or 1 per 30 chars
    if box_char_count < min_box_chars:
        return False, f"Insufficient diagram structure ({box_char_count} box chars, min {min_box_chars})"
    
    return True, ""

