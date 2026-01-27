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
Content Editor Utilities Module

Provides tools for teachers to load, edit, add, and remove topics, subtopics, concepts, and questions in the content JSON. Includes validation and saving.
"""

import json
from typing import Dict, Any, List, Optional
from jsonschema import ValidationError
from system.data_manager.content_manager import ContentManager
from system.security.security_utils import validate_content_input


def load_content_file(filepath: str) -> Dict[str, Any]:
    """
    Load content JSON from file.
    Args:
        filepath (str): Path to the content JSON file
    Returns:
        Dict[str, Any]: Content data
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_content_file(content: Dict[str, Any], filepath: str) -> None:
    """
    Save content JSON to file.
    Args:
        content (Dict[str, Any]): Content data
        filepath (str): Path to save the content JSON
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(content, f, indent=2, ensure_ascii=False)


def validate_content(content: Dict[str, Any], content_manager: ContentManager) -> bool:
    """
    Validate content using ContentManager's schema.
    Args:
        content (Dict[str, Any]): Content data
        content_manager (ContentManager): ContentManager instance
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        content_manager._validate_content(content)
        return True
    except ValidationError:
        return False


def add_topic(content: Dict[str, Any], topic: Dict[str, Any]) -> None:
    """
    Add a new topic to the content. Flexible: creates 'topics' if missing.
    Args:
        content (Dict[str, Any]): Content data
        topic (Dict[str, Any]): Topic to add
    """
    if not validate_content_input(topic):
        print("Error: Invalid topic input (too large).")
        return
    content.setdefault('topics', []).append(topic)


def remove_topic(content: Dict[str, Any], topic_name: str) -> None:
    """
    Remove a topic by name. Flexible: does nothing if 'topics' missing.
    Args:
        content (Dict[str, Any]): Content data
        topic_name (str): Name of the topic to remove
    """
    if 'topics' in content:
        content['topics'] = [t for t in content['topics'] if t.get('name') != topic_name]


def add_concept(content: Dict[str, Any], topic_name: str, subtopic_name: str, concept: Dict[str, Any]) -> bool:
    """
    Add a concept to a subtopic in a topic, searching recursively. Maximally flexible.
    Args:
        content (Dict[str, Any]): Content data
        topic_name (str): Name of the topic
        subtopic_name (str): Name of the subtopic
        concept (Dict[str, Any]): Concept to add
    Returns:
        bool: True if added, False if not found
    """
    if not validate_content_input(concept):
        print("Error: Invalid concept input.")
        return False

    def add_to_subtopic(subtopics):
        for subtopic in subtopics:
            if subtopic.get('name') == subtopic_name:
                subtopic.setdefault('concepts', []).append(concept)
                return True
            if add_to_subtopic(subtopic.get('subtopics', [])):
                return True
        return False
    for topic in content.get('topics', []):
        if topic.get('name') == topic_name:
            if add_to_subtopic(topic.get('subtopics', [])):
                return True
            if topic.get('name') == subtopic_name:
                topic.setdefault('concepts', []).append(concept)
                return True
    return False


def remove_concept(content: Dict[str, Any], topic_name: str, subtopic_name: str, concept_name: str) -> bool:
    """
    Remove a concept by name from a subtopic in a topic, searching recursively. Maximally flexible.
    Args:
        content (Dict[str, Any]): Content data
        topic_name (str): Name of the topic
        subtopic_name (str): Name of the subtopic
        concept_name (str): Name of the concept to remove
    Returns:
        bool: True if removed, False if not found
    """
    def remove_from_subtopic(subtopics):
        for subtopic in subtopics:
            if subtopic.get('name') == subtopic_name:
                before = len(subtopic.get('concepts', []))
                subtopic['concepts'] = [c for c in subtopic.get('concepts', []) if c.get('name') != concept_name]
                return len(subtopic['concepts']) < before
            if remove_from_subtopic(subtopic.get('subtopics', [])):
                return True
        return False
    for topic in content.get('topics', []):
        if topic.get('name') == topic_name:
            if remove_from_subtopic(topic.get('subtopics', [])):
                return True
            if topic.get('name') == subtopic_name:
                before = len(topic.get('concepts', []))
                topic['concepts'] = [c for c in topic.get('concepts', []) if c.get('name') != concept_name]
                return len(topic['concepts']) < before
    return False


def add_question(content: Dict[str, Any], topic_name: str, subtopic_name: str, concept_name: str, question: Dict[str, Any]) -> bool:
    """
    Add a question to a concept, searching recursively. Maximally flexible.
    Args:
        content (Dict[str, Any]): Content data
        topic_name (str): Name of the topic
        subtopic_name (str): Name of the subtopic
        concept_name (str): Name of the concept
        question (Dict[str, Any]): Question to add
    Returns:
        bool: True if added, False if not found
    """
    if not validate_content_input(question):
        print("Error: Invalid question input.")
        return False

    def add_to_concept(subtopics):
        for subtopic in subtopics:
            if subtopic.get('name') == subtopic_name:
                for concept in subtopic.get('concepts', []):
                    if concept.get('name') == concept_name:
                        concept.setdefault('questions', []).append(question)
                        return True
                if add_to_concept(subtopic.get('subtopics', [])):
                    return True
            else:
                if add_to_concept(subtopic.get('subtopics', [])):
                    return True
        return False
    for topic in content.get('topics', []):
        if topic.get('name') == topic_name:
            if add_to_concept(topic.get('subtopics', [])):
                return True
            if topic.get('name') == subtopic_name:
                for concept in topic.get('concepts', []):
                    if concept.get('name') == concept_name:
                        concept.setdefault('questions', []).append(question)
                        return True
    return False


def remove_question(content: Dict[str, Any], topic_name: str, subtopic_name: str, concept_name: str, question_text: str) -> bool:
    """
    Remove a question by text from a concept, searching recursively. Maximally flexible.
    Args:
        content (Dict[str, Any]): Content data
        topic_name (str): Name of the topic
        subtopic_name (str): Name of the subtopic
        concept_name (str): Name of the concept
        question_text (str): Text of the question to remove
    Returns:
        bool: True if removed, False if not found
    """
    def remove_from_concept(subtopics):
        for subtopic in subtopics:
            if subtopic.get('name') == subtopic_name:
                for concept in subtopic.get('concepts', []):
                    if concept.get('name') == concept_name:
                        before = len(concept.get('questions', []))
                        concept['questions'] = [q for q in concept.get('questions', []) if q.get('question') != question_text]
                        return len(concept['questions']) < before
                if remove_from_concept(subtopic.get('subtopics', [])):
                    return True
            else:
                if remove_from_concept(subtopic.get('subtopics', [])):
                    return True
        return False
    for topic in content.get('topics', []):
        if topic.get('name') == topic_name:
            if remove_from_concept(topic.get('subtopics', [])):
                return True
            if topic.get('name') == subtopic_name:
                for concept in topic.get('concepts', []):
                    if concept.get('name') == concept_name:
                        before = len(concept.get('questions', []))
                        concept['questions'] = [q for q in concept.get('questions', []) if q.get('question') != question_text]
                        return len(concept['questions']) < before
    return False 