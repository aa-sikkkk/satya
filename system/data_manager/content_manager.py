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
Content Manager Module

This module handles loading, validating, and managing educational content
for the Satya learning system.
"""

import os
import json
import logging
import shutil
import datetime
import difflib
from typing import Dict, List, Optional, Any
from jsonschema import validate, ValidationError
from student_app.progress import progress_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler('satya.log'),
        logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Strict Question Schema
QUESTION_SCHEMA = {
    "type": "object",
    "required": ["question", "acceptable_answers", "hints"],
    "properties": {
        "question": {"type": "string", "minLength": 1},
        "acceptable_answers": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "minItems": 1
        },
        "hints": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "minItems": 1
        }
    },
    "additionalProperties": False
}

# Strict Concept Schema
CONCEPT_SCHEMA = {
    "type": "object",
    "required": ["name", "summary", "steps", "questions"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "summary": {"type": "string", "minLength": 1},
        "steps": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "minItems": 1
        },
        "questions": {
            "type": "array",
            "items": QUESTION_SCHEMA
        }
    },
    "additionalProperties": False
}

# Recursive Subtopic Schema
def create_subtopic_schema(max_depth=3, current_depth=0):
    schema = {
        "type": "object",
        "required": ["name"],
        "properties": {
            "name": {"type": "string", "minLength": 1},
            "concepts": {
                "type": "array",
                "items": CONCEPT_SCHEMA
            },
            "subtopics": {
                "type": "array",
                "items": create_subtopic_schema(max_depth, current_depth + 1) if current_depth < max_depth else {"type": "object"}
            }
        },
        "additionalProperties": False,
        # Ensure at least one of concepts or subtopics is present (custom validation logic handles this better, 
        # but schema can enforcing structure)
        "anyOf": [
            {"required": ["concepts"]},
            {"required": ["subtopics"]}
        ]
    }
    return schema

SUBTOPIC_SCHEMA = create_subtopic_schema()

CONTENT_SCHEMA = {
    "type": "object",
    "required": ["subject", "grade", "topics"],
    "properties": {
        "subject": {
            "type": "string",
            "enum": ["Computer Science", "Science", "English"]
        },
        "grade": {
            "anyOf": [
                {"type": "integer", "minimum": 1, "maximum": 12},
                {"type": "string", "pattern": "^(1[0-2]|[1-9])$"}
            ]
        },
        "topics": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "subtopics"],
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                    "subtopics": {
                        "type": "array",
                        "items": SUBTOPIC_SCHEMA
                    }
                },
                "additionalProperties": False
            }
        }
    },
    "additionalProperties": False
}

class ContentManager:
    """
    Manages educational content for the Satya learning system.
    
    Attributes:
        content_dir (str): Directory containing content files
        subjects (Dict[str, Dict]): Loaded subject content
    """
    
    def __init__(self, content_dir: str = "scripts/data_collection/data/content"):
        """
        Initialize the content manager.
        
        Args:
            content_dir (str): Path to content directory
        """
        # Resolve content directory robustly: prefer provided path if valid; otherwise compute relative to project root
        provided_path = content_dir
        if not os.path.isabs(provided_path):
            provided_path_abs = os.path.abspath(provided_path)
        else:
            provided_path_abs = provided_path
        if os.path.isdir(provided_path_abs):
            resolved_dir = provided_path_abs
        else:
            # Compute default relative to this file's location (project root -> scripts/data_collection/data/content)
            this_dir = os.path.dirname(__file__)
            project_root = os.path.abspath(os.path.join(this_dir, os.pardir, os.pardir))
            candidate = os.path.join(project_root, "scripts", "data_collection", "data", "content")
            resolved_dir = candidate if os.path.isdir(candidate) else provided_path_abs
        self.content_dir = resolved_dir
        self.subjects = {}
        self._load_content()
        
    def _load_content(self) -> None:
        """Load all subject content from JSON files (flat or subdirectory structure)."""
        try:
            # Load flat .json files in content_dir
            for fname in os.listdir(self.content_dir):
                fpath = os.path.join(self.content_dir, fname)
                if os.path.isfile(fpath) and fname.endswith('.json'):
                    try:
                        with open(fpath, 'r', encoding='utf-8') as f:
                            content = json.load(f)
                            self._validate_content(content)
                            subject_name = content.get('subject') or os.path.splitext(fname)[0]
                            self.subjects[subject_name] = content
                    except Exception as e:
                        logger.error(f"Error loading file {fname}: {str(e)}")
                        continue
                        
            # Also support old subdirectory structure for backward compatibility
            for subject in os.listdir(self.content_dir):
                subject_path = os.path.join(self.content_dir, subject)
                if os.path.isdir(subject_path):
                    content_file = os.path.join(subject_path, "content.json")
                    if os.path.exists(content_file):
                        try:
                            with open(content_file, 'r', encoding='utf-8') as f:
                                content = json.load(f)
                                self._validate_content(content)
                                self.subjects[subject] = content
                        except Exception as e:
                            logger.error(f"Error loading content for {subject}: {str(e)}")
                            continue
                            
        except Exception as e:
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

    def get_subject_structure(self, subject: str) -> Optional[Dict[str, Any]]:
        """
        Return the exact data structure for a subject as loaded from content.
        
        This preserves the nested hierarchy of topics, subtopics, and concepts so
        callers that need the full tree (e.g., UI browse) can render it directly.
        
        Args:
            subject (str): Subject name
        
        Returns:
            Optional[Dict[str, Any]]: The subject dictionary or None if not found
        """
        return self.get_subject(subject)

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

    def search_content(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search through all content for relevant information.
        Optimized to return early when enough results are found.
        
        Args:
            query (str): The search query
            max_results (int): Maximum results to return (default 3 for speed)
            
        Returns:
            List[Dict[str, Any]]: List of matching content items with subject, topic, concept, and summary
        """
        results = []
        query = query.lower()
        
        for subject in self.get_all_subjects():
            subject_content = self.get_subject(subject)
            if not subject_content:
                continue
                
            for topic in subject_content.get("topics", []):
                topic_name = topic.get("name", "")
                
                # Search in topic-level concepts
                for concept in topic.get("concepts", []):
                    if self._content_matches_query(concept, query):
                        results.append({
                            "subject": subject,
                            "topic": topic_name,
                            "concept": concept.get("name", ""),
                            "summary": concept.get("summary", "")
                        })
                        # Early exit: if we have enough results, return immediately
                        if len(results) >= max_results:
                            return results
                
                # Search in subtopics (only if we don't have enough results yet)
                if len(results) < max_results:
                    for subtopic in topic.get("subtopics", []):
                        self._search_in_subtopic(subtopic, subject, topic_name, query, results, max_results)
                        # Check again after subtopic search
                        if len(results) >= max_results:
                            return results
                    
        return results
        
    def _search_in_subtopic(self, subtopic: Dict, subject: str, topic: str, query: str, results: List[Dict], max_results: int = 3) -> None:
        """
        Recursively search through a subtopic and its nested subtopics.
        Optimized to stop early when enough results are found.
        
        Args:
            subtopic (Dict): The subtopic to search
            subject (str): The subject name
            topic (str): The topic name
            query (str): The search query
            results (List[Dict]): List to append results to
            max_results (int): Maximum results to collect (for early exit)
        """
        # Search in concepts
        for concept in subtopic.get("concepts", []):
            if len(results) >= max_results:
                return  # Early exit
            if self._content_matches_query(concept, query):
                results.append({
                    "subject": subject,
                    "topic": topic,
                    "concept": concept.get("name", ""),
                    "summary": concept.get("summary", "")
                })
                if len(results) >= max_results:
                    return  # Early exit
        
        # Recursively search in nested subtopics (only if we need more results)
        if len(results) < max_results:
            for nested_subtopic in subtopic.get("subtopics", []):
                self._search_in_subtopic(nested_subtopic, subject, topic, query, results, max_results)
                if len(results) >= max_results:
                    return  # Early exit
            
    def _content_matches_query(self, content: Dict, query: str) -> bool:
        """
        Check if content matches the search query using fuzzy matching.
        """
        # Fuzzy match threshold
        threshold = 0.6
        query_lc = query.lower()
        # Check in name
        name = content.get("name", "").lower()
        if difflib.SequenceMatcher(None, query_lc, name).ratio() > threshold:
            return True
        # Check in summary
        summary = content.get("summary", "").lower()
        if difflib.SequenceMatcher(None, query_lc, summary).ratio() > threshold:
            return True
        # Search in steps
        for step in content.get("steps", []):
            if difflib.SequenceMatcher(None, query_lc, step.lower()).ratio() > threshold:
                return True
        # Search in questions
        for question in content.get("questions", []):
            if isinstance(question, dict):
                qtext = question.get("question", "").lower()
                if difflib.SequenceMatcher(None, query_lc, qtext).ratio() > threshold:
                    return True
                for answer in question.get("acceptable_answers", []):
                    if difflib.SequenceMatcher(None, query_lc, answer.lower()).ratio() > threshold:
                        return True
            elif isinstance(question, str):
                if difflib.SequenceMatcher(None, query_lc, question.lower()).ratio() > threshold:
                    return True
        # Fallback: keyword logic
        keywords = query_lc.split()
        if all(word in name for word in keywords):
            return True
        if all(word in summary for word in keywords):
            return True
        for step in content.get("steps", []):
            if all(word in step.lower() for word in keywords):
                return True
        for question in content.get("questions", []):
            if isinstance(question, dict):
                if all(word in question.get("question", "").lower() for word in keywords):
                    return True
                for answer in question.get("acceptable_answers", []):
                    if all(word in answer.lower() for word in keywords):
                        return True
            elif isinstance(question, str):
                if all(word in question.lower() for word in keywords):
                    return True
        return False

    def list_browseable_topics(self, subject: str) -> List[Dict[str, Any]]:
        """
        Produce a flattened list of browseable topic entries for a subject.

        Each entry represents either a top-level topic or a nested subtopic
        path that actually contains concepts (directly or nested). This helps
        when content extraction placed many subtopics under a single topic.

        Args:
            subject (str): Subject name

        Returns:
            List[Dict[str, Any]]: Entries with keys:
              - label: display string (e.g., "Topic > Subtopic > Nested")
              - topic: top-level topic name
              - subtopic_path: list[str] path to nested subtopic (may be empty)
        """
        subject_content = self.get_subject(subject)
        if not subject_content:
            return []

        entries: List[Dict[str, Any]] = []

        def subtopic_has_concepts(node: Dict[str, Any]) -> bool:
            if node.get("concepts"):
                return True
            for child in node.get("subtopics", []):
                if subtopic_has_concepts(child):
                    return True
            return False

        def add_entries_for_subtopics(topic_name: str, subtopics: List[Dict[str, Any]], path_prefix: List[str]):
            for st in subtopics or []:
                current_path = path_prefix + [st.get("name", "")] if st.get("name") else path_prefix
                if subtopic_has_concepts(st):
                    entries.append({
                        "label": " > ".join([topic_name] + current_path),
                        "topic": topic_name,
                        "subtopic_path": current_path,
                    })
                # Recurse to nested
                add_entries_for_subtopics(topic_name, st.get("subtopics", []), current_path)

        for topic in subject_content.get("topics", []):
            topic_name = topic.get("name", "")
            # If topic or any of its subtopics have concepts, include an entry for the topic root
            if topic.get("concepts") or subtopic_has_concepts({"subtopics": topic.get("subtopics", [])}):
                entries.append({
                    "label": topic_name,
                    "topic": topic_name,
                    "subtopic_path": [],
                })
            # Also include each nested subtopic path with content as its own entry
            add_entries_for_subtopics(topic_name, topic.get("subtopics", []), [])

        # Deduplicate by (topic, tuple(path)) while keeping first label
        seen = set()
        deduped: List[Dict[str, Any]] = []
        for e in entries:
            key = (e["topic"], tuple(e["subtopic_path"]))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(e)

        return deduped

    def get_concepts_at_path(self, subject: str, topic_name: str, subtopic_path: List[str]) -> List[Dict[str, Any]]:
        """
        Return concepts at a specific nested path within a topic.

        If subtopic_path is empty, behaves like get_all_concepts for this topic.
        Otherwise, finds the subtopic by walking the path and returns concepts
        directly under it plus any nested concepts.

        Args:
            subject (str): Subject name
            topic_name (str): Top-level topic name
            subtopic_path (List[str]): List of subtopic names representing the path

        Returns:
            List[Dict[str, Any]]: Concepts at the path (including nested)
        """
        topic = self.get_topic(subject, topic_name)
        if not topic:
            return []

        def collect_concepts(node: Dict[str, Any]) -> List[Dict[str, Any]]:
            concepts: List[Dict[str, Any]] = []
            concepts.extend(node.get("concepts", []))
            for st in node.get("subtopics", []):
                concepts.extend(collect_concepts(st))
            return concepts

        if not subtopic_path:
            # Topic-wide concepts including nested
            concepts: List[Dict[str, Any]] = []
            if "concepts" in topic:
                concepts.extend(topic["concepts"])
            for st in topic.get("subtopics", []):
                concepts.extend(collect_concepts(st))
            return concepts

        # Walk down the path
        current: Optional[Dict[str, Any]] = {"subtopics": topic.get("subtopics", [])}
        for name in subtopic_path:
            if not current:
                return []
            next_node = None
            for st in current.get("subtopics", []):
                if st.get("name") == name:
                    next_node = st
                    break
            current = next_node
        if not current:
            return []
        return collect_concepts(current)

    def get_default_context(self) -> str:
        """
        Get a default context for when no specific content is found.
        This is used as a fallback when the search returns no results.
        
        Returns:
            str: A default context string
        """
        # Try to find a general introduction concept in any subject
        for subject in self.get_all_subjects():
            subject_content = self.get_subject(subject)
            if not subject_content:
                continue
                
            for topic in subject_content.get("topics", []):
                for concept in topic.get("concepts", []):
                    if "introduction" in concept.get("name", "").lower():
                        return concept.get("summary", "")
                        
        # If no introduction found, return a generic context
        return "This is a learning system for Grade 10 students. Please ask a specific question about your subjects."

def get_most_relevant_sentence(summary, question):
    sentences = summary.split('. ')
    best = max(sentences, key=lambda s: difflib.SequenceMatcher(None, s.lower(), question.lower()).ratio())
    return best