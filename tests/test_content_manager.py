"""
Test suite for the ContentManager class.
"""

import pytest
import os
import json
import tempfile
from system.data_manager.content_manager import ContentManager, CONTENT_SCHEMA

@pytest.fixture
def content_dir():
    """Create a temporary directory with sample content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample content
        sample_content = {
            "subject": "Computer Science",
            "grade": "10",
            "topics": [
                {
                    "name": "Introduction to Computers",
                    "subtopics": [
                        {
                            "name": "Basic Concepts",
                            "concepts": [
                                {
                                    "id": "comp_01",
                                    "title": "What is a Computer?",
                                    "summary": "A computer is an electronic device that processes data.",
                                    "questions": [
                                        {
                                            "type": "conceptual",
                                            "question": "What is a computer?",
                                            "acceptable_answers": [
                                                "An electronic device that processes data",
                                                "A device that processes input to produce output"
                                            ],
                                            "hints": [
                                                "It's an electronic device",
                                                "It processes data",
                                                "It can perform calculations"
                                            ],
                                            "explanation": "A computer is an electronic device that can process data according to a set of instructions."
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Create subject directory and content file
        subject_dir = os.path.join(tmpdir, "computer_science")
        os.makedirs(subject_dir)
        content_file = os.path.join(subject_dir, "content.json")
        
        with open(content_file, 'w', encoding='utf-8') as f:
            json.dump(sample_content, f, indent=2)
            
        yield tmpdir

@pytest.fixture
def content_manager(content_dir):
    """Create a ContentManager instance with sample content."""
    return ContentManager(content_dir)

def test_content_loading(content_manager):
    """Test content loading."""
    assert "computer_science" in content_manager.subjects
    assert content_manager.subjects["computer_science"]["subject"] == "Computer Science"
    assert content_manager.subjects["computer_science"]["grade"] == "10"

def test_get_subject(content_manager):
    """Test getting subject content."""
    subject = content_manager.get_subject("computer_science")
    assert subject is not None
    assert subject["subject"] == "Computer Science"
    
    # Test non-existent subject
    assert content_manager.get_subject("non_existent") is None

def test_get_topic(content_manager):
    """Test getting topic content."""
    topic = content_manager.get_topic("computer_science", "Introduction to Computers")
    assert topic is not None
    assert topic["name"] == "Introduction to Computers"
    
    # Test non-existent topic
    assert content_manager.get_topic("computer_science", "non_existent") is None

def test_get_concept(content_manager):
    """Test getting concept content."""
    concept = content_manager.get_concept(
        "computer_science",
        "Introduction to Computers",
        "comp_01"
    )
    assert concept is not None
    assert concept["id"] == "comp_01"
    assert concept["title"] == "What is a Computer?"
    
    # Test non-existent concept
    assert content_manager.get_concept(
        "computer_science",
        "Introduction to Computers",
        "non_existent"
    ) is None

def test_get_question(content_manager):
    """Test getting question content."""
    question = content_manager.get_question(
        "computer_science",
        "Introduction to Computers",
        "comp_01",
        0
    )
    assert question is not None
    assert question["type"] == "conceptual"
    assert question["question"] == "What is a computer?"
    
    # Test invalid question index
    assert content_manager.get_question(
        "computer_science",
        "Introduction to Computers",
        "comp_01",
        999
    ) is None

def test_update_content(content_manager, content_dir):
    """Test updating content."""
    # Create new content
    new_content = {
        "subject": "Computer Science",
        "grade": "10",
        "topics": [
            {
                "name": "New Topic",
                "subtopics": [
                    {
                        "name": "New Subtopic",
                        "concepts": [
                            {
                                "id": "comp_02",
                                "title": "New Concept",
                                "summary": "A new concept",
                                "questions": [
                                    {
                                        "type": "conceptual",
                                        "question": "What is new?",
                                        "acceptable_answers": ["Something new"],
                                        "hints": ["Think about it"],
                                        "explanation": "This is new"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    # Update content
    content_manager.update_content("computer_science", new_content)
    
    # Verify update
    assert content_manager.subjects["computer_science"]["topics"][0]["name"] == "New Topic"
    
    # Verify file was updated
    content_file = os.path.join(content_dir, "computer_science", "content.json")
    with open(content_file, 'r', encoding='utf-8') as f:
        saved_content = json.load(f)
        assert saved_content["topics"][0]["name"] == "New Topic"

def test_invalid_content(content_manager):
    """Test handling of invalid content."""
    invalid_content = {
        "subject": "Computer Science",
        "grade": "10"
        # Missing required "topics" field
    }
    
    with pytest.raises(Exception):
        content_manager.update_content("computer_science", invalid_content)

def test_get_all_subjects(content_manager):
    """Test getting all subjects."""
    subjects = content_manager.get_all_subjects()
    assert "computer_science" in subjects
    assert len(subjects) == 1

def test_get_all_topics(content_manager):
    """Test getting all topics."""
    topics = content_manager.get_all_topics("computer_science")
    assert "Introduction to Computers" in topics
    assert len(topics) == 1
    
    # Test non-existent subject
    assert content_manager.get_all_topics("non_existent") == []

def test_get_all_concepts(content_manager):
    """Test getting all concepts."""
    concepts = content_manager.get_all_concepts(
        "computer_science",
        "Introduction to Computers"
    )
    assert len(concepts) == 1
    assert concepts[0]["id"] == "comp_01"
    
    # Test non-existent topic
    assert content_manager.get_all_concepts(
        "computer_science",
        "non_existent"
    ) == [] 