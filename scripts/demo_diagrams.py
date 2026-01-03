#!/usr/bin/env python3
"""
ASCII Diagram Generation Demo

This script demonstrates the ASCII diagram generation capabilities of the Satya system.
It shows how diagrams are automatically generated for different types of questions.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from system.diagrams import generate_and_append_diagram


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def demo_water_cycle():
    """Demonstrate diagram generation for the water cycle."""
    print_section("Example 1: Water Cycle (Process Diagram with Cycle)")
    
    question = "What is the water cycle?"
    answer = ("The water cycle is a continuous process. First, water evaporates "
             "from bodies of water. Then, water vapor rises and condenses into clouds. "
             "Finally, precipitation falls back to Earth as rain or snow.")
    
    print(f"Question: {question}\n")
    print(f"Answer: {answer}\n")
    
    result = generate_and_append_diagram(question, answer)
    
    # Extract and print just the diagram part
    if "Diagram:" in result:
        diagram_part = result.split("Diagram:")[1].strip()
        print("Generated Diagram:")
        print(diagram_part)
    else:
        print("No diagram generated")


def demo_photosynthesis():
    """Demonstrate diagram generation for photosynthesis."""
    print_section("Example 2: Photosynthesis (Process Diagram with Numbered Stages)")
    
    question = "How does photosynthesis work?"
    answer = """Photosynthesis is the process by which plants convert sunlight into energy.
Stage 1: Light Absorption - chlorophyll in leaves absorbs light energy.
Stage 2: Water Splitting - water molecules are broken down into hydrogen and oxygen.
Stage 3: Carbon Fixation - CO2 from air is converted into glucose using the energy."""
    
    print(f"Question: {question}\n")
    print(f"Answer: {answer}\n")
    
    result = generate_and_append_diagram(question, answer)
    
    if "Diagram:" in result:
        diagram_part = result.split("Diagram:")[1].strip()
        print("Generated Diagram:")
        print(diagram_part)
    else:
        print("No diagram generated")


def demo_cell_structure():
    """Demonstrate diagram generation for cell structure."""
    print_section("Example 3: Cell Structure (Hierarchical Structure Diagram)")
    
    question = "What is the structure of a plant cell?"
    answer = ("A plant cell consists of several components. The main parts include "
             "the cell wall, cell membrane, nucleus, cytoplasm, chloroplasts, and vacuole. "
             "Each component has a specific function in the cell.")
    
    print(f"Question: {question}\n")
    print(f"Answer: {answer}\n")
    
    result = generate_and_append_diagram(question, answer)
    
    if "Diagram:" in result:
        diagram_part = result.split("Diagram:")[1].strip()
        print("Generated Diagram:")
        print(diagram_part)
    else:
        print("No diagram generated")


def demo_algorithm():
    """Demonstrate diagram generation for an algorithm."""
    print_section("Example 4: Algorithm (Flowchart with Decisions)")
    
    question = "How does a binary search algorithm work?"
    answer = ("Binary search works by repeatedly dividing the search space in half. "
             "First, check the middle element. Then, if the target is less than the middle, "
             "search the left half. Otherwise, search the right half. "
             "Finally, repeat until the target is found or the search space is empty.")
    
    print(f"Question: {question}\n")
    print(f"Answer: {answer}\n")
    
    result = generate_and_append_diagram(question, answer)
    
    if "Diagram:" in result:
        diagram_part = result.split("Diagram:")[1].strip()
        print("Generated Diagram:")
        print(diagram_part)
    else:
        print("No diagram generated")


def demo_rock_cycle():
    """Demonstrate diagram generation for geological process."""
    print_section("Example 5: Rock Cycle (Cyclic Process in Science)")
    
    question = "What is the rock cycle?"
    answer = ("The rock cycle is a continuous transformation process. "
             "First, igneous rocks form from cooling magma. "
             "Then, weathering breaks rocks into sediments. "
             "Next, sediments compact into sedimentary rocks. "
             "Finally, heat and pressure transform rocks into metamorphic rocks, "
             "which may melt back into magma.")
    
    print(f"Question: {question}\n")
    print(f"Answer: {answer}\n")
    
    result = generate_and_append_diagram(question, answer)
    
    if "Diagram:" in result:
        diagram_part = result.split("Diagram:")[1].strip()
        print("Generated Diagram:")
        print(diagram_part)
    else:
        print("No diagram generated")


def main():
    """Run all demo examples."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "      ASCII Diagram Generation Demo - Satya Learning System".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    
    print("\nThis demo shows how Satya automatically generates ASCII diagrams for")
    print("different types of educational questions across various subjects.")
    print("\nSupported diagram types:")
    print("  • Process Diagrams (step-by-step sequences)")
    print("  • Structure Diagrams (hierarchical components)")
    print("  • Flowcharts (decision-based logic)")
    print("  • Cycle Diagrams (repeating processes)")
    
    demos = [
        demo_water_cycle,
        demo_photosynthesis,
        demo_cell_structure,
        demo_algorithm,
        demo_rock_cycle,
    ]
    
    for demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"Error in demo: {e}")
    
    print_section("Summary")
    print("The ASCII diagram generation system:")
    print("  ✓ Automatically detects when a diagram would be helpful")
    print("  ✓ Extracts key information from the answer")
    print("  ✓ Generates appropriate diagram type (process, structure, flowchart, cycle)")
    print("  ✓ Works across all subjects (Science, Math, Computer Science, etc.)")
    print("  ✓ Adapts to different answer formats and styles")
    print("\nDiagrams enhance learning by providing visual representations of concepts!")
    print()


if __name__ == "__main__":
    main()
