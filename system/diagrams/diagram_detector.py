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
Semantic diagram detection for educational content
"""

import re
import logging
from typing import Optional, NamedTuple, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class DiagramType(Enum):
    FLOWCHART = "flowchart"
    STRUCTURE = "structure"
    PROCESS = "process"

class DiagramDecision(NamedTuple):
    should_generate: bool
    diagram_type: Optional[DiagramType]

@dataclass
class DiagramContext:
    question: str
    answer: str
    diagram_type: DiagramType
    steps: List[str] = field(default_factory=list)
    num_steps: int = 0
    variables: List[str] = field(default_factory=list)
    loop_type: Optional[str] = None
    conditions: List[str] = field(default_factory=list)
    has_decisions: bool = False
    components: List[str] = field(default_factory=list)
    has_hierarchy: bool = False
    relationships: List[str] = field(default_factory=list)
    key_concepts: List[str] = field(default_factory=list)

# Constants tuned for Phi 1.5
STOPWORDS = frozenset({
    "the", "is", "are", "a", "an", "to", "of", "and", "or", "for", "in", "on", 
    "at", "by", "that", "this", "it", "as", "be", "with", "from", "into", 
    "their", "its", "they", "them", "can", "will", "about", "how", "what", 
    "why", "which", "who", "whose", "when", "where", "than", "then", "also"
})

MIN_VISUALIZABLE_INDICATORS = 2
DEFAULT_THRESHOLD = 70
LONG_ANSWER_THRESHOLD = 350 
VERY_LONG_ANSWER_THRESHOLD = 600


class PatternMatcher:
    # Patterns kept broad to catch variations in small model outputs
    PROCESS_PATTERNS = [
        r'\b(how|explain|describe)\s+.*\s+(work|flow|happen|cycle)',
        r'\b(process|procedure|method|sequence|mechanism|stage|phase)\b',
        r'\b(first|then|next|finally|afterward|step)\b',
    ]
    
    FLOWCHART_PATTERNS = [
        r'\b(decide|choose|select|determine|pick|logic|branch)\b',
        r'\b(if|when|whether|condition|loop|repeat|until|while)\b',
    ]
    
    STRUCTURE_PATTERNS = [
        r'\b(structure|organization|layout|hierarchy|tree|network)\b',
        r'\b(component|part|element|piece|layer|tier|segment)\b',
        r'\b(consists of|composed of|made up of|contains|includes)\b',
    ]
    
    @staticmethod
    def count_pattern_matches(text: str, patterns: List[str]) -> int:
        return sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))


class DiagramDetector:
    def __init__(self):
        self.matcher = PatternMatcher()

    def should_generate_diagram(self, question: str, answer: str) -> DiagramDecision:
        # Validation
        if not question or not answer or len(answer) < 20:
            return DiagramDecision(False, None)
        
        # Scores
        combined = f"{question} {answer}".lower()
        
        all_patterns = self.matcher.PROCESS_PATTERNS + self.matcher.FLOWCHART_PATTERNS + self.matcher.STRUCTURE_PATTERNS
        visual_score = self.matcher.count_pattern_matches(combined, all_patterns)
        
        if visual_score < MIN_VISUALIZABLE_INDICATORS:
            return DiagramDecision(False, None)

        scores = {
            DiagramType.PROCESS: self.matcher.count_pattern_matches(combined, self.matcher.PROCESS_PATTERNS),
            DiagramType.FLOWCHART: self.matcher.count_pattern_matches(combined, self.matcher.FLOWCHART_PATTERNS),
            DiagramType.STRUCTURE: self.matcher.count_pattern_matches(combined, self.matcher.STRUCTURE_PATTERNS)
        }
        
        print(f"DEBUG: Visual Score: {visual_score}")
        print(f"DEBUG: Category Scores: {scores}")
        
        max_type = max(scores, key=scores.get)
        
        # TODO: NEEDS BETTER APPROACH
        adaptive_threshold = DEFAULT_THRESHOLD if len(answer) < LONG_ANSWER_THRESHOLD else 2
        
        if scores[max_type] >= adaptive_threshold:
            return DiagramDecision(True, max_type)
            
        return DiagramDecision(False, None)


class ContextExtractor:
    """Extracts data points needed to draw the diagram."""
    
    def extract(self, question: str, answer: str, diagram_type: DiagramType) -> DiagramContext:
        ctx = DiagramContext(question=question, answer=answer, diagram_type=diagram_type)
        
        if diagram_type == DiagramType.PROCESS:
            ctx.steps = self._extract_steps(answer)
            ctx.num_steps = len(ctx.steps)
        elif diagram_type == DiagramType.FLOWCHART:
            ctx.conditions = self._extract_conditions(answer)
            ctx.loop_type = self._detect_loop_type(answer)
            ctx.has_decisions = len(ctx.conditions) > 0
        elif diagram_type == DiagramType.STRUCTURE:
            ctx.components = self._extract_components(answer)
            ctx.has_hierarchy = any(re.search(r'level|layer|tier|top|bottom', answer, re.I) for _ in [1])

        ctx.key_concepts = self._extract_key_concepts(question, answer)
        return ctx

    def _extract_steps(self, text: str) -> List[str]:
        # Support for numbers, "Step 1", and bullets
        steps = []
        # Matches "1. Step" or "1) Step"
        steps.extend(re.findall(r'(?:\d+[\.\)]\s+)([^\n\.\:]{3,40})', text))
        # Matches bullets "- Step"
        if not steps:
            steps.extend(re.findall(r'^\s*[\-\*\u2022]\s+([^\n\.\:]{3,40})', text, re.M))
        return [s.strip() for s in steps if s.strip()][:8]

    def _extract_conditions(self, text: str) -> List[str]:
        patterns = [r'if\s+([^,\.\n]{3,30})', r'whether\s+([^,\.\n]{3,30})']
        results = []
        for p in patterns:
            results.extend(re.findall(p, text, re.I))
        return [r.strip() for r in results][:3]

    def _detect_loop_type(self, text: str) -> Optional[str]:
        if re.search(r'\b(for each|every|iterate)\b', text, re.I): return "for"
        if re.search(r'\b(repeat|while|until|loop)\b', text, re.I): return "while"
        return None

    def _extract_components(self, text: str) -> List[str]:
        match = re.search(r'(?:consists of|includes|contains|components are)[:\s]+([^\.\n]+)', text, re.I)
        if match:
            parts = re.split(r',|and|;', match.group(1))
            return [p.strip() for p in parts if len(p.strip()) > 2][:8]
        return []

    def _extract_key_concepts(self, q: str, a: str) -> List[str]:
        # Phi 1.5 often uses all-caps for technical terms (e.g. CPU, RAM)
        text = f"{q} {a}"
        # Match Title Case or ALL CAPS technical words
        found = re.findall(r'\b([A-Z]{2,}|[A-Z][a-z]{3,})\b', text)
        unique = []
        for f in found:
            if f.lower() not in STOPWORDS and f not in unique:
                unique.append(f)
        return unique[:5]

# Public Helper Functions

def should_generate_diagram(question: str, answer: str) -> Tuple[bool, Optional[str]]:
    detector = DiagramDetector()
    decision = detector.should_generate_diagram(question, answer)
    return decision.should_generate, (decision.diagram_type.value if decision.diagram_type else None)

def extract_context_for_diagram(question: str, answer: str, diagram_type_str: str) -> Dict[str, Any]:
    try:
        dtype = DiagramType(diagram_type_str.lower())
        extractor = ContextExtractor()
        context = extractor.extract(question, answer, dtype)
        return context.__dict__ 
    except Exception as e:
        logger.error(f"Context extraction failed: {e}")
        return {}