"""
ASCII Diagram Extraction Utility

Extracts ASCII diagrams from AI-generated answers.
Lightweight and non-blocking - designed for zero performance impact.
"""

from typing import Tuple, Optional


def extract_diagram_from_answer(answer: str) -> Tuple[str, Optional[str]]:
    """
    Extract diagram from answer text if present.
    
    This function is designed to be fast and non-blocking. It performs
    simple pattern matching to detect and separate diagrams from text.
    
    Args:
        answer: Complete answer text that may contain a diagram
        
    Returns:
        Tuple of (answer_text, diagram_text) where diagram_text is None
        if no diagram is detected
    """
    if not answer:
        return answer, None
    
    # Look for common diagram markers
    diagram_markers = [
        "Diagram:",
        "Visual Representation:",
        "ASCII Diagram:",
        "Visual:",
        "Diagram",
    ]
    
    # Check for box-drawing characters (indicates diagram)
    box_chars = "┌┐└┘│─├┤┬┴"
    
    # Strategy 1: Look for explicit markers
    for marker in diagram_markers:
        if marker in answer:
            # Try case-insensitive search
            marker_lower = marker.lower()
            answer_lower = answer.lower()
            
            if marker_lower in answer_lower:
                # Find the actual marker (preserve case)
                idx = answer_lower.find(marker_lower)
                actual_marker = answer[idx:idx+len(marker)]
                
                # Split on marker
                parts = answer.split(actual_marker, 1)
                if len(parts) == 2:
                    answer_text = parts[0].strip()
                    diagram_section = parts[1].strip()
                    
                    # Verify it's actually a diagram (contains box chars)
                    if any(char in diagram_section for char in box_chars):
                        return answer_text, diagram_section
    
    # Strategy 2: Look for box-drawing characters (diagram without explicit marker)
    lines = answer.split('\n')
    diagram_start = None
    
    for i, line in enumerate(lines):
        # Check if line contains box-drawing characters
        if any(char in line for char in box_chars):
            # Found potential diagram start
            diagram_start = i
            break
    
    if diagram_start is not None:
        # Check if there's substantial diagram content (at least 3 lines)
        potential_diagram_lines = lines[diagram_start:]
        diagram_line_count = sum(
            1 for line in potential_diagram_lines 
            if any(char in line for char in box_chars)
        )
        
        if diagram_line_count >= 2:  # At least 2 lines with box chars
            answer_text = '\n'.join(lines[:diagram_start]).strip()
            diagram_text = '\n'.join(lines[diagram_start:]).strip()
            
            # Additional validation: diagram should have some structure
            if len(diagram_text) > 20:  # Reasonable minimum size
                return answer_text, diagram_text
    
    # No diagram detected
    return answer, None


def is_diagram_present(answer: str) -> bool:
    """
    Quick check if answer likely contains a diagram.
    
    Args:
        answer: Answer text to check
        
    Returns:
        True if diagram is likely present, False otherwise
    """
    _, diagram = extract_diagram_from_answer(answer)
    return diagram is not None


def validate_diagram(diagram_text: str) -> Tuple[bool, str]:
    """
    Validate diagram quality (lightweight check).
    
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
    
    return True, ""

