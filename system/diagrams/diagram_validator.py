"""Validation utilities for diagram content and structure."""

import re
from typing import NamedTuple
from dataclasses import dataclass


class ValidationResult(NamedTuple):
    """Result of diagram validation."""
    is_valid: bool
    error_message: str


@dataclass(frozen=True)
class ValidationConfig:
    """Configuration for diagram validation thresholds."""
    max_generic_ratio: float = 0.5
    base_max_width: int = 80
    max_width_ceiling: int = 150
    width_per_line: int = 2
    min_short_diagram_lines: int = 1
    min_long_diagram_lines: int = 2
    long_diagram_threshold: int = 50
    structure_chars_ratio: int = 30
    min_structure_chars: int = 2


BOX_DRAWING_CHARS = frozenset("┌┐└┘│─├┤┬┴")

GENERIC_PATTERNS = [
    r'Step\s+\d+',
    r'Process\s+\d+',
    r'Stage\s+\d+',
    r'Item\s+\d+',
    r'Part\s+\d+',
    r'Phase\s+\d+',
]


class ContentValidator:
    """Validates diagram content quality."""
    
    def __init__(self, config: ValidationConfig = None):
        self.config = config or ValidationConfig()
    
    def validate(self, diagram_text: str) -> ValidationResult:
        """
        Check if diagram has meaningful content vs generic placeholders.
        
        Returns ValidationResult with error if generic ratio exceeds threshold.
        """
        if not diagram_text:
            return ValidationResult(False, "Empty diagram")
        
        content_lines = self._extract_content_lines(diagram_text)
        
        if not content_lines:
            return ValidationResult(False, "No content in diagram")
        
        generic_ratio = self._calculate_generic_ratio(content_lines)
        
        if generic_ratio > self.config.max_generic_ratio:
            percentage = int(generic_ratio * 100)
            return ValidationResult(
                False, 
                f"Too much generic content ({percentage}% generic)"
            )
        
        return ValidationResult(True, "")
    
    @staticmethod
    def _extract_content_lines(text: str) -> list[str]:
        """Extract lines containing alphanumeric content."""
        lines = text.split('\n')
        return [line for line in lines if any(c.isalnum() for c in line)]
    
    def _calculate_generic_ratio(self, lines: list[str]) -> float:
        """Calculate ratio of lines matching generic patterns."""
        if not lines:
            return 0.0
        
        generic_count = sum(
            1 for line in lines
            if self._is_generic_line(line)
        )
        
        return generic_count / len(lines)
    
    @staticmethod
    def _is_generic_line(line: str) -> bool:
        """Check if line matches any generic pattern."""
        return any(
            re.search(pattern, line, re.IGNORECASE)
            for pattern in GENERIC_PATTERNS
        )


class StructureValidator:
    """Validates diagram structure and formatting."""
    
    def __init__(self, config: ValidationConfig = None):
        self.config = config or ValidationConfig()
    
    def validate(self, diagram_text: str) -> ValidationResult:
        """
        Validate diagram has proper structure with box drawing characters.
        
        Checks for:
        - Presence of box drawing characters
        - Appropriate width
        - Minimum line count
        - Sufficient structural elements
        """
        if not diagram_text:
            return ValidationResult(False, "Empty diagram")
        
        if not self._has_box_chars(diagram_text):
            return ValidationResult(False, "No diagram characters detected")
        
        lines = diagram_text.split('\n')
        if not lines:
            return ValidationResult(False, "No lines in diagram")
        
        width_check = self._validate_width(lines)
        if not width_check.is_valid:
            return width_check
        
        line_count_check = self._validate_line_count(lines, diagram_text)
        if not line_count_check.is_valid:
            return line_count_check
        
        structure_check = self._validate_structure_chars(diagram_text)
        if not structure_check.is_valid:
            return structure_check
        
        return ValidationResult(True, "")
    
    @staticmethod
    def _has_box_chars(text: str) -> bool:
        """Check if text contains box drawing characters."""
        return any(char in text for char in BOX_DRAWING_CHARS)
    
    def _validate_width(self, lines: list[str]) -> ValidationResult:
        """Check if diagram width is within acceptable range."""
        max_width = max(len(line) for line in lines) if lines else 0
        adaptive_limit = self._calculate_adaptive_width_limit(len(lines))
        
        if max_width > adaptive_limit:
            return ValidationResult(
                False,
                f"Diagram too wide ({max_width} chars, max {adaptive_limit})"
            )
        
        return ValidationResult(True, "")
    
    def _calculate_adaptive_width_limit(self, line_count: int) -> int:
        """Calculate adaptive width limit based on line count."""
        calculated = self.config.base_max_width + (line_count * self.config.width_per_line)
        return min(calculated, self.config.max_width_ceiling)
    
    def _validate_line_count(self, lines: list[str], text: str) -> ValidationResult:
        """Check if diagram has minimum required lines."""
        min_lines = (
            self.config.min_long_diagram_lines 
            if len(text) > self.config.long_diagram_threshold 
            else self.config.min_short_diagram_lines
        )
        
        if len(lines) < min_lines:
            return ValidationResult(
                False,
                f"Diagram too short ({len(lines)} lines, min {min_lines})"
            )
        
        return ValidationResult(True, "")
    
    def _validate_structure_chars(self, text: str) -> ValidationResult:
        """Check if diagram has sufficient structural characters."""
        box_char_count = sum(1 for char in text if char in BOX_DRAWING_CHARS)
        min_required = max(
            self.config.min_structure_chars,
            len(text) // self.config.structure_chars_ratio
        )
        
        if box_char_count < min_required:
            return ValidationResult(
                False,
                f"Insufficient diagram structure ({box_char_count} box chars, min {min_required})"
            )
        
        return ValidationResult(True, "")


class DiagramValidator:
    """Complete diagram validation combining content and structure checks."""
    
    def __init__(self, config: ValidationConfig = None):
        self.config = config or ValidationConfig()
        self.content_validator = ContentValidator(self.config)
        self.structure_validator = StructureValidator(self.config)
    
    def validate(self, diagram_text: str, context: dict = None) -> ValidationResult:
        """
        Perform complete diagram validation.
        
        Args:
            diagram_text: Diagram string to validate
            context: Optional context dictionary (currently unused, reserved for future use)
            
        Returns:
            ValidationResult with validation status and error message if invalid
        """
        structure_result = self.structure_validator.validate(diagram_text)
        if not structure_result.is_valid:
            return structure_result
        
        content_result = self.content_validator.validate(diagram_text)
        if not content_result.is_valid:
            return content_result
        
        return ValidationResult(True, "")


def validate_diagram(diagram_text: str, context: dict = None) -> tuple[bool, str]:
    """Legacy wrapper for backward compatibility."""
    validator = DiagramValidator()
    result = validator.validate(diagram_text, context)
    return result.is_valid, result.error_message


def validate_diagram_content(diagram_text: str, context: dict = None) -> tuple[bool, str]:
    """Legacy wrapper for backward compatibility."""
    validator = ContentValidator()
    result = validator.validate(diagram_text)
    return result.is_valid, result.error_message