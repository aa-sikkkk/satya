#!/usr/bin/env python3
"""
Phi 1.5 Handler for Satya Learning System

Lightweight, efficient handler for Microsoft's Phi 1.5 model.
Optimized for low-end hardware with single model for all tasks.
"""

import os
import json
import logging
import time
from typing import Tuple, List, Dict, Any, Optional
from pathlib import Path

# Try to import llama-cpp-python
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    CT_AVAILABLE = False

logger = logging.getLogger(__name__)

class Phi15Handler:
    """
    Lightweight handler for Phi 1.5 model.
    Handles Q&A, hints, and content generation in one efficient model.
    """
    
    def __init__(self, model_path: str):
        """
        Initialize Phi 1.5 handler.
        
        Args:
            model_path (str): Path to model directory containing GGUF file
        """
        self.model_path = Path(model_path)
        self.llm = None
        self.config = self._load_config()
        self.model_file = self._find_model_file()
        
    def _find_model_file(self) -> str:
        """Find the model file (GGUF or other format)."""
        # Look for GGUF first
        for file in self.model_path.iterdir():
            if file.suffix == ".gguf":
                return str(file)
        
        # Look for other formats
        for file in self.model_path.iterdir():
            if file.suffix in [".bin", ".model", ".ggml"]:
                return str(file)
                
        raise FileNotFoundError(f"No model file found in {self.model_path}")
    
    def _load_config(self) -> dict:
        """Load model configuration."""
        config_path = self.model_path / "config.json"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        # Default configuration optimized for low-end hardware
        return {
            'n_ctx': 2048,          # Context window
            'n_threads': 2,          # Conservative thread count
            'n_gpu_layers': 0,       # CPU only
            'max_tokens': 256,       # Increased for better responses
            'temperature': 0.3,      # Lower for more focused answers
            'top_p': 0.9,            # Nucleus sampling
            'stop': ["\n\n", "###", "Question:", "Context:", "Answer:"]  # Better stop sequences
        }
            
    def load_model(self) -> None:
        """Load the model using available backend."""
        if self.llm is not None:
            return
            
        try:

            start_time = time.time()
            
            if LLAMA_AVAILABLE:
                # Use llama-cpp-python (most efficient)
                self.llm = Llama(
                    model_path=self.model_file,
                    n_ctx=self.config.get('n_ctx', 2048),
                    n_threads=self.config.get('n_threads', 2),
                    n_gpu_layers=self.config.get('n_gpu_layers', 0),
                    verbose=False
                )
                backend = "llama-cpp"
                
            else:
                raise ImportError("No compatible backend available. Install llama-cpp-python.")
            
            load_time = time.time() - start_time
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
                
    def get_answer(self, question: str, context: str, answer_length: str = "medium") -> Tuple[str, float]:
        """
        Generate answer using Phi 1.5 with length control.
        
        Args:
            question (str): User's question
            context (str): Relevant context from RAG
            answer_length (str): "very_short", "short", "medium", "long", "very_long"
            
        Returns:
            Tuple[str, float]: Answer and confidence score
        """
        if self.llm is None:
            self.load_model()
            
        # Normalize question text for better model performance
        normalized_question = question.strip()
        if normalized_question.isupper():
            normalized_question = normalized_question.lower().capitalize()
        elif normalized_question.islower():
            normalized_question = normalized_question.capitalize()
            
        # Configure answer length parameters
        length_config = self._get_length_config(answer_length)
            
        try:
            # Optimized prompt for Phi 1.5 with length control
            prompt = (
                "You are a helpful AI tutor for Grade 10 students. "
                "Answer the question clearly and in detail, regardless of how it's written. "
                "Use the context provided to give an accurate and educational response.\n\n"
                "Answer Length: {length_instruction}\n\n"
                "Context: {context}\n\n"
                "Question: {question}\n\n"
                "Answer:"
            ).format(
                length_instruction=length_config['instruction'],
                context=context[:1500], 
                question=normalized_question
            )
            
            start_time = time.time()
            
            if hasattr(self.llm, '__call__'):  # llama-cpp
                response = self.llm(
                    prompt,
                    max_tokens=length_config['max_tokens'],  # Use length-specific token limit
                    temperature=self.config.get('temperature', 0.3),  # Lower for more focused answers
                    top_p=self.config.get('top_p', 0.9),
                    stop=self.config.get('stop', ["\n\n", "###", "Question:", "Context:", "Answer:"]),  # Better stop sequences
                    echo=False,
                    stream=False
                )
                answer = response['choices'][0]['text'].strip()
                logger.debug(f"Raw model response: '{response}'")
                logger.debug(f"Extracted answer: '{answer}'")
                
            else:  # fallback
                answer = "Model not properly loaded. Please check llama-cpp-python installation."
            
            inference_time = time.time() - start_time
            
            # Clean up answer
            if not answer or len(answer.strip()) == 0:
                answer = "I couldn't generate a proper answer. Please try rephrasing your question."
            elif len(answer.strip()) < 5:  # Reduced from 10 to allow valid short answers
                answer = "I couldn't generate a proper answer. Please try rephrasing your question."
            elif answer.lower().startswith("answer:"):  # Remove prompt artifacts
                answer = answer[8:].strip()
                if not answer or len(answer.strip()) < 5:
                    answer = "I couldn't generate a proper answer. Please try rephrasing your question."
            
            # Calculate confidence
            confidence = self._calculate_confidence(answer, context, question)
            
            return answer, confidence
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return "I'm having trouble processing your question. Please try again.", 0.1
    
    def _get_length_config(self, answer_length: str) -> dict:
        """Get configuration for different answer lengths."""
        length_configs = {
            "very_short": {
                "instruction": "Give a very brief, one-sentence answer (10-20 words). Focus on the core concept only.",
                "max_tokens": 64,
                "description": "Quick fact or definition"
            },
            "short": {
                "instruction": "Give a concise answer in 2-3 sentences (30-50 words). Include key points and basic explanation.",
                "max_tokens": 128,
                "description": "Basic explanation with key points"
            },
            "medium": {
                "instruction": "Give a detailed answer in 4-6 sentences (80-120 words). Include explanation, examples, and important details.",
                "max_tokens": 256,
                "description": "Detailed explanation with examples"
            },
            "long": {
                "instruction": "Give a comprehensive answer in 8-12 sentences (150-250 words). Include detailed explanation, multiple examples, and step-by-step breakdown.",
                "max_tokens": 512,
                "description": "Comprehensive coverage with examples"
            },
            "very_long": {
                "instruction": "Give an extensive answer in 15-20 sentences (300-500 words). Include comprehensive coverage, multiple perspectives, detailed examples, and thorough explanation.",
                "max_tokens": 1024,
                "description": "Extensive coverage with multiple perspectives"
            }
        }
        
        return length_configs.get(answer_length, length_configs["medium"])
            
    def get_hints(self, question: str, context: str) -> List[str]:
        """
        Generate hints using Phi 1.5.
        
        Args:
            question (str): User's question
            context (str): Relevant context
            
        Returns:
            List[str]: List of helpful hints
        """
        if self.llm is None:
            self.load_model()
            
        # Normalize question text for better model performance
        normalized_question = question.strip()
        if normalized_question.isupper():
            normalized_question = normalized_question.lower().capitalize()
        elif normalized_question.islower():
            normalized_question = normalized_question.capitalize()
            
        try:
            # Optimized prompt for hints
            prompt = (
                "Context: {context}\n\n"
                "Question: {question}\n\n"
                "Generate 3 short, helpful hints to answer this question:\n"
                "1."
            ).format(context=context[:1000], question=normalized_question)  # Use normalized question
            
            if hasattr(self.llm, '__call__'):  # llama-cpp
                response = self.llm(
                    prompt,
                    max_tokens=150,
                    temperature=0.8,  # Slightly higher for creativity
                    top_p=0.95,
                    stop=["\n4", "###"],
                    echo=False,
                    stream=False
                )
                hints_text = response['choices'][0]['text'].strip()
                
            else:  # fallback
                hints_text = "1. Check the context carefully.\n2. Look for key terms.\n3. Connect related concepts."
            
            # Parse hints
            hints = []
            for line in hints_text.split('\n'):
                line = line.strip()
                if line and line[0].isdigit() and '.' in line:
                    hint = line.split('.', 1)[1].strip()
                    if hint and len(hint) > 10:  # Filter out very short hints
                        hints.append(hint)
            
            # Ensure we have exactly 3 hints
            if len(hints) > 3:
                hints = hints[:3]
            elif len(hints) < 3:
                # Add default hints if needed
                default_hints = [
                    "Look for key terms in the context that relate to the question.",
                    "Think about how different concepts in the context connect to each other.",
                    "Identify the main idea or purpose mentioned in the context."
                ]
                for i in range(3 - len(hints)):
                    hints.append(default_hints[i])
            
            return hints
            
        except Exception as e:
            logger.error(f"Error generating hints: {e}")
            return [
                "Break the question into smaller parts.",
                "Look for clues in the provided context.",
                "Connect what you know to the new information."
            ]
    
    def _calculate_confidence(self, answer: str, context: str, question: str) -> float:
        """Calculate confidence score based on answer quality."""
        # Check if answer is an error message or invalid
        error_phrases = [
            "i couldn't generate a proper answer",
            "i'm having trouble processing",
            "please try rephrasing",
            "model not properly loaded",
            "check llama-cpp-python installation"
        ]
        
        answer_lower = answer.lower()
        if any(phrase in answer_lower for phrase in error_phrases):
            return 0.1  # Very low confidence for error messages
        
        # Base confidence
        confidence = 0.7
        
        # Adjust based on answer length
        word_count = len(answer.split())
        if word_count < 5:
            confidence *= 0.6
        elif word_count > 100:
            confidence *= 0.8
        else:
            confidence += min(0.2, word_count * 0.01)
        
        # Adjust based on content relevance
        question_words = set(question.lower().split())
        answer_words = set(answer.lower().split())
        overlap = len(question_words.intersection(answer_words))
        if overlap > 0:
            confidence += min(0.1, overlap * 0.02)
        
        # Adjust based on context usage
        if any(word in answer.lower() for word in context.lower().split()[:20]):
            confidence += 0.1
        
        # Ensure confidence is within bounds
        return max(0.1, min(0.95, confidence))
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            'name': 'Phi 1.5',
            'version': '1.0',
            'format': 'GGUF',
            'context_size': self.config.get('n_ctx', 2048),
            'threads': self.config.get('n_threads', 2),
            'max_tokens': self.config.get('max_tokens', 128),
            'temperature': self.config.get('temperature', 0.7),
            'top_p': self.config.get('top_p', 0.9),
            'model_path': str(self.model_file)
        }
    
    def cleanup(self):
        """Clean up model resources."""
        if self.llm is not None:
            del self.llm
            self.llm = None 