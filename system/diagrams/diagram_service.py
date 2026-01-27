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
Diagram Service Module
Orchestrates detection, generation, fallback templates, and GUI formatting.
"""

import logging
import re
import textwrap
from typing import Optional, List, Dict, Any

from .diagram_detector import should_generate_diagram, extract_context_for_diagram
from .custom_generator import generate_diagram 
from .diagram_formatter import format_diagram 
from .diagram_validator import validate_diagram
from .diagram_templates import get_template

logger = logging.getLogger(__name__)

def generate_diagram_content(
    question: str, 
    answer: str, 
    rag_chunks: Optional[List[str]] = None, 
    llm_handler=None
) -> Optional[tuple]:
    """Core logic: Returns (formatted_diagram_str, diagram_type) or None."""
    try:
        # Quick Validation
        if not question or not answer or len(answer.strip()) < 20:
            return None
        
        # Fast-fail check (Skip math, short definitions, etc.)
        if not should_attempt_diagram(question):
            return None
        
        should_generate, diagram_type = should_generate_diagram(question, answer)
        print(f"DEBUG: Detector Decision: {should_generate}, Type: {diagram_type}")
        
        if not should_generate or not diagram_type:
            print("DEBUG: Detector said NO.")
            return None
        
        context = extract_context_for_diagram(question, answer, diagram_type)
        context['rag_chunks'] = rag_chunks or []
        context['llm_handler'] = llm_handler
        
        # Custom Rendering
        diagram = generate_diagram(diagram_type, context)
        
        # FALLBACK: If custom drawing fails or is too small, use pre-built templates
        if not diagram or len(diagram.strip()) < 15:
            logger.debug("Custom renderer failed or returned too little data. Using template fallback.")
            
            loop_type = context.get('loop_type')
            if loop_type == 'while':
                diagram = get_template("while_loop")
            elif loop_type == 'for' or loop_type == 'for_each':
                diagram = get_template("for_loop")
            elif context.get('has_decisions') or context.get('conditions'):
                diagram = get_template("if_else")
            else:
                # Default process flow if nothing else fits
                diagram = get_template("process_3_steps")
        
        print(f"DEBUG: Final Diagram Length: {len(diagram) if diagram else 0}")
                
        if not diagram or len(diagram.strip()) < 10:
            print("DEBUG: Diagram too short, aborting.")
            return None
        
        is_valid, error_msg = validate_diagram(diagram, context)
        if not is_valid:
            logger.warning(f"Diagram validation failed: {error_msg}")
            return None
  
        return format_diagram(diagram), diagram_type

    except Exception as e:
        logger.error(f"Diagram generation failed: {e}", exc_info=True)
        return None


def generate_and_append_diagram(
    question: str, 
    answer: str, 
    rag_chunks: Optional[List[str]] = None, 
    llm_handler=None
) -> str:
    """Legacy wrapper: Generates diagram and appends it to answer text."""
    result = generate_diagram_content(question, answer, rag_chunks, llm_handler)
    if not result:
        return answer
        
    formatted_diagram, diagram_type = result

    clean_answer = answer.rstrip()

    wrapped_lines = []
    for line in clean_answer.split('\n'):
        if len(line) > 90:
            wrapped_lines.append(textwrap.fill(line, width=90))
        else:
            wrapped_lines.append(line)
    wrapped_answer = "\n".join(wrapped_lines)

    type_name = diagram_type.value if hasattr(diagram_type, 'value') else str(diagram_type)
    
    return (
        f"{wrapped_answer}\n\n"
        f"### Visual Representation ({type_name.title()})\n"
        f"```text\n"
        f"{formatted_diagram}\n"
        f"```"
    )


def should_attempt_diagram(question: str) -> bool:
    """Fast regex-based pre-filter."""
    q_low = question.lower()
    
    math_patterns = [
        r'\b(solve|calculate|compute|evaluate)\b',
        r'\b(formula|equation|math|algebra)\b',
        r'[\+\-\*\/=]{2,}' 
    ]
    if any(re.search(p, q_low) for p in math_patterns):
        return False
    
    visual_triggers = [
        r'\b(how|process|work|flow|step|stage|phase)\b',
        r'\b(structure|parts|components|hierarchy|layer)\b',
        r'\b(cycle|loop|path|sequence|order)\b',
        r'\b(compare|difference|relationship)\b'
    ]
    
    return any(re.search(p, q_low) for p in visual_triggers)