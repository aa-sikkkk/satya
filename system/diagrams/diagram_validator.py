# Copyright (C) 2026 Aashik
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Validation utilities for diagram content and structure.
"""

import re
from typing import NamedTuple, List, Tuple, Optional
from dataclasses import dataclass


class ValidationResult(NamedTuple):
    """Result of diagram validation."""
    is_valid: bool
    error_message: str


@dataclass(frozen=True)
class ValidationConfig:
    """Configuration for diagram validation thresholds."""
    max_generic_ratio: float = 0.7  
    base_max_width: int = 60
    max_width_ceiling: int = 100    
    width_per_line: int = 2
    min_short_diagram_lines: int = 3 
    min_long_diagram_lines: int = 5
    long_diagram_threshold: int = 100
    structure_chars_ratio: int = 20  
    min_structure_chars: int = 4


# Added '▼' and '▲' as they are core to our renderer
BOX_DRAWING_CHARS = frozenset("┌┐└┘│─├┤┬┴▼▲")

GENERIC_PATTERNS = [
    r'^Step\s+\d+$',
    r'^Process\s+\d+$',
    r'^Stage\s+\d+$',
    r'^Item\s+\d+$',
    r'^Part\s+\d+$',
    r'^Phase\s+\d+$',
]


class ContentValidator:
    """Validates diagram content quality."""
    
    def __init__(self, config: ValidationConfig = None):
        self.config = config or ValidationConfig()
    
    def validate(self, diagram_text: str) -> ValidationResult:
        if not diagram_text:
            return ValidationResult(False, "Empty diagram")
        
        content_lines = self._extract_content_lines(diagram_text)
        
        if not content_lines:
            return ValidationResult(False, "No meaningful text found in diagram boxes")
        
        if len(content_lines) > 3:
            generic_ratio = self._calculate_generic_ratio(content_lines)
            if generic_ratio > self.config.max_generic_ratio:
                percentage = int(generic_ratio * 100)
                return ValidationResult(
                    False, 
                    f"Content is too generic ({percentage}%). Try being more specific."
                )
        
        return ValidationResult(True, "")
    
    @staticmethod
    def _extract_content_lines(text: str) -> List[str]:
        """Extract lines that likely contain diagram labels."""
        lines = text.split('\n')
        # Filter for lines that have letters/numbers and are inside/near box chars
        return [line.strip().strip('│').strip() for line in lines if any(c.isalnum() for c in line)]
    
    def _calculate_generic_ratio(self, lines: List[str]) -> float:
        if not lines:
            return 0.0
        
        generic_count = sum(1 for line in lines if self._is_generic_line(line))
        return generic_count / len(lines)
    
    @staticmethod
    def _is_generic_line(line: str) -> bool:
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in GENERIC_PATTERNS)


class StructureValidator:
    """Validates diagram structure and formatting."""
    
    def __init__(self, config: ValidationConfig = None):
        self.config = config or ValidationConfig()
    
    def validate(self, diagram_text: str) -> ValidationResult:
        if not diagram_text:
            return ValidationResult(False, "Empty diagram")
        
        if not self._has_box_chars(diagram_text):
            return ValidationResult(False, "Plain text detected; no ASCII structure")
        
        lines = [l for l in diagram_text.split('\n') if l.strip()]
        
        max_width = max(len(line) for line in lines) if lines else 0
        if max_width > self.config.max_width_ceiling:
            return ValidationResult(
                False,
                f"Diagram too wide ({max_width} chars). GUI limit is {self.config.max_width_ceiling}."
            )
        
        if len(lines) < self.config.min_short_diagram_lines:
            return ValidationResult(False, "Diagram is vertically too small to be useful")

        box_char_count = sum(1 for char in diagram_text if char in BOX_DRAWING_CHARS)
        if box_char_count < self.config.min_structure_chars:
            return ValidationResult(False, "Diagram structure is too sparse")
        
        return ValidationResult(True, "")
    
    @staticmethod
    def _has_box_chars(text: str) -> bool:
        return any(char in text for char in BOX_DRAWING_CHARS)


class DiagramValidator:
    """Complete diagram validation combining content and structure checks."""
    
    def __init__(self, config: ValidationConfig = None):
        self.config = config or ValidationConfig()
        self.content_validator = ContentValidator(self.config)
        self.structure_validator = StructureValidator(self.config)
    
    def validate(self, diagram_text: str, context: dict = None) -> ValidationResult:
        structure_result = self.structure_validator.validate(diagram_text)
        if not structure_result.is_valid:
            return structure_result
        
        content_result = self.content_validator.validate(diagram_text)
        if not content_result.is_valid:
            return content_result
        
        return ValidationResult(True, "")


# Legacy Wrappers for diagram_service.py

def validate_diagram(diagram_text: str, context: dict = None) -> Tuple[bool, str]:
    validator = DiagramValidator()
    result = validator.validate(diagram_text, context)
    return result.is_valid, result.error_message

def validate_diagram_content(diagram_text: str, context: dict = None) -> Tuple[bool, str]:
    validator = ContentValidator()
    result = validator.validate(diagram_text)
    return result.is_valid, result.error_message