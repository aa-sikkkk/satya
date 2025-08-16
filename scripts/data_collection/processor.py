"""
Content Processor for Satya - PDF-First Approach

This script processes PDF chunks into structured educational content,
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

class PDFContentProcessor:
    """
    Processes PDF chunks into structured educational content.
    
    Attributes:
        processed_dir (str): Directory to save processed content
        chunks_dir (str): Directory containing PDF chunks
    """
    
    def __init__(self, chunks_dir: str = "processed_data_new/chunks", processed_dir: str = "data/content"):
        """
        Initialize the PDF processor.
        
        Args:
            chunks_dir (str): Directory containing PDF chunks
            processed_dir (str): Directory to save processed content
        """
        self.chunks_dir = chunks_dir
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
        Split large content string into logical topics based on PDF structure.
        
        Args:
            content (str): Large content string
            subject (str): Subject name
            
        Returns:
            List[Dict]: List of topics with their content
        """
        topics = []
        
        # Define topic keywords for different subjects (PDF-specific)
        topic_keywords = {
            "Computer Science": [
                r"computer network", r"internet", r"cyber", r"database", r"dbms", 
                r"programming", r"qbasic", r"ecommerce", r"data communication",
                r"transmission media", r"topology", r"security", r"virus",
                r"chapter", r"unit", r"section", r"lesson"
            ],
            "English": [
                r"grammar", r"literature", r"poetry", r"prose", r"comprehension",
                r"writing", r"speaking", r"listening", r"vocabulary",
                r"chapter", r"unit", r"section", r"lesson"
            ],
            "Science": [
                r"physics", r"chemistry", r"biology", r"motion", r"energy",
                r"forces", r"atomic", r"chemical", r"cell", r"ecosystem",
                r"chapter", r"unit", r"section", r"lesson"
            ]
        }
        
        # Split content by major sections (PDF structure)
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

    def process_pdf_chunks(self, subject: str) -> Optional[Dict]:
        """
        Process PDF chunks for a specific subject.
        
        Args:
            subject: str: Subject name
            
        Returns:
            Dict: Structured content or None if failed
        """
        try:
            # Find chunks file for this subject
            chunks_file = os.path.join(self.chunks_dir, f"{subject.lower().replace(' ', '_')}_grade_10_chunks.json")
            
            if not os.path.exists(chunks_file):
                logger.warning(f"Chunks file not found: {chunks_file}")
                return None
            
            # Load chunks
            with open(chunks_file, 'r', encoding='utf-8') as f:
                chunks_data = json.load(f)
            
            # Extract text chunks
            text_chunks = chunks_data.get('text_chunks', [])
            
            if not text_chunks:
                logger.warning(f"No text chunks found in {chunks_file}")
                return None
            
            # Combine all chunks into content
            all_content = "\n\n".join([
                chunk.get('text', '') for chunk in text_chunks
            ])
            
            # Split content into topics
            topics = self.split_content_into_topics(all_content, subject)
            
            # Process each topic
            processed_topics = []
            for topic in topics:
                concepts = self.extract_concepts_from_content(topic["content"])
                
                processed_topics.append({
                    "name": topic["name"],
                    "subtopics": [{
                        "name": topic["name"],
                        "concepts": concepts
                    }]
                })
            
            # Create structured content
            structured_content = {
                "subject": subject,
                "grade": 10,
                "topics": processed_topics
            }
            
            # Validate content
            if not self.validate_content(structured_content):
                logger.warning(f"Invalid content structure for {subject}")
                return None
            
            return structured_content
            
        except Exception as e:
            logger.error(f"Error processing PDF chunks for {subject}: {str(e)}")
            return None
    
    def process_all_subjects(self) -> None:
        """Process all available subjects from PDF chunks."""
        try:
            # Get list of available chunk files
            available_subjects = []
            for filename in os.listdir(self.chunks_dir):
                if filename.endswith('_chunks.json'):
                    # Extract subject name from filename
                    subject = filename.replace('_grade_10_chunks.json', '').replace('_', ' ').title()
                    available_subjects.append(subject)
            
            logger.info(f"Found {len(available_subjects)} subjects to process: {available_subjects}")
            
            # Process each subject
            for subject in available_subjects:
                logger.info(f"Processing {subject}...")
                
                structured_content = self.process_pdf_chunks(subject)
                
                if structured_content:
                    # Save processed content
                    output_name = f"{subject.lower().replace(' ', '_')}.json"
                    output_path = os.path.join(self.processed_dir, output_name)
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(structured_content, f, indent=4, ensure_ascii=False)
                    
                    logger.info(f"✅ Successfully processed {subject} -> {output_name}")
                    logger.info(f"   Topics: {len(structured_content['topics'])}")
                    logger.info(f"   Total Concepts: {sum(len(topic['subtopics'][0]['concepts']) for topic in structured_content['topics'])}")
                else:
                    logger.error(f"❌ Failed to process {subject}")
            
            logger.info("🎉 PDF content processing completed!")
            
        except Exception as e:
            logger.error(f"Error in process_all_subjects: {str(e)}")
    
    def get_available_subjects(self) -> List[str]:
        """Get list of subjects available for processing."""
        available_subjects = []
        try:
            for filename in os.listdir(self.chunks_dir):
                if filename.endswith('_chunks.json'):
                    subject = filename.replace('_grade_10_chunks.json', '').replace('_', ' ').title()
                    available_subjects.append(subject)
        except Exception as e:
            logger.error(f"Error getting available subjects: {str(e)}")
        
        return available_subjects

def main():
    """Main function to run the PDF processor."""
    processor = PDFContentProcessor()
    
    # Show available subjects
    available = processor.get_available_subjects()
    print(f"📚 Available subjects: {available}")
    
    # Process all subjects
    processor.process_all_subjects()

if __name__ == "__main__":
    main()