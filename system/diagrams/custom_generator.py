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
Diagram Generation Module (Facade)
"""

import logging
import re
from typing import Dict, Optional, List, Any
from .diagram_constants import SEQUENTIAL_KEYWORDS_PATTERN, CONDITION_MATCH_PATTERN
from .diagram_extractor import DiagramExtractor
from .diagram_renderer import DiagramRenderer

logger = logging.getLogger(__name__)

def generate_diagram(diagram_type: str, context: Dict[str, Any]) -> str:
    try:
        if diagram_type == "flowchart":
            return generate_flowchart(context) or ""
        elif diagram_type == "structure":
            return generate_structure_diagram(context) or ""
        elif diagram_type == "process":
            return generate_process_diagram(context) or ""
    except Exception as e:
        logger.error(f"Error generating {diagram_type} diagram: {e}")
    
    return ""


def generate_flowchart(context: Dict[str, Any]) -> str:
    answer = context.get("answer", "")
    rag_chunks = context.get("rag_chunks")
    llm_handler = context.get("llm_handler")
    
    # 1. Try Step Extraction
    steps = DiagramExtractor.extract_steps_from_answer(answer, rag_chunks, llm_handler)
    if steps:
        return DiagramRenderer.render_step_based_flowchart(steps)
    
    # 2. Try Decision Logic
    if DiagramExtractor.has_decision_points(answer):
        return generate_decision_flowchart(context)
    
    # 3. Try Iteration/Loops
    loop_type = context.get("loop_type")
    if loop_type:
        return generate_iterative_flowchart(context, loop_type)
    
    # 4. Fallback
    return generate_generic_process_flowchart(context)


def generate_iterative_flowchart(context: Dict[str, Any], iteration_type: str) -> str:
    answer = context.get("answer", "")
    question = context.get("question", "")
    iteration_subject = DiagramExtractor.extract_iteration_subject(answer, question)
    
    conditions = context.get("conditions", [])
    condition_text = conditions[0] if conditions else "Check Condition"
    
    return DiagramRenderer.render_iterative_flowchart(iteration_subject, condition_text)


def generate_process_diagram(context: Dict[str, Any]) -> str:
    answer = context.get("answer", "")
    question = context.get("question", "")
    rag_chunks = context.get("rag_chunks")
    llm_handler = context.get("llm_handler")
    
    is_cycle = DiagramExtractor.is_cyclic_process(question, answer)
    steps = DiagramExtractor.extract_steps_from_answer(answer, rag_chunks, llm_handler)
    
    # Try Answer Steps
    if steps:
        if is_cycle and len(steps) >= 2:
            return DiagramRenderer.render_cycle_diagram(steps)
        return DiagramRenderer.render_step_based_flowchart(steps)
    
    # Try Question Steps
    if question:
        question_steps = DiagramExtractor.extract_steps_from_answer(question, rag_chunks, llm_handler)
        if question_steps:
            return DiagramRenderer.render_step_based_flowchart(question_steps)
    
    # Try Key Terms
    key_terms = DiagramExtractor.extract_key_process_terms(answer)
    if key_terms and len(key_terms) >= 2:
        return DiagramRenderer.render_step_based_flowchart(key_terms)
    
    return generate_generic_process_flowchart(context)


def generate_decision_flowchart(context: Dict[str, Any]) -> str:
    answer = context.get("answer", "")
    conditions = context.get("conditions", [])
    
    condition_text = "Condition Check"
    if conditions:
        condition_text = conditions[0]
    else:
        # Extracted via shared constant
        cond_match = CONDITION_MATCH_PATTERN.search(answer)
        if cond_match:
            condition_text = cond_match.group(1).strip()
    
    return DiagramRenderer.render_decision_flowchart(condition_text)


def generate_generic_process_flowchart(context: Dict[str, Any]) -> str:
    """Generate a generic process flowchart when extraction fails."""
    num_steps = context.get("num_steps", 3)
    answer = context.get("answer", "")
    
    if answer:
        step_count = len(SEQUENTIAL_KEYWORDS_PATTERN.findall(answer))
        if step_count > 0:
            num_steps = min(step_count + 1, 6)
    
    num_steps = max(2, min(num_steps, 6))
    steps = [f"Step {i}" for i in range(1, num_steps + 1)]
    
    return DiagramRenderer.render_step_based_flowchart(steps)


def generate_structure_diagram(context: Dict[str, Any]) -> str:
    answer = context.get("answer", "")
    question = context.get("question", "")
    components = context.get("components", [])
    
    if not components:
        components = DiagramExtractor.extract_structure_components(
            answer, 
            question, 
            calculate_limit_callback=DiagramRenderer.calculate_adaptive_limits
        )
    
    if components:
        return DiagramRenderer.render_component_structure(components)
    
    # Fallback for layered structures
    if answer and re.search(r'(?:top|upper|highest|main).*?(?:level|layer|tier)', answer, re.IGNORECASE):
        levels = ["Top Level", "Middle Level", "Bottom Level"]
        return DiagramRenderer.render_component_structure(levels)
    
    return DiagramRenderer.render_minimal_structure()