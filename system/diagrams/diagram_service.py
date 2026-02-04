# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
Diagram Service Module

Orchestration layer for diagram generation using pre-built YAML library.
"""

import re
import logging
from typing import Optional, List, Tuple

from .diagram_library import DiagramLibrary
from .diagram_renderer import DiagramRenderer
from .diagram_config import PROCESS_KEYWORDS, COMPARISON_KEYWORDS, HIERARCHY_KEYWORDS

logger = logging.getLogger(__name__)


def should_show_diagram(question: str, answer: str, match_confidence: float) -> bool:
    """
    Determine if a diagram should be shown for this question/answer.
    
    Returns True if: confidence >= 0.3, question has visual triggers,
    answer is substantial (>25 words), and not a factual question.
    """
    if match_confidence < 0.3:
        return False
    
    q_lower = question.lower()
    
    visual_triggers = [
        'how does', 'how do', 'explain', 'describe', 'process', 'steps',
        'compare', 'difference', 'types of', 'classification',
        'structure', 'parts of', 'stages', 'cycle', 'hierarchy'
    ]
    has_visual_trigger = any(t in q_lower for t in visual_triggers)
    
    is_substantial = len(answer.split()) > 25
    
    factual_patterns = ['what year', 'when did', 'who invented', 'what is the capital', 'in which year']
    is_factual = any(p in q_lower for p in factual_patterns)
    
    return has_visual_trigger and is_substantial and not is_factual


def should_attempt_diagram(question: str) -> bool:
    """Fast pre-filter to skip diagram generation for unsuitable questions."""
    q_low = question.lower()
    
    math_patterns = [
        r'\b(solve|calculate|compute|evaluate)\b',
        r'\b(formula|equation|algebra)\b',
        r'[\+\-\*\/=]{2,}'
    ]
    if any(re.search(p, q_low) for p in math_patterns):
        return False
    
    visual_triggers = [
        r'\b(how|process|work|flow|step|stage|phase)\b',
        r'\b(structure|parts|components|hierarchy|layer)\b',
        r'\b(cycle|loop|path|sequence|order)\b',
        r'\b(compare|difference|relationship|types)\b'
    ]
    
    return any(re.search(p, q_low) for p in visual_triggers)


def generate_diagram_content(
    question: str, 
    answer: str,
    grade: Optional[int] = None,
    subject: Optional[str] = None
) -> Optional[Tuple[str, str]]:
    """
    Core diagram generation using YAML library.
    
    Returns:
        Tuple of (formatted_diagram, diagram_type) or None
    """
    try:
        if not question or not answer or len(answer.strip()) < 20:
            return None
        
        if not should_attempt_diagram(question):
            return None
        
        library = DiagramLibrary.get_instance()
        match = library.find_diagram(question, subject=subject, grade=grade)
        
        if not match:
            logger.debug(f"No diagram match for: {question[:50]}...")
            return None

        if not should_show_diagram(question, answer, match['confidence']):
            logger.debug(f"Skipping diagram - conditions not met for: {question[:50]}...")
            return None
        
        diagram_data = match['diagram']
        diagram_type = diagram_data.get('type', 'process')
        
        rendered = _render_from_yaml(diagram_data)
        
        if not rendered or len(rendered.strip()) < 10:
            return None
        
        return rendered, diagram_type
        
    except Exception as e:
        logger.error(f"Diagram generation failed: {e}", exc_info=True)
        return None


def _render_from_yaml(diagram_data: dict) -> Optional[str]:
    """Render ASCII diagram from YAML data structure."""
    diagram_type = diagram_data.get('type', 'process')
    
    try:
        if diagram_type == 'process':
            steps = diagram_data.get('steps', [])
            if not steps:
                return None
            clean_steps = [_clean_step(s) for s in steps]
            is_cyclic = diagram_data.get('cyclic', False)
            if is_cyclic:
                return DiagramRenderer.render_cycle_diagram(clean_steps)
            return DiagramRenderer.render_step_based_flowchart(clean_steps)
        
        elif diagram_type == 'hierarchy':
            children = diagram_data.get('children', [])
            components = _extract_children_names(children)
            if components:
                return DiagramRenderer.render_component_structure(components)
        
        elif diagram_type == 'structure':
            components = diagram_data.get('components', diagram_data.get('children', []))
            names = _extract_component_names(components)
            if names:
                return DiagramRenderer.render_component_structure(names)
        
        elif diagram_type == 'comparison':
            data = {
                'similarities': diagram_data.get('similarities', []),
                'differences': diagram_data.get('differences', {})
            }
            return DiagramRenderer.render_comparison_table(data)
        
        if 'steps' in diagram_data:
            steps = [_clean_step(s) for s in diagram_data['steps']]
            return DiagramRenderer.render_step_based_flowchart(steps)
        
    except Exception as e:
        logger.warning(f"Failed to render diagram type '{diagram_type}': {e}")
    
    return None


def _clean_step(step) -> str:
    """Clean step text, handling both strings and dicts."""
    if isinstance(step, str):
        text = re.sub(r'\s*\([^)]+\)\s*$', '', step)
        return text.strip()[:30]
    elif isinstance(step, dict):
        return str(step.get('name', list(step.keys())[0] if step else 'Step'))[:30]
    return str(step)[:30]


def _extract_children_names(children: list) -> List[str]:
    """Extract names from mixed children format."""
    names = []
    for child in children:
        if isinstance(child, str):
            names.append(child)
        elif isinstance(child, dict):
            name = child.get('name', '')
            if name:
                names.append(name)
            else:
                for k in child.keys():
                    if k not in ('children', 'description'):
                        names.append(k)
                        break
    return names[:8]


def _extract_component_names(components: list) -> List[str]:
    """Extract component names from list."""
    names = []
    for comp in components:
        if isinstance(comp, str):
            names.append(comp)
        elif isinstance(comp, dict):
            name = comp.get('name', '')
            if name:
                names.append(name)
    return names[:8]
