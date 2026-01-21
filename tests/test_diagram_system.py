import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from system.diagrams.custom_generator import extract_steps_from_answer, generate_diagram
from system.diagrams.diagram_validator import validate_diagram, validate_diagram_content
from system.diagrams.diagram_detector import should_generate_diagram, extract_context_for_diagram
from system.diagrams.diagram_service import should_attempt_diagram, generate_and_append_diagram


class TestStepExtraction(unittest.TestCase):
    
    def test_biology_life_cycle_extraction(self):
        answer = "The life cycle has four stages. Stage 1: Egg. Stage 2: Larva. Stage 3: Pupa. Stage 4: Adult."
        steps = extract_steps_from_answer(answer)
        self.assertGreaterEqual(len(steps), 3)
        self.assertTrue(any('egg' in s.lower() for s in steps))
        self.assertTrue(any('larva' in s.lower() for s in steps))
    
    def test_chemistry_process_extraction(self):
        answer = "The water cycle involves processes such as evaporation, condensation, precipitation, and collection."
        steps = extract_steps_from_answer(answer)
        self.assertGreaterEqual(len(steps), 3)
        self.assertTrue(any('evaporation' in s.lower() for s in steps))
        self.assertTrue(any('condensation' in s.lower() for s in steps))
    
    def test_numbered_list_extraction(self):
        answer = "The metamorphosis has stages: Stage 1: Egg laid on leaf. Stage 2: Larva hatches and eats. Stage 3: Pupa forms chrysalis."
        steps = extract_steps_from_answer(answer)
        self.assertGreaterEqual(len(steps), 2)
    
    def test_no_extraction_for_simple_definition(self):
        answer = "Photosynthesis is the process by which plants convert sunlight into energy."
        steps = extract_steps_from_answer(answer)
        self.assertEqual(len(steps), 0)
    
    def test_no_generic_steps(self):
        answer = "The process has three steps. First, preparation. Then, execution. Finally, completion."
        steps = extract_steps_from_answer(answer)
        for step in steps:
            self.assertFalse(any(x in step.lower() for x in ['step 1', 'step 2', 'step 3']))


class TestContentValidation(unittest.TestCase):
    
    def test_reject_generic_diagram(self):
        generic_diagram = """
┌────────┐
│ Step 1 │
└────┬───┘
     │
┌────▼───┐
│ Step 2 │
└────────┘
"""
        is_valid, error = validate_diagram_content(generic_diagram)
        self.assertFalse(is_valid)
        self.assertIn('generic', error.lower())
    
    def test_accept_good_diagram(self):
        good_diagram = """
┌──────────┐
│   Egg    │
└────┬─────┘
     │
┌────▼─────┐
│  Larva   │
└──────────┘
"""
        is_valid, error = validate_diagram_content(good_diagram)
        self.assertTrue(is_valid)
    
    def test_reject_empty_diagram(self):
        is_valid, error = validate_diagram_content("")
        self.assertFalse(is_valid)
    
    def test_full_validation_with_context(self):
        good_diagram = """
┌──────────┐
│   Egg    │
└────┬─────┘
     │
┌────▼─────┐
│  Larva   │
└──────────┘
"""
        context = {"question": "life cycle", "answer": "egg larva pupa"}
        is_valid, error = validate_diagram(good_diagram, context)
        self.assertTrue(is_valid)


class TestDiagramDetection(unittest.TestCase):
    
    def test_detect_process_question(self):
        question = "Explain how photosynthesis works"
        answer = "Photosynthesis involves several key processes such as light absorption, water splitting, carbon fixation, and glucose production. First, chlorophyll absorbs light energy. Then, water molecules are split. Next, carbon dioxide is fixed. Finally, glucose is produced."
        should_gen, diagram_type = should_generate_diagram(question, answer)
        self.assertTrue(should_gen)
        self.assertIn(diagram_type, ["flowchart", "process"])
    
    def test_detect_cycle_question(self):
        question = "Describe the water cycle"
        answer = "The water cycle includes evaporation, condensation, precipitation, and collection."
        should_gen, diagram_type = should_generate_diagram(question, answer)
        self.assertTrue(should_gen)
    
    def test_no_diagram_for_short_answer(self):
        question = "What is DNA?"
        answer = "DNA is genetic material."
        should_gen, diagram_type = should_generate_diagram(question, answer)
        self.assertFalse(should_gen)


class TestExclusionPatterns(unittest.TestCase):
    
    def test_exclude_math_solve(self):
        question = "How do you solve a quadratic equation?"
        self.assertFalse(should_attempt_diagram(question))
    
    def test_exclude_math_calculate(self):
        question = "Calculate the value of x in the equation"
        self.assertFalse(should_attempt_diagram(question))
    
    def test_exclude_definition(self):
        question = "What is photosynthesis?"
        self.assertFalse(should_attempt_diagram(question))
    
    def test_exclude_mathematical(self):
        question = "Explain the mathematical formula for area"
        self.assertFalse(should_attempt_diagram(question))
    
    def test_include_process_question(self):
        question = "Explain how the water cycle works"
        self.assertTrue(should_attempt_diagram(question))
    
    def test_include_structure_question(self):
        question = "What is the structure of a cell?"
        self.assertTrue(should_attempt_diagram(question))


class TestEndToEndDiagram(unittest.TestCase):
    
    def test_biology_full_pipeline(self):
        question = "Explain the life cycle of a butterfly"
        answer = "The butterfly life cycle has four stages. Stage 1: Egg. The female lays eggs. Stage 2: Larva. The caterpillar hatches. Stage 3: Pupa. Forms a chrysalis. Stage 4: Adult. The butterfly emerges."
        
        result = generate_and_append_diagram(question, answer)
        
        self.assertIn(answer, result)
        if "Diagram:" in result:
            self.assertIn("Egg", result)
            self.assertNotIn("Step 1", result)
    
    def test_chemistry_full_pipeline(self):
        question = "Describe the water cycle"
        answer = "The water cycle involves processes such as evaporation, condensation, precipitation, and collection."
        
        result = generate_and_append_diagram(question, answer)
        
        self.assertIn(answer, result)
        if "Diagram:" in result:
            self.assertIn("Evaporation", result)
    
    def test_math_excluded(self):
        question = "How do you solve x² + 5x + 6 = 0?"
        answer = "To solve: 1. Identify a=1, b=5, c=6. 2. Apply quadratic formula. 3. Calculate discriminant. 4. Find roots."
        
        result = generate_and_append_diagram(question, answer)
        
        self.assertEqual(result, answer)
        self.assertNotIn("Diagram:", result)
    
    def test_definition_excluded(self):
        question = "What is photosynthesis?"
        answer = "Photosynthesis is the process by which plants convert sunlight into energy."
        
        result = generate_and_append_diagram(question, answer)
        
        self.assertEqual(result, answer)
        self.assertNotIn("Diagram:", result)


class TestContextExtraction(unittest.TestCase):
    
    def test_extract_process_context(self):
        question = "How does photosynthesis work?"
        answer = "Photosynthesis involves light absorption, carbon fixation, and glucose production."
        
        context = extract_context_for_diagram(question, answer, "process")
        
        self.assertIn("question", context)
        self.assertIn("answer", context)
        self.assertEqual(context["diagram_type"], "process")


if __name__ == '__main__':
    unittest.main(verbosity=2)
