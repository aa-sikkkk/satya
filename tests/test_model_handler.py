# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
Test suite for the ModelHandler class.
"""

import os
import pytest
from pathlib import Path
from ai_model.model_utils.model_handler import ModelHandler


@pytest.fixture(scope="session")
def model_path():
    """Get model path, skip if not available."""
    base = Path(__file__).resolve().parents[1]
    path = base / "satya_data" / "models" / "phi15"
    if not path.exists():
        pytest.skip("Model path missing; skipping model handler tests.")
    return str(path)


def test_model_initialization(model_path):
    """Test model initialization."""
    handler = ModelHandler(model_path)
    assert handler.model_path == model_path
    assert handler.handler is not None
    assert handler.simple_handler is not None


def test_get_model_info(model_path):
    """Test getting model information."""
    handler = ModelHandler(model_path)
    info = handler.get_model_info()
    
    assert isinstance(info, dict)
    assert "name" in info
    assert "version" in info
    assert "format" in info
    assert info["format"] == "GGUF"
    assert info["optimized_for"] == "i3_cpu"


def test_get_answer(model_path):
    """Test answer generation."""
    handler = ModelHandler(model_path)
    question = "What is a computer?"
    context = "A computer is an electronic device that processes data."
    
    answer, confidence = handler.get_answer(question, context)
    
    assert isinstance(answer, str)
    assert isinstance(confidence, float)
    assert 0.0 <= confidence <= 1.0
    assert len(answer) > 0


def test_get_answer_with_different_lengths(model_path):
    """Test answer generation with different length parameters."""
    handler = ModelHandler(model_path)
    question = "Define algorithm."
    context = "An algorithm is a step-by-step set of instructions."
    
    # Test different answer lengths
    ans_short, conf_short = handler.get_answer(question, context, "short")
    ans_medium, conf_medium = handler.get_answer(question, context, "medium")
    ans_long, conf_long = handler.get_answer(question, context, "long")
    
    assert isinstance(ans_short, str)
    assert isinstance(ans_medium, str)
    assert isinstance(ans_long, str)
    
    # All should have valid confidence scores
    assert 0.0 <= conf_short <= 1.0
    assert 0.0 <= conf_medium <= 1.0
    assert 0.0 <= conf_long <= 1.0


def test_get_answer_stream(model_path):
    """Test streaming answer generation."""
    handler = ModelHandler(model_path)
    question = "What is a computer?"
    context = "A computer is an electronic device."
    
    # Collect streamed chunks
    chunks = list(handler.get_answer_stream(question, context))
    
    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)
    
    # Concatenated result should be non-empty
    full_answer = "".join(chunks)
    assert len(full_answer) > 0


def test_generate_response(model_path):
    """Test raw prompt generation."""
    handler = ModelHandler(model_path)
    prompt = "Explain photosynthesis in one sentence."
    
    response = handler.generate_response(prompt, max_tokens=100)
    
    assert isinstance(response, str)
    assert len(response) > 0


def test_cleanup(model_path):
    """Test model cleanup."""
    handler = ModelHandler(model_path)
    
    # Should not raise any errors
    handler.cleanup()


def test_error_handling_empty_input(model_path):
    """Test error handling with empty input."""
    handler = ModelHandler(model_path)
    
    # Should handle gracefully and return error message
    answer, confidence = handler.get_answer("", "")
    
    assert isinstance(answer, str)
    assert isinstance(confidence, float)
    # Low confidence for error cases
    assert confidence < 0.5


def test_model_path_validation():
    """Test model path validation."""
    # Test with non-existent path
    with pytest.raises(FileNotFoundError):
        ModelHandler("/non/existent/path")