#!/usr/bin/env python3
"""
Lightweight Model Handler for Satya Learning System

Single Phi 1.5 model for all tasks
"""

import os
import logging
from typing import Dict, Any, List, Tuple, Iterator
from .phi15_handler import Phi15Handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelHandler:
    """
    Lightweight model handler using only Phi 1.5.
    
    Attributes:
        model_path (str): Path to the model directory
        phi15_handler (Phi15Handler): Handler for Phi 1.5 model
    """
    
    def __init__(self, model_path: str, enable_streaming: bool = False):
        """
        Initialize the lightweight model handler.

        Args:
            model_path (str): Path to model directory.
            enable_streaming: Enable token streaming when backend supports it.
        """
        self.model_path = model_path
        self.phi15_handler = Phi15Handler(
            model_path=model_path,
            enable_streaming=enable_streaming,
        )
        
        # Pre-load model for efficiency
        try:
            self.phi15_handler.load_model()

        except Exception as e:
            logger.error(f"Failed to load Phi 1.5 model: {e}")
            raise
        
    def get_answer(self, question: str, context: str, answer_length: str = "medium") -> Tuple[str, float]:
        """
        Get answer with length control.
        
        Args:
            question (str): User's question
            context (str): Relevant context
            answer_length (str): "very_short", "short", "medium", "long", "very_long"
            
        Returns:
            Tuple[str, float]: Answer and confidence score
        """
        try:
            return self.phi15_handler.get_answer(question, context, answer_length)
        except Exception as e:
            logger.error(f"Error getting answer: {e}")
            return "I'm having trouble processing your question. Please try again.", 0.1
    
    def get_answer_stream(self, question: str, context: str, answer_length: str = "medium") -> Iterator[str]:
        """
        Stream answer tokens as they're generated for real-time display.
        
        Args:
            question (str): User's question
            context (str): Relevant context
            answer_length (str): "very_short", "short", "medium", "long", "very_long"
            
        Yields:
            str: Token chunks as they're generated
        """
        try:
            yield from self.phi15_handler.get_answer_stream(question, context, answer_length)
        except Exception as e:
            logger.error(f"Error streaming answer: {e}")
            yield "I'm having trouble processing your question. Please try again."
            
    def get_hints(self, question: str, context: str) -> List[str]:
        """
        Get hints using Phi 1.5.
        
        Args:
            question (str): The question to get hints for
            context (str): Context for the question
            
        Returns:
            List[str]: List of hints
        """
        try:
            return self.phi15_handler.get_hints(question, context)
        except Exception as e:
            logger.error(f"Error getting hints: {e}")
            return [
                "Look for key terms in the context.",
                "Identify the main ideas mentioned.",
                "Connect different concepts together."
            ]
            
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dict[str, Any]: Model information
        """
        try:
            return self.phi15_handler.get_model_info()
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {
                "name": "Phi 1.5",
                "version": "Unknown",
                "format": "Unknown",
                "context_size": 2048,
                "threads": 2,
                "max_tokens": 128,
                "temperature": 0.7,
                "top_p": 0.9
            }
            
    def get_available_models(self) -> List[str]:
        """
        Get list of available models (only Phi 1.5).
        
        Returns:
            List[str]: List of model names
        """
        return ["phi15"]
    
    def cleanup(self):
        """Clean up model resources."""
        try:
            self.phi15_handler.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up model: {e}") 