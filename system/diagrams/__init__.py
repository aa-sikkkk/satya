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

