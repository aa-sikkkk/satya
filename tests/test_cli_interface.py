"""
Test suite for the CLI interface module.

This module contains tests for the CLIInterface class and its methods.
"""

import os
import pytest
from unittest.mock import Mock, patch
from rich.console import Console
from rich.prompt import Prompt, Confirm

from student_app.interface.cli_interface import CLIInterface

# Mock console for testing
console = Console()

@pytest.fixture
def content_dir(tmp_path):
    """Create a temporary content directory with sample data."""
    content = {
        "subject": "Computer Science",
        "grade": "10",
        "topics": [
            {
                "title": "Introduction to Computers",
                "subtopics": [
                    {
                        "title": "What is a Computer?",
                        "concepts": [
                            {
                                "title": "Definition of Computer",
                                "summary": "A computer is an electronic device that processes data.",
                                "questions": [
                                    {
                                        "question": "What is a computer?",
                                        "acceptable_answers": ["electronic device", "processes data"],
                                        "hints": ["Think about what it does with information"],
                                        "explanation": "A computer is a device that takes input, processes it, and produces output."
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    # Create content directory structure
    content_path = tmp_path / "content"
    content_path.mkdir()
    
    # Write sample content
    with open(content_path / "computer_science.json", "w") as f:
        import json
        json.dump(content, f)
        
    return str(content_path)

@pytest.fixture
def model_path(tmp_path):
    """Create a temporary model directory."""
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    return str(model_dir)

@pytest.fixture
def cli_interface(content_dir, model_path):
    """Create a CLIInterface instance for testing."""
    return CLIInterface(content_dir, model_path)

def test_cli_interface_initialization(cli_interface, content_dir, model_path):
    """Test CLIInterface initialization."""
    assert cli_interface.content_manager is not None
    assert cli_interface.model_handler is not None
    assert cli_interface.session is not None

@patch('rich.prompt.Prompt.ask')
def test_create_menu(mock_prompt, cli_interface):
    """Test menu creation and selection."""
    # Mock user input
    mock_prompt.return_value = "1"
    
    # Test menu creation
    options = ["Option 1", "Option 2", "Option 3"]
    result = cli_interface._create_menu("Test Menu", options)
    
    assert result == "Option 1"
    mock_prompt.assert_called_once()

@patch('rich.prompt.Prompt.ask')
@patch('rich.prompt.Confirm.ask')
def test_display_question(mock_confirm, mock_prompt, cli_interface):
    """Test question display and interaction."""
    # Mock user inputs
    mock_prompt.return_value = "electronic device"
    mock_confirm.side_effect = [False, False]  # No hints, no explanation
    
    # Test question
    question = {
        "question": "What is a computer?",
        "acceptable_answers": ["electronic device", "processes data"],
        "hints": ["Think about what it does with information"],
        "explanation": "A computer is a device that takes input, processes it, and produces output."
    }
    
    cli_interface._display_question(question)
    
    # Verify interactions
    mock_prompt.assert_called_once()
    assert mock_confirm.call_count == 2

@patch('rich.prompt.Prompt.ask')
@patch('rich.prompt.Confirm.ask')
def test_handle_free_text_question(mock_confirm, mock_prompt, cli_interface):
    """Test handling of free-text questions."""
    # Mock model responses
    cli_interface.model_handler.get_answer = Mock(return_value=("Test answer", 0.95))
    cli_interface.model_handler.get_hints = Mock(return_value=["Hint 1", "Hint 2"])
    
    # Mock user inputs
    mock_prompt.return_value = "What is a computer?"
    mock_confirm.side_effect = [True, False]  # Want hints, but only one
    
    # Test question handling
    cli_interface._handle_free_text_question("What is a computer?")
    
    # Verify model calls
    cli_interface.model_handler.get_answer.assert_called_once()
    cli_interface.model_handler.get_hints.assert_called_once()

@patch('rich.prompt.Prompt.ask')
@patch('rich.prompt.Confirm.ask')
def test_browse_subjects(mock_confirm, mock_prompt, cli_interface):
    """Test subject browsing functionality."""
    # Mock user inputs
    mock_prompt.side_effect = ["1", "1", "1", "1"]  # Select first option each time
    mock_confirm.side_effect = [True, True, False]  # Try questions, continue, stop
    
    # Test browsing
    cli_interface._browse_subjects()
    
    # Verify interactions
    assert mock_prompt.call_count == 4
    assert mock_confirm.call_count == 3

@patch('rich.prompt.Prompt.ask')
def test_ask_question(mock_prompt, cli_interface):
    """Test question asking functionality."""
    # Mock user inputs
    mock_prompt.side_effect = ["What is a computer?", "back"]
    
    # Test question asking
    cli_interface._ask_question()
    
    # Verify interactions
    assert mock_prompt.call_count == 2

def test_view_progress(cli_interface):
    """Test progress viewing functionality."""
    # Currently just a placeholder
    cli_interface._view_progress()

@patch('rich.prompt.Prompt.ask')
@patch('rich.prompt.Confirm.ask')
def test_start_exit(mock_confirm, mock_prompt, cli_interface):
    """Test CLI start and exit functionality."""
    # Mock user inputs
    mock_prompt.return_value = "4"  # Select Exit
    mock_confirm.return_value = True  # Confirm exit
    
    # Test start and exit
    cli_interface.start()
    
    # Verify interactions
    mock_prompt.assert_called_once()
    mock_confirm.assert_called_once()

@patch('rich.prompt.Prompt.ask')
@patch('rich.prompt.Confirm.ask')
def test_start_keyboard_interrupt(mock_confirm, mock_prompt, cli_interface):
    """Test handling of keyboard interrupt."""
    # Mock keyboard interrupt
    mock_prompt.side_effect = KeyboardInterrupt
    
    # Test start with interrupt
    cli_interface.start()
    
    # Verify no confirm was called
    mock_confirm.assert_not_called() 