#!/usr/bin/env python3
"""
Integration Test for ASCII Diagram Feature
Tests the end-to-end diagram generation in the context of the full system.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from system.diagrams import generate_and_append_diagram


def test_integration():
    """Test diagram generation with various realistic scenarios."""
    
    test_cases = [
        {
            "name": "Science - Water Cycle",
            "question": "What is the water cycle?",
            "answer": "The water cycle is a continuous process. First, water evaporates from bodies of water. Then, water vapor rises and condenses into clouds. Finally, precipitation falls back to Earth as rain or snow.",
            "expected_keywords": ["Diagram:", "┌", "│", "└", "evaporat", "vapor", "precipitation"],
        },
        {
            "name": "Biology - Photosynthesis",
            "question": "How does photosynthesis work?",
            "answer": "Photosynthesis involves processes such as light absorption, water splitting, and carbon fixation. Stage 1: Light Absorption. Stage 2: Water Splitting. Stage 3: Carbon Fixation.",
            "expected_keywords": ["Diagram:", "┌", "│", "└", "Light", "Water", "Carbon"],
        },
        {
            "name": "Computer Science - Algorithm",
            "question": "How does a sorting algorithm work?",
            "answer": "First, compare elements. Then, swap if needed. Finally, repeat until sorted.",
            "expected_keywords": ["Diagram:", "┌", "│", "└"],
        },
        {
            "name": "Geology - Rock Cycle",
            "question": "What is the rock cycle?",
            "answer": "The rock cycle is a continuous transformation. First, igneous rocks form. Then, weathering creates sediments. Next, sedimentary rocks form. Finally, metamorphic rocks transform.",
            "expected_keywords": ["Diagram:", "cycle", "┌", "│"],
        },
        {
            "name": "No Diagram - Simple Answer",
            "question": "What is a computer?",
            "answer": "A computer is an electronic device.",
            "expected_keywords": [],  # Should NOT generate diagram
        },
    ]
    
    print("=" * 80)
    print("ASCII Diagram Integration Tests")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        try:
            print(f"Test {i}: {test['name']}")
            
            result = generate_and_append_diagram(test["question"], test["answer"])
            
            # Check if answer is preserved
            if test["answer"] not in result:
                raise AssertionError("Original answer not preserved")
            
            # Check expected keywords
            if test["expected_keywords"]:
                # Should have diagram
                has_diagram = "Diagram:" in result or "┌" in result
                if not has_diagram:
                    raise AssertionError("Expected diagram but none was generated")
                
                # Check for expected content
                for keyword in test["expected_keywords"]:
                    if keyword not in result:
                        print(f"  Warning: Expected keyword '{keyword}' not found")
                
                print(f"  ✓ Passed - Diagram generated")
            else:
                # Should NOT have diagram
                has_diagram = "Diagram:" in result and "┌" in result
                if has_diagram:
                    raise AssertionError("Did not expect diagram but one was generated")
                
                print(f"  ✓ Passed - No diagram (as expected)")
            
            passed += 1
            
        except AssertionError as e:
            print(f"  ✗ Failed: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ Failed: Unexpected error: {e}")
            failed += 1
        
        print()
    
    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)
