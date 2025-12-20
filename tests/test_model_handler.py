import os
import pytest
from pathlib import Path

from ai_model.model_utils.model_handler import ModelHandler


@pytest.fixture(scope="session")
def model_path():
    base = Path(__file__).resolve().parents[1]
    path = base / "satya_data" / "models" / "phi_1_5"
    if not path.exists():
        pytest.skip("Model path missing; skipping model handler tests.")
    return path


def test_model_info_defaults(model_path):
    handler = ModelHandler(str(model_path), enable_streaming=False)
    info = handler.get_model_info()
    assert info["context_size"] <= 2048
    assert info["threads"] >= 1


def test_answer_length_control(model_path):
    handler = ModelHandler(str(model_path), enable_streaming=False)
    q = "Define algorithm."
    ctx = "An algorithm is a step-by-step set of instructions."
    ans_short, _ = handler.get_answer(q, ctx, "very_short")
    ans_long, _ = handler.get_answer(q, ctx, "long")
    assert isinstance(ans_short, str)
    assert isinstance(ans_long, str)
    assert len(ans_long) >= len(ans_short)
"""
Test suite for the ModelHandler class.
"""

import pytest
import torch
from ai_model.model_utils.model_handler import ModelHandler
import os
import tempfile

@pytest.fixture
def model_path():
    """Create a temporary directory for model files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def model_handler(model_path):
    """Create a ModelHandler instance for testing."""
    return ModelHandler(model_path)

def test_model_initialization(model_handler):
    """Test model initialization."""
    assert model_handler.model_path is not None
    assert model_handler.device is not None
    assert model_handler.model is None  # Model should be None as we're using a temp directory
    assert model_handler.tokenizer is None

def test_prepare_input(model_handler):
    """Test input preparation."""
    question = "What is a computer?"
    context = "A computer is an electronic device that processes data."
    
    inputs = model_handler._prepare_input(question, context)
    
    assert isinstance(inputs, dict)
    assert "input_ids" in inputs
    assert "attention_mask" in inputs
    assert isinstance(inputs["input_ids"], torch.Tensor)
    assert isinstance(inputs["attention_mask"], torch.Tensor)

def test_get_answer(model_handler):
    """Test answer generation."""
    question = "What is a computer?"
    context = "A computer is an electronic device that processes data."
    
    # This will raise an error as we're using a temp directory
    with pytest.raises(Exception):
        answer, confidence = model_handler.get_answer(question, context)

def test_get_hints(model_handler):
    """Test hint generation."""
    question = "What is a computer?"
    context = "A computer is an electronic device that processes data."
    
    # This will raise an error as we're using a temp directory
    with pytest.raises(Exception):
        hints = model_handler.get_hints(question, context)

def test_optimize_for_inference(model_handler):
    """Test model optimization."""
    # This will raise an error as we're using a temp directory
    with pytest.raises(Exception):
        model_handler.optimize_for_inference()

def test_error_handling(model_handler):
    """Test error handling."""
    # Test with invalid input
    with pytest.raises(Exception):
        model_handler._prepare_input("", "")
    
    # Test with None input
    with pytest.raises(Exception):
        model_handler._prepare_input(None, None)

def test_model_path_validation():
    """Test model path validation."""
    # Test with non-existent path
    with pytest.raises(Exception):
        ModelHandler("/non/existent/path")
    
    # Test with invalid path
    with pytest.raises(Exception):
        ModelHandler("")

def test_device_selection():
    """Test device selection logic."""
    handler = ModelHandler(tempfile.mkdtemp())
    assert handler.device.type in ['cpu', 'cuda'] 