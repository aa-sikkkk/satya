"""
Progress Manager Module

Handles loading, saving, and updating user progress for the NEBedu CLI.
"""

import os
import json
from typing import Dict, Any

PROGRESS_DIR = os.path.dirname(os.path.abspath(__file__))


def get_progress_path(username: str) -> str:
    """
    Get the file path for a user's progress file.
    Args:
        username (str): The username
    Returns:
        str: Path to the progress JSON file
    """
    return os.path.join(PROGRESS_DIR, f"progress_{username}.json")


def load_progress(username: str) -> Dict[str, Any]:
    """
    Load a user's progress from file.
    Args:
        username (str): The username
    Returns:
        dict: Progress data (empty if not found)
    """
    path = get_progress_path(username)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_progress(username: str, data: Dict[str, Any]) -> None:
    """
    Save a user's progress to file.
    Args:
        username (str): The username
        data (dict): Progress data
    """
    path = get_progress_path(username)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def update_progress(username: str, subject: str, topic: str, concept: str, question: str, correct: bool) -> None:
    """
    Update a user's progress after a question attempt.
    Args:
        username (str): The username
        subject (str): Subject name
        topic (str): Topic name
        concept (str): Concept name
        question (str): Question text
        correct (bool): Whether the answer was correct
    """
    progress = load_progress(username)
    subj = progress.setdefault(subject, {})
    top = subj.setdefault(topic, {})
    conc = top.setdefault(concept, {})
    qlist = conc.setdefault('questions', [])
    # Check if question already exists
    for q in qlist:
        if q['question'] == question:
            q['attempts'] += 1
            if correct:
                q['correct'] += 1
            break
    else:
        qlist.append({
            'question': question,
            'attempts': 1,
            'correct': 1 if correct else 0
        })
    save_progress(username, progress) 