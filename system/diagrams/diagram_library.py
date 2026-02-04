# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
Diagram Library Module

Loads and searches pre-built diagrams from YAML files in Diagramsdb/.
Provides keyword-based matching for grade/subject-specific diagram lookup.
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

_yaml = None
def _get_yaml():
    global _yaml
    if _yaml is None:
        try:
            import yaml
            _yaml = yaml
        except ImportError:
            logger.error("PyYAML not installed. Run: pip install pyyaml")
            raise
    return _yaml


class DiagramLibrary:
    """
    Manages loading and searching of pre-built diagrams from YAML files.
    
    Usage:
        library = DiagramLibrary.get_instance()
        match = library.find_diagram("photosynthesis process", "science", 10)
        if match:
            diagram_data = match['diagram']
            confidence = match['confidence']
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls) -> 'DiagramLibrary':
        """Get singleton instance of DiagramLibrary."""
        if cls._instance is None:
            base_path = Path(__file__).parent.parent.parent / "satya_data" / "Diagramsdb"
            cls._instance = cls(str(base_path))
            cls._instance.load_all()
        return cls._instance
    
    def __init__(self, library_path: str):
        self.library_path = Path(library_path)
        self.diagrams: Dict[str, Dict] = {}  # id -> diagram data
        self.by_subject: Dict[str, List[str]] = {}  # subject -> list of diagram ids
        self.by_grade: Dict[int, List[str]] = {}  # grade -> list of diagram ids
        self._loaded = False
    
    def load_all(self) -> None:
        """Load all YAML files from Diagramsdb/."""
        if self._loaded:
            return
            
        yaml = _get_yaml()
        
        if not self.library_path.exists():
            logger.warning(f"Diagram library path not found: {self.library_path}")
            return
        
        yaml_files = list(self.library_path.rglob("*.yaml"))
        yaml_files += list(self.library_path.rglob("*.yml"))
        yaml_files = [f for f in yaml_files if not f.name.startswith("_")]
        
        for yaml_file in yaml_files:
            try:
                self._load_file(yaml_file, yaml)
            except Exception as e:
                logger.error(f"Failed to load {yaml_file}: {e}")
        
        self._loaded = True
        logger.info(f"Loaded {len(self.diagrams)} diagrams from {len(yaml_files)} files")
    
    def _load_file(self, file_path: Path, yaml) -> None:
        """Load a single YAML file and index its diagrams."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data:
            return
        
        metadata = data.get('metadata', {})
        subject = metadata.get('subject', file_path.parent.name).lower()
        
        grades_raw = metadata.get('grade') or metadata.get('grades', [])
        if isinstance(grades_raw, int):
            grades = [grades_raw]
        elif isinstance(grades_raw, list):
            grades = [int(g) for g in grades_raw if str(g).isdigit()]
        else:
            match = re.search(r'grade[_\-]?(\d+)', file_path.stem, re.I)
            grades = [int(match.group(1))] if match else list(range(8, 13))
        
        diagrams_data = data.get('diagrams', {})
        for diagram_id, diagram in diagrams_data.items():
            if not isinstance(diagram, dict):
                continue
            
            full_id = f"{subject}_{diagram_id}"
            normalized = self._normalize_diagram(diagram, subject, grades)
            normalized['id'] = full_id
            normalized['source_file'] = str(file_path)
            
            self.diagrams[full_id] = normalized
            
            if subject not in self.by_subject:
                self.by_subject[subject] = []
            self.by_subject[subject].append(full_id)
            
            for grade in grades:
                if grade not in self.by_grade:
                    self.by_grade[grade] = []
                self.by_grade[grade].append(full_id)
    
    def _normalize_diagram(self, raw: Dict, subject: str, grades: List[int]) -> Dict:
        """
        Normalize diagram data to handle schema inconsistencies.
        
        Handles:
        - Missing keywords (extract from title)
        - Mixed children formats
        - 3-item comparisons
        - Structure type with 'children' instead of 'components'
        """
        normalized = dict(raw)
        normalized['subject'] = subject
        normalized['grades'] = grades
        
        if 'keywords' not in normalized or not normalized['keywords']:
            keywords = []
            title = normalized.get('title', '')
            keywords.extend(self._extract_keywords_from_text(title))
            if 'type' in normalized:
                keywords.append(normalized['type'])
            normalized['keywords'] = keywords
        
        if normalized.get('type') == 'structure':
            if 'children' in normalized and 'components' not in normalized:
                normalized['components'] = normalized['children']
        
        return normalized
    
    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        stopwords = {'the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for', 'and', 'or', 'vs'}
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        return [w for w in words if w not in stopwords][:5]
    
    def find_diagram(
        self, 
        question: str, 
        subject: Optional[str] = None, 
        grade: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Find best matching diagram for a question.
        
        Args:
            question: User's question text
            subject: Optional subject filter (e.g., 'science')
            grade: Optional grade filter (e.g., 10)
            
        Returns:
            Dict with 'diagram', 'confidence', 'id' or None if no match
        """
        if not self._loaded:
            self.load_all()
        
        candidates = set(self.diagrams.keys())
        
        if grade and grade in self.by_grade:
            candidates &= set(self.by_grade[grade])
        
        if subject:
            subject_lower = subject.lower()
            if subject_lower in self.by_subject:
                candidates &= set(self.by_subject[subject_lower])
        
        if not candidates:
            candidates = set(self.diagrams.keys())
        
        question_keywords = set(self._extract_keywords_from_text(question))
        
        best_match = None
        best_score = 0.0
        
        for diagram_id in candidates:
            diagram = self.diagrams[diagram_id]
            score = self._calculate_match_score(question_keywords, diagram)
            
            if score > best_score:
                best_score = score
                best_match = diagram
        
        if best_score >= 0.3:
            return {
                'diagram': best_match,
                'confidence': best_score,
                'id': best_match['id']
            }
        
        return None
    
    def _calculate_match_score(self, question_keywords: set, diagram: Dict) -> float:
        """Calculate match score between question keywords and diagram."""
        diagram_keywords = set(k.lower() for k in diagram.get('keywords', []))
        title_keywords = set(self._extract_keywords_from_text(diagram.get('title', '')))
        all_diagram_keywords = diagram_keywords | title_keywords
        
        if not all_diagram_keywords:
            return 0.0
        
        matches = question_keywords & all_diagram_keywords
        
        if not matches:
            return 0.0
        
        if not question_keywords:
            return 0.0
        
        score = len(matches) / len(question_keywords)
        
        if len(matches) >= 2:
            score *= 1.1
        
        return min(score, 1.0)
