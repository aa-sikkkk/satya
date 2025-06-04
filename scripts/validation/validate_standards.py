"""
Standards validation script for NEBedu project.

This script validates code against the project standards defined in PROJECT_STANDARDS.md.
It checks for:
- Directory structure
- Naming conventions
- Documentation requirements
- Content structure
- Testing requirements
"""

import os
import re
import json
import ast
from pathlib import Path
from typing import List, Dict, Set, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StandardsValidator:
    """Validates code against project standards."""
    
    def __init__(self, project_root: str):
        """Initialize validator with project root path.
        
        Args:
            project_root: Path to project root directory
        """
        self.project_root = Path(project_root)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate_directory_structure(self) -> bool:
        """Validate project directory structure.
        
        Returns:
            bool: True if structure is valid, False otherwise
        """
        required_dirs = {
            'ai_model',
            'system',
            'student_app',
            'scripts',
            'data',
            'tests',
            'docs'
        }
        
        found_dirs = {d.name for d in self.project_root.iterdir() if d.is_dir()}
        missing_dirs = required_dirs - found_dirs
        
        if missing_dirs:
            self.errors.append(f"Missing required directories: {missing_dirs}")
            return False
        return True
        
    def validate_naming_conventions(self) -> bool:
        """Validate file and function naming conventions.
        
        Returns:
            bool: True if naming is valid, False otherwise
        """
        valid = True
        
        # Check file names
        for file_path in self.project_root.rglob("*.py"):
            if not re.match(r'^[a-z][a-z0-9_]*\.py$', file_path.name):
                self.errors.append(f"Invalid file name: {file_path}")
                valid = False
                
        # Check class names
        for file_path in self.project_root.rglob("*.py"):
            with open(file_path) as f:
                tree = ast.parse(f.read())
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                            self.errors.append(
                                f"Invalid class name '{node.name}' in {file_path}"
                            )
                            valid = False
                            
        return valid
        
    def validate_documentation(self) -> bool:
        """Validate code documentation requirements.
        
        Returns:
            bool: True if documentation is valid, False otherwise
        """
        valid = True
        
        for file_path in self.project_root.rglob("*.py"):
            with open(file_path) as f:
                content = f.read()
                
            # Check file docstring
            if not re.search(r'^""".*?"""', content, re.DOTALL):
                self.errors.append(f"Missing file docstring: {file_path}")
                valid = False
                
            # Check function docstrings and type hints
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not ast.get_docstring(node):
                        self.errors.append(
                            f"Missing function docstring: {node.name} in {file_path}"
                        )
                        valid = False
                        
                    # Check type hints
                    if not node.returns:
                        self.warnings.append(
                            f"Missing return type hint: {node.name} in {file_path}"
                        )
                        
        return valid
        
    def validate_content_structure(self) -> bool:
        """Validate content JSON structure.
        
        Returns:
            bool: True if content structure is valid, False otherwise
        """
        valid = True
        content_dir = self.project_root / 'data' / 'content'
        
        if not content_dir.exists():
            self.errors.append("Content directory not found")
            return False
            
        required_fields = {
            'subject', 'grade', 'topics'
        }
        
        for file_path in content_dir.glob("*.json"):
            try:
                with open(file_path) as f:
                    content = json.load(f)
                    
                # Check required fields
                missing_fields = required_fields - set(content.keys())
                if missing_fields:
                    self.errors.append(
                        f"Missing required fields in {file_path}: {missing_fields}"
                    )
                    valid = False
                    
                # Validate topics structure
                if 'topics' in content:
                    for topic in content['topics']:
                        if not self._validate_topic_structure(topic):
                            valid = False
                            
            except json.JSONDecodeError:
                self.errors.append(f"Invalid JSON in {file_path}")
                valid = False
                
        return valid
        
    def _validate_topic_structure(self, topic: Dict) -> bool:
        """Validate topic structure in content.
        
        Args:
            topic: Topic dictionary to validate
            
        Returns:
            bool: True if topic structure is valid, False otherwise
        """
        valid = True
        required_fields = {'name', 'subtopics'}
        
        # Check required fields
        missing_fields = required_fields - set(topic.keys())
        if missing_fields:
            self.errors.append(f"Missing required fields in topic: {missing_fields}")
            valid = False
            
        # Validate subtopics
        if 'subtopics' in topic:
            for subtopic in topic['subtopics']:
                if not self._validate_subtopic_structure(subtopic):
                    valid = False
                    
        return valid
        
    def _validate_subtopic_structure(self, subtopic: Dict) -> bool:
        """Validate subtopic structure in content.
        Args:
            subtopic: Subtopic dictionary to validate
        Returns:
            bool: True if subtopic structure is valid, False otherwise
        """
        valid = True
        # Must have 'name' and at least one of 'concepts' or 'subtopics'
        if 'name' not in subtopic:
            self.errors.append(f"Missing required field 'name' in subtopic: {subtopic}")
            valid = False
        has_concepts = 'concepts' in subtopic and isinstance(subtopic['concepts'], list)
        has_subtopics = 'subtopics' in subtopic and isinstance(subtopic['subtopics'], list)
        if not (has_concepts or has_subtopics):
            self.errors.append(f"Subtopic must have at least 'concepts' or 'subtopics': {subtopic}")
            valid = False
        if has_concepts:
            for concept in subtopic['concepts']:
                if not self._validate_concept_structure(concept):
                    valid = False
        if has_subtopics:
            for sub in subtopic['subtopics']:
                if not self._validate_subtopic_structure(sub):
                    valid = False
        return valid
        
    def _validate_concept_structure(self, concept: Dict) -> bool:
        """Validate concept structure in content.
        
        Args:
            concept: Concept dictionary to validate
            
        Returns:
            bool: True if concept structure is valid, False otherwise
        """
        valid = True
        required_fields = {'name', 'summary', 'steps', 'questions'}
        
        # Check required fields
        missing_fields = required_fields - set(concept.keys())
        if missing_fields:
            self.errors.append(f"Missing required fields in concept: {missing_fields}")
            valid = False
            
        # Validate questions
        if 'questions' in concept:
            for question in concept['questions']:
                if not self._validate_question_structure(question):
                    valid = False
                    
        return valid
        
    def _validate_question_structure(self, question: Dict) -> bool:
        """Validate question structure in content.
        
        Args:
            question: Question dictionary to validate
            
        Returns:
            bool: True if question structure is valid, False otherwise
        """
        required_fields = {'question', 'acceptable_answers', 'hints'}
        
        # Check required fields
        missing_fields = required_fields - set(question.keys())
        if missing_fields:
            self.errors.append(f"Missing required fields in question: {missing_fields}")
            return False
            
        return True
        
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """Run all validations.
        
        Returns:
            Tuple[bool, List[str], List[str]]: (is_valid, errors, warnings)
        """
        valid = True
        
        # Run all validations
        if not self.validate_directory_structure():
            valid = False
        if not self.validate_naming_conventions():
            valid = False
        if not self.validate_documentation():
            valid = False
        if not self.validate_content_structure():
            valid = False
            
        return valid, self.errors, self.warnings

def main():
    """Main validation function."""
    project_root = os.getcwd()
    validator = StandardsValidator(project_root)
    
    valid, errors, warnings = validator.validate_all()
    
    # Print results
    if errors:
        logger.error("Validation errors found:")
        for error in errors:
            logger.error(f"- {error}")
            
    if warnings:
        logger.warning("Validation warnings found:")
        for warning in warnings:
            logger.warning(f"- {warning}")
            
    if not errors and not warnings:
        logger.info("All validations passed successfully!")
        
    return 0 if valid else 1

if __name__ == "__main__":
    exit(main()) 