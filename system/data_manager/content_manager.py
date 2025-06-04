"""
Content Manager Module

This module handles loading, validating, and managing educational content
for the NEBedu learning system.
"""

import os
import json
import logging
import shutil
import datetime
from typing import Dict, List, Optional, Any
from jsonschema import validate, ValidationError
from student_app.progress import progress_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Maximally flexible concept schema: only 'name' is required, all else is optional, and 'questions' can be any array of objects or strings
CONCEPT_SCHEMA = {
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {"type": "string"},
        "summary": {"type": "string"},
        "steps": {
            "type": "array",
            "items": {"type": "string"}
        },
        "questions": {
            "type": "array",
            "items": {}
        }
    },
    "additionalProperties": True
}

# Maximally flexible recursive subtopic schema: only 'name' is required, all else is optional
# Subtopics and concepts can coexist or be absent, and any additional properties are allowed

def create_subtopic_schema(max_depth=3, current_depth=0):
    schema = {
        "type": "object",
        "required": ["name"],
        "properties": {
            "name": {"type": "string"},
            "concepts": {
                "type": "array",
                "items": CONCEPT_SCHEMA
            },
            "subtopics": {
                "type": "array",
                "items": create_subtopic_schema(max_depth, current_depth + 1) if current_depth < max_depth else {"type": "object"}
            }
        },
        "additionalProperties": True
    }
    return schema

SUBTOPIC_SCHEMA = create_subtopic_schema()

CONTENT_SCHEMA = {
    "type": "object",
    "required": ["subject", "grade", "topics"],
    "properties": {
        "subject": {"type": "string"},
        "grade": {"anyOf": [{"type": "string"}, {"type": "number"}]},
        "topics": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                    "subtopics": {
                        "type": "array",
                        "items": SUBTOPIC_SCHEMA
                    },
                    "concepts": {
                        "type": "array",
                        "items": CONCEPT_SCHEMA
                    }
                },
                "additionalProperties": True
            }
        }
    },
    "additionalProperties": True
}

class ContentManager:
    """
    Manages educational content for the NEBedu learning system.
    
    Attributes:
        content_dir (str): Directory containing content files
        subjects (Dict[str, Dict]): Loaded subject content
    """
    
    def __init__(self, content_dir: str):
        """
        Initialize the content manager.
        
        Args:
            content_dir (str): Path to content directory
        """
        # [DEBUG] Uncomment for developer debugging
        # print("[DEBUG] Loading content from directory:", content_dir)
        self.content_dir = content_dir
        self.subjects = {}
        self._load_content()
        # [DEBUG] Uncomment for developer debugging
        # print("[DEBUG] Subjects loaded:", list(self.subjects.keys()))
        
    def _load_content(self) -> None:
        """Load all subject content from JSON files (flat or subdirectory structure)."""
        try:
            # [DEBUG] Uncomment for developer debugging
            # print("[DEBUG] Files in content_dir:", os.listdir(self.content_dir))
            # Load flat .json files in content_dir
            for fname in os.listdir(self.content_dir):
                fpath = os.path.join(self.content_dir, fname)
                if os.path.isfile(fpath) and fname.endswith('.json'):
                    # [DEBUG] Uncomment for developer debugging
                    # print(f"[DEBUG] Attempting to load file: {fname}")
                    try:
                        with open(fpath, 'r', encoding='utf-8') as f:
                            content = json.load(f)
                            self._validate_content(content)
                            subject_name = content.get('subject') or os.path.splitext(fname)[0]
                            self.subjects[subject_name] = content
                            # [DEBUG] Uncomment for developer debugging
                            # print(f"[DEBUG] Loaded content for {subject_name} (flat file)")
                    except Exception as e:
                        # [DEBUG] Uncomment for developer debugging
                        # print(f"[DEBUG] Error loading file {fname}: {str(e)}")
                        logger.error(f"Error loading file {fname}: {str(e)}")
                        continue
                        
            # Also support old subdirectory structure for backward compatibility
            for subject in os.listdir(self.content_dir):
                subject_path = os.path.join(self.content_dir, subject)
                if os.path.isdir(subject_path):
                    content_file = os.path.join(subject_path, "content.json")
                    if os.path.exists(content_file):
                        # [DEBUG] Uncomment for developer debugging
                        # print(f"[DEBUG] Attempting to load subdir content: {content_file}")
                        try:
                            with open(content_file, 'r', encoding='utf-8') as f:
                                content = json.load(f)
                                self._validate_content(content)
                                self.subjects[subject] = content
                                # [DEBUG] Uncomment for developer debugging
                                # print(f"[DEBUG] Loaded content for {subject} (subdir)")
                        except Exception as e:
                            # [DEBUG] Uncomment for developer debugging
                            # print(f"[DEBUG] Error loading content for {subject}: {str(e)}")
                            logger.error(f"Error loading content for {subject}: {str(e)}")
                            continue
                            
        except Exception as e:
            # [DEBUG] Uncomment for developer debugging
            # print(f"[DEBUG] Error loading content: {str(e)}")
            logger.error(f"Error loading content: {str(e)}")
            # Don't raise here, allow partial loading
            
    def _validate_content(self, content: Dict) -> None:
        """
        Validate content against schema.
        
        Args:
            content (Dict): Content to validate
            
        Raises:
            ValidationError: If content is invalid
        """
        try:
            validate(instance=content, schema=CONTENT_SCHEMA)
        except ValidationError as e:
            # [DEBUG] Uncomment for developer debugging
            # print(f"[DEBUG] Content validation error: {str(e)}")
            # print(f"[DEBUG] Failed content structure: {json.dumps(content, indent=2)[:500]}...")
            logger.error(f"Content validation error: {str(e)}")
            logger.error(f"Failed content structure: {json.dumps(content, indent=2)[:500]}...")
            raise
            
    def get_subject(self, subject: str) -> Optional[Dict]:
        """
        Get content for a specific subject.
        
        Args:
            subject (str): Subject name
            
        Returns:
            Optional[Dict]: Subject content if found
        """
        return self.subjects.get(subject)
        
    def get_topic(self, subject: str, topic_name: str) -> Optional[Dict]:
        """
        Get content for a specific topic.
        
        Args:
            subject (str): Subject name
            topic_name (str): Topic name
            
        Returns:
            Optional[Dict]: Topic content if found
        """
        subject_content = self.get_subject(subject)
        if subject_content:
            for topic in subject_content["topics"]:
                if topic["name"] == topic_name:
                    return topic
        return None
        
    def get_concept(self, subject: str, topic_name: str, concept_id: str) -> Optional[Dict]:
        """
        Get content for a specific concept.
        
        Args:
            subject (str): Subject name
            topic_name (str): Topic name
            concept_id (str): Concept ID
            
        Returns:
            Optional[Dict]: Concept content if found
        """
        def search_concepts_in_subtopics(subtopics, concept_id):
            """Recursively search for concept in subtopics."""
            for subtopic in subtopics:
                # Check concepts in this subtopic
                if "concepts" in subtopic:
                    for concept in subtopic["concepts"]:
                        if concept["name"] == concept_id:
                            return concept
                # Recursively check nested subtopics
                if "subtopics" in subtopic:
                    result = search_concepts_in_subtopics(subtopic["subtopics"], concept_id)
                    if result:
                        return result
            return None
        
        topic = self.get_topic(subject, topic_name)
        if topic:
            # Check concepts directly in topic
            if "concepts" in topic:
                for concept in topic["concepts"]:
                    if concept["name"] == concept_id:
                        return concept
            
            # Check concepts in subtopics
            if "subtopics" in topic:
                return search_concepts_in_subtopics(topic["subtopics"], concept_id)
        
        return None
        
    def get_question(self, subject: str, topic_name: str, concept_id: str, question_index: int) -> Optional[Dict]:
        """
        Get a specific question from a concept.
        
        Args:
            subject (str): Subject name
            topic_name (str): Topic name
            concept_id (str): Concept ID
            question_index (int): Question index
            
        Returns:
            Optional[Dict]: Question content if found
        """
        concept = self.get_concept(subject, topic_name, concept_id)
        if concept and 0 <= question_index < len(concept["questions"]):
            return concept["questions"][question_index]
        return None
        
    def update_content(self, subject: str, content: Dict) -> None:
        """
        Update content for a subject, with versioning (backup old content).
        Args:
            subject (str): Subject name
            content (Dict): New content
        Raises:
            ValidationError: If content is invalid
        """
        try:
            self._validate_content(content)
            self.subjects[subject] = content
            # Save to file
            subject_path = os.path.join(self.content_dir, subject)
            os.makedirs(subject_path, exist_ok=True)
            content_file = os.path.join(subject_path, "content.json")
            # Versioning: backup old content
            if os.path.exists(content_file):
                backup_dir = os.path.join(subject_path, "backups")
                os.makedirs(backup_dir, exist_ok=True)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = os.path.join(backup_dir, f"content_{timestamp}.json")
                shutil.copy2(content_file, backup_file)
            with open(content_file, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            logger.info(f"Updated content for {subject}")
        except Exception as e:
            logger.error(f"Error updating content: {str(e)}")
            raise

    def suggest_content_update(self, subject: str, suggestion: Dict, username: str) -> None:
        """
        Allow community members to suggest content updates. Suggestions are saved for review.
        Args:
            subject (str): Subject name
            suggestion (Dict): Suggested content (partial or full)
            username (str): Username of the suggester
        """
        suggestions_dir = os.path.join(self.content_dir, subject, "suggestions")
        os.makedirs(suggestions_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        suggestion_file = os.path.join(suggestions_dir, f"suggestion_{username}_{timestamp}.json")
        with open(suggestion_file, 'w', encoding='utf-8') as f:
            json.dump(suggestion, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved content suggestion for {subject} by {username}")
            
    def get_all_subjects(self) -> List[str]:
        """
        Get list of all subjects.
        
        Returns:
            List[str]: List of subject names
        """
        return list(self.subjects.keys())
        
    def get_all_topics(self, subject: str) -> List[str]:
        """
        Get list of all topics for a subject.
        
        Args:
            subject (str): Subject name
            
        Returns:
            List[str]: List of topic names
        """
        subject_content = self.get_subject(subject)
        if subject_content:
            return [topic["name"] for topic in subject_content["topics"]]
        return []
        
    def get_all_concepts(self, subject: str, topic_name: str) -> List[Dict]:
        """
        Get list of all concepts for a topic.
        
        Args:
            subject (str): Subject name
            topic_name (str): Topic name
            
        Returns:
            List[Dict]: List of concept dictionaries
        """
        def collect_concepts_from_subtopics(subtopics):
            """Recursively collect concepts from subtopics."""
            concepts = []
            for subtopic in subtopics:
                if "concepts" in subtopic:
                    concepts.extend(subtopic["concepts"])
                if "subtopics" in subtopic:
                    concepts.extend(collect_concepts_from_subtopics(subtopic["subtopics"]))
            return concepts
        
        topic = self.get_topic(subject, topic_name)
        if topic:
            concepts = []
            # Add concepts directly from topic
            if "concepts" in topic:
                concepts.extend(topic["concepts"])
            # Add concepts from subtopics
            if "subtopics" in topic:
                concepts.extend(collect_concepts_from_subtopics(topic["subtopics"]))
            return concepts
        return []

    def suggest_next_concept(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Suggest the next concept for a user to study based on their progress.
        Args:
            username (str): The username
        Returns:
            Optional[Dict]: Dictionary with subject, topic, concept if found
        """
        progress = progress_manager.load_progress(username)
        for subject in self.get_all_subjects():
            for topic in self.get_all_topics(subject):
                for concept in self.get_all_concepts(subject, topic):
                    # Check if all questions in this concept are mastered
                    concept_name = concept.get("name")
                    all_mastered = True
                    for q in concept.get("questions", []):
                        found = False
                        if subject in progress:
                            if topic in progress[subject]:
                                if concept_name in progress[subject][topic]:
                                    for pq in progress[subject][topic][concept_name].get('questions', []):
                                        if pq['question'] == q['question'] and pq['correct'] >= 3:
                                            found = True
                                            break
                        if not found:
                            all_mastered = False
                            break
                    if not all_mastered:
                        return {
                            "subject": subject,
                            "topic": topic,
                            "concept": concept
                        }
        return None

    def get_weak_concepts(self, username: str) -> List[Dict[str, Any]]:
        """
        Get a list of weak concepts/questions for a user (repeated mistakes).
        Args:
            username (str): The username
        Returns:
            List[Dict]: List of dicts with subject, topic, concept, question
        """
        progress = progress_manager.load_progress(username)
        weak = []
        for subject in self.get_all_subjects():
            for topic in self.get_all_topics(subject):
                for concept in self.get_all_concepts(subject, topic):
                    concept_name = concept.get("name")
                    for q in concept.get("questions", []):
                        attempts = 0
                        correct = 0
                        if subject in progress:
                            if topic in progress[subject]:
                                if concept_name in progress[subject][topic]:
                                    for pq in progress[subject][topic][concept_name].get('questions', []):
                                        if pq['question'] == q['question']:
                                            attempts = pq['attempts']
                                            correct = pq['correct']
                                            break
                        if attempts >= 2 and correct == 0:
                            weak.append({
                                "subject": subject,
                                "topic": topic,
                                "concept": concept,
                                "question": q['question']
                            })
        return weak

    def debug_content_structure(self, subject: str = None) -> None:
        """
        Debug method to print content structure for troubleshooting.
        
        Args:
            subject (str, optional): Specific subject to debug, or None for all
        """
        if subject:
            subjects_to_debug = [subject] if subject in self.subjects else []
        else:
            subjects_to_debug = list(self.subjects.keys())
        
        for subj in subjects_to_debug:
            content = self.subjects[subj]
            print(f"\n=== Subject: {subj} ===")
            print(f"Grade: {content.get('grade', 'Unknown')}")
            print(f"Topics: {len(content.get('topics', []))}")
            
            for i, topic in enumerate(content.get('topics', [])):
                print(f"  Topic {i+1}: {topic.get('name', 'Unknown')}")
                print(f"    Direct concepts: {len(topic.get('concepts', []))}")
                print(f"    Subtopics: {len(topic.get('subtopics', []))}")
                
                # Show structure of first few items for debugging
                if topic.get('concepts'):
                    print(f"    First concept keys: {list(topic['concepts'][0].keys())}")
                if topic.get('subtopics'):
                    print(f"    First subtopic keys: {list(topic['subtopics'][0].keys())}")