"""
Semantic diagram detection for educational content.

Analyzes questions and answers to determine if visual diagrams would enhance
understanding, and what type of diagram would be most appropriate.
"""

import re
import logging
from typing import Optional, NamedTuple
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
    steps: list[str] = field(default_factory=list)
    num_steps: int = 0
    variables: list[str] = field(default_factory=list)
    loop_type: Optional[str] = None
    conditions: list[str] = field(default_factory=list)
    has_decisions: bool = False
    components: list[str] = field(default_factory=list)
    has_hierarchy: bool = False
    relationships: list[str] = field(default_factory=list)
    key_concepts: list[str] = field(default_factory=list)


STOPWORDS = frozenset({
    "the", "is", "are", "a", "an", "to", "of", "and", "or", "for", "in", "on", 
    "at", "by", "that", "this", "it", "as", "be", "with", "from", "into", 
    "their", "its", "they", "them", "can", "will", "about", "how", "what", 
    "why", "which", "who", "whose", "when", "where", "than", "then", "also",
    "has", "have", "had", "do", "does", "did", "was", "were", "been", "being", 
    "would", "could", "should"
})

MIN_QUESTION_LENGTH = 3
MIN_ANSWER_LENGTH = 10
MIN_VISUALIZABLE_INDICATORS = 2
DEFAULT_THRESHOLD = 3
LONG_ANSWER_THRESHOLD = 500
LONG_ANSWER_REDUCED_THRESHOLD = 2
VERY_LONG_ANSWER_THRESHOLD = 800


class PatternMatcher:
    
    PROCESS_PATTERNS = [
        r'\b(how|what|explain|describe|tell)\s+(do|does|did|is|are|was|were)\s+.*\s+(work|happen|occur|proceed|flow|go)',
        r'\b(process|procedure|method|way|approach|mechanism)',
        r'\b(step|stage|phase|level|part)\s+(by|in|of)',
        r'\b(sequence|order|series|chain|cycle)',
        r'\b(first|then|next|finally|after|before|during)',
        r'\b(explain|describe|show|tell)\s+(me|us)?\s+(the|a|an)?\s+(process|procedure|method|way)',
        r'^(explain|describe|how)\s+(?!.*(formula|calculate|equation))', # Generic explain/describe
    ]
    
    FLOWCHART_PATTERNS = [
        r'\b(how|what)\s+(do|does|did)\s+.*\s+(decide|choose|select|determine|pick)',
        r'\b(if|when|whether|condition|conditional|decision|branch)',
        r'\b(loop|iterate|repeat|while|for|until)',
        r'\b(flow|path|route|direction|sequence)',
        r'\b(logic|reasoning|thinking)\s+(flow|work|process)',
    ]
    
    STRUCTURE_PATTERNS = [
        r'\b(what|how)\s+(is|are)\s+(the|a|an)?\s+(structure|organization|layout|arrangement|format|form|shape)',
        r'\b(show|display|draw|illustrate|visualize)\s+(the|a|an)?\s+(structure|organization|layout)',
        r'\b(how|what)\s+(is|are)\s+.*\s+(organized|structured|arranged|laid\s+out|formatted|built|made)',
        r'\b(hierarchy|tree|graph|network|system|framework|model)',
        r'\b(component|part|element|piece|section|segment)\s+(of|in|within)',
    ]
    
    @staticmethod
    def count_pattern_matches(text: str, patterns: list[str]) -> int:
        return sum(
            len(re.findall(pattern, text, re.IGNORECASE))
            for pattern in patterns
        )
    
    @staticmethod
    def has_pattern_match(text: str, patterns: list[str]) -> bool:
        return any(
            re.search(pattern, text, re.IGNORECASE)
            for pattern in patterns
        )


class QuestionAnalyzer:
    
    def __init__(self):
        self.matcher = PatternMatcher()
    
    def analyze_intent(self, question: str) -> dict[str, int]:
        scores = {"flowchart": 0, "structure": 0, "process": 0}
        
        if self.matcher.has_pattern_match(question, self.matcher.PROCESS_PATTERNS):
            scores["process"] += 2
        
        if self.matcher.has_pattern_match(question, self.matcher.FLOWCHART_PATTERNS):
            scores["flowchart"] += 2
        
        if self.matcher.has_pattern_match(question, self.matcher.STRUCTURE_PATTERNS):
            scores["structure"] += 2
        
        return scores


class AnswerAnalyzer:
    
    STEP_PATTERNS = [
        r'\b(step|stage|phase|part)\s+(\d+|one|two|three|four|five)',
        r'^\s*[\d\.\)]\s+',
        r'^\s*[-•*]\s+',
        r'\b(first|second|third|fourth|fifth|then|next|finally)',
    ]
    
    CONDITIONAL_PATTERNS = [
        r'\b(if|when|whether|condition)\s+.*\s+(then|else|otherwise)',
        r'\b(decision|choice|select|choose|determine)',
        r'\b(loop|iterate|repeat|while|for|until)',
    ]
    
    STRUCTURE_INDICATORS = [
        r'\b(consists\s+of|composed\s+of|made\s+up\s+of|contains|includes)',
        r'\b(part|component|element|piece|section)',
        r'\b(hierarchy|level|layer|tier|rank)',
        r'\b(tree|graph|network|structure|organization)',
    ]
    
    def __init__(self):
        self.matcher = PatternMatcher()
    
    def analyze_structure(self, answer: str) -> dict[str, int]:
        scores = {"flowchart": 0, "structure": 0, "process": 0}
        
        step_count = self.matcher.count_pattern_matches(answer, self.STEP_PATTERNS)
        scores["process"] += 3 if step_count >= 2 else (1 if step_count >= 1 else 0)
        
        conditional_count = self.matcher.count_pattern_matches(answer, self.CONDITIONAL_PATTERNS)
        if conditional_count >= 1:
            scores["flowchart"] += 2
        
        structure_count = self.matcher.count_pattern_matches(answer, self.STRUCTURE_INDICATORS)
        scores["structure"] += 2 if structure_count >= 2 else (1 if structure_count >= 1 else 0)
        
        return scores


class ContentAnalyzer:
    
    def __init__(self):
        self.matcher = PatternMatcher()
    
    def detect_patterns(self, question: str, answer: str) -> dict[str, int]:
        scores = {"flowchart": 0, "structure": 0, "process": 0}
        combined = f"{question} {answer}".lower()
        
        self._score_process_indicators(combined, scores)
        self._score_flowchart_indicators(combined, scores)
        self._score_structure_indicators(combined, scores)
        
        return scores
    
    def _score_process_indicators(self, text: str, scores: dict):
        action_verbs = [
            r'\b(transform|convert|change|move|flow|create|produce)',
            r'\b(absorb|release|emit|occur|happen|take place|start|begin|end|finish|complete)',
        ]
        action_count = self.matcher.count_pattern_matches(text, action_verbs)
        scores["process"] += min(action_count, 2)
        
        temporal = [r'\b(cycle|circular|recurring|loop|iteration|repeat)']
        if self.matcher.count_pattern_matches(text, temporal) >= 1:
            scores["process"] += 2
    
    def _score_flowchart_indicators(self, text: str, scores: dict):
        conditional = [
            r'\b(if|when|whether|unless)\s+\w+',
            r'\b(then|else|otherwise|alternatively)',
            r'\b(decision|choice|select|condition)',
        ]
        conditional_count = self.matcher.count_pattern_matches(text, conditional)
        scores["flowchart"] += 3 if conditional_count >= 2 else (2 if conditional_count >= 1 else 0)
        
        iterative = [r'\b(iterate|iteration|loop|each|every|while|until)']
        if self.matcher.count_pattern_matches(text, iterative) >= 1:
            scores["flowchart"] += 2
    
    def _score_structure_indicators(self, text: str, scores: dict):
        part_whole = [
            r'\b(consists of|composed of|contains|includes)',
            r'\b(part|component|element|whole|entire)',
        ]
        count = self.matcher.count_pattern_matches(text, part_whole)
        scores["structure"] += 3 if count >= 2 else (2 if count >= 1 else 0)
        
        hierarchical = [
            r'\b(hierarchy|level|layer|tier)',
            r'\b(parent|child|root|branch)',
        ]
        if self.matcher.count_pattern_matches(text, hierarchical) >= 1:
            scores["structure"] += 2


class VisualizabilityChecker:
    
    VISUALIZABLE_PATTERNS = [
        r'\b(step|stage|phase|component|element)',
        r'\b(flow|process|procedure|method)',
        r'\b(structure|organization|layout)',
        r'\b(relationship|connection|link)',
        r'\b(cycle|sequence|order)',
        r'\b(if|when|condition|decision)',
    ]
    
    def __init__(self):
        self.matcher = PatternMatcher()
    
    def is_visualizable(self, question: str, answer: str) -> bool:
        min_length = max(MIN_ANSWER_LENGTH * 3, len(question) * 2)
        if len(answer) < min_length:
            return False
        
        combined = f"{question} {answer}"
        match_count = self.matcher.count_pattern_matches(
            combined, 
            self.VISUALIZABLE_PATTERNS
        )
        
        return match_count >= MIN_VISUALIZABLE_INDICATORS


class DiagramDetector:
    """
    Determines if diagrams should be generated for Q&A content.
    
    Uses multi-heuristic analysis:
    - Question intent patterns
    - Answer structure analysis
    - Conceptual pattern detection
    - Content complexity scoring
    """
    
    def __init__(self):
        self.question_analyzer = QuestionAnalyzer()
        self.answer_analyzer = AnswerAnalyzer()
        self.content_analyzer = ContentAnalyzer()
        self.visualizability_checker = VisualizabilityChecker()
    
    def should_generate_diagram(
        self, 
        question: str, 
        answer: str
    ) -> DiagramDecision:
        if not self._validate_inputs(question, answer):
            return DiagramDecision(False, None)
        
        if not self.visualizability_checker.is_visualizable(question, answer):
            return DiagramDecision(False, None)
        
        scores = self._calculate_scores(question, answer)
        threshold = self._get_adaptive_threshold(answer)
        
        if len(answer) > VERY_LONG_ANSWER_THRESHOLD:
            diagram_type = self._check_long_answer(scores)
            if diagram_type:
                return DiagramDecision(True, diagram_type)
        
        max_score = max(scores.values())
        if max_score < threshold:
            return DiagramDecision(False, None)
        
        diagram_type = max(scores, key=scores.get)
        return DiagramDecision(True, DiagramType(diagram_type))
    
    def _validate_inputs(self, question: str, answer: str) -> bool:
        if not question or not answer:
            return False
        
        min_q_len = max(MIN_QUESTION_LENGTH, len(question) // 10)
        min_a_len = max(MIN_ANSWER_LENGTH, len(answer) // 20)
        
        return len(question) >= min_q_len and len(answer) >= min_a_len
    
    def _calculate_scores(self, question: str, answer: str) -> dict[str, int]:
        scores = {"flowchart": 0, "structure": 0, "process": 0}
        
        question_scores = self.question_analyzer.analyze_intent(question.lower())
        answer_scores = self.answer_analyzer.analyze_structure(answer.lower())
        content_scores = self.content_analyzer.detect_patterns(question, answer)
        
        for key in scores:
            scores[key] = (
                question_scores[key] + 
                answer_scores[key] + 
                content_scores[key]
            )
        
        return scores
    
    def _get_adaptive_threshold(self, answer: str) -> int:
        return (
            LONG_ANSWER_REDUCED_THRESHOLD 
            if len(answer) > LONG_ANSWER_THRESHOLD 
            else DEFAULT_THRESHOLD
        )
    
    def _check_long_answer(self, scores: dict[str, int]) -> Optional[DiagramType]:
        if scores["process"] >= 1:
            return DiagramType.PROCESS
        elif scores["structure"] >= 1:
            return DiagramType.STRUCTURE
        elif scores["flowchart"] >= 1:
            return DiagramType.FLOWCHART
        return None


def should_generate_diagram(question: str, answer: str) -> tuple[bool, Optional[str]]:
    """
    Determine if diagram should be generated and what type.
    
    Returns:
        (should_generate, diagram_type) where diagram_type is one of:
        "flowchart", "structure", "process", or None
    """
    detector = DiagramDetector()
    decision = detector.should_generate_diagram(question, answer)
    
    diagram_type_str = decision.diagram_type.value if decision.diagram_type else None
    return decision.should_generate, diagram_type_str


def extract_context_for_diagram(
    question: str, 
    answer: str, 
    diagram_type: str
) -> dict:
    """Extract contextual information needed for diagram generation."""
    try:
        dtype = DiagramType(diagram_type)
    except ValueError:
        logger.warning(f"Invalid diagram type: {diagram_type}")
        return {}
    
    extractor = ContextExtractor()
    context = extractor.extract(question, answer, dtype)
    
    return {
        "question": context.question,
        "answer": context.answer,
        "diagram_type": context.diagram_type.value,
        "steps": context.steps,
        "num_steps": context.num_steps,
        "variables": context.variables,
        "loop_type": context.loop_type,
        "conditions": context.conditions,
        "has_decisions": context.has_decisions,
        "components": context.components,
        "has_hierarchy": context.has_hierarchy,
        "relationships": context.relationships,
        "key_concepts": context.key_concepts,
    }


class ContextExtractor:
    
    def extract(
        self, 
        question: str, 
        answer: str, 
        diagram_type: DiagramType
    ) -> DiagramContext:
        context = DiagramContext(
            question=question,
            answer=answer,
            diagram_type=diagram_type
        )
        
        if diagram_type == DiagramType.PROCESS:
            self._extract_process_context(answer, context)
        elif diagram_type == DiagramType.FLOWCHART:
            self._extract_flowchart_context(answer, context)
        elif diagram_type == DiagramType.STRUCTURE:
            self._extract_structure_context(answer, context)
        
        context.key_concepts = self._extract_key_concepts(question, answer)
        
        return context
    
    def _extract_process_context(self, answer: str, context: DiagramContext):
        context.steps = self._extract_steps(answer)
        context.num_steps = len(context.steps) if context.steps else self._estimate_steps(answer)
    
    def _extract_flowchart_context(self, answer: str, context: DiagramContext):
        context.variables = self._extract_variables(answer)[:5]
        context.loop_type = self._detect_loop_type(answer)
        context.conditions = self._extract_conditions(answer)[:3]
        context.has_decisions = self._has_decisions(answer)
    
    def _extract_structure_context(self, answer: str, context: DiagramContext):
        context.components = self._extract_components(answer)[:8]
        context.has_hierarchy = self._has_hierarchy(answer)
        context.relationships = self._extract_relationships(answer)[:5]
    
    def _extract_steps(self, answer: str) -> list[str]:
        steps = []
        
        patterns = [
            r'(?:step|stage|phase)\s+\d+[:\.]?\s*([^\n\.]+)',
            r'^\s*\d+[\.\)]\s+([^\n\.]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, answer, re.MULTILINE | re.IGNORECASE)
            steps.extend(m.strip() for m in matches)
        
        return steps[:10]
    
    def _estimate_steps(self, answer: str) -> int:
        indicators = [
            r'\b(first|second|third|fourth|fifth)',
            r'\b(then|next|after|finally)',
        ]
        
        count = sum(
            len(re.findall(p, answer, re.IGNORECASE))
            for p in indicators
        )
        
        return min(count, 10) if count > 0 else 3
    
    def _extract_variables(self, answer: str) -> list[str]:
        entities = set()
        
        patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            r'\b([a-z_][a-z0-9_]*)\s*=',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, answer)
            entities.update(matches)
        
        return [e for e in entities if e.lower() not in STOPWORDS and len(e) > 2]
    
    def _detect_loop_type(self, text: str) -> Optional[str]:
        """
        Detect loop construct type from text patterns.
        
        Returns one of: "for", "while", "until", "do_while", or None
        """
        text = text.lower()
        
        loop_patterns = {
            "for": r'\bfor\s+(?:each|every)\s+\w+\s+in\s+',
            "while": r'\bwhile\s+\w+.*(?::|do|then)',
            "until": r'\b(?:repeat|continue)\s+until\s+',
            "do_while": r'\bdo\s+.*\s+while\s+',
        }
        
        for loop_type, pattern in loop_patterns.items():
            if re.search(pattern, text):
                return loop_type
        
        return None
    
    def _extract_conditions(self, answer: str) -> list[str]:
        patterns = [
            r'\bif\s+([^,\.]+?)\s+(?:then|do|does)',
            r'\bwhen\s+([^,\.]+?)\s*[,\.]',
        ]
        
        conditions = []
        for pattern in patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            conditions.extend(m.strip() for m in matches if len(m.strip()) > 3)
        
        return conditions
    
    def _has_decisions(self, answer: str) -> bool:
        patterns = [
            r'\b(if|when|whether)\s+.*\s+(then|else)',
            r'\b(decision|choice|select|choose)',
        ]
        return any(re.search(p, answer, re.IGNORECASE) for p in patterns)
    
    def _extract_components(self, answer: str) -> list[str]:
        patterns = [
            r'\b(?:consists|composed|made)\s+of\s+([^\.]+)',
            r'\b(?:contains|includes)\s+([^\.]+)',
        ]
        
        components = set()
        for pattern in patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            for match in matches:
                parts = re.split(r'[,;]\s*|\s+and\s+', match)
                components.update(p.strip() for p in parts if len(p.strip()) > 2)
        
        return [c for c in components if c.lower() not in STOPWORDS]
    
    def _has_hierarchy(self, answer: str) -> bool:
        patterns = [
            r'\b(hierarchy|level|layer|tier|parent|child)',
            r'\b(above|below|under|over|top|bottom)',
        ]
        return any(re.search(p, answer, re.IGNORECASE) for p in patterns)
    
    def _extract_relationships(self, answer: str) -> list[str]:
        patterns = [
            r'\b(\w+)\s+(?:is|are)\s+(?:related|connected|linked)\s+to\s+(\w+)',
            r'\b(?:relationship|connection)\s+between\s+(\w+)\s+and\s+(\w+)',
        ]
        
        relationships = []
        for pattern in patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            for match in matches:
                rel = " ".join(match) if isinstance(match, tuple) else match
                if len(rel.strip()) > 3:
                    relationships.append(rel.strip())
        
        return relationships
    
    def _extract_key_concepts(self, question: str, answer: str) -> list[str]:
        text = f"{question} {answer}"
        
        capitalized = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', text)
        technical = re.findall(
            r'\b([a-z]+(?:\s+[a-z]+)?)\s+(?:process|cycle|structure|system)\b',
            text.lower()
        )
        
        concepts = set(c.lower() for c in capitalized if len(c) > 3)
        concepts.update(technical)
        
        return [
            c for c in concepts 
            if c.lower() not in STOPWORDS and len(c) > 3
        ][:5]