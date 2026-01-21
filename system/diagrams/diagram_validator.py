import re
from typing import Tuple, Dict


def validate_diagram_content(diagram_text: str, context: Dict = None) -> Tuple[bool, str]:
    if not diagram_text:
        return False, "Empty diagram"
    
    generic_patterns = [
        r'Step\s+\d+',
        r'Process\s+\d+',
        r'Stage\s+\d+',
        r'Item\s+\d+',
        r'Part\s+\d+',
        r'Phase\s+\d+',
    ]
    
    lines = diagram_text.split('\n')
    content_lines = [line for line in lines if any(c.isalnum() for c in line)]
    
    if not content_lines:
        return False, "No content in diagram"
    
    generic_count = 0
    total_content = 0
    
    for line in content_lines:
        for pattern in generic_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                generic_count += 1
                break
        total_content += 1
    
    if total_content > 0:
        generic_ratio = generic_count / total_content
        if generic_ratio > 0.5:
            return False, f"Too much generic content ({generic_ratio*100:.0f}% generic)"
    
    return True, ""


def validate_diagram(diagram_text: str, context: Dict = None) -> Tuple[bool, str]:
    if not diagram_text:
        return False, "Empty diagram"
    
    box_chars = "┌┐└┘│─├┤┬┴"
    if not any(char in diagram_text for char in box_chars):
        return False, "No diagram characters detected"
    
    lines = diagram_text.split('\n')
    if not lines:
        return False, "No lines in diagram"
    
    max_width = max(len(line) for line in lines) if lines else 0
    adaptive_max_width = max(80, min(150, 60 + len(lines) * 2))
    
    if max_width > adaptive_max_width:
        return False, f"Diagram too wide ({max_width} chars, max {adaptive_max_width})"
    
    min_lines = 2 if len(diagram_text) > 50 else 1
    if len(lines) < min_lines:
        return False, f"Diagram too short ({len(lines)} lines, min {min_lines})"
    
    box_char_count = sum(1 for char in diagram_text if char in box_chars)
    min_box_chars = max(2, len(diagram_text) // 30)
    if box_char_count < min_box_chars:
        return False, f"Insufficient diagram structure ({box_char_count} box chars, min {min_box_chars})"
    
    is_valid_content, content_error = validate_diagram_content(diagram_text, context)
    if not is_valid_content:
        return False, content_error
    
    return True, ""

