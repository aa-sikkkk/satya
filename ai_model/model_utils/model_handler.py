"""
Model Handler Module

This module provides utilities for loading and using the trained models
for educational content question answering and hint generation.
"""

import os
import torch
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForQuestionAnswering,
    T5Tokenizer,
    T5ForConditionalGeneration
)
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelHandler:
    """
    Handles loading and inference with the trained models.
    
    Attributes:
        model_path (str): Path to the saved model
        device (torch.device): Device to run inference on
        qna_model (DistilBertForQuestionAnswering): QnA model
        hint_model (T5ForConditionalGeneration): Hint generation model
        qna_tokenizer (DistilBertTokenizerFast): QnA tokenizer
        hint_tokenizer (T5Tokenizer): Hint generation tokenizer
    """
    
    def __init__(self, model_path: str):
        """
        Initialize the model handler.
        
        Args:
            model_path (str): Path to the saved model directory
        """
        self.model_path = model_path
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.qna_model = None
        self.hint_model = None
        self.qna_tokenizer = None
        self.hint_tokenizer = None
        self._load_models()
        
    def _load_models(self) -> None:
        """Load the models and tokenizers from disk."""
        try:
            logger.info(f"Loading models from {self.model_path}")
            
            # Load QnA model
            qna_path = os.path.join(self.model_path, 'qna')
            self.qna_model = DistilBertForQuestionAnswering.from_pretrained(qna_path)
            self.qna_tokenizer = DistilBertTokenizerFast.from_pretrained(qna_path)
            self.qna_model.to(self.device)
            self.qna_model.eval()
            
            # Load Hint model
            hint_path = os.path.join(self.model_path, 'hint')
            self.hint_model = T5ForConditionalGeneration.from_pretrained(hint_path)
            self.hint_tokenizer = T5Tokenizer.from_pretrained(hint_path)
            self.hint_model.to(self.device)
            self.hint_model.eval()
            
            logger.info("Models loaded successfully")
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            raise
            
    def _prepare_qna_input(self, question: str, context: str) -> Dict[str, torch.Tensor]:
        """
        Prepare input for QnA model inference.
        
        Args:
            question (str): The question to answer
            context (str): The context to find the answer in
            
        Returns:
            Dict[str, torch.Tensor]: Tokenized input
        """
        return self.qna_tokenizer(
            question,
            context,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=True
        ).to(self.device)
        
    def get_answer(self, question: str, context: str) -> Tuple[str, float]:
        """
        Get answer for a question from the given context.
        
        Args:
            question (str): The question to answer
            context (str): The context to find the answer in
            
        Returns:
            Tuple[str, float]: The answer and its confidence score
        """
        try:
            # Prepare input
            inputs = self._prepare_qna_input(question, context)
            
            # Get model prediction
            with torch.no_grad():
                outputs = self.qna_model(**inputs)
                
            # Get start and end positions
            start_logits = outputs.start_logits
            end_logits = outputs.end_logits
            
            # Get most likely start and end positions
            start_idx = torch.argmax(start_logits, dim=1)[0]
            end_idx = torch.argmax(end_logits, dim=1)[0]
            
            # Get confidence scores
            start_score = torch.softmax(start_logits, dim=1)[0][start_idx].item()
            end_score = torch.softmax(end_logits, dim=1)[0][end_idx].item()
            confidence = (start_score + end_score) / 2
            
            # Get answer text
            answer_tokens = inputs["input_ids"][0][start_idx:end_idx + 1]
            answer = self.qna_tokenizer.decode(answer_tokens)
            
            return answer, confidence
            
        except Exception as e:
            logger.error(f"Error getting answer: {str(e)}")
            raise
            
    def get_hints(self, question: str, context: str, num_hints: int = 3) -> List[str]:
        """
        Generate hints for a question using T5 model.
        
        Args:
            question (str): The question to generate hints for
            context (str): The context to generate hints from
            num_hints (int): Number of hints to generate
            
        Returns:
            List[str]: List of generated hints
        """
        try:
            # Prepare input for T5
            input_text = f"hint: {question} context: {context}"
            inputs = self.hint_tokenizer(
                input_text,
                return_tensors="pt",
                max_length=128,
                truncation=True,
                padding=True
            ).to(self.device)
            
            # Generate hints
            with torch.no_grad():
                outputs = self.hint_model.generate(
                    **inputs,
                    max_length=32,
                    num_return_sequences=num_hints,
                    temperature=0.7,
                    do_sample=True
                )
            
            # Decode hints
            hints = [
                self.hint_tokenizer.decode(output, skip_special_tokens=True)
                for output in outputs
            ]
            
            return hints
            
        except Exception as e:
            logger.error(f"Error generating hints: {str(e)}")
            raise
            
    def optimize_for_inference(self) -> None:
        """Optimize models for inference on low-resource systems."""
        try:
            # Quantize models
            self.qna_model = torch.quantization.quantize_dynamic(
                self.qna_model, {torch.nn.Linear}, dtype=torch.qint8
            )
            self.hint_model = torch.quantization.quantize_dynamic(
                self.hint_model, {torch.nn.Linear}, dtype=torch.qint8
            )
            
            # Move to CPU if on GPU
            if self.device.type == 'cuda':
                self.qna_model = self.qna_model.cpu()
                self.hint_model = self.hint_model.cpu()
                self.device = torch.device('cpu')
                
            logger.info("Models optimized for inference")
            
        except Exception as e:
            logger.error(f"Error optimizing models: {str(e)}")
            raise 