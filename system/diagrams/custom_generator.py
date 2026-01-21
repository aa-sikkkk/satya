import re
from typing import Dict, Optional, List, Tuple

STOPWORDS = {
    "the", "is", "are", "a", "an", "to", "of", "and", "or", "for", "in", "on", "at", "by", "that",
    "this", "it", "as", "be", "with", "from", "into", "their", "its", "they", "them", "can", "will",
    "about", "how", "what", "why", "which", "who", "whose", "when", "where", "than", "then", "also",
    "been", "has", "have", "had", "does", "did", "do", "would", "could", "should"
}

SENTENCE_INDICATORS = {
    "occurs", "happens", "takes", "place", "when", "where", "which", "that", "been", "warmed",
    "system", "process", "stage", "phase", "step"
}


def is_valid_process_name(text: str) -> bool:
    if not text or len(text) < 3:
        return False
    
    words = text.lower().split()
    
    if len(words) > 3:
        return False
    
    stopword_count = sum(1 for w in words if w in STOPWORDS)
    if stopword_count > 1:
        return False
    
    sentence_indicator_count = sum(1 for w in words if w in SENTENCE_INDICATORS)
    if sentence_indicator_count > 0:
        return False
    
    if any(char in text for char in [',', '.', '!', '?', ';', ':']):
        return False
    
    return True


def generate_diagram(diagram_type: str, context: Dict[str, any]) -> Optional[str]:
    if diagram_type == "flowchart":
        return generate_flowchart(context)
    elif diagram_type == "structure":
        return generate_structure_diagram(context)
    elif diagram_type == "process":
        return generate_process_diagram(context)
    
    return None


def generate_flowchart(context: Dict[str, any]) -> Optional[str]:
    question = context.get("question", "")
    answer = context.get("answer", "")
    rag_chunks = context.get("rag_chunks")
    llm_handler = context.get("llm_handler")
    
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
    answer = context.get("answer", "")
    question = context.get("question", "")
    iteration_subject = _extract_iteration_subject(answer, question)
    
    conditions = context.get("conditions", [])
    condition_text = conditions[0] if conditions else "Check Condition"
    labels = ["Start", iteration_subject, condition_text, "Process", "Continue", "End"]
    max_label_len = max(len(label) for label in labels) if labels else 12
    content_width = max(12, min(max_label_len + 2, 30))
    box_width = content_width + 4
    center_pos = box_width // 2
    
    lines = []
    
    lines.append("┌" + "─" * (box_width - 2) + "┐")
    lines.append("│" + "Start".center(box_width - 2) + "│")
    lines.append("└" + "─" * (center_pos - 1) + "┬" + "─" * (box_width - center_pos - 2) + "┘")
    lines.append(" " * (center_pos - 1) + "│")
    
    init_text = iteration_subject
    if len(init_text) > content_width:
        init_text = _truncate_at_word_boundary(init_text, content_width)
    lines.append(" " * (center_pos - 1) + "┌" + "─" * (box_width - 2) + "┐")
    lines.append(" " * (center_pos - 1) + "│" + init_text.center(box_width - 2) + "│")
    lines.append(" " * (center_pos - 1) + "└" + "─" * (center_pos - 1) + "┬" + "─" * (box_width - center_pos - 2) + "┘")
    lines.append(" " * (center_pos - 1) + " " * (center_pos - 1) + "│")
    

    if len(condition_text) > content_width:
        condition_text = _truncate_at_word_boundary(condition_text, content_width)
    lines.append(" " * (center_pos - 1) + " " * (center_pos - 1) + "┌" + "─" * (box_width - 2) + "┐")
    lines.append(" " * (center_pos - 1) + " " * (center_pos - 1) + "│" + condition_text.center(box_width - 2) + "│")
    lines.append(" " * (center_pos - 1) + " " * (center_pos - 1) + "└" + "─" * (center_pos - 3) + "┬" + "─" * (box_width - center_pos * 2 + 2) + "┬" + "─" * (center_pos - 3) + "┘")
    
    branch_width = min(12, box_width - 6)
    indent_left = " " * (center_pos - 1) + " " * (center_pos - 4)
    branch_spacing = max(2, box_width - center_pos * 2 - branch_width * 2)
    
    lines.append(indent_left + "Yes│" + " " * branch_spacing + "│No")
    lines.append(indent_left + "   │" + " " * branch_spacing + "│")
    
    process_label = "Process"
    end_label = "End"
    lines.append(indent_left + "┌" + "─" * (branch_width - 2) + "┐" + " " * branch_spacing + "┌" + "─" * (branch_width - 2) + "┐")
    lines.append(indent_left + "│" + process_label.center(branch_width - 2) + "│" + " " * branch_spacing + "│" + end_label.center(branch_width - 2) + "│")
    lines.append(indent_left + "└" + "─" * (branch_width - 2) + "┘" + " " * branch_spacing + "└" + "─" * (branch_width - 2) + "┘")
    lines.append(indent_left + "   │")
    
    continue_text = "Continue"
    lines.append(indent_left + "   ┌" + "─" * (box_width - 2) + "┐")
    lines.append(indent_left + "   │" + continue_text.center(box_width - 2) + "│")
    lines.append(indent_left + "   └" + "─" * (center_pos - 1) + "┘")
    lines.append(indent_left + "     │")
    lines.append(indent_left + "     └───► (repeat)")
    
    return "\n".join(lines)


def _extract_iteration_subject(answer: str, question: str) -> str:
    combined = f"{question} {answer}".lower()
    
    patterns = [
        r'(?:for|each|every)\s+(\w+)', 
        r'(?:iterate|repeat|cycle)\s+(?:over|through|on)\s+(\w+)',  
        r'(\w+)\s+(?:in|of)\s+(?:the|a|an)?\s+(?:cycle|loop|iteration|process)',  
    ]
    
    import re
    for pattern in patterns:
        match = re.search(pattern, combined, re.IGNORECASE)
        if match:
            subject = match.group(1)
            if subject.lower() not in STOPWORDS and len(subject) > 2:
                return subject.capitalize()
    
    return "Item"


def _calculate_adaptive_limits(content_length: int, num_items: int) -> Tuple[int, int]:
    if content_length < 100:
        max_items = min(num_items, 3)  
    elif content_length < 500:
        max_items = min(num_items, 5) 
    elif content_length < 2000:
        max_items = min(num_items, 8)  
    else:
        max_items = min(num_items, 10)  
    
    if num_items <= 3:
        max_item_length = 25  
    elif num_items <= 5:
        max_item_length = 18 
    elif num_items <= 8:
        max_item_length = 15  
    else:
        max_item_length = 12  
    
    return max_items, max_item_length


def extract_steps_from_rag(rag_chunks: List[str]) -> List[str]:
    if not rag_chunks:
        return []
    
    steps = []
    combined_text = ' '.join(rag_chunks)
    
    numbered_list_patterns = [
        r'(\d+)\.\s+([A-Z][a-zA-Z\s]+?)(?:\s*[-–—:]\s*|\s*\n)',
        r'(?:Step|Stage|Phase)\s+(\d+)[:\.]?\s*([A-Z][a-zA-Z\s]+?)(?:\s*[-–—:]\s*|\s*\n)',
    ]
    
    for pattern in numbered_list_patterns:
        matches = re.findall(pattern, combined_text, re.MULTILINE)
        if matches:
            for match in matches:
                text = match[1] if len(match) > 1 else match[0]
                text = text.strip()
                
                words = text.split()
                if len(words) <= 4:
                    clean_text = ' '.join(words)
                else:
                    clean_text = ' '.join(words[:3])
                
                clean_text = re.sub(r'[.,;:]+$', '', clean_text)
                
                if len(clean_text) >= 3 and clean_text not in steps:
                    steps.append(clean_text)
            
            if len(steps) >= 2:
                return steps[:8]
    
    process_list_patterns = [
        r'(?:consists of|includes|involves|comprises)[:\s]+([^\.]+)',
        r'(?:stages?|steps?|phases?|processes?)[:\s]+([^\.]+)',
    ]
    
    for pattern in process_list_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        if matches:
            for match in matches:
                items = re.split(r',\s*(?:and\s+)?|;\s*|\s+and\s+', match)
                
                for item in items:
                    item = item.strip()
                    item = re.sub(r'^(?:the|a|an)\s+', '', item, flags=re.IGNORECASE)
                    
                    words = item.split()
                    if len(words) <= 3:
                        clean_item = ' '.join(words)
                    else:
                        clean_item = ' '.join(words[:2])
                    
                    clean_item = re.sub(r'[.,;:]+$', '', clean_item)
                    clean_item = clean_item.capitalize()
                    
                    if len(clean_item) >= 3 and clean_item not in steps:
                        steps.append(clean_item)
            
            if len(steps) >= 2:
                return steps[:8]
    
    capitalized_terms = re.findall(r'\b([A-Z][a-z]+(?:ation|tion|sion|ment)?)\b', combined_text)
    
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
    if not answer or not llm_handler or len(answer.strip()) < 10:
        return []
    
    try:
        extraction_prompt = f"""Extract the main process names from this explanation. List only 1-3 word process names, comma-separated.

Explanation: {answer}

Process names:"""
        
        extracted = llm_handler.generate_response(extraction_prompt, max_tokens=50)
        
        steps = [s.strip() for s in extracted.split(',') if s.strip()]
        steps = [s for s in steps if len(s.split()) <= 3][:8]
        
        return steps if len(steps) >= 2 else []
    except Exception:
        return []


def extract_steps_from_answer(answer: str, rag_chunks: Optional[List[str]] = None, llm_handler=None) -> List[str]:
    if llm_handler:
        llm_steps = extract_steps_with_llm(answer, llm_handler)
        if len(llm_steps) >= 2:
            return llm_steps
    
    if rag_chunks:
        rag_steps = extract_steps_from_rag(rag_chunks)
        if len(rag_steps) >= 2:
            return rag_steps
    
    if not answer or len(answer.strip()) < 10:

        return []
    
    steps = []
    
    numbered_patterns = [
        (r'Stage\s+(\d+)[:\.]?\s*([^\n\.]+)', 2),
        (r'(\d+)[\.\)]\s+([^\n]+?)(?=\n\s*\d+[\.\)]|\n\n|$)', 2),
        (r'(?:Step|Phase|Part)\s+(\d+)[:\.]?\s*([^\n\.]+)', 2),
    ]
    
    for pattern, text_group in numbered_patterns:
        matches = re.findall(pattern, answer, re.IGNORECASE | re.MULTILINE)
        if matches:
            for match in matches:
                text = match[text_group - 1] if isinstance(match, tuple) else match
                text = text.strip()
                
                if len(text) < 3:
                    continue
                
                first_sentence = text.split('.')[0].strip()
                first_sentence = re.sub(r'^(?:the|a|an)\s+', '', first_sentence, flags=re.IGNORECASE)
                
                words = first_sentence.split()
                meaningful = [w for w in words[:5] if len(w) > 1]
                
                if meaningful:
                    step = ' '.join(meaningful).capitalize()
                    step = re.sub(r'[.,;:]+$', '', step)
                    
                    if len(step) >= 2 and not step.isdigit() and step not in steps:
                        steps.append(step)
            
            if len(steps) >= 2:
                break
    
    if not steps:
        list_patterns = [
            r'(?:involves|includes|contains)\s+(?:processes?|steps?)\s+(?:such as|like|including)\s+([^\.]+)',
            r'(?:processes?|steps?|stages?|phases?)\s*[:]\s*([^\.]+)',
        ]
        
        for pattern in list_patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            if matches:
                for match in matches:
                    items = re.split(r'[,;]\s*|\s+and\s+|\s+or\s+', match)
                    
                    for item in items:
                        item = item.strip()
                        if len(item) < 2:
                            continue
                        
                        item = re.sub(r'^(?:the|a|an)\s+', '', item, flags=re.IGNORECASE)
                        words = item.split()
                        meaningful = [w for w in words[:2] if len(w) > 1]
                        
                        if meaningful:
                            step = ' '.join(meaningful).capitalize()
                            step = re.sub(r'[.,;]+$', '', step)
                            
                            if len(step) >= 2 and not step.isdigit() and step not in steps:
                                steps.append(step)
                
                if len(steps) >= 2:
                    break
    
    if not steps:
        process_name_patterns = [
            r'([A-Z][a-z]+(?:ation|tion|sion)?)\s+(?:occurs|happens|takes place|then occurs)',
            r'([A-Z][a-z]+(?:ation|tion|sion)?)\s+is\s+(?:the|a)\s+(?:process|stage|phase)',
        ]
        
        for pattern in process_name_patterns:
            matches = re.findall(pattern, answer)
            if matches:
                for match in matches:
                    text = match if isinstance(match, str) else match[0] if isinstance(match, tuple) else str(match)
                    text = text.strip()
                    
                    if len(text) >= 4 and text not in steps:
                        steps.append(text)
                
                if len(steps) >= 2:
                    break
        
        if len(steps) < 2:
            steps = []
    
    if not steps:
        sequential_markers = [
            r'(?:first|second|third|fourth|fifth|sixth)[,:\s]+([^\.]+?)(?:occurs|happens|is|involves)',
            r'(?:then|next|after|finally)[,:\s]+(?:the\s+)?([A-Z][a-z]+)',
        ]
        
        for pattern in sequential_markers:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            if matches:
                for match in matches[:6]:
                    text = match.strip() if isinstance(match, str) else match[0].strip() if isinstance(match, tuple) else str(match)
                    words = text.split()
                    meaningful = [w for w in words[:2] if len(w) > 2]
                    
                    if meaningful:
                        step = ' '.join(meaningful).capitalize()
                        step = re.sub(r'[.,;:]+$', '', step)
                        
                        if len(step) >= 3 and not step.isdigit() and step not in steps:
                            steps.append(step)
                
                if len(steps) >= 2:
                    break
    
    if not steps or len(steps) < 2:
        process_patterns = [
            r'([A-Z][a-z]{3,}(?:\s+[a-z]+)?)\s+(?:occurs|happens|takes place)',
            r'(?:process|stage|phase)\s+of\s+([a-z]{4,}(?:\s+[a-z]+)?)',
        ]
        
        for pattern in process_patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            if matches:
                for match in matches[:8]:
                    text = match if isinstance(match, str) else match[0] if isinstance(match, tuple) else str(match)
                    text = text.strip()
                    
                    if len(text) >= 4:
                        words = text.split()
                        meaningful = [w for w in words[:2] if len(w) > 2]
                        
                        if meaningful:
                            step = ' '.join(meaningful).capitalize()
                            step = re.sub(r'[.,;:]+$', '', step)
                            
                            if len(step) >= 4 and not step.isdigit() and step not in steps:
                                steps.append(step)
                
                if steps and len(steps) >= 2:
                    break
    
    max_items = min(len(steps), 8) if len(answer) > 200 else min(len(steps), 5)
    return steps[:max_items]


def _extract_meaningful_phrase(text: str) -> str:
    if not text:
        return ""
    
    words = text.split()
    meaningful = [w for w in words[:5] if len(w) > 1]
    
    if not meaningful:
        meaningful = words[:3]
    
    result = ' '.join(meaningful).capitalize()
    return re.sub(r'[.,;:]+$', '', result.strip())


def _truncate_at_word_boundary(text: str, max_length: int) -> str:
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


def has_decision_points(answer: str) -> bool:
    decision_keywords = [
        "if", "else", "condition", "decision", "check",
        "whether", "depending", "based on"
    ]
    return any(kw in answer.lower() for kw in decision_keywords)


def _calculate_box_dimensions(steps: List[str]) -> Tuple[int, int]:
    if not steps:
        return 15, 13 
    
    max_step_len = max(len(step) for step in steps) if steps else 0
    
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
        content_width = 35
        box_width = content_width + 4
    
    if len(steps) > 8:
        content_width = min(content_width, 18)
        box_width = content_width + 4
    elif len(steps) > 5:
        content_width = min(content_width, 22)
        box_width = content_width + 4
    
    return box_width, content_width


def generate_step_based_flowchart(steps: List[str]) -> str:
    if not steps:
        return _generate_minimal_flowchart()
    
    box_width, content_width = _calculate_box_dimensions(steps)
    formatted_steps = []
    for step in steps:
        step = step.strip()
        if len(step) > content_width:
            step = _truncate_at_word_boundary(step, content_width)
        
        if step:
            step = step[0].upper() + step[1:] if len(step) > 1 else step.upper()
        
        formatted_steps.append(step)
    
    top_left = "┌"
    top_right = "┐"
    bottom_left = "└"
    bottom_right = "┘"
    horizontal = "─"
    vertical = "│"
    down_arrow = "▼"
    connector = "┬"
    
    lines = []
    
    start_label = "Start"
    start_box_width = max(len(start_label) + 2, box_width)
    lines.append(top_left + horizontal * (start_box_width - 2) + top_right)
    lines.append(vertical + start_label.center(start_box_width - 2) + vertical)
    lines.append(bottom_left + horizontal * ((start_box_width - 2) // 2) + connector + horizontal * ((start_box_width - 2) // 2) + bottom_right)
    lines.append(" " * ((start_box_width - 2) // 2) + vertical)
    
    for i, step in enumerate(formatted_steps):
        step_padded = step.center(content_width)
        
        lines.append(" " * ((start_box_width - 2) // 2) + top_left + horizontal * (content_width - 2) + top_right)
        lines.append(" " * ((start_box_width - 2) // 2) + vertical + step_padded + vertical)
        lines.append(" " * ((start_box_width - 2) // 2) + bottom_left + horizontal * (content_width - 2) + bottom_right)
        
        if i < len(formatted_steps) - 1:
            lines.append(" " * ((start_box_width - 2) // 2) + vertical)

    end_label = "Complete"
    end_box_width = max(len(end_label) + 2, box_width)
    lines.append(" " * ((start_box_width - 2) // 2) + top_left + horizontal * (end_box_width - 2) + top_right)
    lines.append(" " * ((start_box_width - 2) // 2) + vertical + end_label.center(end_box_width - 2) + vertical)
    lines.append(" " * ((start_box_width - 2) // 2) + bottom_left + horizontal * (end_box_width - 2) + bottom_right)
    
    return "\n".join(lines)


def _generate_minimal_flowchart() -> str:
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
    answer = context.get("answer", "")
    conditions = context.get("conditions", [])
    
    condition_text = "Condition Check"
    if conditions:
        condition_text = conditions[0]
        if len(condition_text) > 20:
            condition_text = _truncate_at_word_boundary(condition_text, 20)
    else:
        cond_match = re.search(r'(?:if|when|whether)\s+([^,\.]+?)(?:,|\.|then)', answer, re.IGNORECASE)
        if cond_match:
            condition_text = cond_match.group(1).strip()
            if len(condition_text) > 20:
                condition_text = _truncate_at_word_boundary(condition_text, 20)
    
    path_a = "Path A"
    path_b = "Path B"
    
    max_label_len = max(len(condition_text), len(path_a), len(path_b), 10)
    content_width = min(max(max_label_len + 2, 12), 25)
    box_width = content_width + 4
    
    lines = []
    
    lines.append("┌" + "─" * (box_width - 2) + "┐")
    lines.append("│" + "Start".center(box_width - 2) + "│")
    lines.append("└" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 2) + "┘")
    lines.append(" " * ((box_width - 2) // 2) + "│")
    
    lines.append(" " * ((box_width - 2) // 2) + "┌" + "─" * (box_width - 2) + "┐")
    lines.append(" " * ((box_width - 2) // 2) + "│" + condition_text.center(box_width - 2) + "│")
    lines.append(" " * ((box_width - 2) // 2) + "└" + "─" * ((box_width - 2) // 4) + "┬" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 4) + "┘")
    
    indent_yes = " " * ((box_width - 2) // 2 - 2)
    indent_no = " " * ((box_width - 2) // 2 + (box_width - 2) // 2)
    
    lines.append(indent_yes + "Yes│" + " " * ((box_width - 2) // 2) + "│No")
    lines.append(indent_yes + "   │" + " " * ((box_width - 2) // 2) + "│")
    
    path_box_width = min(box_width - 4, 15)
    lines.append(indent_yes + "┌" + "─" * (path_box_width - 2) + "┐" + " " * 2 + "┌" + "─" * (path_box_width - 2) + "┐")
    lines.append(indent_yes + "│" + path_a.center(path_box_width - 2) + "│" + " " * 2 + "│" + path_b.center(path_box_width - 2) + "│")
    lines.append(indent_yes + "└" + "─" * (path_box_width - 2) + "┘" + " " * 2 + "└" + "─" * (path_box_width - 2) + "┘")
    lines.append(indent_yes + "   │" + " " * ((box_width - 2) // 2) + "│")
    lines.append(indent_yes + "   └" + "─" * ((box_width - 2) // 2) + "─" + "┘")
    lines.append(indent_yes + "     │")

    lines.append(indent_yes + "     ┌" + "─" * (box_width - 2) + "┐")
    lines.append(indent_yes + "     │" + "Continue".center(box_width - 2) + "│")
    lines.append(indent_yes + "     └" + "─" * (box_width - 2) + "┘")
    
    return "\n".join(lines)


def generate_generic_process_flowchart(context: Dict[str, any]) -> str:
    num_steps = context.get("num_steps", 3)
    answer = context.get("answer", "")
    if num_steps == 3 and answer:
        step_count = len(re.findall(r'\b(?:step|stage|phase|part)\s+\d+', answer, re.IGNORECASE))
        if step_count > 0:
            num_steps = min(step_count, 6)
    num_steps = max(2, min(num_steps, 6))
    steps = []
    for i in range(1, num_steps + 1):
        steps.append(f"Step {i}")
    
    return generate_step_based_flowchart(steps)


def generate_for_loop_flowchart(context: Dict[str, any]) -> str:
    return generate_iterative_flowchart(context, "for")
    variables = context.get("variables", [])
    var_name = variables[0] if variables else "item"
    labels = ["Start", f"Initialize {var_name}", "Condition Check", "Body", "Exit", "Update"]
    max_label_len = max(len(label) for label in labels)
    
    content_width = max(12, min(max_label_len + 2, 25))
    box_width = content_width + 4
    center_pos = box_width // 2
    
    lines = []

    lines.append("┌" + "─" * (box_width - 2) + "┐")
    lines.append("│" + "Start".center(box_width - 2) + "│")
    lines.append("└" + "─" * (center_pos - 1) + "┬" + "─" * (box_width - center_pos - 2) + "┘")
    lines.append(" " * (center_pos - 1) + "│")
    
    init_text = f"Initialize {var_name}"
    if len(init_text) > content_width:
        init_text = _truncate_at_word_boundary(init_text, content_width)
    lines.append(" " * (center_pos - 1) + "┌" + "─" * (box_width - 2) + "┐")
    lines.append(" " * (center_pos - 1) + "│" + init_text.center(box_width - 2) + "│")
    lines.append(" " * (center_pos - 1) + "└" + "─" * (center_pos - 1) + "┬" + "─" * (box_width - center_pos - 2) + "┘")
    lines.append(" " * (center_pos - 1) + " " * (center_pos - 1) + "│")
    
    cond_text = "Condition Check"
    if len(cond_text) > content_width:
        cond_text = _truncate_at_word_boundary(cond_text, content_width)
    lines.append(" " * (center_pos - 1) + " " * (center_pos - 1) + "┌" + "─" * (box_width - 2) + "┐")
    lines.append(" " * (center_pos - 1) + " " * (center_pos - 1) + "│" + cond_text.center(box_width - 2) + "│")
    lines.append(" " * (center_pos - 1) + " " * (center_pos - 1) + "└" + "─" * (center_pos - 3) + "┬" + "─" * (box_width - center_pos * 2 + 2) + "┬" + "─" * (center_pos - 3) + "┘")
    branch_width = min(12, box_width - 6)
    indent_left = " " * (center_pos - 1) + " " * (center_pos - 4)
    branch_spacing = max(2, box_width - center_pos * 2 - branch_width * 2)
    lines.append(indent_left + "Yes│" + " " * branch_spacing + "│No")
    lines.append(indent_left + "   │" + " " * branch_spacing + "│")
    lines.append(indent_left + "┌" + "─" * (branch_width - 2) + "┐" + " " * branch_spacing + "┌" + "─" * (branch_width - 2) + "┐")
    lines.append(indent_left + "│" + "Body".center(branch_width - 2) + "│" + " " * branch_spacing + "│" + "Exit".center(branch_width - 2) + "│")
    lines.append(indent_left + "└" + "─" * (branch_width - 2) + "┘" + " " * branch_spacing + "└" + "─" * (branch_width - 2) + "┘")
    lines.append(indent_left + "   │")
    
    update_text = "Update"
    lines.append(indent_left + "   ┌" + "─" * (box_width - 2) + "┐")
    lines.append(indent_left + "   │" + update_text.center(box_width - 2) + "│")
    lines.append(indent_left + "   └" + "─" * (center_pos - 1) + "┘")
    lines.append(indent_left + "     │")
    lines.append(indent_left + "     └───► (loop back)")
    
    return "\n".join(lines)


def generate_while_loop_flowchart(context: Dict[str, any]) -> str:
    return generate_iterative_flowchart(context, "while")   
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
    answer = context.get("answer", "")
    question = context.get("question", "")
    components = context.get("components", [])
    if not components:
        components = extract_structure_components(answer, question)

    if components:
        return generate_component_structure(components)
  
    if answer:
        hierarchy_match = re.search(r'(?:top|upper|highest|main).*?(?:level|layer|tier)', answer, re.IGNORECASE)
        if hierarchy_match:
            levels = ["Top Level", "Middle Level", "Bottom Level"]
            return generate_component_structure(levels)
    return _generate_minimal_structure()


def extract_structure_components(answer: str, question: str) -> List[str]:
    if not answer:
        return []
    
    components = []
    answer_lower = answer.lower()
    combined_text = f"{question} {answer}".lower()
    component_patterns = [
        r'(?:consists|composed|made)\s+of\s+([^\.]+?)(?:\.|$)',
        r'(?:has|contains|includes|comprises)\s+([^\.]+?)(?:\.|$)',
        r'(?:components?|parts?|elements?)\s+(?:are|is|include|consist of)\s+([^\.]+?)(?:\.|$)',
    ]
    
    for pattern in component_patterns:
        matches = re.findall(pattern, answer, re.IGNORECASE)
        if matches:
            for match in matches:
                parts = re.split(r'[,;]\s*|\s+and\s+|\s+or\s+', match)
                for part in parts:
                    part = part.strip()
                    words = part.split()
                    meaningful = [w for w in words[:3] if w.lower() not in STOPWORDS]
                    if meaningful:
                        comp = ' '.join(meaningful).capitalize()
                        if len(comp) >= 2 and comp not in components:
                            components.append(comp)
            if components:
                break
    
    if not components:
        capitalized = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', answer)
        for cap in capitalized[:10]:  
            if len(cap) >= 3 and cap.lower() not in STOPWORDS:
                components.append(cap)

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
    
    if not components and question:
        question_components = re.findall(r'(?:parts?|components?|elements?)\s+of\s+(\w+)', question, re.IGNORECASE)
        if question_components:
            components.extend([c.capitalize() for c in question_components[:3]])
    
    max_items, _ = _calculate_adaptive_limits(len(answer), len(components))
    return components[:max_items]


def generate_component_structure(components: List[str]) -> str:
    if not components:
        return _generate_minimal_structure()
    
    max_comp_len = max(len(comp) for comp in components) if components else 0
    content_width = max(12, min(max_comp_len + 2, 30))  
    box_width = content_width + 4
    
    formatted = []
    for comp in components:
        if len(comp) > content_width:
            comp = _truncate_at_word_boundary(comp, content_width)
        formatted.append(comp)
    
    lines = []
    
    if len(formatted) == 1:
        lines.append("┌" + "─" * (box_width - 2) + "┐")
        lines.append("│" + formatted[0].center(box_width - 2) + "│")
        lines.append("└" + "─" * (box_width - 2) + "┘")
    elif len(formatted) == 2:
        lines.append("┌" + "─" * (box_width - 2) + "┐")
        lines.append("│" + formatted[0].center(box_width - 2) + "│")
        lines.append("└" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 2) + "┘")
        lines.append(" " * ((box_width - 2) // 2) + "│")
        lines.append(" " * ((box_width - 2) // 2) + "┌" + "─" * (box_width - 2) + "┐")
        lines.append(" " * ((box_width - 2) // 2) + "│" + formatted[1].center(box_width - 2) + "│")
        lines.append(" " * ((box_width - 2) // 2) + "└" + "─" * (box_width - 2) + "┘")
    else:
        lines.append("┌" + "─" * (box_width - 2) + "┐")
        lines.append("│" + formatted[0].center(box_width - 2) + "│")
        lines.append("└" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 2) + "┘")
        lines.append(" " * ((box_width - 2) // 2) + "│")
        
        for comp in formatted[1:-1]:
            lines.append(" " * ((box_width - 2) // 2) + "┌" + "─" * (box_width - 2) + "┐")
            lines.append(" " * ((box_width - 2) // 2) + "│" + comp.center(box_width - 2) + "│")
            lines.append(" " * ((box_width - 2) // 2) + "└" + "─" * ((box_width - 2) // 2) + "┬" + "─" * ((box_width - 2) // 2) + "┘")
            lines.append(" " * ((box_width - 2) // 2) + " " * ((box_width - 2) // 2) + "│")
        
        if len(formatted) > 1:
            indent = " " * ((box_width - 2) // 2) * (len(formatted) - 1)
            lines.append(indent + "┌" + "─" * (box_width - 2) + "┐")
            lines.append(indent + "│" + formatted[-1].center(box_width - 2) + "│")
            lines.append(indent + "└" + "─" * (box_width - 2) + "┘")
    
    return "\n".join(lines)


def _generate_minimal_structure() -> str:
    return """┌────────┐
│Component│
└─────────┘"""


def _is_cyclic_process(question: str, answer: str) -> bool:
    combined = f"{question} {answer}".lower()
    
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
    if not steps or len(steps) < 2:
        return generate_step_based_flowchart(steps)

    steps = steps[:6]

    max_step_len = max(len(step) for step in steps) if steps else 12
    content_width = max(12, min(max_step_len + 2, 22))
    box_width = content_width + 4
    
    lines = []

    formatted_steps = []
    for step in steps:
        step = step.strip()
        if len(step) > content_width:
            step = _truncate_at_word_boundary(step, content_width)
        if step:
            step = step[0].upper() + step[1:] if len(step) > 1 else step.upper()
        formatted_steps.append(step)
    
    for i, step in enumerate(formatted_steps):
        step_padded = step.center(content_width)
        
        if i == 0:
            lines.append("┌" + "─" * (box_width - 2) + "┐")
            lines.append("│" + step_padded + "│")
            lines.append("└" + "─" * (box_width // 2 - 1) + "┬" + "─" * (box_width // 2 - 1) + "┘")
            lines.append(" " * (box_width // 2 - 1) + "│")
        else:
            lines.append(" " * (box_width // 2 - 1) + "┌" + "─" * (box_width - 2) + "┐")
            lines.append(" " * (box_width // 2 - 1) + "│" + step_padded + "│")
            
            if i < len(formatted_steps) - 1:
                lines.append(" " * (box_width // 2 - 1) + "└" + "─" * (box_width // 2 - 1) + "┬" + "─" * (box_width // 2 - 1) + "┘")
                lines.append(" " * (box_width // 2 - 1) + " " * (box_width // 2 - 1) + "│")
            else:
                lines.append(" " * (box_width // 2 - 1) + "└" + "─" * (box_width // 2 - 1) + "┘")
                lines.append(" " * (box_width // 2 - 1) + " " * (box_width // 2 - 1) + "│")
                lines.append(" " * (box_width // 2 - 1) + " " * (box_width // 2 - 1) + "└───► (cycle)")
                lines.append(" " * (box_width // 2 - 2) + "◄───┘")
                lines.append(" " * (box_width // 2 - 2) + "│")
                lines.append(" " * (box_width // 2 - 2) + "└─── (repeats)")
    
    return "\n".join(lines)


def generate_process_diagram(context: Dict[str, any]) -> Optional[str]:
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
    
    if not steps and question:
        question_steps = extract_steps_from_answer(question, rag_chunks, llm_handler)
        if question_steps:
            return generate_step_based_flowchart(question_steps)
    
    if not steps and answer:
        key_terms = _extract_key_process_terms(answer)
        if key_terms and len(key_terms) >= 2:
            return generate_step_based_flowchart(key_terms)
    
    num_steps = context.get("num_steps", 3)
    if num_steps == 3 and answer:
        sequential_count = len(re.findall(
            r'\b(first|second|third|fourth|fifth|sixth|then|next|after|finally)', 
            answer, re.IGNORECASE
        ))
        if sequential_count > 0:
            num_steps = min(sequential_count + 1, 6)
    
    num_steps = max(2, min(num_steps, 6))
    generic_steps = [f"Step {i}" for i in range(1, num_steps + 1)]
    
    return generate_step_based_flowchart(generic_steps)


def _extract_key_process_terms(text: str) -> List[str]:
    terms = []
    text_lower = text.lower()
    
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
            if term and len(term) > 3 and term.lower() not in STOPWORDS:
                words = term.split()
                meaningful = [w for w in words[:2] if w.lower() not in STOPWORDS]
                if meaningful:
                    term = ' '.join(meaningful).capitalize()
                    if term not in terms:
                        terms.append(term)
    
    return terms[:6] 

