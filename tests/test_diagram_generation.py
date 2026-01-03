#!/usr/bin/env python3
"""
Tests for ASCII Diagram Generation
Tests the diagram system's ability to generate diagrams for various question types.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from system.diagrams import (
    generate_and_append_diagram,
    should_generate_diagram,
    extract_context_for_diagram,
    generate_diagram,
    validate_diagram
)
from system.diagrams.custom_generator import extract_steps_from_answer


def test_step_extraction_sequential():
    """Test extraction of sequential steps (First, Then, Finally)."""
    answer = ("The water cycle is a continuous process. First, water evaporates "
             "from bodies of water. Then, water vapor rises and condenses into clouds. "
             "Finally, precipitation falls back to Earth as rain or snow.")
    
    steps = extract_steps_from_answer(answer)
    
    assert len(steps) >= 3, f"Expected at least 3 steps, got {len(steps)}"
    assert any("evaporat" in step.lower() for step in steps), "Missing evaporation step"
    assert any("vapor" in step.lower() or "rises" in step.lower() for step in steps), "Missing condensation step"
    assert any("precipitation" in step.lower() or "falls" in step.lower() for step in steps), "Missing precipitation step"
    print(f"✓ Sequential step extraction: {len(steps)} steps extracted")


def test_step_extraction_numbered():
    """Test extraction of numbered steps (Stage 1, Stage 2)."""
    answer = """Photosynthesis involves multiple stages. 
    Stage 1: Light Absorption - chlorophyll absorbs light energy.
    Stage 2: Water Splitting - water molecules are broken down.
    Stage 3: Carbon Fixation - CO2 is converted to glucose."""
    
    steps = extract_steps_from_answer(answer)
    
    assert len(steps) >= 3, f"Expected at least 3 steps, got {len(steps)}"
    assert any("light" in step.lower() or "absorption" in step.lower() for step in steps), "Missing light absorption"
    assert any("water" in step.lower() or "splitting" in step.lower() for step in steps), "Missing water splitting"
    assert any("carbon" in step.lower() or "fixation" in step.lower() for step in steps), "Missing carbon fixation"
    print(f"✓ Numbered step extraction: {len(steps)} steps extracted")


def test_step_extraction_process_list():
    """Test extraction from process lists (involves X, Y, and Z)."""
    answer = ("Photosynthesis involves processes such as light absorption, "
             "water splitting, and carbon fixation.")
    
    steps = extract_steps_from_answer(answer)
    
    assert len(steps) >= 2, f"Expected at least 2 steps, got {len(steps)}"
    print(f"✓ Process list extraction: {len(steps)} steps extracted")


def test_diagram_detection_process():
    """Test that process-type questions are detected."""
    question = "What is the water cycle?"
    answer = ("The water cycle is a continuous process. First, water evaporates. "
             "Then, water vapor condenses. Finally, precipitation falls.")
    
    should_generate, diagram_type = should_generate_diagram(question, answer)
    
    assert should_generate, "Should generate diagram for water cycle question"
    assert diagram_type is not None, "Diagram type should be detected"
    print(f"✓ Process diagram detection: type={diagram_type}")


def test_diagram_detection_structure():
    """Test that structure-type questions are detected."""
    question = "What is the structure of a computer network?"
    answer = ("A computer network consists of several components. "
             "It includes computers, routers, switches, and cables.")
    
    should_generate, diagram_type = should_generate_diagram(question, answer)
    
    assert should_generate, "Should generate diagram for structure question"
    print(f"✓ Structure diagram detection: type={diagram_type}")


def test_diagram_generation_water_cycle():
    """Test complete diagram generation for water cycle."""
    question = "What is the water cycle?"
    answer = ("The water cycle is a continuous process. First, water evaporates "
             "from bodies of water. Then, water vapor rises and condenses into clouds. "
             "Finally, precipitation falls back to Earth as rain or snow.")
    
    result = generate_and_append_diagram(question, answer)
    
    # Check that answer is preserved
    assert "water cycle" in result.lower(), "Original answer should be preserved"
    
    # Check that diagram was added
    assert "Diagram:" in result or "┌" in result, "Diagram should be added"
    
    # Check for box-drawing characters
    box_chars = "┌┐└┘│─"
    assert any(char in result for char in box_chars), "Should contain box-drawing characters"
    
    print("✓ Water cycle diagram generation")


def test_diagram_generation_photosynthesis():
    """Test complete diagram generation for photosynthesis."""
    question = "How does photosynthesis work?"
    answer = """Photosynthesis involves processes such as light absorption, water splitting, and carbon fixation. 
    Stage 1: Light Absorption - chlorophyll absorbs light energy.
    Stage 2: Water Splitting - water molecules are broken down.
    Stage 3: Carbon Fixation - CO2 is converted to glucose."""
    
    result = generate_and_append_diagram(question, answer)
    
    # Check that answer is preserved
    assert "Photosynthesis" in result, "Original answer should be preserved"
    
    # Check that diagram was added
    assert "Diagram:" in result or "┌" in result, "Diagram should be added"
    
    # Check for step labels in diagram
    assert "Light absorption" in result or "light" in result.lower(), "Should contain light absorption"
    
    print("✓ Photosynthesis diagram generation")


def test_diagram_validation():
    """Test diagram validation."""
    # Valid diagram
    valid_diagram = """┌─────────┐
│  Start  │
└────┬────┘
     │
┌────▼────┐
│  Step 1 │
└─────────┘"""
    
    is_valid, error = validate_diagram(valid_diagram)
    assert is_valid, f"Valid diagram rejected: {error}"
    print("✓ Diagram validation (valid)")
    
    # Invalid diagram (no box chars)
    invalid_diagram = "This is just text"
    is_valid, error = validate_diagram(invalid_diagram)
    assert not is_valid, "Invalid diagram should be rejected"
    print("✓ Diagram validation (invalid)")


def test_no_diagram_for_simple_question():
    """Test that simple questions don't get diagrams."""
    question = "What is a computer?"
    answer = "A computer is an electronic device."
    
    result = generate_and_append_diagram(question, answer)
    
    # Should return answer unchanged (no diagram)
    assert result == answer, "Simple question should not get diagram"
    print("✓ No diagram for simple question")


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        ("Step Extraction - Sequential", test_step_extraction_sequential),
        ("Step Extraction - Numbered", test_step_extraction_numbered),
        ("Step Extraction - Process List", test_step_extraction_process_list),
        ("Diagram Detection - Process", test_diagram_detection_process),
        ("Diagram Detection - Structure", test_diagram_detection_structure),
        ("Diagram Generation - Water Cycle", test_diagram_generation_water_cycle),
        ("Diagram Generation - Photosynthesis", test_diagram_generation_photosynthesis),
        ("Diagram Validation", test_diagram_validation),
        ("No Diagram for Simple Question", test_no_diagram_for_simple_question),
    ]
    
    print("=" * 70)
    print("ASCII Diagram Generation Tests")
    print("=" * 70)
    print()
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_name}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_name}: Unexpected error: {e}")
            failed += 1
    
    print()
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
