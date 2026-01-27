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
Analytics Utilities Module

Provides tools for generating student progress reports, identifying weak concepts, and exporting analytics.
"""

import os
import json
import csv
from typing import List, Dict, Any
from student_app.progress import progress_manager
from system.data_manager.content_manager import ContentManager


def generate_student_report(username: str, content_manager: ContentManager) -> Dict[str, Any]:
    """
    Generate a progress report for a student.
    Args:
        username (str): The student's username
        content_manager (ContentManager): The content manager instance
    Returns:
        Dict[str, Any]: Report data
    """
    progress = progress_manager.load_progress(username)
    report = {
        "username": username,
        "total_questions": 0,
        "total_attempts": 0,
        "total_correct": 0,
        "mastered_concepts": 0,
        "weak_concepts": []
    }
    for subject in content_manager.get_all_subjects():
        for topic in content_manager.get_all_topics(subject):
            for concept in content_manager.get_all_concepts(subject, topic):
                concept_name = concept.get("name")
                for q in concept.get("questions", []):
                    report["total_questions"] += 1
                    attempts = 0
                    correct = 0
                    if subject in progress and topic in progress[subject] and concept_name in progress[subject][topic]:
                        for pq in progress[subject][topic][concept_name].get('questions', []):
                            if pq['question'] == q['question']:
                                attempts = pq['attempts']
                                correct = pq['correct']
                                break
                    report["total_attempts"] += attempts
                    report["total_correct"] += correct
                    if correct >= 3:
                        report["mastered_concepts"] += 1
                    elif attempts >= 2 and correct == 0:
                        report["weak_concepts"].append({
                            "subject": subject,
                            "topic": topic,
                            "concept": concept_name,
                            "question": q['question']
                        })
    return report


def export_report_csv(report: Dict[str, Any], filename: str) -> None:
    """
    Export a student report to CSV.
    Args:
        report (Dict[str, Any]): The report data
        filename (str): Output CSV filename
    """
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Username", report["username"]])
        writer.writerow(["Total Questions", report["total_questions"]])
        writer.writerow(["Total Attempts", report["total_attempts"]])
        writer.writerow(["Total Correct", report["total_correct"]])
        writer.writerow(["Mastered Concepts", report["mastered_concepts"]])
        writer.writerow([])
        writer.writerow(["Weak Concepts"])
        writer.writerow(["Subject", "Topic", "Concept", "Question"])
        for wc in report["weak_concepts"]:
            writer.writerow([wc["subject"], wc["topic"], wc["concept"], wc["question"]])


def export_report_json(report: Dict[str, Any], filename: str) -> None:
    """
    Export a student report to JSON.
    Args:
        report (Dict[str, Any]): The report data
        filename (str): Output JSON filename
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False) 