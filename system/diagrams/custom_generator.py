"""
Custom ASCII Diagram Generator

Pure Python generator that creates ASCII diagrams using box-drawing characters.
No external dependencies - uses only standard library.
Fully adaptive and handles real-world edge cases with dynamic sizing.
"""

import re
from typing import Dict, Optional, List, Tuple

# Common stopwords for text processing
STOPWORDS = {
    "the", "is", "are", "a", "an", "to", "of", "and", "or", "for", "in", "on", "at", "by", "that",
    "this", "it", "as", "be", "with", "from", "into", "their", "its", "they", "them", "can", "will",
    "about", "how", "what", "why", "which", "who", "whose", "when", "where", "than", "then", "also"
}


def generate_diagram(diagram_type: str, context: Dict[str, any]) -> Optional[str]:
    """
    Generate ASCII diagram based on type and context.
    
    Args:
        diagram_type: Type of diagram ("flowchart", "structure", "process")
        context: Dictionary with relevant information
    
    Returns:
        ASCII diagram string or None if generation fails
    """
    if diagram_type == "flowchart":
        return generate_flowchart(context)
    elif diagram_type == "structure":
        return generate_structure_diagram(context)
    elif diagram_type == "process":
        return generate_process_diagram(context)
    
    return None


def generate_flowchart(context: Dict[str, any]) -> Optional[str]:
    """
    Generate flowchart diagram based on context.
    Fully universal - works for EVERY subject and EVERY question type.
    
    Strategy: Let content determine the diagram type based on semantic patterns,
    not domain-specific assumptions. Works for:
    - Science: processes, cycles, mechanisms
    - English: grammar rules, decision trees, sentence structures
    - Math: algorithms, procedures, problem-solving steps
    - History: timelines, cause-effect flows
    - Programming: loops, conditionals, algorithms
    - ANY other subject
    
    Args:
        context: Dictionary with question, answer, and extracted info
    
    Returns:
        ASCII flowchart string
    """
    question = context.get("question", "")
    answer = context.get("answer", "")
    
    # Extract key concepts from answer (works for ANY subject, ANY format)
    steps = extract_steps_from_answer(answer)
    
    # Priority 1: If we found clear steps, use step-based flowchart
    # Universal: works for ANY sequential process in ANY subject
    if steps and len(steps) > 0:
        return generate_step_based_flowchart(steps)
    
    # Priority 2: Check for decision points (universal conditional logic)
    # Works for: choices, conditions, decisions in ANY domain
    # Examples: "if X then Y" (any subject), "when to use A vs B" (any subject)
    if has_decision_points(answer):
        return generate_decision_flowchart(context)
    
    # Priority 3: Check for iterative/cyclic processes (universal, not just programming)
    # Works for: any repeating process, cycle, or iteration in ANY subject
    # Examples: water cycle, life cycle, iterative problem-solving, loops
    loop_type = context.get("loop_type")
    if loop_type:
        # Use generic iterative flowchart for ANY iterative process
        return generate_iterative_flowchart(context, loop_type)
    
    # Priority 4: Generic flowchart for any process (universal fallback)
    # Works for ANY subject when no specific pattern is found
    return generate_generic_process_flowchart(context)


def generate_iterative_flowchart(context: Dict[str, any], iteration_type: str) -> str:
    """
    Generate flowchart for ANY iterative/cyclic process.
    Universal - works for programming loops, natural cycles, repeating processes, etc.
    
    Args:
        context: Dictionary with context information
        iteration_type: Type of iteration ("for", "while", "cycle", "repeat", etc.)
    
    Returns:
        ASCII flowchart string
    """
    # Extract iteration details from context (works for any domain)
    answer = context.get("answer", "")
    question = context.get("question", "")
    
    # Extract what's being iterated (could be: items, steps, stages, elements, etc.)
    # Works for: "for each item", "while condition", "repeat process", "cycle continues"
    iteration_subject = _extract_iteration_subject(answer, question)
    
    # Extract condition/check (works for any domain)
    conditions = context.get("conditions", [])
    condition_text = conditions[0] if conditions else "Check Condition"
    
    # Adaptive sizing based on content
    labels = ["Start", iteration_subject, condition_text, "Process", "Continue", "End"]
    max_label_len = max(len(label) for label in labels) if labels else 12
    content_width = max(12, min(max_label_len + 2, 30))
    box_width = content_width + 4
    center_pos = box_width // 2
    
    lines = []
    
    # Start
    lines.append("┌" + "─" * (box_width - 2) + "┐")
    lines.append("│" + "Start".center(box_width - 2) + "│")
    lines.append("└" + "─" * (center_pos - 1) + "┬" + "─" * (box_width - center_pos - 2) + "┘")
    lines.append(" " * (center_pos - 1) + "│")
    
    # Initialize/Prepare (adaptive label)
    init_text = iteration_subject
    if len(init_text) > content_width:
        init_text = _truncate_at_word_boundary(init_text, content_width)
    lines.append(" " * (center_pos - 1) + "┌" + "─" * (box_width - 2) + "┐")
    lines.append(" " * (center_pos - 1) + "│" + init_text.center(box_width - 2) + "│")
    lines.append(" " * (center_pos - 1) + "└" + "─" * (center_pos - 1) + "┬" + "─" * (box_width - center_pos - 2) + "┘")
    lines.append(" " * (center_pos - 1) + " " * (center_pos - 1) + "│")
    
    # Condition check (universal)
    if len(condition_text) > content_width:
        condition_text = _truncate_at_word_boundary(condition_text, content_width)
    lines.append(" " * (center_pos - 1) + " " * (center_pos - 1) + "┌" + "─" * (box_width - 2) + "┐")
    lines.append(" " * (center_pos - 1) + " " * (center_pos - 1) + "│" + condition_text.center(box_width - 2) + "│")
    lines.append(" " * (center_pos - 1) + " " * (center_pos - 1) + "└" + "─" * (center_pos - 3) + "┬" + "─" * (box_width - center_pos * 2 + 2) + "┬" + "─" * (center_pos - 3) + "┘")
    
    # Decision branches (universal Yes/No or True/False)
    branch_width = min(12, box_width - 6)
    indent_left = " " * (center_pos - 1) + " " * (center_pos - 4)
    branch_spacing = max(2, box_width - center_pos * 2 - branch_width * 2)
    
    lines.append(indent_left + "Yes│" + " " * branch_spacing + "│No")
    lines.append(indent_left + "   │" + " " * branch_spacing + "│")
    
    # Process and End boxes (universal labels)
    process_label = "Process"
    end_label = "End"
    lines.append(indent_left + "┌" + "─" * (branch_width - 2) + "┐" + " " * branch_spacing + "┌" + "─" * (branch_width - 2) + "┐")
    lines.append(indent_left + "│" + process_label.center(branch_width - 2) + "│" + " " * branch_spacing + "│" + end_label.center(branch_width - 2) + "│")
    lines.append(indent_left + "└" + "─" * (branch_width - 2) + "┘" + " " * branch_spacing + "└" + "─" * (branch_width - 2) + "┘")
    lines.append(indent_left + "   │")
    
    # Continue/Update (universal)
    continue_text = "Continue"
    lines.append(indent_left + "   ┌" + "─" * (box_width - 2) + "┐")
    lines.append(indent_left + "   │" + continue_text.center(box_width - 2) + "│")
    lines.append(indent_left + "   └" + "─" * (center_pos - 1) + "┘")
    lines.append(indent_left + "     │")
    lines.append(indent_left + "     └───► (repeat)")
    
    return "\n".join(lines)


def _extract_iteration_subject(answer: str, question: str) -> str:
    """
    Extract what's being iterated/cycled (works for ANY domain).
    Examples: "items", "steps", "stages", "elements", "processes", etc.
    """
    combined = f"{question} {answer}".lower()
    
    # Universal patterns for iteration subjects
    patterns = [
        r'(?:for|each|every)\s+(\w+)',  # "for each item", "every step"
        r'(?:iterate|repeat|cycle)\s+(?:over|through|on)\s+(\w+)',  # "iterate over items"
        r'(\w+)\s+(?:in|of)\s+(?:the|a|an)?\s+(?:cycle|loop|iteration|process)',  # "items in the cycle"
    ]
    
    import re
    for pattern in patterns:
        match = re.search(pattern, combined, re.IGNORECASE)
        if match:
            subject = match.group(1)
            if subject.lower() not in STOPWORDS and len(subject) > 2:
                return subject.capitalize()
    
    # Default to generic term
    return "Item"


def _calculate_adaptive_limits(content_length: int, num_items: int) -> Tuple[int, int]:
    """
    Calculate adaptive limits based on content size and number of items.
    Handles edge cases: very short/long content, many/few items.
    
    Args:
        content_length: Length of content text
        num_items: Number of items to display
    
    Returns:
        Tuple of (max_items, max_item_length)
    """
    # Adaptive max items based on content complexity
    if content_length < 100:
        max_items = min(num_items, 3)  # Short content: max 3 items
    elif content_length < 500:
        max_items = min(num_items, 5)  # Medium content: max 5 items
    elif content_length < 2000:
        max_items = min(num_items, 8)  # Long content: max 8 items
    else:
        max_items = min(num_items, 10)  # Very long: max 10 items
    
    # Adaptive item length based on number of items
    if num_items <= 3:
        max_item_length = 25  # Few items: can be longer
    elif num_items <= 5:
        max_item_length = 18  # Medium: moderate length
    elif num_items <= 8:
        max_item_length = 15  # Many items: shorter
    else:
        max_item_length = 12  # Very many: very short
    
    return max_items, max_item_length


def extract_steps_from_answer(answer: str) -> List[str]:
    """
    Extract steps or stages from the answer text using multiple strategies.
    Fully adaptive - handles various formats and edge cases.
    
    Args:
        answer: Answer text
    
    Returns:
        List of step descriptions (cleaned and shortened adaptively)
    """
    if not answer or len(answer.strip()) < 10:
        return []
    
    steps = []
    answer_lower = answer.lower()
    
    # Strategy 1: Numbered steps (most reliable) - multiple patterns
    # Note: Sequential word pattern (first, second, third) moved to Strategy 1.5
    numbered_patterns = [
        r'(?:^|\n)\s*Stage\s+(\d+)[:\.]\s+(.+?)(?=\n\s*Stage\s+\d+[:\.]|\n\n|$)',  # "Stage 1: text" (prioritize this)
        r'(?:^|\n)\s*(\d+)[\.\)]\s+(.+?)(?=\n\s*\d+[\.\)]|\n\n|$)',  # "1. Step text"
        r'(?:step|stage|phase|part)\s+(\d+)[:\.]\s*(.+?)(?=\n|\.|$)',  # "Step 1: text"
    ]
    
    for pattern in numbered_patterns:
        matches = re.findall(pattern, answer, re.IGNORECASE | re.MULTILINE)
        if matches:
            for match in matches:
                # Handle tuple matches (number + text) or single matches
                if isinstance(match, tuple):
                    # For "Stage 1: text" pattern, match[0] is number, match[1] is text
                    if len(match) == 2:
                        step_text = match[1].strip()  # Take the text part
                    else:
                        step_text = match[-1].strip()  # Take last element
                else:
                    step_text = match.strip()
                
                if step_text and len(step_text) > 3:
                    # Extract stage name (first sentence or key term)
                    # For "Stage 1: Egg" -> extract "Egg"
                    # For "Stage 2: Pupa\nThe pupae grow..." -> extract "Pupa"
                    first_line = step_text.split('\n')[0].strip()
                    # Remove common prefixes
                    first_line = re.sub(r'^(?:the|a|an)\s+', '', first_line, flags=re.IGNORECASE)
                    # Take first meaningful word/phrase (usually the stage name)
                    words = first_line.split()
                    meaningful = [w for w in words[:2] if w.lower() not in STOPWORDS and len(w) > 1]
                    if meaningful:
                        cleaned = ' '.join(meaningful).capitalize()
                        # Remove trailing punctuation
                        cleaned = re.sub(r'[.,;:]+$', '', cleaned)
                        if cleaned and cleaned not in steps:
                            steps.append(cleaned)
            
            if steps:
                break  # Found numbered steps, use them
    
    # Strategy 1.5: Sequential word enumeration (first, second, third, then, finally)
    # This should catch sequences like "First, X. Then, Y. Finally, Z."
    if not steps:
        # Look for all sequential markers in order
        sequential_word_patterns = [
            (r'(?:^|\.\s+)(?:first|firstly)[\s:,]+(.+?)(?=\.\s+(?:then|next|second|finally)|$)', 'first'),
            (r'(?:^|\.\s+)(?:second|secondly)[\s:,]+(.+?)(?=\.\s+(?:then|next|third|finally)|$)', 'second'),
            (r'(?:^|\.\s+)(?:third|thirdly)[\s:,]+(.+?)(?=\.\s+(?:then|next|fourth|finally)|$)', 'third'),
            (r'(?:^|\.\s+)(?:then|next|after that)[\s:,]+(.+?)(?=\.\s+(?:then|next|finally)|$)', 'then'),
            (r'(?:^|\.\s+)(?:finally|lastly|ultimately)[\s:,]+(.+?)(?=\.|$)', 'finally'),
        ]
        
        for pattern, label in sequential_word_patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE | re.DOTALL)
            if matches:
                for match in matches[:2]:  # Max 2 per pattern type
                    cleaned = _extract_meaningful_phrase(match.strip())
                    if cleaned and len(cleaned) > 3 and cleaned not in steps:
                        steps.append(cleaned)
    
    # Strategy 2: Sequential markers (then, next, after, etc.)
    # Enhanced to capture First, Second, Then, Finally sequences
    if not steps:
        # First, explicitly look for First/Then/Finally sequences
        first_then_pattern = r'(?:first|firstly)[\s,]+(.+?)(?=\.|then|next|finally|$)'
        then_pattern = r'(?:then|next|after|following|subsequently)[\s,]+(.+?)(?=\.|then|next|finally|$)'
        finally_pattern = r'(?:finally|lastly|ultimately)[\s,]+(.+?)(?=\.|$)'
        
        # Try to extract First step
        first_matches = re.findall(first_then_pattern, answer, re.IGNORECASE | re.DOTALL)
        if first_matches:
            for match in first_matches[:1]:  # Usually only one "First"
                # Clean and extract just the action/process
                cleaned = _extract_meaningful_phrase(match.strip())
                if cleaned and cleaned not in steps:
                    steps.append(cleaned)
        
        # Extract Then/Next steps
        then_matches = re.findall(then_pattern, answer, re.IGNORECASE | re.DOTALL)
        if then_matches:
            for match in then_matches[:5]:  # Limit to 5 "then" steps
                cleaned = _extract_meaningful_phrase(match.strip())
                if cleaned and cleaned not in steps:
                    steps.append(cleaned)
        
        # Extract Finally step
        finally_matches = re.findall(finally_pattern, answer, re.IGNORECASE | re.DOTALL)
        if finally_matches:
            for match in finally_matches[:1]:  # Usually only one "Finally"
                cleaned = _extract_meaningful_phrase(match.strip())
                if cleaned and cleaned not in steps:
                    steps.append(cleaned)
    
    # Strategy 3: Action verbs indicating processes
    if not steps:
        action_patterns = [
            r'(\w+(?:\s+\w+){0,2})\s+(?:absorbs|converts|produces|creates|splits|releases|utilizes|transforms|changes|becomes)',
            r'(\w+(?:\s+\w+){0,2})\s+(?:uses|utilizes|applies|performs|executes)',
            r'(?:the|a|an)\s+(\w+(?:\s+\w+){0,1})\s+(?:process|stage|phase|step|action)',
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            if matches:
                for match in matches[:8]:
                    words = match.split()
                    words = [w for w in words if w.lower() not in STOPWORDS]
                    if words:
                        step = ' '.join(words[:4]).capitalize()
                        if len(step) >= 3 and step not in steps:
                            steps.append(step)
                if steps:
                    break
    
    # Strategy 4: Process lists (comma-separated items) - Universal extraction
    # Works for: any list format in any subject (processes, steps, components, etc.)
    if not steps:
        process_list_patterns = [
            # Pattern 1: "involves processes such as X, Y, Z" - handle "processes such as" explicitly
            r'(?:involves|includes|contains|has)\s+(?:processes?|steps?|stages?|phases?|parts?|components?)\s+(?:such as|like|including|namely)\s+([^\.]+?)(?:\.|$)',
            # Pattern 2: "including X, Y, Z" or "such as X, Y, Z" (direct)
            r'(?:including|such as|like|namely)\s+([^\.]+?)(?:\.|$)',
            # Pattern 3: "consists of X, Y, Z" or "comprises X, Y, Z"
            r'(?:consists of|comprises)\s+([^\.]+?)(?:\.|$)',
            # Pattern 4: Labeled lists: "processes: X, Y, Z" or "steps: A, B, C"
            r'(?:processes?|steps?|stages?|phases?|parts?|components?|elements?|items?)\s*[:]\s*([^\.]+?)(?:\.|$)',
            # Pattern 5: Verb lists: "processes are X, Y, Z" or "steps include A, B, C"
            r'(?:processes?|steps?|stages?|phases?)\s+(?:are|is|include|consist of|comprise|contain)\s+([^\.]+?)(?:\.|$)',
            # Pattern 6: Generic lists: "are X, Y, and Z" (works for any subject)
            r'(?:are|is)\s+([^\.]+?)(?:\.|$)',
            # Pattern 7: Action lists: "X, Y, Z occur" or "X, Y, Z happen"
            r'([^\.]+?)\s+(?:occur|happen|take place|begin|start)(?:\.|$)',
        ]
        
        for pattern in process_list_patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[-1]
                    
                    # Split by commas, "and", "or" - handle various formats
                    # Pattern: "X, Y, and Z" or "X, Y, Z" or "X and Y"
                    process_list = re.split(r'[,;]\s*|\s+and\s+|\s+or\s+', match)
                    
                    for process in process_list:
                        process = process.strip()
                        
                        # Skip empty or very short
                        if not process or len(process) < 2:
                            continue
                        
                        # Remove common prefixes/suffixes
                        process = re.sub(r'^(?:the|a|an)\s+', '', process, flags=re.IGNORECASE)
                        process = re.sub(r'\s+(?:process|stage|phase|step|part)$', '', process, flags=re.IGNORECASE)
                        
                        # Extract key term - adaptive extraction (works for any format)
                        words = process.split()
                        meaningful = [w for w in words if w.lower() not in STOPWORDS and len(w) > 1]
                        
                        if meaningful:
                            # Adaptive: take 1-3 words based on content
                            # Single-word processes: "evaporation", "condensation"
                            # Multi-word: "water vapor", "carbon dioxide"
                            num_words = min(len(meaningful), 3)
                            step = ' '.join(meaningful[:num_words]).capitalize()
                            # Clean up: remove trailing punctuation
                            step = re.sub(r'[.,;]+$', '', step)
                            
                            if len(step) >= 2 and step not in steps:  # Minimum 2 chars
                                steps.append(step)
                
                # If we found items, use them (don't continue to other strategies)
                # Adaptive threshold: need at least 2 items for a meaningful diagram
                if steps and len(steps) >= 2:
                    break
    
    # Strategy 5: Bullet points or list items
    if not steps:
        bullet_patterns = [
            r'^\s*[-•*]\s+(.+?)(?=\n|$)',  # Bullet points
            r'^\s*[○●]\s+(.+?)(?=\n|$)',  # Circle bullets
        ]
        
        for pattern in bullet_patterns:
            matches = re.findall(pattern, answer, re.MULTILINE | re.IGNORECASE)
            if matches:
                for match in matches[:10]:
                    cleaned = _extract_meaningful_phrase(match.strip())
                    if cleaned and cleaned not in steps:
                        steps.append(cleaned)
                if steps:
                    break
    
    # Strategy 6: Named processes/actions (extract key terms)
    # Pattern: "X is the process" or "X occurs" or "X happens"
    if not steps:
        named_process_patterns = [
            r'(\w+(?:\s+\w+)?)\s+(?:is|are)\s+(?:the|a|an)?\s+(?:process|stage|phase|step)',
            r'(\w+(?:\s+\w+)?)\s+(?:occurs|happens|takes place)',
            r'(?:the|a|an)\s+(\w+(?:\s+\w+)?)\s+(?:of|in|during)',
        ]
        
        for pattern in named_process_patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            if matches:
                for match in matches[:6]:
                    if isinstance(match, tuple):
                        match = match[-1]
                    words = match.split()
                    words = [w for w in words if w.lower() not in STOPWORDS]
                    if words:
                        step = ' '.join(words[:3]).capitalize()
                        if len(step) >= 3 and step not in steps:
                            steps.append(step)
                if steps:
                    break
    
    # Strategy 7: Extract named entities/processes mentioned in sentences
    # Universal: works for any capitalized term or process noun in any subject
    if not steps or len(steps) < 2:
        sentence_process_patterns = [
            # Capitalized terms at sentence start: "Evaporation is..." or "Photosynthesis occurs..."
            r'\b([A-Z][a-z]+(?:\s+[a-z]+)?)\s+(?:is|are|occurs|happens|takes place|begins|starts|involves)',
            # Process phrases: "the process of X" or "process of Y"
            r'(?:the|a|an)?\s+process\s+of\s+(\w+(?:\s+\w+)?)',
            # Temporal phrases: "during X" or "in the X process"
            r'(?:during|in|through)\s+(?:the|a|an)?\s+(\w+(?:\s+\w+)?)\s*(?:process|stage|phase)?',
            # Action phrases: "X begins" or "Y occurs"
            r'(\w+(?:\s+\w+)?)\s+(?:begins|starts|occurs|happens|takes place)',
        ]
        
        for pattern in sentence_process_patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            if matches:
                for match in matches[:10]:  # Increased limit for better coverage
                    if isinstance(match, tuple):
                        match = match[-1]
                    process = match.strip()
                    
                    # Universal filtering: meaningful terms (any subject)
                    if process and len(process) > 2:
                        # Check if it's capitalized (likely important term) or process noun ending
                        is_capitalized = process[0].isupper()
                        is_process_noun = re.search(r'(?:ion|tion|ing|ment|ism|ure)$', process.lower())
                        # Also check for common process indicators
                        has_process_indicator = any(ind in process.lower() for ind in ['process', 'stage', 'phase', 'step'])
                        
                        if is_capitalized or is_process_noun or has_process_indicator:
                            words = process.split()
                            meaningful = [w for w in words[:3] if w.lower() not in STOPWORDS and len(w) > 1]
                            if meaningful:
                                step = ' '.join(meaningful).capitalize()
                                # Clean punctuation
                                step = re.sub(r'[.,;:]+$', '', step)
                                if len(step) >= 2 and step not in steps:
                                    steps.append(step)
                if steps and len(steps) >= 2:
                    break
    
    # Strategy 8: Extract from any enumeration pattern (universal fallback)
    # Works for: any numbered/bulleted/listed content in any format
    if not steps or len(steps) < 2:
        # Look for any enumeration: "first X, second Y, third Z"
        enum_patterns = [
            r'(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+([^,\.]+?)(?:,|\.|$)',
            r'(\w+)\s*[,;]\s+(\w+)\s*[,;]\s+(\w+)',  # "X, Y, Z" pattern
        ]
        
        for pattern in enum_patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        # Multiple captures - extract each
                        for item in match:
                            if item and len(item.strip()) > 2:
                                cleaned = _extract_meaningful_phrase(item.strip())
                                if cleaned and cleaned not in steps:
                                    steps.append(cleaned)
                    else:
                        cleaned = _extract_meaningful_phrase(match.strip())
                        if cleaned and cleaned not in steps:
                            steps.append(cleaned)
                if steps and len(steps) >= 2:
                    break
    
    # Strategy 9: Extract key phrases from sentences (universal semantic extraction)
    # Works for: any subject - finds important action/process phrases
    if not steps or len(steps) < 2:
        # Find sentences that describe processes/actions
        sentences = re.split(r'[.!?]\s+', answer)
        for sentence in sentences[:15]:  # Check first 15 sentences
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            # Look for action phrases: "X does Y" or "X becomes Y" or "X transforms into Y"
            action_phrases = re.findall(
                r'(\w+(?:\s+\w+){0,2})\s+(?:does|becomes|transforms|changes|turns|converts|produces|creates)',
                sentence, re.IGNORECASE
            )
            
            for phrase in action_phrases[:3]:  # Limit per sentence
                words = phrase.split()
                meaningful = [w for w in words[:2] if w.lower() not in STOPWORDS and len(w) > 2]
                if meaningful:
                    step = ' '.join(meaningful).capitalize()
                    if len(step) >= 3 and step not in steps:
                        steps.append(step)
            
            if steps and len(steps) >= 3:
                break
    
    # Adaptive cleaning and truncation
    max_items, max_length = _calculate_adaptive_limits(len(answer), len(steps))
    cleaned_steps = []
    
    for step in steps[:max_items]:
        # Don't remove filler words here - already done in _extract_meaningful_phrase
        # Just normalize whitespace
        step = ' '.join(step.split())
        
        # Only truncate if significantly longer than max_length
        # Allow some flexibility to avoid truncating good short phrases
        if len(step) > max_length + 5:  # Add 5 char buffer
            step = _truncate_at_word_boundary(step, max_length)
        
        if step and len(step) >= 2:  # Minimum 2 chars
            cleaned_steps.append(step)
    
    return cleaned_steps


def _extract_meaningful_phrase(text: str) -> str:
    """Extract meaningful phrase from text, keeping it concise (2-3 words max)."""
    if not text:
        return ""
    
    # Clean up the text first
    text = text.strip()
    
    # Split into words
    words = text.split()
    
    # Extract just the main action/subject (first 2-3 meaningful words)
    # Goal: "water evaporates" not "water evaporates bodies water"
    meaningful = []
    for word in words:
        word_clean = word.strip('.,;:!?')
        # Skip obvious stopwords (but keep first word even if it's a stopword)
        if len(meaningful) == 0 or (word_clean.lower() not in STOPWORDS and len(word_clean) > 1):
            meaningful.append(word_clean)
        # Stop after 2-3 meaningful words (keep it short and clear)
        if len(meaningful) >= 3:
            break
    
    if not meaningful:
        # Fallback: take first 2 words
        meaningful = [w.strip('.,;:!?') for w in words[:2]]
    
    result = ' '.join(meaningful)
    
    # Capitalize first letter
    if result:
        result = result[0].upper() + result[1:] if len(result) > 1 else result.upper()
    
    return result.strip()


def _truncate_at_word_boundary(text: str, max_length: int) -> str:
    """Truncate text at word boundary, preserving meaning."""
    if len(text) <= max_length:
        return text
    
    words = text.split()
    truncated = []
    
    for word in words:
        potential = ' '.join(truncated + [word])
        if len(potential) <= max_length - 3:  # Leave room for "..."
            truncated.append(word)
        else:
            break
    
    result = ' '.join(truncated) if truncated else text[:max_length - 3]
    
    # Add ellipsis if truncated
    if len(result) < len(text):
        result += "..."
    
    return result


def has_decision_points(answer: str) -> bool:
    """Check if answer contains decision/conditional logic."""
    decision_keywords = [
        "if", "else", "condition", "decision", "check",
        "whether", "depending", "based on"
    ]
    return any(kw in answer.lower() for kw in decision_keywords)


def _calculate_box_dimensions(steps: List[str]) -> Tuple[int, int]:
    """
    Calculate adaptive box dimensions based on step content.
    Handles edge cases: very long steps, many steps, short steps.
    
    Args:
        steps: List of step texts
    
    Returns:
        Tuple of (box_width, content_width)
    """
    if not steps:
        return 15, 13  # Default
    
    # Find longest step
    max_step_len = max(len(step) for step in steps) if steps else 0
    
    # Adaptive width calculation
    if max_step_len <= 10:
        content_width = 10
        box_width = content_width + 4
    elif max_step_len <= 15:
        content_width = 15
        box_width = content_width + 4
    elif max_step_len <= 20:
        content_width = 20
        box_width = content_width + 4
    elif max_step_len <= 30:
        content_width = 30
        box_width = content_width + 4
    else:
        # Very long steps: cap at reasonable size
        content_width = 35
        box_width = content_width + 4
    
    # Adjust based on number of steps (more steps = narrower to fit)
    if len(steps) > 8:
        content_width = min(content_width, 18)
        box_width = content_width + 4
    elif len(steps) > 5:
        content_width = min(content_width, 22)
        box_width = content_width + 4
    
    return box_width, content_width


def generate_step_based_flowchart(steps: List[str]) -> str:
    """
    Generate adaptive flowchart from extracted steps.
    Box sizes adjust automatically based on content.
    
    Args:
        steps: List of step descriptions (already cleaned)
    
    Returns:
        ASCII flowchart string
    """
    if not steps:
        return _generate_minimal_flowchart()
    
    # Calculate adaptive dimensions
    box_width, content_width = _calculate_box_dimensions(steps)
    
    # Format steps with adaptive truncation
    formatted_steps = []
    for step in steps:
        step = step.strip()
        # Truncate if needed
        if len(step) > content_width:
            step = _truncate_at_word_boundary(step, content_width)
        
        # Capitalize first letter
        if step:
            step = step[0].upper() + step[1:] if len(step) > 1 else step.upper()
        
        formatted_steps.append(step)
    
    # Generate box drawing characters based on width
    top_left = "┌"
    top_right = "┐"
    bottom_left = "└"
    bottom_right = "┘"
    horizontal = "─"
    vertical = "│"
    down_arrow = "▼"
    connector = "┬"
    
    lines = []
    
    # Start box (adaptive width)
    start_label = "Start"
    start_box_width = max(len(start_label) + 2, box_width)
    lines.append(top_left + horizontal * (start_box_width - 2) + top_right)
    lines.append(vertical + start_label.center(start_box_width - 2) + vertical)
    lines.append(bottom_left + horizontal * ((start_box_width - 2) // 2) + connector + horizontal * ((start_box_width - 2) // 2) + bottom_right)
    lines.append(" " * ((start_box_width - 2) // 2) + vertical)
    
    # Steps with adaptive boxes
    for i, step in enumerate(formatted_steps):
        # Center step text in box
        step_padded = step.center(content_width)
        
        lines.append(" " * ((start_box_width - 2) // 2) + top_left + horizontal * (content_width - 2) + top_right)
        lines.append(" " * ((start_box_width - 2) // 2) + vertical + step_padded + vertical)
        lines.append(" " * ((start_box_width - 2) // 2) + bottom_left + horizontal * (content_width - 2) + bottom_right)
        
        if i < len(formatted_steps) - 1:
            lines.append(" " * ((start_box_width - 2) // 2) + vertical)
    
    # End box
    end_label = "Complete"
    end_box_width = max(len(end_label) + 2, box_width)
    lines.append(" " * ((start_box_width - 2) // 2) + top_left + horizontal * (end_box_width - 2) + top_right)
    lines.append(" " * ((start_box_width - 2) // 2) + vertical + end_label.center(end_box_width - 2) + vertical)
    lines.append(" " * ((start_box_width - 2) // 2) + bottom_left + horizontal * (end_box_width - 2) + bottom_right)
    
    return "\n".join(lines)


def _generate_minimal_flowchart() -> str:
    """Generate minimal flowchart for edge cases."""
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
    """
    Generate adaptive decision flowchart based on context.
    Extracts actual conditions and paths from answer.
    """
    answer = context.get("answer", "")
    conditions = context.get("conditions", [])
    
    # Extract condition text if available
    condition_text = "Condition Check"
    if conditions:
        condition_text = conditions[0]
        if len(condition_text) > 20:
            condition_text = _truncate_at_word_boundary(condition_text, 20)
    else:
        # Try to extract from answer
        cond_match = re.search(r'(?:if|when|whether)\s+([^,\.]+?)(?:,|\.|then)', answer, re.IGNORECASE)
        if cond_match:
            condition_text = cond_match.group(1).strip()
            if len(condition_text) > 20:
                condition_text = _truncate_at_word_boundary(condition_text, 20)
    
    # Extract path labels if available
    path_a = "Path A"
    path_b = "Path B"
    
    # Calculate adaptive box width
    max_label_len = max(len(condition_text), len(path_a), len(path_b), 10)
    content_width = min(max(max_label_len + 2, 12), 25)
    box_width = content_width + 4
    
    lines = []
    
    # Start
    lines.append("┌" + "─" * (box_width - 2) + "┐")
    lines.append("│" + "Start".center(box_width - 2) + "│")
    lines.append("└" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 2) + "┘")
    lines.append(" " * ((box_width - 2) // 2) + "│")
    
    # Condition box
    lines.append(" " * ((box_width - 2) // 2) + "┌" + "─" * (box_width - 2) + "┐")
    lines.append(" " * ((box_width - 2) // 2) + "│" + condition_text.center(box_width - 2) + "│")
    lines.append(" " * ((box_width - 2) // 2) + "└" + "─" * ((box_width - 2) // 4) + "┬" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 4) + "┘")
    
    # Decision branches
    indent_yes = " " * ((box_width - 2) // 2 - 2)
    indent_no = " " * ((box_width - 2) // 2 + (box_width - 2) // 2)
    
    lines.append(indent_yes + "Yes│" + " " * ((box_width - 2) // 2) + "│No")
    lines.append(indent_yes + "   │" + " " * ((box_width - 2) // 2) + "│")
    
    # Path boxes
    path_box_width = min(box_width - 4, 15)
    lines.append(indent_yes + "┌" + "─" * (path_box_width - 2) + "┐" + " " * 2 + "┌" + "─" * (path_box_width - 2) + "┐")
    lines.append(indent_yes + "│" + path_a.center(path_box_width - 2) + "│" + " " * 2 + "│" + path_b.center(path_box_width - 2) + "│")
    lines.append(indent_yes + "└" + "─" * (path_box_width - 2) + "┘" + " " * 2 + "└" + "─" * (path_box_width - 2) + "┘")
    lines.append(indent_yes + "   │" + " " * ((box_width - 2) // 2) + "│")
    lines.append(indent_yes + "   └" + "─" * ((box_width - 2) // 2) + "─" + "┘")
    lines.append(indent_yes + "     │")
    
    # Continue
    lines.append(indent_yes + "     ┌" + "─" * (box_width - 2) + "┐")
    lines.append(indent_yes + "     │" + "Continue".center(box_width - 2) + "│")
    lines.append(indent_yes + "     └" + "─" * (box_width - 2) + "┘")
    
    return "\n".join(lines)


def generate_generic_process_flowchart(context: Dict[str, any]) -> str:
    """
    Generate adaptive generic process flowchart.
    Uses context to determine number of steps and labels.
    """
    num_steps = context.get("num_steps", 3)
    answer = context.get("answer", "")
    
    # Try to extract step count from answer if not provided
    if num_steps == 3 and answer:
        step_count = len(re.findall(r'\b(?:step|stage|phase|part)\s+\d+', answer, re.IGNORECASE))
        if step_count > 0:
            num_steps = min(step_count, 6)  # Cap at 6 for readability
    
    # Adaptive step count (handle edge cases)
    num_steps = max(2, min(num_steps, 6))  # Between 2 and 6 steps
    
    # Generate steps
    steps = []
    for i in range(1, num_steps + 1):
        steps.append(f"Step {i}")
    
    return generate_step_based_flowchart(steps)


def generate_for_loop_flowchart(context: Dict[str, any]) -> str:
    """
    DEPRECATED: Use generate_iterative_flowchart instead.
    Kept for backward compatibility but redirects to universal iterative flowchart.
    """
    return generate_iterative_flowchart(context, "for")
    """
    Generate adaptive flowchart for for loop.
    All dimensions calculate dynamically - NO hardcoded sizes.
    """
    variables = context.get("variables", [])
    var_name = variables[0] if variables else "item"
    
    # Adaptive box sizing based on content
    labels = ["Start", f"Initialize {var_name}", "Condition Check", "Body", "Exit", "Update"]
    max_label_len = max(len(label) for label in labels)
    
    # Calculate adaptive box width
    content_width = max(12, min(max_label_len + 2, 25))
    box_width = content_width + 4
    center_pos = box_width // 2
    
    lines = []
    
    # Start box (adaptive width)
    lines.append("┌" + "─" * (box_width - 2) + "┐")
    lines.append("│" + "Start".center(box_width - 2) + "│")
    lines.append("└" + "─" * (center_pos - 1) + "┬" + "─" * (box_width - center_pos - 2) + "┘")
    lines.append(" " * (center_pos - 1) + "│")
    
    # Initialize (adaptive)
    init_text = f"Initialize {var_name}"
    if len(init_text) > content_width:
        init_text = _truncate_at_word_boundary(init_text, content_width)
    lines.append(" " * (center_pos - 1) + "┌" + "─" * (box_width - 2) + "┐")
    lines.append(" " * (center_pos - 1) + "│" + init_text.center(box_width - 2) + "│")
    lines.append(" " * (center_pos - 1) + "└" + "─" * (center_pos - 1) + "┬" + "─" * (box_width - center_pos - 2) + "┘")
    lines.append(" " * (center_pos - 1) + " " * (center_pos - 1) + "│")
    
    # Condition check (adaptive)
    cond_text = "Condition Check"
    if len(cond_text) > content_width:
        cond_text = _truncate_at_word_boundary(cond_text, content_width)
    lines.append(" " * (center_pos - 1) + " " * (center_pos - 1) + "┌" + "─" * (box_width - 2) + "┐")
    lines.append(" " * (center_pos - 1) + " " * (center_pos - 1) + "│" + cond_text.center(box_width - 2) + "│")
    lines.append(" " * (center_pos - 1) + " " * (center_pos - 1) + "└" + "─" * (center_pos - 3) + "┬" + "─" * (box_width - center_pos * 2 + 2) + "┬" + "─" * (center_pos - 3) + "┘")
    
    # Decision branches (adaptive spacing)
    branch_width = min(12, box_width - 6)
    indent_left = " " * (center_pos - 1) + " " * (center_pos - 4)
    branch_spacing = max(2, box_width - center_pos * 2 - branch_width * 2)
    
    lines.append(indent_left + "Yes│" + " " * branch_spacing + "│No")
    lines.append(indent_left + "   │" + " " * branch_spacing + "│")
    
    # Body and Exit boxes (adaptive)
    lines.append(indent_left + "┌" + "─" * (branch_width - 2) + "┐" + " " * branch_spacing + "┌" + "─" * (branch_width - 2) + "┐")
    lines.append(indent_left + "│" + "Body".center(branch_width - 2) + "│" + " " * branch_spacing + "│" + "Exit".center(branch_width - 2) + "│")
    lines.append(indent_left + "└" + "─" * (branch_width - 2) + "┘" + " " * branch_spacing + "└" + "─" * (branch_width - 2) + "┘")
    lines.append(indent_left + "   │")
    
    # Update (adaptive)
    update_text = "Update"
    lines.append(indent_left + "   ┌" + "─" * (box_width - 2) + "┐")
    lines.append(indent_left + "   │" + update_text.center(box_width - 2) + "│")
    lines.append(indent_left + "   └" + "─" * (center_pos - 1) + "┘")
    lines.append(indent_left + "     │")
    lines.append(indent_left + "     └───► (loop back)")
    
    return "\n".join(lines)


def generate_while_loop_flowchart(context: Dict[str, any]) -> str:
    """
    DEPRECATED: Use generate_iterative_flowchart instead.
    Kept for backward compatibility but redirects to universal iterative flowchart.
    """
    return generate_iterative_flowchart(context, "while")
    """Generate adaptive flowchart for while loop."""
    # Similar structure but condition check comes first
    box_width = 18
    
    lines = []
    lines.append("┌" + "─" * (box_width - 2) + "┐")
    lines.append("│" + "Start".center(box_width - 2) + "│")
    lines.append("└" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 2) + "┘")
    lines.append(" " * ((box_width - 2) // 2) + "│")
    
    cond_text = "Check Condition"
    lines.append(" " * ((box_width - 2) // 2) + "┌" + "─" * (box_width - 2) + "┐")
    lines.append(" " * ((box_width - 2) // 2) + "│" + cond_text.center(box_width - 2) + "│")
    lines.append(" " * ((box_width - 2) // 2) + "└" + "─" * ((box_width - 2) // 4) + "┬" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 4) + "┘")
    
    indent_true = " " * ((box_width - 2) // 2 - 1)
    lines.append(indent_true + "True│" + " " * ((box_width - 2) // 2) + "│False")
    lines.append(indent_true + "    │" + " " * ((box_width - 2) // 2) + "│")
    
    lines.append(indent_true + "┌" + "─" * 10 + "┐" + " " * 2 + "┌" + "─" * 8 + "┐")
    lines.append(indent_true + "│" + "Body".center(10) + "│" + " " * 2 + "│" + "Exit".center(8) + "│")
    lines.append(indent_true + "└" + "─" * 5 + "┬" + "─" * 5 + "┘" + " " * 2 + "└" + "─" * 8 + "┘")
    lines.append(indent_true + "    │")
    
    update_text = "Update"
    lines.append(indent_true + "    ┌" + "─" * (box_width - 2) + "┐")
    lines.append(indent_true + "    │" + update_text.center(box_width - 2) + "│")
    lines.append(indent_true + "    └" + "─" * ((box_width - 2) // 2) + "┘")
    lines.append(indent_true + "      │")
    lines.append(indent_true + "      └───► (loop)")
    
    return "\n".join(lines)


def generate_structure_diagram(context: Dict[str, any]) -> Optional[str]:
    """
    Generate adaptive structure diagram based on context.
    Fully extracts components and adapts to content.
    
    Args:
        context: Dictionary with structure information
    
    Returns:
        ASCII structure diagram string
    """
    answer = context.get("answer", "")
    question = context.get("question", "")
    components = context.get("components", [])
    
    # Extract structure components if not provided
    if not components:
        components = extract_structure_components(answer, question)
    
    # If we found components, use them
    if components:
        return generate_component_structure(components)
    
    # Fallback: try to extract from answer structure
    if answer:
        # Look for hierarchical indicators
        hierarchy_match = re.search(r'(?:top|upper|highest|main).*?(?:level|layer|tier)', answer, re.IGNORECASE)
        if hierarchy_match:
            # Try to extract 3-level hierarchy
            levels = ["Top Level", "Middle Level", "Bottom Level"]
            return generate_component_structure(levels)
    
    # Minimal fallback
    return _generate_minimal_structure()


def extract_structure_components(answer: str, question: str) -> List[str]:
    """
    Extract structure components from answer using multiple strategies.
    Fully adaptive - handles various formats and edge cases.
    
    Args:
        answer: Answer text
        question: Question text
    
    Returns:
        List of component names (adaptively limited)
    """
    if not answer:
        return []
    
    components = []
    answer_lower = answer.lower()
    combined_text = f"{question} {answer}".lower()
    
    # Strategy 1: Explicit component lists ("consists of X, Y, Z")
    component_patterns = [
        r'(?:consists|composed|made)\s+of\s+([^\.]+?)(?:\.|$)',
        r'(?:has|contains|includes|comprises)\s+([^\.]+?)(?:\.|$)',
        r'(?:components?|parts?|elements?)\s+(?:are|is|include|consist of)\s+([^\.]+?)(?:\.|$)',
    ]
    
    for pattern in component_patterns:
        matches = re.findall(pattern, answer, re.IGNORECASE)
        if matches:
            for match in matches:
                # Split by commas, semicolons, "and", "or"
                parts = re.split(r'[,;]\s*|\s+and\s+|\s+or\s+', match)
                for part in parts:
                    part = part.strip()
                    # Extract meaningful component name
                    words = part.split()
                    # Take first 2-3 meaningful words
                    meaningful = [w for w in words[:3] if w.lower() not in STOPWORDS]
                    if meaningful:
                        comp = ' '.join(meaningful).capitalize()
                        if len(comp) >= 2 and comp not in components:
                            components.append(comp)
            if components:
                break
    
    # Strategy 2: Named entities (capitalized words often indicate components)
    if not components:
        # Find capitalized phrases (likely proper nouns or important terms)
        capitalized = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', answer)
        for cap in capitalized[:10]:  # Limit to prevent too many
            if len(cap) >= 3 and cap.lower() not in STOPWORDS:
                components.append(cap)
    
    # Strategy 3: Generic component indicators
    if not components:
        generic_patterns = [
            r'(?:element|item|part|component|piece|section)\s+(\d+)',
            r'(?:first|second|third|fourth|fifth)\s+(?:component|part|element)\s+is\s+([^\.]+?)(?:\.|$)',
        ]
        
        for pattern in generic_patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            if matches:
                for match in matches[:5]:
                    if isinstance(match, tuple):
                        match = match[-1]
                    comp = str(match).strip().capitalize()
                    if comp and comp not in components:
                        components.append(comp)
                if components:
                    break
    
    # Strategy 4: Extract from question if answer doesn't have components
    if not components and question:
        # Look for "what are the parts of X" -> extract X
        question_components = re.findall(r'(?:parts?|components?|elements?)\s+of\s+(\w+)', question, re.IGNORECASE)
        if question_components:
            components.extend([c.capitalize() for c in question_components[:3]])
    
    # Adaptive limiting based on content
    max_items, _ = _calculate_adaptive_limits(len(answer), len(components))
    return components[:max_items]


def generate_component_structure(components: List[str]) -> str:
    """
    Generate adaptive structure diagram from components.
    Handles edge cases: single component, many components, long names.
    """
    if not components:
        return _generate_minimal_structure()
    
    # Calculate adaptive dimensions
    max_comp_len = max(len(comp) for comp in components) if components else 0
    content_width = max(12, min(max_comp_len + 2, 30))  # Adaptive width
    box_width = content_width + 4
    
    # Format components with adaptive truncation
    formatted = []
    for comp in components:
        if len(comp) > content_width:
            comp = _truncate_at_word_boundary(comp, content_width)
        formatted.append(comp)
    
    lines = []
    
    # Handle different structure types based on number of components
    if len(formatted) == 1:
        # Single component - simple box
        lines.append("┌" + "─" * (box_width - 2) + "┐")
        lines.append("│" + formatted[0].center(box_width - 2) + "│")
        lines.append("└" + "─" * (box_width - 2) + "┘")
    elif len(formatted) == 2:
        # Two components - parent-child
        lines.append("┌" + "─" * (box_width - 2) + "┐")
        lines.append("│" + formatted[0].center(box_width - 2) + "│")
        lines.append("└" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 2) + "┘")
        lines.append(" " * ((box_width - 2) // 2) + "│")
        lines.append(" " * ((box_width - 2) // 2) + "┌" + "─" * (box_width - 2) + "┐")
        lines.append(" " * ((box_width - 2) // 2) + "│" + formatted[1].center(box_width - 2) + "│")
        lines.append(" " * ((box_width - 2) // 2) + "└" + "─" * (box_width - 2) + "┘")
    else:
        # Multiple components - hierarchical
        # Top level
        lines.append("┌" + "─" * (box_width - 2) + "┐")
        lines.append("│" + formatted[0].center(box_width - 2) + "│")
        lines.append("└" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 2) + "┘")
        lines.append(" " * ((box_width - 2) // 2) + "│")
        
        # Middle levels
        for comp in formatted[1:-1]:
            lines.append(" " * ((box_width - 2) // 2) + "┌" + "─" * (box_width - 2) + "┐")
            lines.append(" " * ((box_width - 2) // 2) + "│" + comp.center(box_width - 2) + "│")
            lines.append(" " * ((box_width - 2) // 2) + "└" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 2) + "┘")
            lines.append(" " * ((box_width - 2) // 2) + " " * ((box_width - 2) // 2) + "│")
        
        # Bottom level
        if len(formatted) > 1:
            indent = " " * ((box_width - 2) // 2) * (len(formatted) - 1)
            lines.append(indent + "┌" + "─" * (box_width - 2) + "┐")
            lines.append(indent + "│" + formatted[-1].center(box_width - 2) + "│")
            lines.append(indent + "└" + "─" * (box_width - 2) + "┘")
    
    return "\n".join(lines)


def _generate_minimal_structure() -> str:
    """Generate minimal structure for edge cases."""
    return """┌────────┐
│Component│
└─────────┘"""


def _is_cyclic_process(question: str, answer: str) -> bool:
    """
    Detect if process is cyclic (repeating/continuous).
    Universal detection - works for ANY cyclic process in ANY subject.
    """
    combined = f"{question} {answer}".lower()
    
    # Universal cycle indicators (semantic patterns, not domain-specific)
    cycle_patterns = [
        r'\b(cycle|circular|continuous|repeating|recurring|ongoing|perpetual)',
        r'\b(returns?|goes back|comes back|repeats?|loops?|recur)',
        r'\b(continuous\s+(?:movement|process|flow|sequence))',
        r'\b(cycle\s+(?:of|in|continues?|repeats?))',
        r'\b(again|once more|repeatedly|continuously)',
        r'\b(restart|begin again|start over)',
    ]
    
    import re
    return any(re.search(pattern, combined, re.IGNORECASE) for pattern in cycle_patterns)


def generate_cycle_diagram(steps: List[str]) -> str:
    """
    Generate circular/cyclic diagram for repeating processes.
    Universal - works for ANY cyclic process in ANY subject.
    Shows steps in sequence with loop-back indicator.
    """
    if not steps or len(steps) < 2:
        return generate_step_based_flowchart(steps)
    
    # Limit steps for cycle diagram (too many becomes cluttered)
    steps = steps[:6]
    
    # Calculate adaptive dimensions
    max_step_len = max(len(step) for step in steps) if steps else 12
    # Allow wider boxes for cycle diagrams to avoid unnecessary truncation
    content_width = max(12, min(max_step_len + 2, 30))  # Increased from 22 to 30
    box_width = content_width + 4
    
    lines = []
    
    # Format steps with adaptive truncation
    formatted_steps = []
    for step in steps:
        step = step.strip()
        if len(step) > content_width:
            step = _truncate_at_word_boundary(step, content_width)
        if step:
            step = step[0].upper() + step[1:] if len(step) > 1 else step.upper()
        formatted_steps.append(step)
    
    # Generate cycle: steps flow down, then loop back
    for i, step in enumerate(formatted_steps):
        step_padded = step.center(content_width)
        
        if i == 0:
            # First step
            lines.append("┌" + "─" * (box_width - 2) + "┐")
            lines.append("│" + step_padded + "│")
            lines.append("└" + "─" * (box_width // 2 - 1) + "┬" + "─" * (box_width // 2 - 1) + "┘")
            lines.append(" " * (box_width // 2 - 1) + "│")
        else:
            # Subsequent steps
            lines.append(" " * (box_width // 2 - 1) + "┌" + "─" * (box_width - 2) + "┐")
            lines.append(" " * (box_width // 2 - 1) + "│" + step_padded + "│")
            
            if i < len(formatted_steps) - 1:
                # Not last step
                lines.append(" " * (box_width // 2 - 1) + "└" + "─" * (box_width // 2 - 1) + "┬" + "─" * (box_width // 2 - 1) + "┘")
                lines.append(" " * (box_width // 2 - 1) + " " * (box_width // 2 - 1) + "│")
            else:
                # Last step - loop back
                lines.append(" " * (box_width // 2 - 1) + "└" + "─" * (box_width // 2 - 1) + "┘")
                lines.append(" " * (box_width // 2 - 1) + " " * (box_width // 2 - 1) + "│")
                lines.append(" " * (box_width // 2 - 1) + " " * (box_width // 2 - 1) + "└───► (cycle)")
                # Loop back arrow
                lines.append(" " * (box_width // 2 - 2) + "◄───┘")
                lines.append(" " * (box_width // 2 - 2) + "│")
                lines.append(" " * (box_width // 2 - 2) + "└─── (repeats)")
    
    return "\n".join(lines)


def generate_process_diagram(context: Dict[str, any]) -> Optional[str]:
    """
    Generate adaptive process diagram based on context.
    Fully extracts ACTUAL processes from answer - NO generic placeholders.
    
    Args:
        context: Dictionary with process information
    
    Returns:
        ASCII process diagram string
    """
    answer = context.get("answer", "")
    question = context.get("question", "")
    
    # Check if this is a cyclic process (universal detection)
    is_cycle = _is_cyclic_process(question, answer)
    
    # Extract steps from answer (adaptive extraction with multiple strategies)
    steps = extract_steps_from_answer(answer)
    
    # If we found steps, use them (reflects ACTUAL content)
    if steps and len(steps) > 0:
        # Use cycle diagram for cyclic processes, linear for sequential
        if is_cycle and len(steps) >= 2:
            return generate_cycle_diagram(steps)
        else:
            return generate_step_based_flowchart(steps)
    
    # Fallback: Try to extract from question if answer doesn't have steps
    if not steps and question:
        # Look for process names in question
        question_steps = extract_steps_from_answer(question)
        if question_steps:
            return generate_step_based_flowchart(question_steps)
    
    # Last resort: Try to extract key terms from answer
    if not steps and answer:
        # Extract capitalized terms or important concepts
        key_terms = _extract_key_process_terms(answer)
        if key_terms and len(key_terms) >= 2:
            return generate_step_based_flowchart(key_terms)
    
    # Only use generic steps if absolutely nothing can be extracted
    # This should be rare - most answers have extractable content
    num_steps = context.get("num_steps", 3)
    if num_steps == 3 and answer:
        # Count sequential indicators as last attempt
        sequential_count = len(re.findall(
            r'\b(first|second|third|fourth|fifth|sixth|then|next|after|finally)', 
            answer, re.IGNORECASE
        ))
        if sequential_count > 0:
            num_steps = min(sequential_count + 1, 6)
    
    # Only use generic if we truly have no content
    num_steps = max(2, min(num_steps, 6))
    generic_steps = [f"Step {i}" for i in range(1, num_steps + 1)]
    
    return generate_step_based_flowchart(generic_steps)


def _extract_key_process_terms(text: str) -> List[str]:
    """
    Extract key process/action terms from text as last resort.
    Works for any domain - finds important action/process words.
    """
    terms = []
    text_lower = text.lower()
    
    # Find process/action nouns (common patterns)
    # Pattern: "X is" or "X occurs" where X is a process name
    patterns = [
        r'\b(\w+(?:\s+\w+)?)\s+(?:is|are)\s+(?:the|a|an)?\s+(?:process|stage|phase)',
        r'\b(\w+(?:\s+\w+)?)\s+(?:occurs|happens|takes place)',
        r'(?:the|a|an)\s+(\w+(?:\s+\w+)?)\s+(?:of|in|during|cycle)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                match = match[-1]
            term = match.strip()
            # Filter out stopwords and very short terms
            if term and len(term) > 3 and term.lower() not in STOPWORDS:
                words = term.split()
                # Take first 2 meaningful words
                meaningful = [w for w in words[:2] if w.lower() not in STOPWORDS]
                if meaningful:
                    term = ' '.join(meaningful).capitalize()
                    if term not in terms:
                        terms.append(term)
    
    return terms[:6]  # Limit to 6 terms

