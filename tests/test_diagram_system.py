# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
Tests for the YAML-based Diagram Library System.

This test suite validates:
- DiagramLibrary loading and indexing
- Keyword matching and scoring algorithm
- Diagram rendering pipeline
- should_show_diagram logic
- End-to-end diagram generation
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from system.diagrams.diagram_library import DiagramLibrary
from system.diagrams.diagram_renderer import DiagramRenderer
from system.diagrams.diagram_service import (
    generate_diagram_content,
    should_show_diagram,
    should_attempt_diagram
)
from system.diagrams.diagram_config import PROCESS_KEYWORDS, COMPARISON_KEYWORDS


class TestDiagramLibraryLoading(unittest.TestCase):
    """Tests for DiagramLibrary initialization and YAML loading."""
    
    @classmethod
    def setUpClass(cls):
        """Load library once for all tests."""
        cls.library = DiagramLibrary.get_instance()
    
    def test_library_loads_diagrams(self):
        """Verify library loads diagrams from YAML files."""
        self.assertGreater(len(self.library.diagrams), 0)
    
    def test_diagrams_indexed_by_subject(self):
        """Verify diagrams are indexed by subject."""
        self.assertIn('science', self.library.by_subject)
    
    def test_diagrams_indexed_by_grade(self):
        """Verify diagrams are indexed by grade."""
        # At least some grades should be indexed
        self.assertGreater(len(self.library.by_grade), 0)
    
    def test_diagram_has_required_fields(self):
        """Verify normalized diagrams have required fields."""
        for diagram_id, diagram in self.library.diagrams.items():
            self.assertIn('id', diagram)
            self.assertIn('type', diagram)
            self.assertIn('keywords', diagram)
            self.assertIn('subject', diagram)
    
    def test_photosynthesis_diagram_exists(self):
        """Verify photosynthesis diagram is loaded from general.yaml."""
        photo_diagrams = [k for k in self.library.diagrams.keys() if 'photosynthesis' in k]
        self.assertGreater(len(photo_diagrams), 0)


class TestKeywordMatching(unittest.TestCase):
    """Tests for the keyword matching and scoring algorithm."""
    
    @classmethod
    def setUpClass(cls):
        cls.library = DiagramLibrary.get_instance()
    
    def test_photosynthesis_query_matches(self):
        """Verify photosynthesis query finds correct diagram."""
        match = self.library.find_diagram("What is photosynthesis process?", "Science")
        self.assertIsNotNone(match)
        self.assertIn('photosynthesis', match['id'].lower())
    
    def test_score_above_threshold(self):
        """Verify matched diagram has score above 0.3 threshold."""
        match = self.library.find_diagram("Explain photosynthesis", "Science")
        self.assertIsNotNone(match)
        self.assertGreaterEqual(match['confidence'], 0.3)
    
    def test_no_match_for_random_query(self):
        """Verify no match for unrelated queries."""
        match = self.library.find_diagram("How to cook pasta?", "Science")
        # Should return None or very low confidence
        self.assertTrue(match is None or match['confidence'] < 0.3)
    
    def test_grade_filtering(self):
        """Verify grade filter narrows candidates."""
        # General diagrams should match any grade
        match = self.library.find_diagram("photosynthesis", "Science", grade=10)
        self.assertIsNotNone(match)
    
    def test_subject_filtering(self):
        """Verify subject filter works correctly."""
        match = self.library.find_diagram("electric circuit", "Science")
        if match:
            self.assertEqual(match['diagram']['subject'].lower(), 'science')


class TestShouldShowDiagram(unittest.TestCase):
    """Tests for the should_show_diagram logic."""
    
    def test_process_question_triggers_diagram(self):
        """Process questions should trigger diagram display."""
        question = "Explain how photosynthesis works"
        answer = "Photosynthesis is a process involving light absorption, water splitting, and glucose production. " * 5
        result = should_show_diagram(question, answer, match_confidence=0.7)
        self.assertTrue(result)
    
    def test_short_answer_skips_diagram(self):
        """Short answers should not show diagrams."""
        question = "What is DNA?"
        answer = "DNA is genetic material."
        result = should_show_diagram(question, answer, match_confidence=0.8)
        self.assertFalse(result)
    
    def test_definition_skips_diagram(self):
        """Definition questions should skip diagrams."""
        question = "What is photosynthesis?"
        answer = "Photosynthesis is a process. " * 10
        result = should_show_diagram(question, answer, match_confidence=0.8)
        self.assertFalse(result)
    
    def test_low_confidence_skips_diagram(self):
        """Low confidence matches should skip diagrams."""
        question = "Explain how cells divide"
        answer = "Cell division involves multiple steps. " * 10
        result = should_show_diagram(question, answer, match_confidence=0.2)
        self.assertFalse(result)


class TestShouldAttemptDiagram(unittest.TestCase):
    """Tests for the exclusion pattern logic."""
    
    def test_exclude_math_solve(self):
        """Math solve questions should be excluded."""
        self.assertFalse(should_attempt_diagram("How do you solve x + 5 = 10?"))
    
    def test_exclude_calculate(self):
        """Calculate questions should be excluded."""
        self.assertFalse(should_attempt_diagram("Calculate the value of x"))
    
    def test_exclude_definition(self):
        """What is questions should be excluded."""
        self.assertFalse(should_attempt_diagram("What is photosynthesis?"))
    
    def test_include_explain_process(self):
        """Explain process questions should be included."""
        self.assertTrue(should_attempt_diagram("Explain how the water cycle works"))
    
    def test_include_describe_structure(self):
        """Describe structure questions should be included."""
        self.assertTrue(should_attempt_diagram("Describe the structure of a cell"))


class TestDiagramRenderer(unittest.TestCase):
    """Tests for the ASCII diagram renderer."""
    
    def test_render_flowchart(self):
        """Verify flowchart rendering produces valid output."""
        steps = ["Step 1", "Step 2", "Step 3"]
        result = DiagramRenderer.render_step_based_flowchart(steps)
        self.assertIsNotNone(result)
        # Renderer uppercases labels
        self.assertIn("STEP 1", result)
        self.assertIn("STEP 2", result)
        self.assertIn("│", result)  # Vertical connector
    
    def test_render_structure(self):
        """Verify structure diagram rendering."""
        components = ["Part A", "Part B", "Part C"]
        result = DiagramRenderer.render_component_structure(components)
        self.assertIsNotNone(result)
        # Check case-insensitive since renderer may uppercase
        self.assertIn("PART A", result.upper())
    
    def test_render_comparison(self):
        """Verify comparison table rendering."""
        data = {
            'similarities': ['Both are processes'],
            'differences': {'key': ['Value A', 'Value B']}
        }
        result = DiagramRenderer.render_comparison_table(data)
        self.assertIsNotNone(result)
    
    def test_render_cycle(self):
        """Verify cyclic diagram rendering."""
        steps = ["Evaporation", "Condensation", "Precipitation"]
        result = DiagramRenderer.render_cycle_diagram(steps)
        self.assertIsNotNone(result)


class TestEndToEndGeneration(unittest.TestCase):
    """End-to-end tests for diagram generation pipeline."""
    
    def test_photosynthesis_generates_diagram(self):
        """Verify photosynthesis query generates a diagram."""
        # Use simpler query with fewer keywords for better match ratio
        question = "Describe photosynthesis process"
        answer = "Photosynthesis is a complex process involving light absorption, water splitting, electron transport, and glucose synthesis. " * 3
        
        result = generate_diagram_content(question, answer, subject="Science")
        
        self.assertIsNotNone(result)
        diagram, diagram_type = result
        self.assertIn("process", diagram_type.lower())
        self.assertGreater(len(diagram), 50)
    
    def test_definition_returns_none(self):
        """Verify definition questions return None."""
        question = "What is DNA?"
        answer = "DNA is genetic material."
        
        result = generate_diagram_content(question, answer, subject="Science")
        self.assertIsNone(result)
    
    def test_random_query_returns_none(self):
        """Verify unrelated queries return None."""
        question = "What is the capital of Nepal?"
        answer = "Kathmandu is the capital of Nepal."
        
        result = generate_diagram_content(question, answer, subject="Science")
        self.assertIsNone(result)


class TestDiagramConfig(unittest.TestCase):
    """Tests for diagram configuration."""
    
    def test_process_keywords_exist(self):
        """Verify process keywords are defined."""
        self.assertIsInstance(PROCESS_KEYWORDS, (list, set, tuple))
        self.assertGreater(len(PROCESS_KEYWORDS), 0)
    
    def test_comparison_keywords_exist(self):
        """Verify comparison keywords are defined."""
        self.assertIsInstance(COMPARISON_KEYWORDS, (list, set, tuple))
        self.assertGreater(len(COMPARISON_KEYWORDS), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
