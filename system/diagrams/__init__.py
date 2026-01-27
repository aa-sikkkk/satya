# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
Diagram utilities for ASCII diagram extraction, generation, and validation.

This module provides lightweight utilities for working with ASCII diagrams.
"""

from .diagram_service import generate_and_append_diagram, should_attempt_diagram, generate_diagram_content
from .diagram_detector import should_generate_diagram, extract_context_for_diagram
from .custom_generator import generate_diagram
from .diagram_validator import validate_diagram
from .diagram_formatter import format_diagram

__all__ = [
    'generate_and_append_diagram',
    'generate_diagram_content',
    'should_attempt_diagram',
    'should_generate_diagram',
    'extract_context_for_diagram',
    'generate_diagram',
    'validate_diagram',
    'format_diagram',
]

