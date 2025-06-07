"""
Model Handler Module

This module provides utilities for loading and using the trained models
for educational content question answering and hint generation.
Optimized for low-resource systems with CPU-only operation.
"""

import os
import torch
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForQuestionAnswering,
    T5Tokenizer,
    T5ForConditionalGeneration,
    AutoModelForQuestionAnswering,
    AutoTokenizer
)
from typing import Dict, List, Tuple, Optional
import logging
import sys

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "nebedu.log")

# Remove any existing handlers
logger = logging.getLogger(__name__)
logger.handlers = []

# Create file handler
file_handler = logging.FileHandler(log_file, mode='w')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Add only file handler to logger
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)

# Log startup with more details
logger.info("="*50)
logger.info("Starting NEBedu model handler (CPU-only mode)")
logger.info(f"Log file location: {log_file}")
logger.info(f"PyTorch version: {torch.__version__}")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info("="*50)

class ModelHandler:
    """
    Handles loading and inference with the trained models.
    Optimized for CPU-only operation on low-resource systems.
    
    Attributes:
        model_path (str): Path to the saved model
        device (torch.device): Device to run inference on (CPU only)
        qna_model (DistilBertForQuestionAnswering): QnA model
        hint_model (T5ForConditionalGeneration): Hint generation model
        qna_tokenizer (DistilBertTokenizerFast): QnA tokenizer
        hint_tokenizer (T5Tokenizer): Hint generation tokenizer
    """
    
    def __init__(self, model_path: str = "ai_model/exported_model"):
        """
        Initialize the model handler.
        
        Args:
            model_path (str): Path to the saved model directory
        """
        self.model_path = model_path
        self.device = torch.device('cpu')  # Force CPU-only operation
        self.qna_model = None
        self.hint_model = None
        self.qna_tokenizer = None
        self.hint_tokenizer = None
        
        # Set PyTorch to use CPU threads efficiently
        torch.set_num_threads(os.cpu_count() or 1)
        torch.set_num_interop_threads(1)
        
        logger.info(f"Using {torch.get_num_threads()} CPU threads")
        self._load_models()
        
    def _load_models(self) -> None:
        """Load the models and tokenizers from disk with CPU optimization."""
        try:
            logger.info(f"Loading models from ai_model/exported_model/qna and ai_model/exported_model/hint")
            qna_path = "ai_model/exported_model/qna"
            hint_path = "ai_model/exported_model/hint"
            if not os.path.exists(qna_path):
                raise FileNotFoundError(f"QnA model not found at {qna_path}")
            if not os.path.exists(hint_path):
                raise FileNotFoundError(f"Hint model not found at {hint_path}")
            logger.info(f"Loading QnA model from {qna_path}")
            try:
                # Load model with proper configuration
                self.qna_model = DistilBertForQuestionAnswering.from_pretrained(
                    qna_path,
                    local_files_only=True
                )
                self.qna_tokenizer = DistilBertTokenizerFast.from_pretrained(
                    qna_path,
                    local_files_only=True
                )
                
                # Move model to CPU and set to eval mode
                self.qna_model = self.qna_model.cpu()
                self.qna_model.eval()
                
                # Log model configuration
                logger.info(f"QnA model configuration: {self.qna_model.config}")
                logger.info(f"QnA model type: {type(self.qna_model)}")
                
                # Verify model structure
                if not hasattr(self.qna_model, 'distilbert'):
                    raise RuntimeError("Model missing distilbert attribute")
                
                logger.info("QnA model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading QnA model: {str(e)}")
                raise RuntimeError(f"Failed to load QnA model: {str(e)}")
            
            logger.info(f"Loading Hint model from {hint_path}")
            try:
                self.hint_model = T5ForConditionalGeneration.from_pretrained(
                    hint_path,
                    local_files_only=True
                )
                self.hint_tokenizer = T5Tokenizer.from_pretrained(
                    hint_path,
                    local_files_only=True
                )
                
                # Move model to CPU and set to eval mode
                self.hint_model = self.hint_model.cpu()
                self.hint_model.eval()
                
                logger.info("Hint model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading Hint model: {str(e)}")
                raise RuntimeError(f"Failed to load Hint model: {str(e)}")
            
            logger.info("All models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            raise RuntimeError(f"Failed to initialize models: {str(e)}")
            
    def _prepare_qna_input(self, question: str, context: str) -> Dict[str, torch.Tensor]:
        """
        Prepare input for QnA model inference.
        
        Args:
            question (str): The question to answer
            context (str): The context to find the answer in
            
        Returns:
            Dict[str, torch.Tensor]: Tokenized input
        """
        try:
            # Ensure inputs are strings
            question = str(question).strip()
            context = str(context).strip()
            
            if not question or not context:
                raise ValueError("Question and context must not be empty")
                
            # Tokenize with error handling
            inputs = self.qna_tokenizer(
                question,
                context,
                return_tensors="pt",
                max_length=512,
                truncation=True,
                padding=True
            )
            
            # Move to CPU
            return {k: v.to(self.device) for k, v in inputs.items()}
            
        except Exception as e:
            logger.error(f"Error in _prepare_qna_input: {str(e)}")
            raise
        
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
            if not self.qna_model or not self.qna_tokenizer:
                logger.error("QnA model not loaded")
                return "I'm having trouble processing your question. Please try again.", 0.0
                
            # Prepare input with error handling
            try:
                # Ensure inputs are strings and not empty
                question = str(question).strip()
                context = str(context).strip()
                
                if not question or not context:
                    logger.error("Empty question or context")
                    return "Please provide both a question and context.", 0.0
                
                # Tokenize with error handling
                inputs = self.qna_tokenizer(
                    question,
                    context,
                    return_tensors="pt",
                    max_length=512,
                    truncation=True,
                    padding=True
                )
                
                logger.info(f"Input shape: {inputs['input_ids'].shape}")
                logger.info(f"Question: {question}")
                logger.info(f"Context length: {len(context)}")
                
            except Exception as e:
                logger.error(f"Error preparing input: {str(e)}")
                return "I'm having trouble understanding your question. Please try rephrasing it.", 0.0
            
            # Get model prediction with error handling
            try:
                with torch.no_grad():
                    # Ensure model is in eval mode
                    self.qna_model.eval()
                    
                    # Run inference
                    outputs = self.qna_model(**inputs)
                    logger.info(f"Output type: {type(outputs)}")
                    
                    # Get start and end logits
                    start_logits = outputs.start_logits
                    end_logits = outputs.end_logits
                    
                    logger.info(f"Start logits shape: {start_logits.shape}")
                    logger.info(f"End logits shape: {end_logits.shape}")
                    
                    # Get most likely start and end positions
                    start_idx = torch.argmax(start_logits, dim=1)[0]
                    end_idx = torch.argmax(end_logits, dim=1)[0]
                    
                    logger.info(f"Start index: {start_idx}, End index: {end_idx}")
                    
                    # Get confidence scores
                    start_score = torch.softmax(start_logits, dim=1)[0][start_idx].item()
                    end_score = torch.softmax(end_logits, dim=1)[0][end_idx].item()
                    confidence = (start_score + end_score) / 2
                    
                    logger.info(f"Confidence scores - Start: {start_score:.4f}, End: {end_score:.4f}, Avg: {confidence:.4f}")
                    
                    # Validate indices
                    if start_idx >= end_idx:
                        logger.warning("Invalid answer span: start_idx >= end_idx")
                        return "I couldn't find a specific answer in the context.", 0.0
                    
                    if start_idx >= len(inputs["input_ids"][0]) or end_idx >= len(inputs["input_ids"][0]):
                        logger.warning("Answer span outside input length")
                        return "I couldn't find a specific answer in the context.", 0.0
                    
                    # Get answer text
                    answer_tokens = inputs["input_ids"][0][start_idx:end_idx + 1]
                    answer = self.qna_tokenizer.decode(answer_tokens)
                    
                    # Clean up answer
                    answer = answer.strip()
                    if not answer:
                        logger.warning("Empty answer generated")
                        return "I couldn't find a specific answer in the context.", 0.0
                    
                    # Check if answer is too short or too long
                    if len(answer.split()) < 2:
                        logger.warning("Answer too short")
                        return "I couldn't find a specific answer in the context.", 0.0
                    
                    if len(answer.split()) > 50:
                        logger.warning("Answer too long")
                        return "I couldn't find a specific answer in the context.", 0.0
                    
                    logger.info(f"Generated answer: {answer}")
                    return answer, confidence
                    
            except Exception as e:
                logger.error(f"Error during model inference: {str(e)}")
                return "I'm having trouble processing your question. Please try again.", 0.0
            
        except Exception as e:
            logger.error(f"Unexpected error in get_answer: {str(e)}")
            return "I'm having trouble processing your question. Please try again.", 0.0
            
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
            if not self.hint_model or not self.hint_tokenizer:
                raise RuntimeError("Hint model not loaded")
                
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
            
            # Clean up hints
            hints = [hint.strip() for hint in hints if hint.strip()]
            if not hints:
                return ["Try breaking down the question into smaller parts.",
                       "Review the related concepts in your study materials.",
                       "Look for examples in your textbook."]
                
            return hints
            
        except Exception as e:
            logger.error(f"Error generating hints: {str(e)}")
            return ["Try breaking down the question into smaller parts.",
                   "Review the related concepts in your study materials.",
                   "Look for examples in your textbook."]
            
    def optimize_for_inference(self) -> None:
        """Optimize models for CPU inference on low-resource systems."""
        try:
            # Quantize models for CPU
            self.qna_model = torch.quantization.quantize_dynamic(
                self.qna_model,
                {torch.nn.Linear},
                dtype=torch.qint8
            )
            self.hint_model = torch.quantization.quantize_dynamic(
                self.hint_model,
                {torch.nn.Linear},
                dtype=torch.qint8
            )
            
            # Set models to eval mode and disable gradient computation
            self.qna_model.eval()
            self.hint_model.eval()
            torch.set_grad_enabled(False)
            
            # Clear CUDA cache if it exists (shouldn't be used but just in case)
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info("Models optimized for CPU inference")
            
        except Exception as e:
            logger.error(f"Error optimizing models: {str(e)}")
            # Continue without optimization
            logger.info("Continuing without model optimization") 