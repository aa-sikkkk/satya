"""
Content Processor for NEBedu

This script processes and cleans the crawled educational content,
ensuring it follows our structured format and is ready for the AI model.
"""

import os
import json
import logging
import re
from typing import Dict, List, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

content_dir = "data/raw_content"
processed_dir = "data/content"

class ContentProcessor:
    """
    Processes and cleans crawled educational content.
    
    Attributes:
        content_dir (str): Directory containing crawled content
        processed_dir (str): Directory to save processed content
    """
    
    def __init__(self, content_dir: str = "data/raw_content", processed_dir: str = "data/content"):
        """
        Initialize the processor.
        
        Args:
            content_dir (str): Directory containing crawled content
            processed_dir (str): Directory to save processed content
        """
        self.content_dir = content_dir
        self.processed_dir = processed_dir
        
        # Create processed directory if it doesn't exist
        os.makedirs(processed_dir, exist_ok=True)
        
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text (str): Text to clean
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
            
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Keep basic punctuation and alphanumeric characters
        text = re.sub(r'[^\w\s\u0900-\u097F.,!?():;-]', '', text)
        
        # Normalize whitespace
        text = text.strip()
        
        return text
        
    def validate_content(self, content: Dict) -> bool:
        """
        Recursively validate content structure to match the actual JSON files.
        - Each topic must have 'name' and 'subtopics'.
        - Each subtopic must have 'name' and at least one of 'concepts' or 'subtopics'.
        - Concepts must have 'name', 'summary', 'steps', and 'questions'.
        - Questions must have 'question', 'acceptable_answers', and 'hints'.
        """
        def validate_subtopic(subtopic: Dict) -> bool:
            if "name" not in subtopic:
                return False
            has_concepts = "concepts" in subtopic and isinstance(subtopic["concepts"], list)
            has_subtopics = "subtopics" in subtopic and isinstance(subtopic["subtopics"], list)
            if not (has_concepts or has_subtopics):
                return False
            if has_concepts:
                for concept in subtopic["concepts"]:
                    if not ("name" in concept and "summary" in concept and "steps" in concept and "questions" in concept):
                        return False
                    for question in concept["questions"]:
                        if not ("question" in question and "acceptable_answers" in question and "hints" in question):
                            return False
            if has_subtopics:
                for sub in subtopic["subtopics"]:
                    if not validate_subtopic(sub):
                        return False
            return True

        if not all(field in content for field in ["subject", "grade", "topics"]):
            return False
        for topic in content["topics"]:
            if "name" not in topic or "subtopics" not in topic:
                return False
            for subtopic in topic["subtopics"]:
                if not validate_subtopic(subtopic):
                    return False
        return True
        
    def process_concept(self, concept: Dict) -> Dict:
        """
        Process a single concept to match the schema: 'name', 'summary', 'steps', 'questions'.
        """
        concept["name"] = self.clean_text(concept.get("name", ""))
        concept["summary"] = self.clean_text(concept.get("summary", ""))
        concept["steps"] = [self.clean_text(step) for step in concept.get("steps", []) if self.clean_text(step)]
        for question in concept.get("questions", []):
            question["question"] = self.clean_text(question.get("question", ""))
            question["acceptable_answers"] = [self.clean_text(ans) for ans in question.get("acceptable_answers", []) if self.clean_text(ans)]
            question["hints"] = [self.clean_text(hint) for hint in question.get("hints", []) if self.clean_text(hint)]
        return concept
        
    def process_subtopic(self, subtopic: Dict) -> Dict:
        """
        Recursively process a subtopic, handling both 'concepts' and nested 'subtopics'.
        """
        subtopic["name"] = self.clean_text(subtopic.get("name", ""))
        if "concepts" in subtopic:
            subtopic["concepts"] = [self.process_concept(c) for c in subtopic["concepts"]]
        if "subtopics" in subtopic:
            subtopic["subtopics"] = [self.process_subtopic(st) for st in subtopic["subtopics"]]
        return subtopic
        
    def split_content_into_topics(self, content: str, subject: str) -> List[Dict]:
        """
        Split large content string into logical topics based on keywords and structure.
        
        Args:
            content (str): Large content string
            subject (str): Subject name
            
        Returns:
            List[Dict]: List of topics with their content
        """
        topics = []
        
        # Define topic keywords for different subjects
        topic_keywords = {
            "Computer Science": [
                r"computer network", r"internet", r"cyber", r"database", r"dbms", 
                r"programming", r"qbasic", r"ecommerce", r"data communication",
                r"transmission media", r"topology", r"security", r"virus"
            ]
        }
        
        # Split content by major sections
        sections = re.split(r'\n\s*\n', content)
        current_topic = None
        current_content = []
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
                
            # Check if this section starts a new topic
            found_topic = False
            if subject in topic_keywords:
                for keyword in topic_keywords[subject]:
                    if re.search(keyword, section.lower()):
                        # Save previous topic if exists
                        if current_topic and current_content:
                            topics.append({
                                "name": current_topic,
                                "content": "\n".join(current_content)
                            })
                        
                        # Start new topic
                        current_topic = self.extract_topic_name(section, keyword)
                        current_content = [section]
                        found_topic = True
                        break
            
            if not found_topic:
                if current_topic:
                    current_content.append(section)
                else:
                    # First section without clear topic
                    current_topic = "Introduction"
                    current_content = [section]
        
        # Add the last topic
        if current_topic and current_content:
            topics.append({
                "name": current_topic,
                "content": "\n".join(current_content)
            })
        
        return topics if topics else [{"name": subject, "content": content}]
    
    def extract_topic_name(self, section: str, keyword: str) -> str:
        """
        Extract a clean topic name from a section.
        
        Args:
            section (str): Text section
            keyword (str): Matched keyword
            
        Returns:
            str: Clean topic name
        """
        lines = section.split('\n')
        first_line = lines[0].strip()
        
        # If first line is short and contains the keyword, use it
        if len(first_line) < 100 and keyword.replace(r"\b", "").replace(r"\s+", " ") in first_line.lower():
            return first_line.title()
        
        # Otherwise, create a topic name from the keyword
        return keyword.replace(r"\b", "").replace(r"\s+", " ").title()
        
    def parse_raw_content(self, raw: Dict, subject: str) -> Dict:
        """
        Convert raw crawled data into structured topics, subtopics, concepts, steps, and questions.
        
        Args:
            raw (Dict): Raw content from crawler
            subject (str): Subject name
            
        Returns:
            Dict: Structured content
        """
        # Extract all text content
        all_text = ""
        if "paragraphs" in raw:
            all_text = "\n".join(raw["paragraphs"])
        elif "content" in raw:
            all_text = raw["content"]
        elif "text" in raw:
            all_text = raw["text"]
        
        # If content is too large, split into topics first
        if len(all_text) > 5000:  # Threshold for splitting
            topic_chunks = self.split_content_into_topics(all_text, subject)
        else:
            topic_chunks = [{"name": subject, "content": all_text}]
        
        topics = []
        
        for topic_chunk in topic_chunks:
            topic_name = topic_chunk["name"]
            topic_content = topic_chunk["content"]
            
            # Split topic content into concepts
            concepts = self.extract_concepts_from_content(topic_content)
            
            if concepts:
                topics.append({
                    "name": topic_name,
                    "subtopics": [{
                        "name": topic_name,
                        "concepts": concepts
                    }]
                })
        
        return {
            "subject": subject,
            "grade": 10,
            "topics": topics if topics else [{
                "name": subject,
                "subtopics": [{
                    "name": subject,
                    "concepts": [{
                        "name": subject,
                        "summary": self.clean_text(all_text[:500]) + "...",
                        "steps": [],
                        "questions": []
                    }]
                }]
            }]
        }
    
    def extract_concepts_from_content(self, content: str) -> List[Dict]:
        """
        Extract individual concepts from content.
        
        Args:
            content (str): Content text
            
        Returns:
            List[Dict]: List of concepts
        """
        concepts = []
        
        # Split content into paragraphs
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        
        if not paragraphs:
            return concepts
        
        # Group paragraphs into concept chunks (every 3-5 paragraphs)
        chunk_size = min(5, max(2, len(paragraphs) // 3))  # Dynamic chunk size
        
        for i in range(0, len(paragraphs), chunk_size):
            chunk = paragraphs[i:i + chunk_size]
            
            if chunk:
                # Extract concept name from first sentence
                first_sentence = chunk[0]
                concept_name = self.extract_concept_name(first_sentence)
                
                # Create summary from chunk
                summary = " ".join(chunk)
                
                # Extract steps and questions
                steps, questions = self.extract_steps_and_questions(chunk)
                
                concepts.append({
                    "name": concept_name,
                    "summary": self.clean_text(summary),
                    "steps": steps,
                    "questions": questions
                })
        
        return concepts
    
    def extract_concept_name(self, text: str) -> str:
        """
        Extract a concept name from text.
        
        Args:
            text (str): Text to extract name from
            
        Returns:
            str: Concept name
        """
        # Take first sentence or first 50 characters
        first_sentence = text.split('.')[0].strip()
        if len(first_sentence) > 50:
            first_sentence = first_sentence[:50] + "..."
        
        return first_sentence if first_sentence else "Concept"
    
    def extract_steps_and_questions(self, paragraphs: List[str]) -> tuple:
        """
        Extract steps and questions from paragraphs.
        
        Args:
            paragraphs (List[str]): List of paragraphs
            
        Returns:
            tuple: (steps, questions)
        """
        steps = []
        questions = []
        
        for para in paragraphs:
            # Look for numbered steps or bullet points
            if re.match(r'^\d+\.', para.strip()) or re.match(r'^[-*]', para.strip()):
                steps.append(self.clean_text(para))
            
            # Look for questions
            if '?' in para or para.lower().startswith(('what', 'how', 'why', 'when', 'where')):
                questions.append({
                    "question": self.clean_text(para),
                    "acceptable_answers": ["Multiple answers possible based on context"],
                    "hints": ["Think about the key concepts discussed", "Consider the practical applications"]
                })
        
        # If no steps found, create some generic ones
        if not steps and len(paragraphs) > 1:
            steps = [
                "Understand the basic concept",
                "Learn the key components",
                "Practice with examples",
                "Apply in real situations"
            ]
        
        # If no questions found, create some generic ones
        if not questions:
            questions = [{
                "question": "What are the main points to remember about this concept?",
                "acceptable_answers": ["Key points from the content"],
                "hints": ["Review the main ideas", "Focus on important details"]
            }]
        
        return steps, questions

    def process_file(self, filepath: str) -> Optional[Dict]:
        """
        Process a single content file, recursively processing subtopics and concepts.
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = json.load(f)
            # Clean subject name
            content["subject"] = self.clean_text(content.get("subject", ""))
            for topic in content.get("topics", []):
                topic["name"] = self.clean_text(topic.get("name", ""))
                topic["subtopics"] = [self.process_subtopic(st) for st in topic.get("subtopics", [])]
            if not self.validate_content(content):
                logger.warning(f"Invalid content structure in {filepath}")
                return None
            return content
        except Exception as e:
            logger.error(f"Error processing {filepath}: {str(e)}")
            return None
            
    def process_all(self) -> None:
        """Process all content files in the content directory."""
        for filename in os.listdir(self.content_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.content_dir, filename)
                processed_content = self.process_file(filepath)
                
                if processed_content:
                    # Save processed content with final name
                    # Check for 'computer' before 'science' to avoid mislabeling
                    if "computer" in filename.lower():
                        output_name = "computer_science.json"
                    elif "science" in filename.lower():
                        output_name = "science.json"
                    else:
                        output_name = filename.replace("_raw", "")
                    output_path = os.path.join(self.processed_dir, output_name)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(processed_content, f, indent=4, ensure_ascii=False)
                    logger.info(f"Processed {filename} -> {output_name}")
                    
def main():
    """Main function to run the processor."""
    processor = ContentProcessor()
    processor.process_all()

if __name__ == "__main__":
    main()