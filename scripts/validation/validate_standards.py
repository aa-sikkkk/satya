"""
Standards validation script for NEBedu project.
Validates a specific file against project standards.
"""

import re
import json
import ast
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StandardsValidator:
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_file(self) -> bool:
        if not self.file_path.exists():
            self.errors.append(f"File not found: {self.file_path}")
            return False
            
        suffix = self.file_path.suffix
        
        if suffix == '.py':
            return self._validate_python_file()
        elif suffix == '.json':
            return self._validate_json_file()
        else:
            self.errors.append(f"Unsupported file type: {suffix}")
            return False
            
    def _validate_python_file(self) -> bool:
        valid = True
        
        if not re.match(r'^[a-z][a-z0-9_]*\.py$', self.file_path.name):
            self.errors.append(f"Invalid file name: {self.file_path.name}")
            valid = False
        
        with open(self.file_path, encoding='utf-8') as f:
            content = f.read()
            
        if not re.search(r'^""".*?"""', content, re.DOTALL):
            self.errors.append(f"Missing file docstring")
            valid = False
            
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            self.errors.append(f"Syntax error: {e}")
            return False
            
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                    self.errors.append(f"Invalid class name '{node.name}'")
                    valid = False
                    
            if isinstance(node, ast.FunctionDef):
                if not ast.get_docstring(node):
                    self.errors.append(f"Missing function docstring: {node.name}")
                    valid = False
                    
                if not node.returns:
                    self.warnings.append(f"Missing return type hint: {node.name}")
                    
        return valid
        
    def _validate_json_file(self) -> bool:
        valid = True
        
        try:
            with open(self.file_path, encoding='utf-8') as f:
                content = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {e}")
            return False
            
        required_fields = {'subject', 'grade', 'topics'}
        missing_fields = required_fields - set(content.keys())
        
        if missing_fields:
            self.errors.append(f"Missing required fields: {missing_fields}")
            valid = False
            
        # Validate Subject
        allowed_subjects = {"Computer Science", "Science", "English"}
        if 'subject' in content:
            if content['subject'] not in allowed_subjects:
                self.errors.append(f"Invalid subject '{content['subject']}'. Must be one of {allowed_subjects}")
                valid = False
                
        # Validate Grade
        if 'grade' in content:
            grade = content['grade']
            is_valid_grade = False
            try:
                grade_num = int(grade)
                if 1 <= grade_num <= 12:
                    is_valid_grade = True
            except (ValueError, TypeError):
                pass
                
            if not is_valid_grade:
                self.errors.append(f"Invalid grade '{grade}'. Must be a number between 1 and 12")
                valid = False
            
        if 'topics' in content:
            if not isinstance(content['topics'], list):
                self.errors.append("'topics' must be a list")
                valid = False
            else:
                for topic in content['topics']:
                    if not self._validate_topic_structure(topic, str(self.file_path)):
                        valid = False
                    
        return valid
        
    def _validate_topic_structure(self, topic: Dict, file_context: str = "") -> bool:
        valid = True
        required_fields = {'name', 'subtopics'}
        
        topic_name = topic.get('name', 'unknown')
        context = f"{file_context} > Topic '{topic_name}'"
        
        missing_fields = required_fields - set(topic.keys())
        if missing_fields:
            self.errors.append(f"{context}: Missing required fields: {missing_fields}")
            valid = False
            
        if 'subtopics' in topic:
            for subtopic in topic['subtopics']:
                if not self._validate_subtopic_structure(subtopic, context):
                    valid = False
                    
        return valid
        
    def _validate_subtopic_structure(self, subtopic: Dict, parent_context: str = "") -> bool:
        valid = True
        
        subtopic_name = subtopic.get('name', 'unknown')
        context = f"{parent_context} > Subtopic '{subtopic_name}'"
        
        if 'name' not in subtopic:
            self.errors.append(f"{context}: Missing required field 'name'")
            valid = False
            
        has_concepts = 'concepts' in subtopic and isinstance(subtopic['concepts'], list)
        has_subtopics = 'subtopics' in subtopic and isinstance(subtopic['subtopics'], list)
        
        if not (has_concepts or has_subtopics):
            self.errors.append(f"{context}: Must have at least 'concepts' or 'subtopics'")
            valid = False
            
        if has_concepts:
            for concept in subtopic['concepts']:
                if not self._validate_concept_structure(concept, context):
                    valid = False
                    
        if has_subtopics:
            for sub in subtopic['subtopics']:
                if not self._validate_subtopic_structure(sub, context):
                    valid = False
                    
        return valid
        
    def _validate_concept_structure(self, concept: Dict, parent_context: str = "") -> bool:
        valid = True
        required_fields = {'name', 'summary', 'steps', 'questions'}
        
        concept_name = concept.get('name', 'unknown')
        context = f"{parent_context} > Concept '{concept_name}'"
        
        missing_fields = required_fields - set(concept.keys())
        if missing_fields:
            self.errors.append(f"{context}: Missing required fields: {missing_fields}")
            valid = False
            
        # Validate Steps
        if 'steps' in concept:
            if not isinstance(concept['steps'], list):
                self.errors.append(f"{context}: 'steps' must be a list")
                valid = False
            else:
                for i, step in enumerate(concept['steps']):
                    if not isinstance(step, str) or not step.strip():
                        self.errors.append(f"{context}: Step {i+1} must be a non-empty string")
                        valid = False

        # Validate Questions
        if 'questions' in concept:
            if not isinstance(concept['questions'], list):
                self.errors.append(f"{context}: 'questions' must be a list")
                valid = False
            else:
                for idx, question in enumerate(concept['questions']):
                    if not isinstance(question, dict):
                         self.errors.append(f"{context}: Question {idx+1} must be an object")
                         valid = False
                         continue
                         
                    if not self._validate_question_structure(question, f"{context} > Question {idx+1}"):
                        valid = False
                    
        return valid
        
    def _validate_question_structure(self, question: Dict, parent_context: str = "") -> bool:
        valid = True
        required_fields = {'question', 'acceptable_answers', 'hints'}
        
        missing_fields = required_fields - set(question.keys())
        if missing_fields:
            self.errors.append(f"{parent_context}: Missing required fields: {missing_fields}")
            return False # Cannot proceed with further checks if key fields are missing
            
        # Validate Question Text
        if not isinstance(question['question'], str) or not question['question'].strip():
            self.errors.append(f"{parent_context}: 'question' must be a non-empty string")
            valid = False
            
        # Validate Acceptable Answers
        if not isinstance(question['acceptable_answers'], list):
            self.errors.append(f"{parent_context}: 'acceptable_answers' must be a list")
            valid = False
        else:
            if not question['acceptable_answers']:
                self.errors.append(f"{parent_context}: 'acceptable_answers' cannot be empty")
                valid = False
            for i, ans in enumerate(question['acceptable_answers']):
                if not isinstance(ans, str) or not ans.strip():
                    self.errors.append(f"{parent_context}: Answer {i+1} must be a non-empty string")
                    valid = False
                    
        # Validate Hints
        if not isinstance(question['hints'], list):
            self.errors.append(f"{parent_context}: 'hints' must be a list")
            valid = False
        else:
            for i, hint in enumerate(question['hints']):
                if not isinstance(hint, str) or not hint.strip():
                    self.errors.append(f"{parent_context}: Hint {i+1} must be a non-empty string")
                    valid = False
            
        return valid

def main():
    parser = argparse.ArgumentParser(description='Validate a file against NEBedu project standards')
    parser.add_argument('--input-file', type=str, required=True, help='Path to file to validate')
    
    args = parser.parse_args()
    
    validator = StandardsValidator(args.input_file)
    valid = validator.validate_file()
    
    if validator.errors:
        logger.error("Validation errors found:")
        for error in validator.errors:
            logger.error(f"- {error}")
            
    if validator.warnings:
        logger.warning("Validation warnings found:")
        for warning in validator.warnings:
            logger.warning(f"- {warning}")
            
    if not validator.errors and not validator.warnings:
        logger.info("Validation passed successfully!")
        
    return 0 if valid else 1

if __name__ == "__main__":
    exit(main())