#!/usr/bin/env python3
"""
Phi 1.5 Handler for Satya Learning System

Lightweight, efficient handler for Microsoft's Phi 1.5 model.
Optimized for low-end hardware with single model for all tasks.
"""

import os
import sys

# MINIMAL Windows memory safety
if sys.platform == "win32":
    os.environ["LLAMA_CPP_MLOCK"] = "0"  # Prevent memory locking
    os.environ["OMP_NUM_THREADS"] = "4"  
    
import json
import logging
import re
import time
from typing import Tuple, List, Dict, Any, Optional, Iterator
from pathlib import Path

# Try to import llama-cpp-python
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False

logger = logging.getLogger(__name__)

class Phi15Handler:
    """
    Satya personality + Windows compatible
    """
    
    # Essential stop sequences for quality + speed balance
    STOP_SEQUENCES = [
        "</s>",  # Model's end token (critical)
        "\n\nQuestion:",  # Question format (prevent prompt leakage)
        "\nQuestion:",  # Question format (prevent prompt leakage)
        "\n\nQ:", 
        "\nQ:", 
        "\n\nAnswer:", 
        "\nAnswer:", 
        "\n\nA:",  
        "\nA:",  
        "\n\nExercise:",  
        "\n\nPractice:", 
        "\n\nNow, let's",  
        "\n\nExplanation:",  
        "\n\nIn summary", 
        "\n\nDiagram:",  # Diagram patterns (prevent ASCII art)
        "\nDiagram:",  
        "\n┌",  
        "\n│",  
        "\n└",  
        "\n1.",  
        "\n2.",  
        "\n3.",  
    ]
    
    # Dynamic token limits based on question complexity
    # Base token limit - will be adjusted based on question type
    BASE_MAX_TOKENS = 80
    
    def __init__(self, model_path: str, enable_streaming: bool = False):
        """
        Initialize with SATYA PERSONALITY.
        """
        self.model_path = Path(model_path)
        self.llm = None
        self.config = self._load_config()
        self.model_file = self._find_model_file()
        self.enable_streaming = enable_streaming
        
    
        # Educational focus: Helpful, detailed answers for student learning
        self.system_prompt = (
            "You are Satya, an expert tutor for Grade 8-12 students in Nepal (NEB curriculum). "
            "Your goal is to help students learn and understand. "
            "Provide clear, detailed explanations that directly answer the question. "
            "Be thoughtful - consider what information is most important for understanding the concept. "
            "Adjust answer length based on question type: "
            "- Simple definitions: 2-3 sentences "
            "- Explanations and descriptions: 4-6 sentences with examples "
            "- Complex topics: 5-8 sentences with detailed explanations "
            "CRITICAL: Always finish each sentence completely with proper punctuation (., !, or ?). "
            "Never cut off mid-sentence. Be educational, helpful, and thorough. "
            "NEVER add: Question:, Answer:, Q:, A:, exercises, diagrams, ASCII art (┌, │, └), numbered lists. "
            "Give complete, educational answers that help students learn."
        )
        
    def _find_model_file(self) -> str:
        """ Model finding logic."""
        for file in self.model_path.iterdir():
            if file.suffix == ".gguf":
                logger.info(f"Found model: {file.name}")
                return str(file)
        raise FileNotFoundError(f"No model file found in {self.model_path}")
    
    def _load_config(self) -> dict:
        """Configuration."""
        config_path = self.model_path / "config.json"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        return {
            "n_ctx": 512,                     # Increased for longer, more detailed educational answers
            "n_threads": max(1, os.cpu_count() // 2 or 1),  # threading
            "n_gpu_layers": 0,
            "max_tokens": 80,                 # Base token limit - adjusted dynamically
            "temperature": 0.4,              # Slightly higher for creativity
            "top_p": 0.92,                    # Slightly relaxed for variety
            "repeat_penalty": 1.06,           
            "stop": ["</s>", "\n\nContext:", "\n\nQuestion:", "\n\nQ:"],  # Removed "\n\nProvide" to avoid stopping on prompt
        }
            
    def load_model(self) -> None:
        """Load model with MINIMAL Windows fix - preserve Satya personality."""
        if self.llm is not None:
            return
            
        try:
            start_time = time.time()
            
            if LLAMA_AVAILABLE:
                
                self.llm = Llama(
                    model_path=self.model_file,
                    n_ctx=self.config.get('n_ctx', 512),      # Increased for longer answers
                    n_threads=self.config.get('n_threads', 4),
                    n_batch=512,           # Batch size for prompt processing
                    n_gpu_layers=self.config.get('n_gpu_layers', 0),
                    use_mmap=True,         
                    use_mlock=False,       
                    verbose=False            
                )
                logger.info(f"Model loaded successfully in {time.time() - start_time:.2f}s")
            else:
                raise ImportError("llama-cpp-python not available")
            
        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            raise RuntimeError(f"Could not load Phi 1.5 model: {e}")
    
    def _calculate_max_tokens(self, question: str, context: str) -> int:
        """
        Dynamically calculate max_tokens based on question complexity.
        
        Args:
            question: Student's question
            context: RAG context (if available)
            
        Returns:
            Appropriate max_tokens value
        """
        # Base tokens - adjusted based on question type
        base_tokens = self.BASE_MAX_TOKENS
        
        # Adjust based on question length
        question_words = len(question.split())
        if question_words > 15:
            base_tokens += 30  # Complex questions need more tokens
        elif question_words > 8:
            base_tokens += 15  # Medium questions
        # Short questions stay at base
        
        # Adjust based on question type - more generous for explanatory questions
        question_lower = question.lower()
        if any(word in question_lower for word in ["explain", "describe", "discuss", "analyze", "how does", "how do"]):
            base_tokens += 40  # Explanatory questions need detailed answers
        elif any(word in question_lower for word in ["what is", "define", "what are"]):
            base_tokens += 15  # Definition questions need clear explanations
        elif any(word in question_lower for word in ["compare", "difference", "similarities"]):
            base_tokens += 35  # Comparison questions need more detail
        
        # If RAG context is available, might need more tokens to incorporate it
        if context and len(context.strip()) > 50:
            base_tokens += 20
            # Cap at reasonable maximum for context-based answers
            return min(base_tokens, 150)
        else:
            # No context (fallback) - allow enough tokens for 2-4 complete sentences
            # Let the model generate naturally but with a reasonable limit
            # 80-100 tokens should allow 2-4 sentences without cutting off
            return min(base_tokens, 100)
                
    def get_answer(self, question: str, context: str, answer_length: str = "medium") -> Tuple[str, float]:
        """
        Generate answer using RAG context when available, otherwise use Phi's own knowledge.
        
        Args:
            question: Student's question
            context: RAG context (can be empty/minimal - Phi will use own knowledge)
            answer_length: Deprecated - kept for API compatibility, not used
            
        Returns:
            Tuple of (answer, confidence)
        """
        if self.llm is None:
            self.load_model()
            
        # Input validation - allow empty context (Phi will use own knowledge)
        if not question or len(question.strip()) < 3:
            return "Please provide a question about your Grade 8-12 curriculum.", 0.1
        
        # Ensure context is a string (handle None case)
        if context is None:
            context = ""
            
        # Question normalization
        normalized_question = question.strip()
        if normalized_question.isupper():
            normalized_question = normalized_question.lower().capitalize()
        elif normalized_question.islower():
            normalized_question = normalized_question.capitalize()
        if len(normalized_question) < 3:
            return "Please provide a more detailed question.", 0.1
            
        try:
            # Prompt building
            prompt = self._build_prompt(normalized_question, context)
            
            # Log prompt for debugging
            logger.info(f"Full prompt length: {len(prompt)}")
            logger.info(f"Prompt (first 500 chars): {prompt[:500]}")
            logger.info(f"Prompt (last 200 chars): {prompt[-200:]}")
            logger.info(f"Question: {normalized_question}, Context length: {len(context) if context else 0}")
            logger.info(f"Stop sequences: {self.STOP_SEQUENCES[:5]}... (showing first 5)")
            
            # Check if model is loaded
            if self.llm is None:
                logger.error("Model not loaded for non-streaming inference!")
                return "Error: Model not loaded. Please check model files.", 0.1
            
            # Calculate max_tokens based on context (shorter for fallback)
            max_tokens = self._calculate_max_tokens(normalized_question, context)
            
            # Try inference with logging - use more permissive parameters
            logger.info(f"Calling model with max_tokens={max_tokens}, temperature=0.7")
            response = self.llm(
                prompt,
                max_tokens=max_tokens,  
                temperature=0.7,  # Increased for better generation
                top_p=0.9,  # More permissive
                repeat_penalty=1.1, 
                stop=self.STOP_SEQUENCES, 
                echo=False,
                stream=False
            )
            
            # Log raw response for debugging
            logger.info(f"Raw response type: {type(response)}")
            if isinstance(response, dict):
                logger.info(f"Response keys: {list(response.keys())}")
                if "choices" in response:
                    choices = response.get('choices', [])
                    logger.info(f"Choices count: {len(choices)}")
                    if len(choices) > 0:
                        logger.info(f"First choice keys: {list(choices[0].keys()) if isinstance(choices[0], dict) else 'Not a dict'}")
                        logger.info(f"First choice type: {type(choices[0])}")
                        if isinstance(choices[0], dict):
                            for key in choices[0].keys():
                                value = choices[0][key]
                                if isinstance(value, str):
                                    logger.info(f"  {key}: {value[:100]}...")
                                else:
                                    logger.info(f"  {key}: {type(value)}")
            
            answer = self._extract_text(response)
            logger.info(f"Extracted answer length: {len(answer) if answer else 0}")
            if answer:
                logger.info(f"Extracted answer (first 200 chars): {answer[:200]}...")
            else:
                logger.warning("Extracted answer is empty or None!")
            
            # Answer validation
            if not answer or len(answer.strip()) < 10:
                logger.warning(f"Answer too short or empty. Length: {len(answer) if answer else 0}, Content: {answer}")
                return "I couldn't generate a proper response. Please try rephrasing your question.", 0.1
            
            # Answer cleaning - remove prompt echoes and formatting
            answer = answer.strip()
            
            # Remove common prompt echoes
            if answer.lower().startswith("answer:"):
                answer = answer[7:].strip()
            if answer.lower().startswith("a:"):
                answer = answer[2:].strip()
            if answer.lower().startswith("q:"):
                # If it starts with Q:, it's echoing the prompt - find the actual answer
                if "\n\n" in answer:
                    parts = answer.split("\n\n")
                    # Find the part that looks like an answer (not a question)
                    for part in parts:
                        if not part.strip().lower().startswith("q:") and len(part.strip()) > 10:
                            answer = part.strip()
                            break
            
            # Remove any Q: or A: patterns from the answer
            answer = re.sub(r'^Q:\s*', '', answer, flags=re.IGNORECASE | re.MULTILINE)
            answer = re.sub(r'^A:\s*', '', answer, flags=re.IGNORECASE | re.MULTILINE)
            answer = re.sub(r'\nQ:\s*', '\n', answer, flags=re.IGNORECASE)
            answer = re.sub(r'\nA:\s*', '\n', answer, flags=re.IGNORECASE)
            
            # Remove off-topic content if it slips through (comprehensive cleanup)
            off_topic_markers = [
                # Exercise/practice patterns
                "\n\nExercise:", "\nExercise:", "Exercise:",
                "\n\nPractice:", "\nPractice:", "Practice:",
                "\n\nTry this:", "\nTry this:", "Try this:",
                "\n\nNow try", "\nNow try",
                # Use case/real-world patterns
                "\n\nNow, let's", "\nNow, let's", "Now, let's",
                "\n\nLet's explore", "\nLet's explore", "Let's explore",
                "\n\nUse Case", "\nUse Case", "Use Case",
                "\n\nReal-world", "\nReal-world", "Real-world",
                "\n\nAnother example", "\nAnother example", "Another example",
                # Continuation patterns
                "\n\nAdditionally,", "\nAdditionally,",
                "\n\nFurthermore,", "\nFurthermore,",
                "\n\nMoreover,", "\nMoreover,",
                # Explanation/elaboration patterns (prevent repetitive explanations)
                "\n\nExplanation:", "\nExplanation:", "Explanation:",
                "\nExplanation", "\n\nExplanation",
                "\n\nIn summary", "\nIn summary",
                "\n\nTo summarize", "\nTo summarize",
                "\n\nIn other words", "\nIn other words",
                "\n\nSimilarly,", "\nSimilarly,",
                # Numbered list patterns (prevent lists)
                "\n1.", "\n2.", "\n3.", "\n4.", "\n5.", "\n6.",
                "\n\n1.", "\n\n2.", "\n\n3.", "\n\n4.",
                "\n1 ", "\n2 ", "\n3 ", "\n4 ",
                # Diagram/visualization patterns (prevent verbosity after answer)
                "\n\nDiagram:", "\nDiagram:", "Diagram:",
                "\nDiagram", "\n\nDiagram",
                # Box-drawing character patterns (ASCII art diagrams)
                "\n┌", "\n│", "\n└", "\n├",
                "\n\n┌", "\n\n│", "\n\n└", "\n\n├",
            # Reference context patterns (when model starts explaining the prompt structure)
            "\n\nReference Context", "\nReference Context",
            "\n\nReference material", "\nReference material",
            "\n\nStudy material", "\nStudy material",
            "\n\nStudent Question", "\nStudent Question",
            "\n\nQuestion:", "\nQuestion:", "Question:",
            "\n\nAnswer:", "\nAnswer:", "Answer:",
            "\n\nAnswer using the study material", "\nAnswer using the study material",
            "\n\nIMPORTANT:", "\nIMPORTANT:",
            "IMPORTANT:",
            # Prompt echo patterns (prevent Q:/A: format in output)
            "\nQ:", "\n\nQ:", "Q:",
            "\nA:", "\n\nA:", "A:",
            ]
            for marker in off_topic_markers:
                if marker in answer:
                    # Split at the marker and keep only the part before it
                    answer = answer.split(marker)[0].strip()
                    logger.debug(f"Removed off-topic content after {marker}")
                    break
            
            # Remove numbered lists if they appear (convert to flowing sentences)
            if answer:
                # Pattern: "1. Text" or "1 Text" -> remove numbering
                answer = re.sub(r'^\d+\.\s*', '', answer, flags=re.MULTILINE)  # Remove "1. " at start of lines
                answer = re.sub(r'\n\d+\.\s*', '. ', answer)  # Replace "\n2. " with ". "
                answer = re.sub(r'\n\d+\s+', '. ', answer)  # Replace "\n2 " with ". "
                # Clean up multiple spaces
                answer = re.sub(r'\s+', ' ', answer)
                answer = answer.strip()
            
            # Remove any Q:/A: echo patterns that might remain
            if "\nQ:" in answer or "\nA:" in answer or answer.startswith("Q:") or answer.startswith("A:"):
                # Split on Q: or A: and take only the actual answer part
                parts = re.split(r'\n?[QA]:\s*', answer, flags=re.IGNORECASE)
                # Find the longest part that looks like an answer (not a question)
                best_part = ""
                for part in parts:
                    part = part.strip()
                    # Skip if it looks like a question (ends with ?) or is too short
                    if len(part) > len(best_part) and not part.endswith("?") and len(part) > 10:
                        best_part = part
                if best_part:
                    answer = best_part.strip()
            
            # Allow comprehensive answers (4-6 sentences) for educational value
            # CRITICAL: Never cut off mid-sentence - always ensure completeness
            if answer:
                # Split on sentence endings, but preserve abbreviations
                sentences = re.split(r'(?<=[.!?])\s+', answer)
                sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
                
                # Only trim if we have more than 6 complete sentences
                if len(sentences) > 6:
                    # Check if the 6th sentence is complete
                    if sentences[5].endswith(('.', '!', '?')):
                        # 6th sentence is complete - keep 6
                        keep_count = 6
                    else:
                        # 6th sentence incomplete - keep only 5 complete sentences
                        keep_count = 5
                    
                    answer = '. '.join(sentences[:keep_count])
                    if not answer.endswith(('.', '!', '?')):
                        answer += '.'
                    if len(sentences) > keep_count:
                        logger.debug(f"Trimmed answer from {len(sentences)} to {keep_count} complete sentences")
                
                # CRITICAL: Always ensure the final answer ends with proper punctuation
                if answer and not answer.rstrip().endswith(('.', '!', '?')):
                    # Answer doesn't end properly - find last complete sentence
                    trimmed = answer.rstrip()
                    for punct in ['.', '!', '?']:
                        last_punct = trimmed.rfind(punct)
                        if last_punct > len(trimmed) * 0.3:  # If punctuation is in last 70%
                            # Found a complete sentence - use everything up to that point
                            answer = trimmed[:last_punct + 1].strip()
                            logger.debug(f"Fixed incomplete answer by using last complete sentence ending at {punct}")
                            break
                    else:
                        # No sentence-ending punctuation found - add a period
                        answer = trimmed + '.'
                        logger.debug("Added period to ensure answer completeness")
            
            # Final completeness check - ensure answer ends properly
            # This is a safety net after all other processing
            if answer and len(answer) > 20:
                trimmed = answer.rstrip()
                if not trimmed.endswith(('.', '!', '?')):
                    # Still incomplete - find last complete sentence
                    for punct in ['.', '!', '?']:
                        last_punct = trimmed.rfind(punct)
                        if last_punct > len(trimmed) * 0.3:  # If punctuation is in last 70%
                            answer = trimmed[:last_punct + 1].strip()
                            logger.debug(f"Final fix: used last complete sentence ending at {punct}")
                            break
                    else:
                        # No punctuation found - add period
                        answer = trimmed + '.'
                        logger.debug("Final fix: added period to complete answer")
                
            # Confidence calculation
            confidence = self._calculate_confidence(answer, context, question)
            return answer, confidence
            
        except Exception as e:
            logger.error(f"Inference error: {e}")
            return "I'm having trouble processing your question. Please try again.", 0.1

    def get_answer_stream(self, question: str, context: str, answer_length: str = "medium") -> Iterator[str]:
        """
        Stream answer tokens as they're generated for real-time display.
        Uses RAG context when available, otherwise uses Phi's own knowledge.
        
        Args:
            question (str): User's question
            context (str): RAG context (can be empty - Phi will use own knowledge)
            answer_length (str): Deprecated - kept for API compatibility, not used
            
        Yields:
            str: Token chunks as they're generated
        """
        if self.llm is None:
            self.load_model()
            
        # Input validation - allow empty context (Phi will use own knowledge)
        if not question or len(question.strip()) < 3:
            yield "Please provide a question about your Grade 8-12 curriculum."
            return
        
        # Ensure context is a string (handle None case)
        if context is None:
            context = ""
            
        # Question normalization
        normalized_question = question.strip()
        if normalized_question.isupper():
            normalized_question = normalized_question.lower().capitalize()
        elif normalized_question.islower():
            normalized_question = normalized_question.capitalize()
        if len(normalized_question) < 3:
            yield "Please provide a more detailed question."
            return
            
        try:
            # Prompt building
            prompt = self._build_prompt(normalized_question, context)
            
            # Calculate dynamic max_tokens based on question
            max_tokens = self._calculate_max_tokens(normalized_question, context)
            
            # Log prompt for debugging (reduced verbosity)
            logger.debug(f"Full prompt length: {len(prompt)}")
            logger.debug(f"Question: {normalized_question}, Context length: {len(context) if context else 0}")
            logger.debug(f"Calculated max_tokens: {max_tokens}")
            
            # Streaming inference - always stream for better UX
            # Users need to see tokens appearing in real-time
            full_answer = ""
            chunk_count = 0
            tokens_yielded = 0
            
            # Check if model is loaded
            if self.llm is None:
                logger.error("Model not loaded!")
                yield "Error: Model not loaded. Please check model files."
                return
            
            for chunk in self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=0.5,
                top_p=0.9,
                repeat_penalty=1.1,
                stop=self.STOP_SEQUENCES,
                echo=False,
                stream=True  # Always stream for real-time feedback
            ):
                chunk_count += 1
                if chunk is None:
                    continue
                    
                # Extract text from chunk - handle multiple formats
                token = None
                try:
                    # Log first few chunks to understand format
                    if chunk_count <= 3:
                        logger.info(f"Stream chunk #{chunk_count}: type={type(chunk)}")
                        if isinstance(chunk, dict):
                            logger.info(f"  Chunk keys: {list(chunk.keys())}")
                            if "choices" in chunk:
                                logger.info(f"  Choices count: {len(chunk.get('choices', []))}")
                                if len(chunk.get('choices', [])) > 0:
                                    choice = chunk["choices"][0]
                                    logger.info(f"  First choice type: {type(choice)}, keys: {list(choice.keys()) if isinstance(choice, dict) else 'N/A'}")
                    
                    if isinstance(chunk, dict):
                        # Format 1: {"choices": [{"text": "..."}]}
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            choice = chunk["choices"][0]
                            
                            # Check for finish_reason - if model finished, stop processing
                            if "finish_reason" in choice and choice["finish_reason"]:
                                if chunk_count <= 3:
                                    logger.info(f"  Model finished with reason: {choice['finish_reason']}")
                                # Don't break, continue to process any remaining text
                            
                            # Format 1: Standard text field (may be None or empty in early chunks)
                            if "text" in choice:
                                token = choice["text"]
                                if chunk_count <= 3:
                                    # Show full token for debugging (not truncated)
                                    token_repr = repr(token) if token is not None else "None"
                                    logger.info(f"  Extracted from choices[0]['text']: {token_repr} (len={len(token) if token else 0})")
                                
                                # If text is None or empty, this might be a metadata-only chunk
                                # In llama-cpp-python streaming, first chunk is often metadata
                                if token is None or (isinstance(token, str) and len(token) == 0):
                                    if chunk_count <= 3:
                                        logger.info(f"  Chunk #{chunk_count} has empty text field (likely metadata chunk), skipping")
                                    # Don't set token to None - keep it as is so we can check later
                                    # But don't yield empty tokens
                                    
                            # Format 2: OpenAI-style delta format
                            elif "delta" in choice and isinstance(choice["delta"], dict):
                                if "content" in choice["delta"]:
                                    token = choice["delta"]["content"]
                                    if chunk_count <= 3:
                                        logger.info(f"  Extracted from choices[0]['delta']['content']: {repr(token)}")
                            # Format 3: Direct text in choice
                            elif isinstance(choice, str):
                                token = choice
                                if chunk_count <= 3:
                                    logger.info(f"  Choice is string: {repr(token)}")
                        # Format 4: Direct text in chunk
                        elif "text" in chunk:
                            token = chunk["text"]
                            if chunk_count <= 3:
                                logger.info(f"  Extracted from chunk['text']: '{token[:50]}...'")
                        # Format 5: Direct content field
                        elif "content" in chunk:
                            token = chunk["content"]
                            if chunk_count <= 3:
                                logger.info(f"  Extracted from chunk['content']: '{token[:50]}...'")
                        # Format 6: Check if chunk itself is a string-like value
                        else:
                            # Log chunk structure for debugging
                            logger.warning(f"Chunk #{chunk_count} dict but no recognized format. Keys: {list(chunk.keys())}")
                    elif isinstance(chunk, str):
                        # Format 7: Chunk is directly a string
                        token = chunk
                        if chunk_count <= 3:
                            logger.info(f"  Chunk is string: '{token[:50]}...'")
                    else:
                        # Unknown format - try to convert to string
                        token = str(chunk) if chunk else None
                        logger.warning(f"Chunk #{chunk_count} unknown type: {type(chunk)}, converted: '{token[:50] if token else None}...'")
                    
                    # Yield token if we found a valid one
                    # IMPORTANT: In streaming, even single characters or whitespace might be valid tokens
                    # Don't filter them out - let the model generate naturally
                    if token is not None and isinstance(token, str) and len(token) > 0:
                        # Valid token - add to full_answer and yield
                        full_answer += token
                        tokens_yielded += 1
                        yield token
                        if chunk_count <= 3:
                            logger.info(f"  [OK] Yielded token #{tokens_yielded}: {repr(token)}")
                    elif token is None:
                        # Token is None - this is a metadata-only chunk, skip it
                        if chunk_count <= 3:
                            logger.info(f"  Chunk #{chunk_count} has None token (metadata chunk), skipping")
                    elif isinstance(token, str) and len(token) == 0:
                        # Empty string token - skip it
                        if chunk_count <= 3:
                            logger.info(f"  Chunk #{chunk_count} has empty string token, skipping")
                    else:
                        # Token exists but is not a string or has unexpected type
                        if chunk_count <= 3:
                            logger.warning(f"  Chunk #{chunk_count} has unexpected token type: {type(token)}, value: {token}")
                        
                except (KeyError, IndexError, TypeError, AttributeError) as e:
                    logger.error(f"Error extracting token from chunk {chunk_count}: {e}, chunk type: {type(chunk)}", exc_info=True)
                    if chunk_count <= 3:
                        logger.error(f"Problematic chunk: {chunk}")
                    continue
            
            # Log streaming results
            logger.info(f"Streaming completed: {chunk_count} chunks processed, {tokens_yielded} tokens yielded, answer length: {len(full_answer)}")
            
            # If no tokens were yielded, try non-streaming fallback
            if tokens_yielded == 0 and not full_answer:
                logger.warning(f"No tokens yielded from streaming. Chunk count: {chunk_count}, Prompt length: {len(prompt)}")
                logger.info("Attempting non-streaming fallback...")
                
                try:
                    # Try non-streaming inference with dynamic token limit
                    max_tokens = self._calculate_max_tokens(normalized_question, context)
                    logger.info(f"Trying non-streaming fallback with max_tokens={max_tokens}...")
                    response = self.llm(
                        prompt,
                        max_tokens=max_tokens,
                        temperature=0.5,
                        top_p=0.9,
                        repeat_penalty=1.1,
                        stop=self.STOP_SEQUENCES,
                        echo=False,
                        stream=False
                    )
                    
                    # Log full response structure
                    logger.info(f"Non-streaming response type: {type(response)}")
                    if isinstance(response, dict):
                        logger.info(f"Response keys: {list(response.keys())}")
                        if "choices" in response:
                            choices = response.get("choices", [])
                            logger.info(f"Choices count: {len(choices)}")
                            if len(choices) > 0:
                                choice = choices[0]
                                logger.info(f"First choice keys: {list(choice.keys()) if isinstance(choice, dict) else 'N/A'}")
                                if isinstance(choice, dict):
                                    for key in choice.keys():
                                        value = choice[key]
                                        if isinstance(value, str):
                                            logger.info(f"  {key}: {repr(value[:100])}...")
                                        else:
                                            logger.info(f"  {key}: {type(value)} = {value}")
                    
                    answer = self._extract_text(response)
                    logger.info(f"Non-streaming fallback extracted answer: {repr(answer[:200]) if answer else 'None'} (length: {len(answer) if answer else 0})")
                    
                    if answer and len(answer.strip()) > 10:
                        # Yield the answer in chunks to simulate streaming
                        words = answer.split()
                        for i, word in enumerate(words):
                            if i == 0:
                                yield word
                            else:
                                yield " " + word
                        logger.info("Non-streaming fallback succeeded")
                        return
                    else:
                        logger.error("Non-streaming fallback also returned empty answer")
                except Exception as e:
                    logger.error(f"Non-streaming fallback failed: {e}", exc_info=True)
                
                # Final fallback - yield error message
                yield "I'm having trouble generating a response. Please try rephrasing your question."
                return
            
            # Post-streaming: Ensure answer is complete
            # Check if the streamed answer ends properly
            if full_answer and len(full_answer) > 20:
                trimmed = full_answer.rstrip()
                if not trimmed.endswith(('.', '!', '?')):
                    # Answer is incomplete - find last complete sentence
                    for punct in ['.', '!', '?']:
                        last_punct = trimmed.rfind(punct)
                        if last_punct > len(trimmed) * 0.3:  # If punctuation is in last 70%
                            # Found complete sentence - yield the missing punctuation if needed
                            missing = trimmed[last_punct + 1:].strip()
                            if missing:
                                # There's incomplete text after last punctuation - don't yield it
                                logger.debug(f"Streamed answer incomplete - last complete sentence at position {last_punct}")
                            break
                    else:
                        # No punctuation found - answer needs completion
                        logger.debug("Streamed answer has no sentence-ending punctuation")
            
            # Clean up answer if needed (post-streaming check)
            # Note: This won't affect already-streamed tokens, but we can log if off-topic content was added
            off_topic_markers = [
                "\n\nExercise:", "\nExercise:", "Exercise:",
                "\n\nPractice:", "\nPractice:", "Practice:",
                "\n\nTry this:", "\nTry this:", "Try this:",
                "\n\nNow try", "\nNow try",
                "\n\nNow, let's", "\nNow, let's", "Now, let's",
                "\n\nLet's explore", "\nLet's explore", "Let's explore",
                "\n\nUse Case", "\nUse Case", "Use Case",
                "\n\nReal-world", "\nReal-world", "Real-world",
                # Diagram/visualization patterns
                "\n\nDiagram:", "\nDiagram:", "Diagram:",
                "\nDiagram", "\n\nDiagram",
                # Box-drawing character patterns
                "\n┌", "\n│", "\n└", "\n├",
                "\n\n┌", "\n\n│", "\n\n└", "\n\n├",
                # Reference context patterns
                "\n\nReference Context", "\nReference Context",
                "\n\nStudent Question", "\nStudent Question",
            ]
            for marker in off_topic_markers:
                if marker in full_answer:
                    logger.warning(f"Off-topic marker detected in streamed answer: {marker}")
                    # Note: Can't remove from already-streamed tokens, but stop sequences should prevent this
                    break
                
        except Exception as e:
            logger.error(f"Streaming inference error: {e}", exc_info=True)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            yield "I'm having trouble processing your question. Please try again."

    def _build_prompt(self, question: str, context: str) -> str:
        """
        Build prompt template that intelligently handles RAG context.
        Encourages Phi to use its own knowledge even when RAG context is provided.
        
        Args:
            question: Student's question
            context: RAG context (can be empty/minimal)
            
        Returns:
            Formatted prompt string
        """
        # Handle context intelligently
        trimmed_context = (context or "").strip()
        
        # Distinguish between actual RAG content and general knowledge instructions
        # RAG content should be factual content, not instructions
        is_instruction_context = any(phrase in trimmed_context.lower() for phrase in [
            "you are a helpful", "use your knowledge", "provide an accurate answer",
            "focus on curriculum", "grade 8-12 curriculum", "neb standards"
        ])
        
        # Check if it's actual RAG content (not instructions and has meaningful content)
        has_rag_context = (
            len(trimmed_context) > 50 and 
            not is_instruction_context and
            # Additional check: RAG content usually has factual statements, not just instructions
            not trimmed_context.lower().startswith("you are")
        )
        
        if has_rag_context:
            # Educational focus: Allow more context for better answers
            # Students need comprehensive information to learn effectively
            if len(trimmed_context) > 300:
                trimmed_context = trimmed_context[:300]
                last_period = trimmed_context.rfind('.')
                if last_period > 250:
                    trimmed_context = trimmed_context[:last_period + 1]
            
            # Present RAG context as the primary knowledge source
            # Make it clear this is the curriculum content to use
            context_section = f"Study material:\n{trimmed_context}"
        else:
            # No RAG context - use own knowledge
            context_section = None
        
        # Educational prompt format - use direct Q&A format that Phi models work better with
        if context_section:
            return (
                f"{self.system_prompt}\n\n"
                f"{context_section}\n\n"
                f"Q: {question}\n"
                f"A:"
            )
        else:
            # No context - use concise fallback prompt
            concise_prompt = (
                "You are Satya, an expert tutor for Grade 8-12 students in Nepal (NEB curriculum). "
                "Provide a brief, concise answer. Be direct and helpful. "
                "Focus on answering the question clearly and completely. "
                "CRITICAL: Always finish each sentence completely with proper punctuation (., !, or ?). "
                "NEVER add: Question:, Answer:, Q:, A:, exercises, diagrams, ASCII art, numbered lists."
            )
            return (
                f"{concise_prompt}\n\n"
                f"Q: {question}\n"
                f"A:"
            )

    def _extract_text(self, response: Any) -> str:
        """Extract text from llama-cpp-python response with multiple format support."""
        if response is None:
            logger.debug("Response is None")
            return ""
        
        try:
            # Format 1: Standard dict with choices
            if isinstance(response, dict):
                if "choices" in response and len(response["choices"]) > 0:
                    choice = response["choices"][0]
                    # Check for text field
                    if "text" in choice:
                        text = choice["text"]
                        logger.debug(f"Extracted text from choices[0]['text']: {len(text) if text else 0} chars")
                        return text.strip() if text else ""
                    # Check for content field (OpenAI-style)
                    elif "content" in choice:
                        text = choice["content"]
                        logger.debug(f"Extracted text from choices[0]['content']: {len(text) if text else 0} chars")
                        return text.strip() if text else ""
                    # Check if choice itself is a string
                    elif isinstance(choice, str):
                        logger.debug(f"Choice is string: {len(choice)} chars")
                        return choice.strip()
                    # Check if choice is a dict with message
                    elif isinstance(choice, dict) and "message" in choice:
                        message = choice["message"]
                        if isinstance(message, dict) and "content" in message:
                            text = message["content"]
                            logger.debug(f"Extracted text from choices[0]['message']['content']: {len(text) if text else 0} chars")
                            return text.strip() if text else ""
                
                # Format 2: Direct text field
                if "text" in response:
                    text = response["text"]
                    logger.debug(f"Extracted text from response['text']: {len(text) if text else 0} chars")
                    return text.strip() if text else ""
                
                # Format 3: Direct content field
                if "content" in response:
                    text = response["content"]
                    logger.debug(f"Extracted text from response['content']: {len(text) if text else 0} chars")
                    return text.strip() if text else ""
                
                # Log what we got for debugging
                logger.warning(f"Response dict but couldn't extract text. Keys: {response.keys()}")
            
            # Format 4: Response is directly a string
            elif isinstance(response, str):
                logger.debug(f"Response is string: {len(response)} chars")
                return response.strip()
            
            # Format 5: Try to convert to string
            else:
                text = str(response)
                logger.debug(f"Converted response to string: {len(text)} chars")
                if len(text) > 1000:  # Probably not what we want
                    logger.warning(f"Response converted to very long string ({len(text)} chars), might be wrong format")
                return text.strip() if text else ""
                
        except Exception as e:
            logger.error(f"Text extraction error: {e}", exc_info=True)
            # Try one more time with str() conversion
            try:
                result = str(response).strip()
                logger.debug(f"Fallback str() conversion: {len(result)} chars")
                return result
            except:
                return ""
        
        logger.warning(f"Could not extract text from response type: {type(response)}")
        return ""

    def get_hints(self, question: str, context: str) -> List[str]:
        """Generate hints using Phi 1.5 - restored to original quality."""
        if self.llm is None:
            self.load_model()
            
        try:
            # Your ORIGINAL context handling for hints
            trimmed_context = (context or "").strip()
            if len(trimmed_context) > 500:
                last_period = trimmed_context.rfind('.')
                if last_period > 400:
                    trimmed_context = trimmed_context[:last_period + 1]
            
            # Your ORIGINAL hint prompt
            prompt = (
                f"You are a helpful tutor. Based on the context, give 3 specific hints to answer this question.\n\n"
                f"Context: {trimmed_context}\n\n"
                f"Question: {question}\n\n"
                f"Hints (be specific and related to the question):\n"
                f"1."
            )
            
            response = self.llm(
                prompt,
                max_tokens=120,  # More tokens for better hints
                temperature=0.2,  # Balanced for creativity
                top_p=0.9,
                stop=["\n4", "4.", "###", "\n\nQuestion:", "\n\nContext:"],
                echo=False,
                stream=False
            )
            hints_text = self._extract_text(response)
            
            # Your ORIGINAL hint parsing
            hints = []
            lines = hints_text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line[0].isdigit():
                    if '.' in line:
                        parts = line.split('.', 1)
                    elif ')' in line:
                        parts = line.split(')', 1)
                    else:
                        parts = line.split(' ', 1)
                    
                    if len(parts) > 1:
                        hint = parts[1].strip()
                        for prefix in ["Hint:", "•", "-"]:
                            if hint.startswith(prefix):
                                hint = hint[len(prefix):].strip()
                        if hint and len(hint) > 8:
                            hints.append(hint)
            
            # Hint filtering
            generic_phrases = ["review the context", "look for key terms", "think about", 
                             "consider the", "examine the", "check the"]
            filtered_hints = []
            for hint in hints:
                hint_lower = hint.lower()
                if not any(phrase in hint_lower for phrase in generic_phrases) or len(hint) > 30:
                    filtered_hints.append(hint)
            
            if len(filtered_hints) >= 3:
                return filtered_hints[:3]
            elif len(filtered_hints) > 0:
                return filtered_hints[:3]
            else:
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
        """
        Calculate confidence score based on answer quality and accuracy.
        Focuses on whether the answer actually addresses the question correctly.
        """
        answer_lower = answer.lower()
        question_lower = question.lower()
        
        # Error detection - very low confidence for errors
        if any(phrase in answer_lower for phrase in ["i couldn't", "i'm having trouble", "error", "i need both"]):
            return 0.1
        
        # Check if answer is too short to be meaningful
        word_count = len(answer.split())
        if word_count < 5:
            return 0.3
        
        # Check if RAG context was provided (higher accuracy source)
        has_rag_context = context and len(context.strip()) > 50
        
        # KEY: Check if answer actually addresses the question
        # Extract key terms from question (remove common words)
        question_words = set(word for word in question_lower.split() 
                           if len(word) > 3 and word not in ["what", "how", "why", "when", "where", "which", "explain", "describe", "define"])
        answer_words = set(word for word in answer_lower.split() if len(word) > 3)
        
        # Calculate relevance - how well answer matches question
        if question_words:
            question_relevance = len(question_words.intersection(answer_words)) / len(question_words)
            # If answer contains key terms from question, it's likely addressing it
            addresses_question = question_relevance > 0.3  # At least 30% of question terms in answer
        else:
            addresses_question = True  # If no specific terms, assume it addresses it
        
        # Quality indicators
        has_structure = answer.count(".") >= 2  # At least 2 sentences (complete answer)
        has_definition = any(phrase in answer_lower for phrase in ["is a", "is an", "are", "means", "refers to"])
        has_examples = any(word in answer_lower for word in ["example", "like", "such as", "for instance"])
        is_complete = word_count >= 15 and has_structure  # Complete, well-formed answer
        
        # Base confidence - start high for valid answers that address the question
        if addresses_question and is_complete:
            base_score = 0.85  # High confidence for complete, relevant answers
        elif addresses_question:
            base_score = 0.75  # Good confidence if it addresses question
        elif is_complete:
            base_score = 0.70  # Medium confidence if complete but may not fully address
        else:
            base_score = 0.60  # Lower confidence for incomplete or off-topic
        
        # Quality boosts
        if has_definition:
            base_score += 0.05  # Definitions are clear and accurate
        if has_examples:
            base_score += 0.05  # Examples show understanding
        if has_structure and word_count >= 20:
            base_score += 0.05  # Well-structured, detailed answers
        
        # Knowledge source boost
        if has_rag_context:
            base_score += 0.10  # RAG = study materials, highest accuracy
        else:
            base_score += 0.05  # Own knowledge is also reliable for curriculum
            
        return min(1.0, base_score)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Your ORIGINAL model info."""
        return {
            'name': 'Phi 1.5',
            'version': '1.0',
            'format': 'GGUF',
            'context_size': self.config.get('n_ctx', 2048),
            'threads': self.config.get('n_threads', 4),
            'max_tokens': self.config.get('max_tokens', 256),
            'temperature': self.config.get('temperature', 0.35),
            'top_p': self.config.get('top_p', 0.92),
            'model_path': str(self.model_file),
            'quantization': Path(self.model_file).name,
            'backend': 'llama-cpp-python',
            'optimized_for': 'accuracy_with_personality'
        }
    
    def cleanup(self):
        """Your ORIGINAL cleanup."""
        if self.llm is not None:
            try:
                del self.llm
                self.llm = None
                logger.info("Model resources cleaned up")
            except Exception as e:
                logger.error(f"Cleanup error: {e}")