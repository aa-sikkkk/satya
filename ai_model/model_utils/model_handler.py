"""
Model Handler Module

This module provides the interface for interacting with different AI models.
"""

import os
import json
import logging
from typing import Dict, Any, List, Tuple, Optional
from .phi2_handler import Phi2Handler
from .qna_handler import QnAHandler
from .hint_handler import HintHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelHandler:
    """
    Handler for managing different AI models with fallback logic.
    
    Attributes:
        model_path (str): Path to the model directory
        qna_handler (QnAHandler): Handler for QnA model
        hint_handler (HintHandler): Handler for Hint model
        phi2_handler (Phi2Handler): Handler for Phi-2 model
        current_model (str): Name of the currently active model
    """
    
    def __init__(self, model_path: str):
        """
        Initialize the model handler.
        
        Args:
            model_path (str): Path to the model directory
        """
        self.model_path = model_path
        self.phi2_handler = Phi2Handler(os.path.join(model_path, "phi2"))
        self.qna_handler = QnAHandler(os.path.join(model_path, "qna"))
        self.hint_handler = HintHandler(os.path.join(model_path, "hint"), phi2_handler=self.phi2_handler)
        self.current_model = "qna"  # Default to QnA
        # Pre-load models for efficiency
        try:
            self.qna_handler.load_model()
        except Exception as e:
            logger.warning(f"QnA model not loaded: {e}")
        try:
            self.hint_handler.load_model()
        except Exception as e:
            logger.warning(f"Hint model not loaded: {e}")
        try:
            self.phi2_handler.load_model()
        except Exception as e:
            logger.warning(f"Phi-2 model not loaded: {e}")
        
    def get_answer(self, question: str, context: str) -> Tuple[str, float]:
        """
        Get an answer from the current model.
        
        Args:
            question (str): The question to answer
            context (str): Context for the question
            
        Returns:
            Tuple[str, float]: The answer and confidence score
        """
        try:
            # Try QnAHandler (DistilBERT) first
            answer, confidence = self.qna_handler.get_answer(question, context)
            if answer and confidence >= 0.7:
                self.current_model = "qna"
                return answer, confidence
        except Exception as e:
            logger.warning(f"QnAHandler failed: {e}")
        # Fallback to Phi-2
        try:
            answer, confidence = self.phi2_handler.get_answer(question, context)
            self.current_model = "phi2"
            return answer, confidence
        except Exception as e:
            logger.error(f"Phi2Handler failed: {e}")
            return "I'm having trouble processing your question. Please try again.", 0.0
            
    def get_hints(self, question: str, context: str) -> List[str]:
        """
        Get hints from the current model.
        
        Args:
            question (str): The question to get hints for
            context (str): Context for the question
            
        Returns:
            List[str]: List of hints
        """
        try:
            # Try HintHandler (T5) first
            hints = self.hint_handler.get_hints(question, context)
            # If hints are not generic, return them
            if hints and not all('key terms' in h or 'main idea' in h for h in hints):
                self.current_model = "hint"
                return hints
        except Exception as e:
            logger.warning(f"HintHandler failed: {e}")
        # Fallback to Phi-2
        try:
            hints = self.phi2_handler.get_hints(question, context)
            self.current_model = "phi2"
            return hints
        except Exception as e:
            logger.error(f"Phi2Handler failed for hints: {e}")
            return []
            
    def switch_model(self, model_name: str) -> None:
        """
        Switch to a different model.
        
        Args:
            model_name (str): Name of the model to switch to
        """
        if model_name == "phi2":
            self.current_model = "phi2"
        elif model_name == "qna":
            self.current_model = "qna"
        elif model_name == "hint":
            self.current_model = "hint"
        else:
            raise ValueError(f"Unknown model: {model_name}")
            
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dict[str, Any]: Model information
        """
        try:
            if self.current_model == "phi2":
                return self.phi2_handler.get_model_info()
            elif self.current_model == "qna":
                return self.qna_handler.get_model_info()
            elif self.current_model == "hint":
                return self.hint_handler.get_model_info()
        except Exception as e:
            logger.error(f"Error getting model info: {str(e)}")
            return {
                "name": "Unknown",
                "version": "Unknown",
                "quantization": "Unknown",
                "max_length": 0,
                "temperature": 0.0,
                "top_p": 0.0,
                "num_beams": 0
            }
            
    def get_available_models(self) -> List[str]:
        """
        Get list of available models.
        
        Returns:
            List[str]: List of model names
        """
        return ["qna", "hint", "phi2"] 