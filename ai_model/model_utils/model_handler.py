#!/usr/bin/env python3
"""
Model Handler for Satya Learning System
Simple wrapper around Phi 1.5 handler
"""

import os
import logging
from typing import Dict, Any, List, Tuple, Iterator, Optional

# Import the FIXED handler
from .phi15_handler import Phi15Handler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelHandler:
    """
    Simple model handler using Phi 1.5.
    No complexity, just works.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize handler.

        Args:
            model_path: Path to model directory. Defaults to "satya_data/models/phi15"
        """
        # Default path
        if model_path is None:
            model_path = os.path.join("satya_data", "models", "phi15")
            
        self.model_path = model_path
        self.handler = Phi15Handler(model_path)
        
        # Pre-load model
        try:
            logger.info("Loading Phi 1.5...")
            self.handler.load_model()
            logger.info("Model ready!")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
        
    def get_answer(self, question: str, context: str = "", answer_length: str = "medium") -> Tuple[str, float]:
        """
        Get answer (answer_length is ignored - handler auto-detects).
        
        Args:
            question: User's question
            context: RAG context (optional)
            answer_length: Ignored (kept for compatibility)
            
        Returns:
            (answer, confidence)
        """
        try:
            return self.handler.get_answer(question, context)
        except Exception as e:
            logger.error(f"Error: {e}")
            return "I'm having trouble with your question. Please try again.", 0.1
    
    def get_answer_stream(self, question: str, context: str = "", answer_length: str = "medium") -> Iterator[str]:
        """
        Stream answer tokens.
        
        Args:
            question: User's question
            context: RAG context (optional)
            answer_length: Ignored
            
        Yields:
            Token chunks
        """
        try:
            yield from self.handler.get_answer_stream(question, context)
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield "I'm having trouble with your question. Please try again."
    
    def get_hints(self, question: str, context: str = "") -> List[str]:
        """
        Get 3 hints.
        
        Args:
            question: Question to get hints for
            context: Context (optional)
            
        Returns:
            List of 3 hints
        """
        try:
            return self.handler.get_hints(question, context)
        except Exception as e:
            logger.error(f"Hints error: {e}")
            return [
                "Think about the key concepts.",
                "Break the question into parts.",
                "Connect to what you already know."
            ]
            
    def get_model_info(self) -> Dict[str, Any]:
        """Get model info."""
        return {
            "name": "Phi 1.5",
            "version": "1.5",
            "format": "GGUF",
            "backend": "llama-cpp-python",
            "optimized_for": "educational_answers",
            "adaptive_tokens": True
        }
            
    def get_available_models(self) -> List[str]:
        """Get available models."""
        return ["phi15"]
    
    def cleanup(self):
        """Clean up resources."""
        try:
            self.handler.cleanup()
            logger.info("Model cleaned up")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")