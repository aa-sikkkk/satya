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
    
    # Stop sequences to prevent off-topic content (OPTIMIZED: Safe 25 stops - 6.7x faster)
    # Reduced from 97 to 28 essential stops based on performance testing
    # This configuration provides best speed (9.9s vs 66s) while maintaining quality
    STOP_SEQUENCES = [
        "</s>",  # Model's end token
        # Exercise/practice patterns
        "\n\nExercise:",
        "\n\nPractice:",
        "\n\nTry this:",
        "\n\nNow try",
        # Use case/real-world patterns
        "\n\nNow, let's",
        "\n\nLet's explore",
        "\n\nUse Case",
        "\n\nReal-world",
        "\n\nAnother example",
        # Continuation phrases (edge cases)
        "\n\nAdditionally,",
        "\n\nFurthermore,",
        "\n\nMoreover,",
        # Explanation/elaboration patterns
        "\n\nExplanation:",
        "\n\nIn summary",
        "\n\nTo summarize",
        "\n\nIn other words",
        "\n\nSimilarly,",
        # Numbered lists
        "\n1.",
        "\n2.",
        "\n3.",
        # Diagram patterns
        "\n\nDiagram:",
        # Box-drawing characters (edge cases)
        "\n┌",
        "\n│",
        "\n└",
        # Prompt leakage prevention
        "\n\nQuestion:",
        "\n\nAnswer:",
        "\n\nIMPORTANT:",
    ]
    
    # Fixed max tokens for concise answers (system prompt enforces 2-3 sentences)
    # Reduced to 50 tokens to enforce strict conciseness and ensure fast generation
    # 50 tokens ≈ 2-3 sentences for most answers - prevents slow generation
    DEFAULT_MAX_TOKENS = 50
    
    def __init__(self, model_path: str, enable_streaming: bool = False):
        """
        Initialize with SATYA PERSONALITY.
        """
        self.model_path = Path(model_path)
        self.llm = None
        self.config = self._load_config()
        self.model_file = self._find_model_file()
        self.enable_streaming = enable_streaming
        
        # SATYA PERSONALITY - Grade 8-12 Nepal Curriculum Tutor
        # Optimized for curriculum questions with intelligent RAG + own knowledge integration
        self.system_prompt = (
            "You are Satya, an expert tutor for Grade 8-12 students in Nepal. "
            "You specialize in Nepal's curriculum (NEB - National Examination Board) covering: "
            "Computer Science, English, Mathematics, Science, Social Studies, and other subjects. "
            "Answer ONLY curriculum-related questions. Be direct, clear, and age-appropriate. "
            "ABSOLUTE RULES - NO EXCEPTIONS: "
            "1. Answer the question in 2-3 sentences maximum + ONE code example (if programming). Then STOP immediately. "
            "2. NEVER add: exercises, practice problems, use cases, real-world examples, 'let's explore', or extra content. "
            "3. NEVER say: 'Now let's', 'Use Case', 'Real-world', 'Another example', or similar phrases. "
            "4. NEVER add sections like 'Explanation:', 'In summary', 'To summarize', or any additional explanations. "
            "5. NEVER generate diagrams, ASCII art, box-drawing characters, or visual representations. "
            "6. NEVER repeat or copy instruction text, prompt labels, or context labels in your answer. "
            "7. NEVER explain the prompt structure, reference context labels, or student question labels. "
            "8. 'How does X work?' → Explain mechanism in 2-3 sentences. STOP. "
            "9. 'How to do X?' → Show code/process directly. STOP. "
            "10. 'What is X?' → Definition in 1-2 sentences + one example. STOP. "
            "11. Complete your sentences. End with proper punctuation. "
            "12. Maximum 3 sentences total. Answer the question, then STOP immediately. "
            "13. NEVER use numbered lists (1., 2., 3., etc.). Answer in flowing sentences, not a list. "
            "14. If you finish explaining, STOP. Do not continue. Do not add 'Explanation:' sections. Do not add diagrams. Do not add extra content. "
            "15. Answer ONLY the question asked. Do not answer different questions. "
            "16. KNOWLEDGE PRIORITY: If reference material is provided, USE IT as your primary knowledge source. It contains accurate curriculum content from study materials. "
            "17. If no reference material is provided, use your own knowledge of Grade 8-12 curriculum (NEB standards). "
            "18. Answer in clear, direct sentences. Use the information from reference material when available, but explain it naturally. "
            "19. CRITICAL: After answering the question in 2-3 sentences, STOP immediately. Do not add explanations, summaries, or additional sections. Do not continue describing processes in detail."
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
        
        # SETTINGS
        return {
            "n_ctx": 2048,                    # context size
            "n_threads": max(1, os.cpu_count() // 2 or 1),  # threading
            "n_gpu_layers": 0,
            "max_tokens": 300,                # More tokens for detailed answers
            "temperature": 0.4,              # Slightly higher for creativity
            "top_p": 0.92,                    # Slightly relaxed for variety
            "repeat_penalty": 1.06,           
            "stop": ["</s>", "\n\nContext:", "\n\nQuestion:", "\n\nQ:", "\n\nProvide"],
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
                    n_ctx=self.config.get('n_ctx', 2048),        
                    n_threads=self.config.get('n_threads', 4),
                    n_gpu_layers=self.config.get('n_gpu_layers', 0),
                    use_mmap=False,         
                    verbose=False            
                )
                logger.info(f"Model loaded successfully in {time.time() - start_time:.2f}s")
            else:
                raise ImportError("llama-cpp-python not available")
            
        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            raise RuntimeError(f"Could not load Phi 1.5 model: {e}")
                
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
            
            # Inference settings (optimized for speed and conciseness)
            # Lower temperature = faster, more deterministic generation
            # Lower top_p = faster token selection
            response = self.llm(
                prompt,
                max_tokens=self.DEFAULT_MAX_TOKENS,
                temperature=0.2,  # Lower for faster generation (was 0.35)
                top_p=0.85,  # Lower for faster selection (was 0.92)
                repeat_penalty=1.1,  # Prevent repetition
                stop=self.STOP_SEQUENCES,
                echo=False,
                stream=False
            )
            
            answer = self._extract_text(response)
            
            # Answer validation
            if not answer or len(answer.strip()) < 10:
                return "I couldn't generate a proper response. Please try rephrasing your question.", 0.1
            
            # Answer cleaning
            answer = answer.strip()
            if answer.lower().startswith("answer:"):
                answer = answer[7:].strip()
            
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
                "\n\nQuestion:", "\nQuestion:",
                "\n\nAnswer:", "\nAnswer:",
                "\n\nAnswer using the study material", "\nAnswer using the study material",
                "\n\nIMPORTANT:", "\nIMPORTANT:",
                "IMPORTANT:",
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
            
            # Enforce maximum sentence limit (3 sentences max) - prevent verbosity
            # More aggressive limiting for faster, concise answers
            if answer:
                # Split on sentence endings, but preserve abbreviations
                sentences = re.split(r'(?<=[.!?])\s+', answer)
                sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
                
                # Early stopping: if we have 2+ complete sentences, that's enough
                # This prevents unnecessary generation for questions that need short answers
                if len(sentences) >= 2:
                    # Keep 2-3 sentences max (prefer 2 if available, max 3)
                    keep_count = min(3, len(sentences))
                    answer = '. '.join(sentences[:keep_count])
                    if not answer.endswith(('.', '!', '?')):
                        answer += '.'
                    if len(sentences) > keep_count:
                        logger.debug(f"Trimmed answer from {len(sentences)} to {keep_count} sentences")
            
            # Check if answer seems incomplete and try to fix it
            if answer and len(answer) > 20:
                trimmed = answer.rstrip()
                # Check if answer ends properly
                if not trimmed.endswith(('.', '!', '?', ':', '\n', ')', ']', '}')):
                    # Might be incomplete - try to find last complete sentence
                    for punct in ['.', '!', '?', ':']:
                        last_punct = trimmed.rfind(punct)
                        if last_punct > len(trimmed) * 0.6:  # If punctuation is in last 40%
                            answer = trimmed[:last_punct + 1].strip()
                            logger.debug(f"Fixed incomplete answer by trimming at {punct}")
                            break
                
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
            
            # Stream inference (optimized for speed and conciseness)
            full_answer = ""
            for chunk in self.llm(
                prompt,
                max_tokens=self.DEFAULT_MAX_TOKENS,
                temperature=0.2,  # Lower for faster generation
                top_p=0.85,  # Lower for faster selection
                repeat_penalty=1.1,  # Prevent repetition
                stop=self.STOP_SEQUENCES,
                echo=False,
                stream=True
            ):
                if chunk is None:
                    continue
                    
                # Extract text from chunk
                try:
                    if isinstance(chunk, dict):
                        # Handle llama-cpp-python format: {"choices": [{"text": "..."}]}
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            choice = chunk["choices"][0]
                            if "text" in choice:
                                token = choice["text"]
                                if token:  # Only yield non-empty tokens
                                    full_answer += token
                                    yield token
                            # Handle OpenAI-style delta format (if supported)
                            elif "delta" in choice and isinstance(choice["delta"], dict):
                                if "content" in choice["delta"]:
                                    token = choice["delta"]["content"]
                                    if token:  # Only yield non-empty tokens
                                        full_answer += token
                                        yield token
                        # Handle direct text in chunk (fallback)
                        elif "text" in chunk:
                            token = chunk["text"]
                            if token:
                                full_answer += token
                                yield token
                except (KeyError, IndexError, TypeError) as e:
                    logger.debug(f"Error extracting token from chunk: {e}")
                    continue
            
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
            logger.error(f"Streaming inference error: {e}")
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
        has_rag_context = len(trimmed_context) > 50  # Meaningful context threshold
        
        if has_rag_context:
            # Trim context if too long
            if len(trimmed_context) > 700:  # Allow more context for better answers
                trimmed_context = trimmed_context[:700]
                last_period = trimmed_context.rfind('.')
                if last_period > 600:
                    trimmed_context = trimmed_context[:last_period + 1]
            
            # Present RAG context as the primary knowledge source
            # Make it clear this is the curriculum content to use
            context_section = f"Study material:\n{trimmed_context}"
        else:
            # No RAG context - use own knowledge
            context_section = None
        
        # Simple, direct prompt format
        # When RAG context exists, Phi should use it as primary knowledge
        if context_section:
            return (
                f"{self.system_prompt}\n\n"
                f"{context_section}\n\n"
                f"Question: {question}\n\n"
                f"Answer using the study material above:"
            )
        else:
            return (
                f"{self.system_prompt}\n\n"
                f"Question: {question}\n\n"
                f"Answer:"
            )

    def _extract_text(self, response: Any) -> str:
        """Your ORIGINAL text extraction."""
        if response is None:
            return ""
        
        try:
            if isinstance(response, dict) and "choices" in response:
                choice = response["choices"][0]
                if "text" in choice:
                    return choice["text"].strip()
        except Exception as e:
            logger.error(f"Text extraction error: {e}")
        
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
            
            # Your ORIGINAL hint filtering
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