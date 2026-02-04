# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
Diagram utilities for ASCII diagram generation.

This module provides:
- DiagramLibrary: Load pre-built diagrams from YAML files
- DiagramRenderer: Render ASCII diagrams (flowcharts, hierarchies, comparisons)
- diagram_service: Main entry points for diagram generation

Usage:
    from system.diagrams import generate_diagram_content, DiagramRenderer
    
    result = generate_diagram_content(question, answer, grade=10, subject="science")
    if result:
        diagram, diagram_type = result
"""

from .diagram_service import (
    generate_diagram_content,
    should_attempt_diagram,
    should_show_diagram,
)
from .diagram_library import DiagramLibrary
from .diagram_renderer import DiagramRenderer
from .diagram_config import (
    DIAGRAM_CONFIG,
    get_template_for_concept,
    PROCESS_KEYWORDS,
    COMPARISON_KEYWORDS,
    HIERARCHY_KEYWORDS,
)

__all__ = [
    'generate_diagram_content',
    'should_attempt_diagram',
    'should_show_diagram',
    
    # Library access
    'DiagramLibrary',
    'DiagramRenderer',
    
    # Configuration
    'DIAGRAM_CONFIG',
    'get_template_for_concept',
    'PROCESS_KEYWORDS',
    'COMPARISON_KEYWORDS',
    'HIERARCHY_KEYWORDS',
]
