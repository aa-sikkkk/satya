# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
Diagram Configuration Module

Centralized configuration for the YAML-based diagram library system.
"""

from typing import Dict, List, Any


DIAGRAM_CONFIG: Dict[str, Any] = {
    'CONCEPT_TYPES': ['PROCESS', 'COMPARISON', 'HIERARCHY', 'STRUCTURE'],
    'CONCEPT_TO_TEMPLATE': {
        'PROCESS': 'flowchart',
        'COMPARISON': 'compare_contrast',
        'HIERARCHY': 'structure',
        'STRUCTURE': 'structure'
    },
    'MIN_ITEMS': 2,
    'MAX_ITEMS': 6,
    'MIN_CONFIDENCE': 0.3,
}

PROCESS_KEYWORDS = [
    'how', 'explain', 'describe', 'process', 'steps', 
    'stages', 'phases', 'procedure', 'sequence', 'cycle', 
    'flow', 'mechanism', 'method', 'happens', 'works'
]

COMPARISON_KEYWORDS = [
    'compare', 'contrast', 'difference', 'similar',
    'versus', 'vs', 'between', 'distinguish', 'differ'
]

HIERARCHY_KEYWORDS = [
    'structure', 'components', 'parts', 'layers',
    'hierarchy', 'types', 'categories', 'classification'
]


def get_template_for_concept(concept_type: str) -> str:
    """Get the diagram template name for a concept type."""
    return DIAGRAM_CONFIG['CONCEPT_TO_TEMPLATE'].get(
        concept_type.upper(), 
        'flowchart'
    )


def is_valid_concept_type(concept_type: str) -> bool:
    """Check if a concept type is supported."""
    return concept_type.upper() in DIAGRAM_CONFIG['CONCEPT_TYPES']
