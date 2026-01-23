import re
import logging
from typing import Tuple, Optional, Dict, List

logger = logging.getLogger(__name__)

# Common stopwords
STOPWORDS = {
    "the", "is", "are", "a", "an", "to", "of", "and", "or", "for", "in", "on", "at", "by", "that",
    "this", "it", "as", "be", "with", "from", "into", "their", "its", "they", "them", "can", "will",
    "about", "how", "what", "why", "which", "who", "whose", "when", "where", "than", "then", "also",
    "has", "have", "had", "do", "does", "did", "was", "were", "been", "being", "would", "could", "should"
}


def should_generate_diagram(question: str, answer: str) -> Tuple[bool, Optional[str]]:
    """
    Determine if diagram should be generated and what type using semantic analysis.
    
    Uses multiple heuristics:
    1. Question intent analysis (what/how/explain patterns)
    2. Answer structure analysis (steps, sequences, hierarchies)
    3. Conceptual pattern detection (processes, flows, structures)
    4. Content complexity scoring
    
    Args:
        question: Student's question
        answer: Generated answer from Phi model
    
    Returns:
        (should_generate, diagram_type) where diagram_type is:
        - "flowchart" for decision flows, loops, conditional logic
        - "structure" for data structures, hierarchies, organizations
        - "process" for step-by-step procedures, cycles, sequences
        - None if no diagram needed
    """
    if not question or not answer:
        return False, None
    
    question_lower = question.lower().strip()
    answer_lower = answer.lower().strip()
    min_question_len = max(3, len(question_lower) // 10)  
    min_answer_len = max(10, len(answer_lower) // 20)  
    
    if len(question_lower) < min_question_len or len(answer_lower) < min_answer_len:
        return False, None
    
    # Multi-heuristic scoring system
    scores = {
        "flowchart": 0,
        "structure": 0,
        "process": 0
    }
    
    # Heuristic 1: Question intent patterns
    scores = _analyze_question_intent(question_lower, scores)
    
    # Heuristic 2: Answer structure patterns
    scores = _analyze_answer_structure(answer_lower, scores)
    
    # Heuristic 3: Conceptual pattern detection
    scores = _detect_conceptual_patterns(question_lower, answer_lower, scores)
    
    visualizable = _is_content_visualizable(question_lower, answer_lower)
    
    if not visualizable:
        return False, None
    
    if len(answer_lower) > 500:
        adaptive_threshold = 2 
    else:
        adaptive_threshold = 3
    
    max_score = max(scores.values())
    
    if len(answer_lower) > 800 and max_score >= 1:
        if scores["process"] >= 1:
            return True, "process"
        elif scores["structure"] >= 1:
            return True, "structure"
        elif scores["flowchart"] >= 1:
            return True, "flowchart"
            
    if max_score < adaptive_threshold:
        return False, None
    
    diagram_type = max(scores, key=scores.get)
    return True, diagram_type


def _analyze_question_intent(question: str, scores: Dict[str, int]) -> Dict[str, int]:
    process_patterns = [
        r'\b(how|what|explain|describe|tell)\s+(do|does|did|is|are|was|were)\s+.*\s+(work|happen|occur|proceed|flow|go)',
        r'\b(process|procedure|method|way|approach|mechanism)',
        r'\b(step|stage|phase|level|part)\s+(by|in|of)',
        r'\b(sequence|order|series|chain|cycle)',
        r'\b(first|then|next|finally|after|before|during)',
        r'\b(explain|describe|show|tell)\s+(me|us)?\s+(the|a|an)?\s+(process|procedure|method|way)',
    ]
    
    flowchart_patterns = [
        r'\b(how|what)\s+(do|does|did)\s+.*\s+(decide|choose|select|determine|pick)',
        r'\b(if|when|whether|condition|conditional|decision|branch)',
        r'\b(loop|iterate|repeat|while|for|until)',
        r'\b(flow|path|route|direction|sequence)',
        r'\b(logic|reasoning|thinking)\s+(flow|work|process)',
        r'\b(how|what)\s+(do|does)\s+.*\s+(know|determine|decide|choose)',
    ]
    
    structure_patterns = [
        r'\b(what|how)\s+(is|are)\s+(the|a|an)?\s+(structure|organization|layout|arrangement|format|form|shape)',
        r'\b(show|display|draw|illustrate|visualize)\s+(the|a|an)?\s+(structure|organization|layout|arrangement|form)',
        r'\b(how|what)\s+(is|are)\s+.*\s+(organized|structured|arranged|laid\s+out|formatted|built|made)',
        r'\b(hierarchy|tree|graph|network|system|framework|model)',
        r'\b(component|part|element|piece|section|segment)\s+(of|in|within)',
        r'\b(what|how)\s+(does|do)\s+.*\s+(look|appear|seem|consist|comprise)',
    ]
    
    for pattern in process_patterns:
        if re.search(pattern, question, re.IGNORECASE):
            scores["process"] += 2
            break
    
    for pattern in flowchart_patterns:
        if re.search(pattern, question, re.IGNORECASE):
            scores["flowchart"] += 2
            break
    
    for pattern in structure_patterns:
        if re.search(pattern, question, re.IGNORECASE):
            scores["structure"] += 2
            break
    
    return scores


def _analyze_answer_structure(answer: str, scores: Dict[str, int]) -> Dict[str, int]:
    step_patterns = [
        r'\b(step|stage|phase|part)\s+(\d+|one|two|three|four|five|first|second|third|fourth|fifth)',
        r'^\s*[\d\.\)]\s+', 
        r'^\s*[-•*]\s+',  
        r'\b(first|second|third|fourth|fifth|then|next|finally|lastly|after|before)',
    ]
    
    step_count = 0
    for pattern in step_patterns:
        matches = re.findall(pattern, answer, re.MULTILINE | re.IGNORECASE)
        step_count += len(matches)
    
    if step_count >= 2:
        scores["process"] += 3
    elif step_count >= 1:
        scores["process"] += 1
    
    conditional_patterns = [
        r'\b(if|when|whether|condition|conditional)\s+.*\s+(then|else|otherwise)',
        r'\b(if|when)\s+.*\s+(do|does|happen|occur)',
        r'\b(decision|choice|select|choose|determine)',
        r'\b(loop|iterate|repeat|while|for|until)',
    ]
    
    conditional_count = sum(len(re.findall(p, answer, re.IGNORECASE)) for p in conditional_patterns)
    if conditional_count >= 1:
        scores["flowchart"] += 2
    
    structure_indicators = [
        r'\b(consists\s+of|composed\s+of|made\s+up\s+of|contains|includes|has|holds)',
        r'\b(part|component|element|piece|section|division|segment|portion)',
        r'\b(hierarchy|level|layer|tier|rank|order|position)',
        r'\b(tree|graph|network|structure|organization|system|framework)',
        r'\b(group|category|class|type|kind|sort|variety)',
    ]
    
    structure_count = sum(len(re.findall(p, answer, re.IGNORECASE)) for p in structure_indicators)
    if structure_count >= 2:
        scores["structure"] += 2
    elif structure_count >= 1:
        scores["structure"] += 1
    
    return scores


def _detect_conceptual_patterns(question: str, answer: str, scores: Dict[str, int]) -> Dict[str, int]:
    combined_text = f"{question} {answer}".lower()
    action_verbs = [
        r'\b(transform|convert|change|become|turn|evolve|develop|grow|form|create|produce|generate|make)',
        r'\b(move|flow|travel|transfer|pass|go|come|enter|exit|leave|arrive)',
        r'\b(break|split|divide|separate|combine|merge|join|unite|connect)',
        r'\b(absorb|release|emit|expel|take|give|receive|send|deliver)',
    ]
    
    action_count = sum(len(re.findall(pattern, combined_text, re.IGNORECASE)) for pattern in action_verbs)
    if action_count >= 2:
        scores["process"] += 2
    elif action_count >= 1:
        scores["process"] += 1
    
    temporal_patterns = [
        r'\b(cycle|circular|recurring|repeating|continuous|ongoing|perpetual)',
        r'\b(again|once more|repeatedly|continuously|constantly)',
        r'\b(return|go back|come back|revert|restart|begin again)',
        r'\b(loop|iteration|repeat|recur|reoccur)',
    ]
    
    temporal_count = sum(len(re.findall(pattern, combined_text, re.IGNORECASE)) for pattern in temporal_patterns)
    if temporal_count >= 1:
        scores["process"] += 2
    
    transformation_patterns = [
        r'\b(from|into|to|toward|towards)\s+\w+',  
        r'\b(before|after|during|while)\s+\w+', 
        r'\b(stage|phase|step|level)\s+(of|in)',  
    ]
    
    transformation_count = sum(len(re.findall(pattern, combined_text, re.IGNORECASE)) for pattern in transformation_patterns)
    if transformation_count >= 2:
        scores["process"] += 1
    
    # Flowchart indicators
    conditional_patterns = [
        r'\b(if|when|whether|unless|provided|assuming|supposing)\s+\w+', 
        r'\b(then|else|otherwise|alternatively|instead|or else)',  
        r'\b(decision|choice|select|choose|pick|determine|decide)', 
        r'\b(condition|criteria|requirement|rule|check|test|verify)', 
    ]
    
    conditional_count = sum(len(re.findall(pattern, combined_text, re.IGNORECASE)) for pattern in conditional_patterns)
    if conditional_count >= 2:
        scores["flowchart"] += 3
    elif conditional_count >= 1:
        scores["flowchart"] += 2
    
    logical_flow_patterns = [
        r'\b(based on|depending on|according to|based upon)',  
        r'\b(if\s+\w+\s+then|when\s+\w+\s+then)', 
        r'\b(yes|no|true|false)\s+(then|do|does|happen)',  
        r'\b(compare|compare to|compare with|versus|vs)',  
    ]
    
    logical_count = sum(len(re.findall(pattern, combined_text, re.IGNORECASE)) for pattern in logical_flow_patterns)
    if logical_count >= 1:
        scores["flowchart"] += 2
    
    iterative_patterns = [
        r'\b(iterate|iteration|repeat|repetition|loop)', 
        r'\b(each|every|all|for each|for every)',  
        r'\b(while|until|as long as|for as long)', 
        r'\b(continue|keep|maintain|persist|carry on)',  
    ]
    
    iterative_count = sum(len(re.findall(pattern, combined_text, re.IGNORECASE)) for pattern in iterative_patterns)
    if iterative_count >= 1:
        scores["flowchart"] += 2
    
    # Structure indicators
    part_whole_patterns = [
        r'\b(consists of|composed of|made up of|made of|comprises)', 
        r'\b(contains|includes|has|holds|encompasses)',  
        r'\b(part|component|element|piece|section|segment|portion)', 
        r'\b(whole|entire|complete|full|total|entirety)',  
    ]
    
    part_whole_count = sum(len(re.findall(pattern, combined_text, re.IGNORECASE)) for pattern in part_whole_patterns)
    if part_whole_count >= 2:
        scores["structure"] += 3
    elif part_whole_count >= 1:
        scores["structure"] += 2
    
    hierarchical_patterns = [
        r'\b(hierarchy|hierarchical|level|layer|tier|rank|order)',  
        r'\b(above|below|under|over|top|bottom|upper|lower)',  
        r'\b(parent|child|ancestor|descendant|root|branch)',  
        r'\b(main|primary|secondary|sub|subordinate|superior)', 
    ]
    
    hierarchical_count = sum(len(re.findall(pattern, combined_text, re.IGNORECASE)) for pattern in hierarchical_patterns)
    if hierarchical_count >= 1:
        scores["structure"] += 2
    
    relationship_patterns = [
        r'\b(related to|connected to|linked to|associated with|tied to)',  
        r'\b(relationship|connection|link|association|bond|tie)', 
        r'\b(between|among|amongst|within|inside|outside)',  
        r'\b(interact|interaction|interconnect|interdependent)',  
    ]
    
    relationship_count = sum(len(re.findall(pattern, combined_text, re.IGNORECASE)) for pattern in relationship_patterns)
    if relationship_count >= 2:
        scores["structure"] += 2
    elif relationship_count >= 1:
        scores["structure"] += 1
    
    organizational_patterns = [
        r'\b(organize|organization|organised|structure|structured)', 
        r'\b(arrange|arrangement|layout|format|form|shape)', 
        r'\b(category|categorize|classify|classification|group|grouping)', 
        r'\b(system|systematic|framework|model|pattern|design)', 
    ]
    
    organizational_count = sum(len(re.findall(pattern, combined_text, re.IGNORECASE)) for pattern in organizational_patterns)
    if organizational_count >= 1:
        scores["structure"] += 1
    
    return scores


def _is_content_visualizable(question: str, answer: str) -> bool:
    min_length = max(30, len(question) * 2)  
    if len(answer) < min_length:
        return False
    
    visualizable_patterns = [
        r'\b(step|stage|phase|part|component|element)',
        r'\b(flow|process|procedure|method|way|approach)',
        r'\b(structure|organization|layout|arrangement|format)',
        r'\b(relationship|connection|link|association|between)',
        r'\b(cycle|circular|repeating|recurring)',
        r'\b(sequence|order|series|chain)',
        r'\b(if|when|then|else|condition|decision)',
        r'\b(loop|iterate|repeat|while|for)',
    ]
    
    match_count = sum(len(re.findall(p, f"{question} {answer}", re.IGNORECASE)) for p in visualizable_patterns)
    
    # Need at least 2 indicators to be visualizable
    return match_count >= 2


def extract_context_for_diagram(question: str, answer: str, diagram_type: str) -> Dict[str, any]:
    context = {
        "question": question,
        "answer": answer,
        "diagram_type": diagram_type
    }
    
    question_lower = question.lower()
    answer_lower = answer.lower()
    combined_text = f"{question} {answer}".lower()
    
    if diagram_type == "process":
        steps = _extract_steps(answer)
        if steps:
            context["steps"] = steps
            context["num_steps"] = len(steps)
        else:
            context["num_steps"] = _estimate_step_count(answer)
    
    if diagram_type == "flowchart":
        variables = _extract_variables(answer)
        if variables:
            context["variables"] = variables[:5]  # Limit to 5
        
        # Detect loop types
        loop_type = _detect_loop_type(combined_text)
        if loop_type:
            context["loop_type"] = loop_type
        
        conditions = _extract_conditions(answer)
        if conditions:
            context["conditions"] = conditions[:3]  # Limit to 3
        
        if _has_decisions(answer):
            context["has_decisions"] = True
    
    if diagram_type == "structure":
        components = _extract_components(answer)
        if components:
            context["components"] = components[:8]  # Limit to 8
        
        if _has_hierarchy(answer):
            context["has_hierarchy"] = True
        
        relationships = _extract_relationships(answer)
        if relationships:
            context["relationships"] = relationships[:5]  
    
    key_concepts = _extract_key_concepts(question, answer)
    if key_concepts:
        context["key_concepts"] = key_concepts[:5]
    
    return context


def _extract_steps(answer: str) -> List[str]:
    steps = []
    
    pattern1 = r'(?:step|stage|phase|part)\s+(\d+)[:\.]?\s*([^\n\.]+)'
    matches = re.findall(pattern1, answer, re.IGNORECASE)
    for num, text in matches:
        steps.append(text.strip())
    
    pattern2 = r'^\s*(\d+)[\.\)]\s+([^\n\.]+)'
    matches = re.findall(pattern2, answer, re.MULTILINE | re.IGNORECASE)
    for num, text in matches:
        steps.append(text.strip())
    
    sequential_words = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth"]
    for word in sequential_words:
        pattern = rf'\b{word}\s*[,:\.]?\s*([^\n\.]+)'
        matches = re.findall(pattern, answer, re.IGNORECASE)
        if matches:
            steps.append(matches[0].strip())
    
    return steps[:10]  


def _estimate_step_count(answer: str) -> int:
    sequential_indicators = [
        r'\b(first|second|third|fourth|fifth|sixth|seventh|eighth)',
        r'\b(then|next|after|before|finally|lastly)',
        r'\b(step|stage|phase|part)',
    ]
    
    count = 0
    for pattern in sequential_indicators:
        count += len(re.findall(pattern, answer, re.IGNORECASE))
    
    return min(count, 10) if count > 0 else 3  


def _extract_variables(answer: str) -> List[str]:
    entities = set()
    
    patterns = [
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  
        r'\b([a-z_][a-z0-9_]*)\s*=',  
        r'(?:the|a|an)\s+(\w+)\s+(?:is|are|was|were|has|have)',  
        r'\b(\w+)\s+(?:in|of|from|to)\s+(?:the|a|an)?\s+\w+',  
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, answer, re.IGNORECASE)
        entities.update(matches)
    
    filtered = [e for e in entities if e.lower() not in STOPWORDS and len(e) > 2]
    return filtered[:5]  


def _detect_loop_type(text: str) -> Optional[str]:
    text_lower = text.lower()
    
    if re.search(r'\bfor\s+(?:each|every)?\s*\w+\s+in\s+', text_lower):
        return "for"
    elif re.search(r'\bwhile\s+\w+.*(?::|do|then|process|cycle)', text_lower):
        return "while"
    elif re.search(r'\b(?:repeat|continue)\s+until\s+', text_lower):
        return "until"
    elif re.search(r'\bdo\s+.*\s+while\s+', text_lower):
        return "do_while"
    elif re.search(r'\b(?:cycle|process|iteration)\s+(?:continues|repeats|loops)', text_lower):
        return "cycle"
    
    false_positives = [
        r'\bfor\s+(?:example|instance|the|a|an|this|that)',  
        r'\bwhile\s+(?:studying|learning|reading|the|a|an|this|that|you|we|they)',  
    ]
    
    if any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in false_positives):
        return None
    
    return None


def _extract_conditions(answer: str) -> List[str]:
    conditions = []
    patterns = [
        r'\bif\s+([^,\.]+?)\s+(?:then|do|does|happen)',
        r'\bwhen\s+([^,\.]+?)\s*[,\.]',
        r'\b(?:condition|check|test)\s+([^,\.]+?)\s*[,\.]',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, answer, re.IGNORECASE)
        conditions.extend([m.strip() for m in matches if len(m.strip()) > 3])
    
    return conditions[:5]  


def _has_decisions(answer: str) -> bool:
    decision_patterns = [
        r'\b(if|when|whether|condition)\s+.*\s+(then|else|otherwise)',
        r'\b(decision|choice|select|choose|determine)',
        r'\b(yes|no|true|false)\s+.*\s+(then|do|does)',
    ]
    
    return any(re.search(p, answer, re.IGNORECASE) for p in decision_patterns)


def _extract_components(answer: str) -> List[str]:
    components = set()
    patterns = [
        r'\b(?:consists|composed|made)\s+of\s+([^\.]+)',
        r'\b(?:has|contains|includes)\s+([^\.]+)',
        r'\b(?:part|component|element|piece)\s+(?:of|is)\s+([^\.]+)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, answer, re.IGNORECASE)
        for match in matches:
            parts = re.split(r'[,;]\s*|\s+and\s+|\s+or\s+', match)
            components.update([p.strip() for p in parts if len(p.strip()) > 2])
    
    filtered = [c for c in components if c.lower() not in STOPWORDS and len(c) > 2]
    return filtered[:10]  


def _has_hierarchy(answer: str) -> bool:
    hierarchy_patterns = [
        r'\b(hierarchy|level|layer|tier|rank|parent|child)',
        r'\b(above|below|under|over|top|bottom)',
        r'\b(tree|branch|root|leaf|node)',
    ]
    
    return any(re.search(p, answer, re.IGNORECASE) for p in hierarchy_patterns)


def _extract_relationships(answer: str) -> List[str]:
    relationships = []
    
    patterns = [
        r'\b(\w+)\s+(?:is|are)\s+(?:related|connected|linked|associated)\s+to\s+(\w+)',
        r'\b(\w+)\s+(?:connects|links|relates)\s+to\s+(\w+)',
        r'\b(?:relationship|connection|link)\s+between\s+(\w+)\s+and\s+(\w+)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, answer, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                rel = " ".join(match)
            else:
                rel = match
            if len(rel.strip()) > 3:
                relationships.append(rel.strip())
    
    return relationships[:5]  


def _extract_key_concepts(question: str, answer: str) -> List[str]:
    text = f"{question} {answer}"
    
    capitalized = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', text)
    
    technical_terms = re.findall(r'\b([a-z]+(?:\s+[a-z]+)?)\s+(?:process|cycle|structure|system|method|algorithm)\b', text.lower())
    
    concepts = set()
    concepts.update([c.lower() for c in capitalized if len(c) > 3])
    concepts.update(technical_terms)
    
    filtered = [c for c in concepts if c.lower() not in STOPWORDS and len(c) > 3]
    return filtered[:5] 