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
    
    # Check width (should be reasonable)
    lines = diagram_text.split('\n')
    if not lines:
        return False, "No lines in diagram"
    
    max_width = max(len(line) for line in lines)
    if max_width > 100:
        return False, f"Diagram too wide ({max_width} chars, max 100)"
    
    # Check for basic structure (at least 2 lines)
    if len(lines) < 2:
        return False, "Diagram too short"
    
    # Check for minimum content (at least some box characters)
    box_char_count = sum(1 for char in diagram_text if char in box_chars)
    if box_char_count < 3:
        return False, "Insufficient diagram structure"
    
    return True, ""

