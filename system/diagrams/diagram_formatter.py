"""
Diagram Formatter

Lightweight formatting utilities for ASCII diagrams.
Minimal processing to avoid adding delay.
"""

from typing import Optional


def format_diagram(diagram: str) -> str:
    """
    Format diagram with minor cleanup.
    
    This function is designed to be fast (<10ms) and lightweight.
    Only performs essential formatting operations.
    
    Args:
        diagram: Raw diagram string
    
    Returns:
        Formatted diagram string
    """
    if not diagram:
        return ""
    
    # Remove leading/trailing whitespace from each line
    lines = [line.rstrip() for line in diagram.split('\n')]
    
    # Remove empty lines at start and end
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    
    # Ensure consistent line endings
    return '\n'.join(lines)


def trim_diagram(diagram: str, max_width: int = 100) -> str:
    """
    Trim diagram if it exceeds maximum width.
    
    Args:
        diagram: Diagram string
        max_width: Maximum allowed width
    
    Returns:
        Trimmed diagram string
    """
    if not diagram:
        return ""
    
    lines = diagram.split('\n')
    trimmed_lines = []
    
    for line in lines:
        if len(line) > max_width:
            # Truncate and add ellipsis
            trimmed_lines.append(line[:max_width - 3] + "...")
        else:
            trimmed_lines.append(line)
    
    return '\n'.join(trimmed_lines)

