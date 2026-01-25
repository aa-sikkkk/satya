import re
import logging
from typing import Dict, Optional, List, Tuple
from functools import lru_cache

logger = logging.getLogger(__name__)

# Constants
STOPWORDS = {
    "the", "is", "are", "a", "an", "to", "of", "and", "or", "for", "in", "on", "at", "by", "that",
    "this", "it", "as", "be", "with", "from", "into", "their", "its", "they", "them", "can", "will",
    "about", "how", "what", "why", "which", "who", "whose", "when", "where", "than", "then", "also",
    "been", "has", "have", "had", "does", "did", "do", "would", "could", "should"
}

# Compiled regex patterns (module level for efficiency)
NUMBERED_PATTERN = re.compile(r'(\d+)\.\s+([A-Z][a-zA-Z\s]+?)(?:\s*[-–—:]\s*|\s*\n)', re.MULTILINE)
STEP_PREFIX_PATTERN = re.compile(r'(?:Step|Stage|Phase)\s+(\d+)[:\.]?\s*([A-Z][a-zA-Z\s]+?)(?:\s*[-–—:]\s*|\s*\n)', re.MULTILINE)
PROCESS_LIST_PATTERN = re.compile(r'(?:consists of|includes|involves|comprises)[:\s]+([^\.]+)', re.IGNORECASE)
STAGE_LIST_PATTERN = re.compile(r'(?:stages?|steps?|phases?|processes?)[:\s]+([^\.]+)', re.IGNORECASE)
CAPITALIZED_TERMS_PATTERN = re.compile(r'\b([A-Z][a-z]+(?:ation|tion|sion|ment)?)\b')
LEADING_NUMBERS_PATTERN = re.compile(r'^[\d\-\.\)\*]+\s*')
TRAILING_PUNCTUATION_PATTERN = re.compile(r'[.,;:]+$')
DECISION_KEYWORDS_PATTERN = re.compile(r'\b(if|else|condition|decision|check|whether|depending|based on)\b', re.IGNORECASE)
ITERATION_PATTERN = re.compile(r'(?:for|each|every)\s+(\w+)', re.IGNORECASE)
ITERATION_OVER_PATTERN = re.compile(r'(?:iterate|repeat|cycle)\s+(?:over|through|on)\s+(\w+)', re.IGNORECASE)
CYCLE_PATTERN = re.compile(
    r'\b(cycle|circular|continuous|repeating|recurring|ongoing|perpetual|'
    r'returns?|goes back|comes back|repeats?|loops?|recur|'
    r'continuous\s+(?:movement|process|flow|sequence)|'
    r'cycle\s+(?:of|in|continues?|repeats?)|'
    r'again|once more|repeatedly|continuously|'
    r'restart|begin again|start over)',
    re.IGNORECASE
)
COMPONENT_PATTERN_1 = re.compile(r'(?:consists|composed|made)\s+of\s+([^\.]+?)(?:\.|$)', re.IGNORECASE)
COMPONENT_PATTERN_2 = re.compile(r'(?:has|contains|includes|comprises)\s+([^\.]+?)(?:\.|$)', re.IGNORECASE)
COMPONENT_PATTERN_3 = re.compile(r'(?:components?|parts?|elements?)\s+(?:are|is|include|consist of)\s+([^\.]+?)(?:\.|$)', re.IGNORECASE)
CONDITION_MATCH_PATTERN = re.compile(r'(?:if|when|whether)\s+([^,\.]+?)(?:,|\.|then)', re.IGNORECASE)
SEQUENTIAL_KEYWORDS_PATTERN = re.compile(r'\b(first|second|third|fourth|fifth|sixth|then|next|after|finally)', re.IGNORECASE)
PROCESS_TERM_PATTERN_1 = re.compile(r'\b(\w+(?:\s+\w+)?)\s+(?:is|are)\s+(?:the|a|an)?\s+(?:process|stage|phase)', re.IGNORECASE)
PROCESS_TERM_PATTERN_2 = re.compile(r'\b(\w+(?:\s+\w+)?)\s+(?:occurs|happens|takes place)', re.IGNORECASE)
PROCESS_TERM_PATTERN_3 = re.compile(r'(?:the|a|an)\s+(\w+(?:\s+\w+)?)\s+(?:of|in|during|cycle)', re.IGNORECASE)


def generate_diagram(diagram_type: str, context: Dict[str, any]) -> Optional[str]:
    """Main entry point for diagram generation."""
    if diagram_type == "flowchart":
        return generate_flowchart(context)
    elif diagram_type == "structure":
        return generate_structure_diagram(context)
    elif diagram_type == "process":
        return generate_process_diagram(context)
    
    return None


def generate_flowchart(context: Dict[str, any]) -> Optional[str]:
    """Generate a flowchart based on context."""
    question = context.get("question", "")
    answer = context.get("answer", "")
    rag_chunks = context.get("rag_chunks")
    llm_handler = context.get("llm_handler")
    
    # Extract steps once
    steps = extract_steps_from_answer(answer, rag_chunks, llm_handler)
    
    if steps and len(steps) > 0:
        return generate_step_based_flowchart(steps)
    
    if has_decision_points(answer):
        return generate_decision_flowchart(context)
    
    loop_type = context.get("loop_type")
    if loop_type:
        return generate_iterative_flowchart(context, loop_type)
    
    return generate_generic_process_flowchart(context)


def generate_iterative_flowchart(context: Dict[str, any], iteration_type: str) -> str:
    """Generate flowchart for iterative processes."""
    answer = context.get("answer", "")
    question = context.get("question", "")
    iteration_subject = _extract_iteration_subject(answer, question)
    
    conditions = context.get("conditions", [])
    condition_text = conditions[0] if conditions else "Check Condition"
    
    labels = ["Start", iteration_subject, condition_text, "Process", "Continue", "End"]
    max_label_len = max(len(label) for label in labels)
    content_width = max(12, min(max_label_len + 2, 30))
    box_width = content_width + 4
    center_pos = box_width // 2
    
    lines = []
    
    # Start box
    lines.append("┌" + "─" * (box_width - 2) + "┐")
    lines.append("│" + "Start".center(box_width - 2) + "│")
    lines.append("└" + "─" * (center_pos - 1) + "┬" + "─" * (box_width - center_pos - 2) + "┘")
    lines.append(" " * (center_pos - 1) + "│")
    
    # Initialize box
    init_text = _truncate_at_word_boundary(iteration_subject, content_width) if len(iteration_subject) > content_width else iteration_subject
    lines.append(" " * (center_pos - 1) + "┌" + "─" * (box_width - 2) + "┐")
    lines.append(" " * (center_pos - 1) + "│" + init_text.center(box_width - 2) + "│")
    lines.append(" " * (center_pos - 1) + "└" + "─" * (center_pos - 1) + "┬" + "─" * (box_width - center_pos - 2) + "┘")
    lines.append(" " * (center_pos - 1) + " " * (center_pos - 1) + "│")
    
    # Condition box
    condition_text = _truncate_at_word_boundary(condition_text, content_width) if len(condition_text) > content_width else condition_text
    lines.append(" " * (center_pos - 1) + " " * (center_pos - 1) + "┌" + "─" * (box_width - 2) + "┐")
    lines.append(" " * (center_pos - 1) + " " * (center_pos - 1) + "│" + condition_text.center(box_width - 2) + "│")
    lines.append(" " * (center_pos - 1) + " " * (center_pos - 1) + "└" + "─" * (center_pos - 3) + "┬" + "─" * (box_width - center_pos * 2 + 2) + "┬" + "─" * (center_pos - 3) + "┘")
    
    # Branches
    branch_width = min(12, box_width - 6)
    indent_left = " " * (center_pos - 1) + " " * (center_pos - 4)
    branch_spacing = max(2, box_width - center_pos * 2 - branch_width * 2)
    
    lines.append(indent_left + "Yes│" + " " * branch_spacing + "│No")
    lines.append(indent_left + "   │" + " " * branch_spacing + "│")
    
    lines.append(indent_left + "┌" + "─" * (branch_width - 2) + "┐" + " " * branch_spacing + "┌" + "─" * (branch_width - 2) + "┐")
    lines.append(indent_left + "│" + "Process".center(branch_width - 2) + "│" + " " * branch_spacing + "│" + "End".center(branch_width - 2) + "│")
    lines.append(indent_left + "└" + "─" * (branch_width - 2) + "┘" + " " * branch_spacing + "└" + "─" * (branch_width - 2) + "┘")
    lines.append(indent_left + "   │")
    
    # Continue and loop back
    lines.append(indent_left + "   ┌" + "─" * (box_width - 2) + "┐")
    lines.append(indent_left + "   │" + "Continue".center(box_width - 2) + "│")
    lines.append(indent_left + "   └" + "─" * (center_pos - 1) + "┘")
    lines.append(indent_left + "     │")
    lines.append(indent_left + "     └───► (repeat)")
    
    return "\n".join(lines)


def _extract_iteration_subject(answer: str, question: str) -> str:
    """Extract the subject of iteration from text."""
    combined = f"{question} {answer}".lower()
    
    # Try iteration patterns
    match = ITERATION_PATTERN.search(combined)
    if not match:
        match = ITERATION_OVER_PATTERN.search(combined)
    
    if match:
        subject = match.group(1)
        if subject.lower() not in STOPWORDS and len(subject) > 2:
            return subject.capitalize()
    
    return "Item"


def _calculate_adaptive_limits(content_length: int, num_items: int) -> Tuple[int, int]:
    """Calculate adaptive limits based on content size."""
    if content_length < 100:
        max_items = min(num_items, 3)
        max_item_length = 25
    elif content_length < 500:
        max_items = min(num_items, 5)
        max_item_length = 18
    elif content_length < 2000:
        max_items = min(num_items, 8)
        max_item_length = 15
    else:
        max_items = min(num_items, 10)
        max_item_length = 12
    
    return max_items, max_item_length


def extract_steps_from_rag(rag_chunks: List[str]) -> List[str]:
    """Extract steps from RAG chunks using pattern matching."""
    if not rag_chunks:
        return []
    
    steps = []
    combined_text = ' '.join(rag_chunks[:100])  # Limit to first 100 chunks for efficiency
    
    # Try numbered list patterns
    for pattern in [NUMBERED_PATTERN, STEP_PREFIX_PATTERN]:
        matches = pattern.findall(combined_text)
        if matches:
            for match in matches:
                text = match[1] if len(match) > 1 else match[0]
                text = text.strip()
                
                words = text.split()
                clean_text = ' '.join(words[:3]) if len(words) > 4 else ' '.join(words)
                clean_text = TRAILING_PUNCTUATION_PATTERN.sub('', clean_text)
                
                if len(clean_text) >= 3 and clean_text not in steps:
                    steps.append(clean_text)
            
            if len(steps) >= 2:
                return steps[:8]
    
    # Try process list patterns
    for pattern in [PROCESS_LIST_PATTERN, STAGE_LIST_PATTERN]:
        matches = pattern.findall(combined_text)
        if matches:
            for match in matches:
                items = re.split(r',\s*(?:and\s+)?|;\s*|\s+and\s+', match)
                
                for item in items:
                    item = item.strip()
                    item = re.sub(r'^(?:the|a|an)\s+', '', item, flags=re.IGNORECASE)
                    
                    words = item.split()
                    clean_item = ' '.join(words[:2]) if len(words) > 3 else ' '.join(words)
                    clean_item = TRAILING_PUNCTUATION_PATTERN.sub('', clean_item).capitalize()
                    
                    if len(clean_item) >= 3 and clean_item not in steps:
                        steps.append(clean_item)
            
            if len(steps) >= 2:
                return steps[:8]
    
    # Try capitalized terms
    capitalized_terms = CAPITALIZED_TERMS_PATTERN.findall(combined_text)
    if capitalized_terms and len(capitalized_terms) >= 3:
        term_counts = {}
        for term in capitalized_terms:
            if len(term) >= 4 and term.lower() not in STOPWORDS:
                term_counts[term] = term_counts.get(term, 0) + 1
        
        frequent_terms = [term for term, count in term_counts.items() if count >= 2]
        if len(frequent_terms) >= 3:
            return frequent_terms[:8]
    
    return steps[:8] if len(steps) >= 2 else []


def extract_steps_with_llm(answer: str, llm_handler) -> List[str]:
    """Extract steps using LLM."""
    if not answer or not llm_handler or len(answer.strip()) < 10:
        return []
    
    try:
        extraction_prompt = f"""Extract the sequential process flow from this text.
Convert descriptions into standard scientific process names (e.g., "Evaporate" -> "Evaporation").
Ignore locations (like "Lakes") or objects (like "Sun") unless they are the name of a stage.

Text: {answer}

Format: Comma-separated list of process names only.
Process Steps:"""
        
        extracted = llm_handler.generate_response(extraction_prompt, max_tokens=200)
        
        # Clean extraction
        if ":" in extracted:
            extracted = extracted.split(":")[-1]
        
        raw_steps = extracted.split(',') if ',' in extracted else extracted.split('\n')
        
        steps = []
        for s in raw_steps:
            clean = s.strip()
            if not clean:
                continue
            
            clean = LEADING_NUMBERS_PATTERN.sub('', clean)
            
            words = clean.split()
            if not words or len(words) > 4:
                continue
            
            if len(words) > 3:
                clean = ' '.join(words[:3])
            
            clean = clean.strip().capitalize()
            clean = TRAILING_PUNCTUATION_PATTERN.sub('', clean)
            
            if len(clean) >= 3 and clean not in steps:
                steps.append(clean)
        
        return steps if len(steps) >= 2 else []
        
    except Exception as e:
        logger.debug(f"LLM extraction failed: {e}")
        return []


def extract_steps_from_answer(answer: str, rag_chunks: Optional[List[str]] = None, llm_handler=None) -> List[str]:
    """Smart extraction of process steps - tries LLM first, then RAG."""
    # Try LLM first (most accurate)
    if llm_handler:
        llm_steps = extract_steps_with_llm(answer, llm_handler)
        if len(llm_steps) >= 2:
            return llm_steps
    
    # Fallback to RAG chunks
    if rag_chunks:
        rag_steps = extract_steps_from_rag(rag_chunks)
        if len(rag_steps) >= 2:
            return rag_steps
    
    return []


def _truncate_at_word_boundary(text: str, max_length: int) -> str:
    """Truncate text at word boundary."""
    if len(text) <= max_length:
        return text
    
    words = text.split()
    truncated = []
    
    for word in words:
        potential = ' '.join(truncated + [word])
        if len(potential) <= max_length:
            truncated.append(word)
        else:
            break
    
    return ' '.join(truncated) if truncated else text[:max_length]


@lru_cache(maxsize=128)
def has_decision_points(answer: str) -> bool:
    """Check if answer contains decision points (cached)."""
    return bool(DECISION_KEYWORDS_PATTERN.search(answer))


def _calculate_box_dimensions(steps: List[str]) -> Tuple[int, int]:
    """Calculate optimal box dimensions based on step lengths."""
    if not steps:
        return 15, 13
    
    max_step_len = max(len(step) for step in steps)
    
    # Determine content width based on max step length
    if max_step_len <= 10:
        content_width = 10
    elif max_step_len <= 15:
        content_width = 15
    elif max_step_len <= 20:
        content_width = 20
    elif max_step_len <= 30:
        content_width = 30
    else:
        content_width = 35
    
    # Adjust for number of steps
    if len(steps) > 8:
        content_width = min(content_width, 18)
    elif len(steps) > 5:
        content_width = min(content_width, 22)
    
    box_width = content_width + 4
    return box_width, content_width


def generate_step_based_flowchart(steps: List[str]) -> str:
    """Generate a step-based flowchart."""
    if not steps:
        return _generate_minimal_flowchart()
    
    box_width, content_width = _calculate_box_dimensions(steps)
    
    # Format steps
    formatted_steps = []
    for step in steps:
        step = step.strip()
        if len(step) > content_width:
            step = _truncate_at_word_boundary(step, content_width)
        
        if step:
            step = step[0].upper() + step[1:] if len(step) > 1 else step.upper()
        
        formatted_steps.append(step)
    
    lines = []
    
    # Start box
    start_label = "Start"
    start_box_width = max(len(start_label) + 2, box_width)
    center = start_box_width // 2
    
    lines.append("┌" + "─" * (start_box_width - 2) + "┐")
    lines.append("│" + start_label.center(start_box_width - 2) + "│")
    lines.append("└" + "─" * (center - 1) + "┬" + "─" * (start_box_width - center - 1) + "┘")
    lines.append(" " * (center - 1) + "│")
    
    # Step boxes
    for i, step in enumerate(formatted_steps):
        step_padded = step.center(content_width)
        
        lines.append(" " * (center - 1) + "┌" + "─" * (content_width - 2) + "┐")
        lines.append(" " * (center - 1) + "│" + step_padded + "│")
        lines.append(" " * (center - 1) + "└" + "─" * (content_width - 2) + "┘")
        
        if i < len(formatted_steps) - 1:
            lines.append(" " * (center - 1) + "│")
        lines.append(" " * (center - 1) + "┌" + "─" * (box_width - 2) + "┐")
        lines.append(" " * (center - 1) + "│" + formatted[1].center(box_width - 2) + "│")
        lines.append(" " * (center - 1) + "└" + "─" * (box_width - 2) + "┘")
    else:
        # Multiple components
        lines.append("┌" + "─" * (box_width - 2) + "┐")
        lines.append("│" + formatted[0].center(box_width - 2) + "│")
        lines.append("└" + "─" * (center - 1) + "┬" + "─" * (box_width - center - 1) + "┘")
        lines.append(" " * (center - 1) + "│")
        
        for comp in formatted[1:-1]:
            lines.append(" " * (center - 1) + "┌" + "─" * (box_width - 2) + "┐")
            lines.append(" " * (center - 1) + "│" + comp.center(box_width - 2) + "│")
            lines.append(" " * (center - 1) + "└" + "─" * (center - 1) + "┬" + "─" * (box_width - center - 1) + "┘")
            lines.append(" " * (center - 1) + " " * (center - 1) + "│")
        
        if len(formatted) > 1:
            indent = " " * (center - 1) * (len(formatted) - 1)
            lines.append(indent + "┌" + "─" * (box_width - 2) + "┐")
            lines.append(indent + "│" + formatted[-1].center(box_width - 2) + "│")
            lines.append(indent + "└" + "─" * (box_width - 2) + "┘")
    
    return "\n".join(lines)


def _generate_minimal_structure() -> str:
    """Generate minimal structure diagram."""
    return """┌────────┐
│Component│
└─────────┘"""


@lru_cache(maxsize=128)
def _is_cyclic_process(question: str, answer: str) -> bool:
    """Check if process is cyclic (cached)."""
    combined = f"{question} {answer}".lower()
    return bool(CYCLE_PATTERN.search(combined))


def generate_cycle_diagram(steps: List[str]) -> str:
    """Generate a cycle diagram."""
    if not steps or len(steps) < 2:
        return generate_step_based_flowchart(steps)
    
    steps = steps[:6]
    
    max_step_len = max(len(step) for step in steps)
    content_width = max(12, min(max_step_len + 2, 22))
    box_width = content_width + 4
    center = box_width // 2
    
    # Format steps
    formatted_steps = []
    for step in steps:
        step = step.strip()
        if len(step) > content_width:
            step = _truncate_at_word_boundary(step, content_width)
        if step:
            step = step[0].upper() + step[1:] if len(step) > 1 else step.upper()
        formatted_steps.append(step)
    
    lines = []
    
    for i, step in enumerate(formatted_steps):
        step_padded = step.center(content_width)
        
        if i == 0:
            lines.append("┌" + "─" * (box_width - 2) + "┐")
            lines.append("│" + step_padded + "│")
            lines.append("└" + "─" * (center - 1) + "┬" + "─" * (box_width - center - 1) + "┘")
            lines.append(" " * (center - 1) + "│")
        else:
            lines.append(" " * (center - 1) + "┌" + "─" * (box_width - 2) + "┐")
            lines.append(" " * (center - 1) + "│" + step_padded + "│")
            
            if i < len(formatted_steps) - 1:
                lines.append(" " * (center - 1) + "└" + "─" * (center - 1) + "┬" + "─" * (box_width - center - 1) + "┘")
                lines.append(" " * (center - 1) + " " * (center - 1) + "│")
            else:
                lines.append(" " * (center - 1) + "└" + "─" * (center - 1) + "┘")
                lines.append(" " * (center - 1) + " " * (center - 1) + "│")
                lines.append(" " * (center - 1) + " " * (center - 1) + "└───► (cycle)")
                lines.append(" " * (center - 2) + "◄───┘")
                lines.append(" " * (center - 2) + "│")
                lines.append(" " * (center - 2) + "└─── (repeats)")
    
    return "\n".join(lines)


def generate_process_diagram(context: Dict[str, any]) -> Optional[str]:
    """Generate a process diagram."""
    answer = context.get("answer", "")
    question = context.get("question", "")
    rag_chunks = context.get("rag_chunks")
    llm_handler = context.get("llm_handler")
    
    is_cycle = _is_cyclic_process(question, answer)
    steps = extract_steps_from_answer(answer, rag_chunks, llm_handler)
    
    if steps and len(steps) > 0:
        if is_cycle and len(steps) >= 2:
            return generate_cycle_diagram(steps)
        else:
            return generate_step_based_flowchart(steps)
    
    # Try extracting from question
    if not steps and question:
        question_steps = extract_steps_from_answer(question, rag_chunks, llm_handler)
        if question_steps:
            return generate_step_based_flowchart(question_steps)
    
    # Try extracting key terms
    if not steps and answer:
        key_terms = _extract_key_process_terms(answer)
        if key_terms and len(key_terms) >= 2:
            return generate_step_based_flowchart(key_terms)
    
    # Generic fallback
    num_steps = context.get("num_steps", 3)
    if num_steps == 3 and answer:
        sequential_count = len(SEQUENTIAL_KEYWORDS_PATTERN.findall(answer))
        if sequential_count > 0:
            num_steps = min(sequential_count + 1, 6)
    
    num_steps = max(2, min(num_steps, 6))
    generic_steps = [f"Step {i}" for i in range(1, num_steps + 1)]
    
    return generate_step_based_flowchart(generic_steps)


def _extract_key_process_terms(text: str) -> List[str]:
    """Extract key process terms from text."""
    terms = []
    
    patterns = [PROCESS_TERM_PATTERN_1, PROCESS_TERM_PATTERN_2, PROCESS_TERM_PATTERN_3]
    
    for pattern in patterns:
        matches = pattern.findall(text)
        for match in matches:
            if isinstance(match, tuple):
                match = match[-1]
            term = match.strip()
            if term and len(term) > 3 and term.lower() not in STOPWORDS:
                words = term.split()
                meaningful = [w for w in words[:2] if w.lower() not in STOPWORDS]
                if meaningful:
                    term = ' '.join(meaningful).capitalize()
                    if term not in terms:
                        terms.append(term)
    
    return terms[:6]
    
    # End box
    end_label = "Complete"
    lines.append(" " * (center - 1) + "┌" + "─" * (box_width - 2) + "┐")
    lines.append(" " * (center - 1) + "│" + end_label.center(box_width - 2) + "│")
    lines.append(" " * (center - 1) + "└" + "─" * (box_width - 2) + "┘")
    
    return "\n".join(lines)


def _generate_minimal_flowchart() -> str:
    """Generate minimal fallback flowchart."""
    return """┌──────┐
│Start │
└──┬───┘
   │
┌──▼───┐
│Step 1│
└──┬───┘
   │
┌──▼───┐
│ End  │
└──────┘"""


def generate_decision_flowchart(context: Dict[str, any]) -> str:
    """Generate a decision-based flowchart."""
    answer = context.get("answer", "")
    conditions = context.get("conditions", [])
    
    # Extract condition
    condition_text = "Condition Check"
    if conditions:
        condition_text = conditions[0]
        if len(condition_text) > 20:
            condition_text = _truncate_at_word_boundary(condition_text, 20)
    else:
        cond_match = CONDITION_MATCH_PATTERN.search(answer)
        if cond_match:
            condition_text = cond_match.group(1).strip()
            if len(condition_text) > 20:
                condition_text = _truncate_at_word_boundary(condition_text, 20)
    
    path_a = "Path A"
    path_b = "Path B"
    
    max_label_len = max(len(condition_text), len(path_a), len(path_b), 10)
    content_width = min(max(max_label_len + 2, 12), 25)
    box_width = content_width + 4
    center = box_width // 2
    
    lines = []
    
    # Start
    lines.append("┌" + "─" * (box_width - 2) + "┐")
    lines.append("│" + "Start".center(box_width - 2) + "│")
    lines.append("└" + "─" * (center - 1) + "┬" + "─" * (box_width - center - 1) + "┘")
    lines.append(" " * (center - 1) + "│")
    
    # Condition
    lines.append(" " * (center - 1) + "┌" + "─" * (box_width - 2) + "┐")
    lines.append(" " * (center - 1) + "│" + condition_text.center(box_width - 2) + "│")
    lines.append(" " * (center - 1) + "└" + "─" * (center // 2) + "┬" + "─" * (center) + "┬" + "─" * (center // 2) + "┘")
    
    # Branches
    indent_yes = " " * (center - 2)
    branch_spacing = center
    
    lines.append(indent_yes + "Yes│" + " " * branch_spacing + "│No")
    lines.append(indent_yes + "   │" + " " * branch_spacing + "│")
    
    path_box_width = min(box_width - 4, 15)
    lines.append(indent_yes + "┌" + "─" * (path_box_width - 2) + "┐" + " " * 2 + "┌" + "─" * (path_box_width - 2) + "┐")
    lines.append(indent_yes + "│" + path_a.center(path_box_width - 2) + "│" + " " * 2 + "│" + path_b.center(path_box_width - 2) + "│")
    lines.append(indent_yes + "└" + "─" * (path_box_width - 2) + "┘" + " " * 2 + "└" + "─" * (path_box_width - 2) + "┘")
    lines.append(indent_yes + "   │" + " " * branch_spacing + "│")
    lines.append(indent_yes + "   └" + "─" * (branch_spacing) + "─" + "┘")
    lines.append(indent_yes + "     │")
    
    # Continue
    lines.append(indent_yes + "     ┌" + "─" * (box_width - 2) + "┐")
    lines.append(indent_yes + "     │" + "Continue".center(box_width - 2) + "│")
    lines.append(indent_yes + "     └" + "─" * (box_width - 2) + "┘")
    
    return "\n".join(lines)


def generate_generic_process_flowchart(context: Dict[str, any]) -> str:
    """Generate a generic process flowchart."""
    num_steps = context.get("num_steps", 3)
    answer = context.get("answer", "")
    
    if num_steps == 3 and answer:
        step_count = len(SEQUENTIAL_KEYWORDS_PATTERN.findall(answer))
        if step_count > 0:
            num_steps = min(step_count + 1, 6)
    
    num_steps = max(2, min(num_steps, 6))
    steps = [f"Step {i}" for i in range(1, num_steps + 1)]
    
    return generate_step_based_flowchart(steps)


def generate_structure_diagram(context: Dict[str, any]) -> Optional[str]:
    """Generate a structure diagram."""
    answer = context.get("answer", "")
    question = context.get("question", "")
    components = context.get("components", [])
    
    if not components:
        components = extract_structure_components(answer, question)
    
    if components:
        return generate_component_structure(components)
    
    if answer and re.search(r'(?:top|upper|highest|main).*?(?:level|layer|tier)', answer, re.IGNORECASE):
        levels = ["Top Level", "Middle Level", "Bottom Level"]
        return generate_component_structure(levels)
    
    return _generate_minimal_structure()


def extract_structure_components(answer: str, question: str) -> List[str]:
    """Extract structural components from text."""
    if not answer:
        return []
    
    components = []
    
    # Try component patterns
    for pattern in [COMPONENT_PATTERN_1, COMPONENT_PATTERN_2, COMPONENT_PATTERN_3]:
        matches = pattern.findall(answer)
        if matches:
            for match in matches:
                parts = re.split(r'[,;]\s*|\s+and\s+|\s+or\s+', match)
                
                for part in parts:
                    part = part.strip()
                    part = re.sub(r'^(?:the|a|an)\s+', '', part, flags=re.IGNORECASE)
                    
                    words = part.split()
                    meaningful = [w for w in words[:3] if w.lower() not in STOPWORDS]
                    if meaningful:
                        comp = ' '.join(meaningful).capitalize()
                        if len(comp) >= 2 and comp not in components:
                            components.append(comp)
            if components:
                break
    
    # Try capitalized terms
    if not components:
        capitalized = CAPITALIZED_TERMS_PATTERN.findall(answer)
        components.extend([cap for cap in capitalized[:10] if len(cap) >= 3 and cap.lower() not in STOPWORDS])
    
    # Try question components
    if not components and question:
        question_components = re.findall(r'(?:parts?|components?|elements?)\s+of\s+(\w+)', question, re.IGNORECASE)
        if question_components:
            components.extend([c.capitalize() for c in question_components[:3]])
    
    max_items, _ = _calculate_adaptive_limits(len(answer), len(components))
    return components[:max_items]


def generate_component_structure(components: List[str]) -> str:
    """Generate a component structure diagram."""
    if not components:
        return _generate_minimal_structure()
    
    max_comp_len = max(len(comp) for comp in components)
    content_width = max(12, min(max_comp_len + 2, 30))
    box_width = content_width + 4
    center = box_width // 2
    
    # Format components
    formatted = [_truncate_at_word_boundary(comp, content_width) if len(comp) > content_width else comp for comp in components]
    
    lines = []
    
    if len(formatted) == 1:
        lines.append("┌" + "─" * (box_width - 2) + "┐")
        lines.append("│" + formatted[0].center(box_width - 2) + "│")
        lines.append("└" + "─" * (box_width - 2) + "┘")
    elif len(formatted) == 2:
        lines.append("┌" + "─" * (box_width - 2) + "┐")
        lines.append("│" + formatted[0].center(box_width - 2) + "│")
        lines.append("└" + "─" * (center - 1) + "┬" + "─" * (box_width - center - 1) + "┘")
        lines.append(" " * (center - 1) + "│")
        lines.append(" " * (center - 1) + "┌" + "─" * (box_width - 2) + "┐")
        lines.append(" " * (center - 1) + "│" + formatted[1].center(box_width - 2) + "│")
        lines.append(" " * (center - 1) + "└" + "─" * (box_width - 2) + "┘")
    else:
        lines.append("┌" + "─" * (box_width - 2) + "┐")
        lines.append("│" + formatted[0].center(box_width - 2) + "│")
        lines.append("└" + "─" * (center - 1) + "┬" + "─" * (box_width - center - 1) + "┘")
        lines.append(" " * (center - 1) + "│")
        
        for comp in formatted[1:-1]:
            lines.append(" " * (center - 1) + "┌" + "─" * (box_width - 2) + "┐")
            lines.append(" " * (center - 1) + "│" + comp.center(box_width - 2) + "│")
            lines.append(" " * (center - 1) + "└" + "─" * (center - 1) + "┬" + "─" * (box_width - center - 1) + "┘")
            lines.append(" " * (center - 1) + " " * (center - 1) + "│")
        
        if len(formatted) > 1:
            lines.append(" " * (center - 1) + "┌" + "─" * (box_width - 2) + "┐")
            lines.append(" " * (center - 1) + "│" + formatted[-1].center(box_width - 2) + "│")
            lines.append(" " * (center - 1) + "└" + "─" * (box_width - 2) + "┘")

    return "\n".join(lines)