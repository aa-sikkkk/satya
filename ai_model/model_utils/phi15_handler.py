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
    
    def __init__(self, model_path: str, enable_streaming: bool = False):
        """
        Initialize Phi 1.5 handler.

        Args:
            model_path: Path to model directory containing GGUF file.
            enable_streaming: Whether to request streaming responses when supported.
        """
        self.model_path = Path(model_path)
        self.llm = None
        self.config = self._load_config()
        self.model_file = self._find_model_file()
        self.enable_streaming = enable_streaming
        # Optimized system prompt for speed and accuracy
        self.system_prompt = (
            "You are Satya, a helpful Grade 10 tutor. "
            "Answer the question using the context provided. "
            "Give a detailed explanation in 4-6 sentences (80-120 words). "
            "Be clear, accurate, and educational."
        )
        
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
        
        # Default configuration optimized for ~4GB RAM, CPU-only
        return {
            "n_ctx": 1024,
            "n_threads": max(1, os.cpu_count() // 2 or 1),
            "n_gpu_layers": 0,
            "max_tokens": 180,  # Reduced for faster generation
            "temperature": 0.25,  # Lower for faster, more focused generation
            "top_p": 0.9,
            "repeat_penalty": 1.08,
            "stop": ["</s>", "\n\nContext:", "\n\nQuestion:", "\n\nQ:", "\n\nProvide"],
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
                
    def get_answer(
        self, question: str, context: str, answer_length: str = "medium"
    ) -> Tuple[str, float]:
        """
        Generate detailed answer using optimized prompt template.
        Always uses "medium" length for consistent, detailed responses.

        Args:
            question (str): User's question
            context (str): Relevant context from RAG
            answer_length (str): Ignored - always uses "medium" for detailed answers

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
            
        # Optimized for speed: reduced tokens for faster generation
        max_tokens = 180  # Reduced from 256 for faster responses (still detailed: 3-5 sentences)

        try:
            prompt = self._build_prompt(
                normalized_question,
                context=context,
            )

            start_time = time.time()

            if hasattr(self.llm, "__call__"):  # llama-cpp
                response = self.llm(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=self.config.get("temperature", 0.2),
                    top_p=self.config.get("top_p", 0.9),
                    stop=self.config.get(
                        "stop", ["</s>", "\n\nContext:", "\n\nQuestion:", "\n\nQ:", "\n\nProvide"]
                    ),
                    echo=False,
                    stream=False,  # Disabled for reliability and speed
                    repeat_penalty=self.config.get("repeat_penalty", 1.08),
                )
                # Streamed responses yield generator; non-stream yields dict
                answer = self._extract_text(response)
                logger.debug(f"Raw model response type: {type(response)}")
                logger.debug(f"Extracted answer length: {len(answer) if answer else 0}")
                logger.debug(f"Extracted answer preview: '{answer[:100] if answer else 'None'}...'")

            else:  # fallback
                answer = "Model not properly loaded. Please check llama-cpp-python installation."

            inference_time = time.time() - start_time

            # Clean up answer - be more lenient with extraction
            if not answer:
                answer = ""
            answer = answer.strip()
            
            # Remove common prompt artifacts
            if answer.lower().startswith("answer:"):
                answer = answer[7:].strip()
            if answer.lower().startswith("a:"):
                answer = answer[2:].strip()
            
            # Validate answer quality
            if not answer or len(answer) < 10:
                logger.warning(f"Answer too short or empty: '{answer}'")
                answer = "I couldn't generate a proper answer. Please try rephrasing your question."
            
            # Calculate confidence
            confidence = self._calculate_confidence(answer, context, question)
            
            return answer, confidence
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return "I'm having trouble processing your question. Please try again.", 0.1

    def _build_prompt(self, question: str, context: str) -> str:
        """
        Build optimized prompt template for fast, accurate responses.
        Balanced between speed and clarity for Phi 1.5.
        """
        # Trim context aggressively for speed (600 chars max for faster processing)
        trimmed_context = (context or "").strip()
        if len(trimmed_context) > 600:
            trimmed_context = trimmed_context[:600] + "..."

        # Ultra-optimized template for speed: minimal, direct format
        return (
            f"{self.system_prompt}\n\n"
            f"C: {trimmed_context}\n\n"
            f"Q: {question}\n"
            f"A:"
        )

    def _extract_text(self, response: Any) -> str:
        """
        Extract text from llama-cpp response (non-streaming for reliability).
        """
        if response is None:
            logger.warning("Response is None")
            return ""
        
        # Handle generator (streaming) - consume it properly
        if hasattr(response, "__iter__") and not isinstance(response, (dict, str)):
            # Check if it's a generator
            try:
                import types
                if isinstance(response, types.GeneratorType):
                    parts: List[str] = []
                    for chunk in response:
                        if isinstance(chunk, dict):
                            choice = chunk.get("choices", [{}])[0]
                            delta = choice.get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                parts.append(content)
                    result = "".join(parts).strip()
                    if result:
                        return result
            except Exception as e:
                logger.error(f"Error consuming generator: {e}")
                return ""
        
        # Non-stream call returns dict
        if isinstance(response, dict):
            try:
                if "choices" in response and len(response["choices"]) > 0:
                    choice = response["choices"][0]
                    # Standard llama-cpp format
                    if "text" in choice:
                        text = choice["text"].strip()
                        if text:
                            return text
            except Exception as e:
                logger.error(f"Error extracting from dict: {e}")
        
        # Last resort: log and return empty
        logger.error(f"Could not extract text from response type: {type(response)}")
        return ""
    
            
    def get_hints(self, question: str, context: str) -> List[str]:
        """
        Generate fast hints using Phi 1.5 - optimized for speed.
        
        Args:
            question (str): User's question
            context (str): Relevant context
            
        Returns:
            List[str]: List of helpful hints
        """
        if self.llm is None:
            self.load_model()
            
        try:
            # Better context for relevant hints (500 chars for enough info)
            trimmed_context = (context or "").strip()
            if len(trimmed_context) > 500:
                # Try to get a complete sentence/paragraph, not cut mid-word
                trimmed_context = trimmed_context[:500]
                last_period = trimmed_context.rfind('.')
                if last_period > 400:  # If we have a period near the end, use it
                    trimmed_context = trimmed_context[:last_period + 1]
            
            # Better prompt that guides the model to give relevant hints
            prompt = (
                f"You are a helpful tutor. Based on the context, give 3 specific hints to answer this question.\n\n"
                f"Context: {trimmed_context}\n\n"
                f"Question: {question}\n\n"
                f"Hints (be specific and related to the question):\n"
                f"1."
            )
            
            if hasattr(self.llm, '__call__'):  # llama-cpp
                response = self.llm(
                    prompt,
                    max_tokens=100,  # Slightly more for better hints
                    temperature=0.5,  # Balanced for relevant but creative hints
                    top_p=0.9,
                    stop=["\n4", "4.", "###", "\n\nQuestion:", "\n\nContext:"],
                    echo=False,
                    stream=False
                )
                hints_text = self._extract_text(response)
                
            else:  # fallback
                hints_text = "1. Check the context\n2. Look for key terms\n3. Connect concepts"
            
            # Improved parsing - handle various formats
            hints = []
            lines = hints_text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # Look for numbered hints (1., 2., 3. or 1) 2) 3))
                if line[0].isdigit():
                    # Extract hint after number
                    if '.' in line:
                        parts = line.split('.', 1)
                    elif ')' in line:
                        parts = line.split(')', 1)
                    else:
                        parts = line.split(' ', 1)
                    
                    if len(parts) > 1:
                        hint = parts[1].strip()
                        # Remove common prefixes
                        for prefix in ["Hint:", "•", "-"]:
                            if hint.startswith(prefix):
                                hint = hint[len(prefix):].strip()
                        if hint and len(hint) > 8:  # Minimum length for meaningful hints
                            hints.append(hint)
            
            # Filter out generic/unhelpful hints
            generic_phrases = ["review the context", "look for key terms", "think about", 
                             "consider the", "examine the", "check the"]
            filtered_hints = []
            for hint in hints:
                hint_lower = hint.lower()
                # Skip if it's too generic
                if not any(phrase in hint_lower for phrase in generic_phrases) or len(hint) > 30:
                    filtered_hints.append(hint)
            
            # Ensure we have exactly 3 hints
            if len(filtered_hints) >= 3:
                return filtered_hints[:3]
            elif len(filtered_hints) > 0:
                # Use what we have, don't add generic defaults
                return filtered_hints[:3]
            else:
                # Only use defaults if we got nothing useful
                return [
                    "Review the specific details mentioned in the context.",
                    "Focus on the key concepts related to your question.",
                    "Consider how the information connects to answer the question."
                ]
            
        except Exception as e:
            logger.error(f"Error generating hints: {e}")
            return [
                "Review the context carefully.",
                "Look for key terms and concepts.",
                "Think about how the information connects."
            ]
    
    def _calculate_confidence(self, answer: str, context: str, question: str) -> float:
        """Fast confidence calculation based on answer quality."""
        # Quick error check
        answer_lower = answer.lower()
        if any(phrase in answer_lower for phrase in ["i couldn't", "i'm having trouble", "please try"]):
            return 0.1
        
        # Fast length-based confidence (most answers are 50-150 words)
        word_count = len(answer.split())
        if word_count < 10:
            return 0.3
        elif word_count > 200:
            return 0.8
        else:
            # Good length range - base confidence
            return 0.75
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            'name': 'Phi 1.5',
            'version': '1.0',
            'format': 'GGUF',
            'context_size': self.config.get('n_ctx', 2048),
            'threads': self.config.get('n_threads', 2),
            'max_tokens': self.config.get('max_tokens', 512),
            'temperature': self.config.get('temperature', 0.2),
            'top_p': self.config.get('top_p', 0.9),
            'repeat_penalty': self.config.get('repeat_penalty', 1.08),
            'model_path': str(self.model_file),
            'quantization': Path(self.model_file).name,
        }
    
    def cleanup(self):
        """Clean up model resources."""
        if self.llm is not None:
            del self.llm
            self.llm = None 