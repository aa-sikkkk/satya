#!/usr/bin/env python3
"""
Test Two-Phase Educational Pipeline

Verifies Phase 1 (fast framing) and Phase 2 (structured depth) work correctly.
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_model.model_utils.model_handler import ModelHandler

def test_two_phase_pipeline():
    """Test the two-phase educational response system."""
    print("🧪 Testing Two-Phase Educational Pipeline")
    print("=" * 60)
    
    # Initialize model
    print("\n⚡ Initializing Phi 1.5...")
    start = time.time()
    model = ModelHandler(model_path="satya_data/models/phi15")
    print(f"✅ Model loaded in {time.time() - start:.2f}s\n")
    
    # Test question
    question = "What is acceleration?"
    context = """
    Acceleration is the rate of change of velocity with respect to time.
    It is a vector quantity, meaning it has both magnitude and direction.
    The SI unit for acceleration is meters per second squared (m/s²).
    """
    
    print(f"❓ Question: {question}")
    print(f"📚 Context: {len(context)} chars\n")
    
    # Test Phase 1 only
    print("=" * 60)
    print("Phase 1: Fast Framing (No RAG)")
    print("=" * 60)
    phase1_start = time.time()
    phase1_answer, phase1_conf = model.phi15_handler.get_answer_phase1(question)
    phase1_time = time.time() - phase1_start
    
    print(f"\n⚡ TTFR: {phase1_time:.3f}s")
    print(f"📝 Answer: {phase1_answer}")
    print(f"🎯 Confidence: {phase1_conf:.2f}\n")
    
    # Test Phase 2 only
    print("=" * 60)
    print("Phase 2: Structured Depth (With RAG)")
    print("=" * 60)
    phase2_start = time.time()
    phase2_answer, phase2_conf = model.phi15_handler.get_answer_phase2(
        question, context, phase1_answer
    )
    phase2_time = time.time() - phase2_start
    
    print(f"\n📚 Phase 2 Time: {phase2_time:.3f}s")
    print(f"📝 Answer: {phase2_answer}")
    print(f"🎯 Confidence: {phase2_conf:.2f}\n")
    
    # Test combined layered response
    print("=" * 60)
    print("Combined: Two-Phase Layered Response")
    print("=" * 60)
    combined_start = time.time()
    full_answer, full_conf = model.get_answer_layered(question, context)
    combined_time = time.time() - combined_start
    
    print(f"\n⏱️ Total Time: {combined_time:.3f}s")
    print(f"📝 Full Answer:\n{full_answer}")
    print(f"\n🎯 Confidence: {full_conf:.2f}\n")
    
    # Summary
    print("=" * 60)
    print("Performance Summary")
    print("=" * 60)
    print(f"Phase 1 TTFR:     {phase1_time:.3f}s  {'✅' if phase1_time < 3.0 else '⚠️'}")
    print(f"Phase 2 Time:     {phase2_time:.3f}s")
    print(f"Total Time:       {combined_time:.3f}s  {'✅' if combined_time < 35.0 else '⚠️'}")
    print(f"Answer Length:    {len(full_answer)} chars")
    print(f"Sections:         {full_answer.count('\\n\\n') + 1}")
    
    # Success criteria
    success = (
        phase1_time < 3.0 and  # Phase 1 TTFR < 3s
        combined_time < 35.0 and  # Total < 35s
        len(full_answer) > 100  # Meaningful answer
    )
    
    print(f"\n{'✅ PASSED' if success else '❌ FAILED'}: Two-phase pipeline test\n")
    
    return success

if __name__ == "__main__":
    try:
        success = test_two_phase_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
