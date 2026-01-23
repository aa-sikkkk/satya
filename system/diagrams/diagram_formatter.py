"""Utilities for formatting and trimming diagram output."""

from typing import Optional

DEFAULT_MAX_WIDTH = 100
MIN_WIDTH = 60
MAX_WIDTH = 120
WIDTH_MULTIPLIER = 1.5
TRUNCATION_SUFFIX = "..."


class DiagramFormatter:
    """Handles formatting and width constraints for diagram strings."""
    
    @staticmethod
    def format(diagram: str) -> str:
        """
        Remove trailing whitespace and empty leading/trailing lines.
        
        Args:
            diagram: Raw diagram string
            
        Returns:
            Cleaned diagram string
        """
        if not diagram:
            return ""
        
        lines = [line.rstrip() for line in diagram.split('\n')]
        
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        
        return '\n'.join(lines)
    
    @staticmethod
    def trim(diagram: str, max_width: Optional[int] = None) -> str:
        """
        Truncate lines exceeding maximum width.
        
        If max_width is not provided, calculates adaptive width based on
        average line length (60-120 character range).
        
        Args:
            diagram: Diagram string to trim
            max_width: Maximum characters per line, or None for adaptive
            
        Returns:
            Diagram with truncated lines
        """
        if not diagram:
            return ""
        
        lines = diagram.split('\n')
        
        if max_width is None:
            max_width = DiagramFormatter._calculate_adaptive_width(lines)
        
        trimmed = [
            DiagramFormatter._truncate_line(line, max_width)
            for line in lines
        ]
        
        return '\n'.join(trimmed)
    
    @staticmethod
    def _calculate_adaptive_width(lines: list[str]) -> int:
        """Calculate width based on average line length."""
        if not lines:
            return DEFAULT_MAX_WIDTH
        
        avg_length = sum(len(line) for line in lines) / len(lines)
        adaptive_width = int(avg_length * WIDTH_MULTIPLIER)
        
        return max(MIN_WIDTH, min(MAX_WIDTH, adaptive_width))
    
    @staticmethod
    def _truncate_line(line: str, max_width: int) -> str:
        """Truncate single line if it exceeds max width."""
        if len(line) <= max_width:
            return line
        
        truncate_at = max_width - len(TRUNCATION_SUFFIX)
        return line[:truncate_at] + TRUNCATION_SUFFIX


def format_diagram(diagram: str) -> str:
    """Legacy wrapper for backward compatibility."""
    return DiagramFormatter.format(diagram)


def trim_diagram(diagram: str, max_width: Optional[int] = None) -> str:
    """Legacy wrapper for backward compatibility."""
    return DiagramFormatter.trim(diagram, max_width)