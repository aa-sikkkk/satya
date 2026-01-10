#!/usr/bin/env python3
"""
Smart Phi 1.5 Handler - Educational depth for old hardware
Adapts answer length based on question type while staying performant.
"""

import os
import sys
import logging
import re
from pathlib import Path

# Memory safety for Windows
if sys.platform == "win32":
    os.environ["LLAMA_CPP_MLOCK"] = "0"
    os.environ["OMP_NUM_THREADS"] = "2"

try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    
logger = logging.getLogger(__name__)


class SmartPhi15Handler:
    """Educational assistant that adapts to question complexity."""
    
    # Question type patterns - determines answer depth needed
    QUESTION_TYPES = {
        'definition': {
            'patterns': ['what is', 'what are', 'define', 'meaning of'],
            'tokens': 100,
            'description': 'Simple definition'
        },
        'explanation': {
            'patterns': ['explain', 'how does', 'how do', 'why does', 'why is', 'describe'],
            'tokens': 180,
            'description': 'Detailed explanation'
        },
        'comparison': {
            'patterns': ['difference between', 'compare', 'contrast', 'versus', 'vs'],
            'tokens': 160,
            'description': 'Comparison'
        },
        'problem_solving': {
            'patterns': ['solve', 'calculate', 'find the', 'compute'],
            'tokens': 140,
            'description': 'Step-by-step solution'
        },
        'list': {
            'patterns': ['list', 'types of', 'examples of', 'enumerate'],
            'tokens': 120,
            'description': 'Listed items'
        }
    }
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.llm = None
        self.model_file = self._find_model()
        
    def _find_model(self) -> str:
        """Find .gguf file."""
        for file in self.model_path.iterdir():
            if file.suffix == ".gguf":
                logger.info(f"Found: {file.name}")
                return str(file)
        raise FileNotFoundError(f"No .gguf in {self.model_path}")
    
    def load_model(self):
        """Load with optimized settings for old hardware."""
        if self.llm:
            return
            
        if not LLAMA_AVAILABLE:
            raise ImportError("llama-cpp-python not installed")
        
        logger.info("Loading model...")
        self.llm = Llama(
            model_path=self.model_file,
            n_ctx=1024,          # Enough for educational answers
            n_threads=2,         # Conservative for old i3
            n_batch=256,
            n_gpu_layers=0,
            use_mmap=True,
            use_mlock=False,
            verbose=False
        )
        logger.info("Model loaded!")
    
    def _detect_question_type(self, question: str) -> tuple[str, int]:
        """
        Detect question type and return appropriate token limit.
        
        Returns:
            (question_type, max_tokens)
        """
        q_lower = question.lower()
        
        # Check each question type
        for qtype, config in self.QUESTION_TYPES.items():
            if any(pattern in q_lower for pattern in config['patterns']):
                logger.info(f"Detected: {config['description']} ({config['tokens']} tokens)")
                return qtype, config['tokens']
        
        # Default: medium explanation
        base_tokens = 120
        
        # Adjust by question length (longer questions = more complex)
        word_count = len(question.split())
        if word_count > 15:
            base_tokens = 160
        elif word_count < 5:
            base_tokens = 80
        
        logger.info(f"Default type ({base_tokens} tokens)")
        return 'general', base_tokens
    
    def _build_prompt(self, question: str, context: str) -> str:
        """
        Build educational prompt that encourages complete answers.
        """
        # Detect question type for better prompting
        qtype, _ = self._detect_question_type(question)
        
        # Type-specific instructions
        instructions = {
            'definition': 'Give a clear definition with an example.',
            'explanation': 'Explain step-by-step with examples.',
            'comparison': 'Compare point-by-point, highlighting key differences.',
            'problem_solving': 'Show the solution step-by-step.',
            'list': 'List the items with brief explanations.',
            'general': 'Provide a complete, educational answer.'
        }
        
        instruction = instructions.get(qtype, instructions['general'])
        
        # Build prompt based on context availability
        if context and len(context.strip()) > 30:
            # Has context - use it
            trimmed_context = context[:600]  # Reasonable limit
            prompt = (
                f"You are a helpful tutor for high school students.\n"
                f"{instruction}\n\n"
                f"Reference: {trimmed_context}\n\n"
                f"Question: {question}\n"
                f"Answer:"
            )
        else:
            # No context - use model knowledge
            prompt = (
                f"You are a helpful tutor for high school students.\n"
                f"{instruction}\n\n"
                f"Question: {question}\n"
                f"Answer:"
            )
        
        return prompt
    
    def get_answer(self, question: str, context: str = "") -> tuple[str, float]:
        """
        Get educational answer with adaptive depth.
        
        Returns:
            (answer, confidence)
        """
        if not self.llm:
            self.load_model()
        
        # Clean inputs
        question = question.strip()
        context = (context or "").strip()
        
        if len(question) < 3:
            return "Please ask a clearer question.", 0.1
        
        # Detect question type and get appropriate token limit
        qtype, max_tokens = self._detect_question_type(question)
        
        # Build smart prompt
        prompt = self._build_prompt(question, context)
        
        try:
            # Generate with adaptive token limit
            response = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=0.5,        # Balanced for educational content
                top_p=0.9,
                repeat_penalty=1.1,
                stop=[
                    "</s>",             # Model end token
                    "\n\nQuestion:",    # Don't continue to next Q
                    "\nQuestion:",
                    "\n\n\n"            # Stop at large gaps
                ],
                echo=False,
                stream=False
            )
            
            # Extract text
            answer = self._extract_text(response)
            
            # Clean up answer
            answer = self._clean_answer(answer)
            
            # Ensure answer is complete
            answer = self._ensure_complete(answer)
            
            # Calculate confidence
            confidence = self._calculate_confidence(answer, context, qtype)
            
            return answer or "I couldn't generate an answer.", confidence
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return "Error generating answer.", 0.1
    
    def get_answer_stream(self, question: str, context: str = ""):
        """
        Stream tokens for real-time display.
        Maintains educational depth while streaming.
        """
        if not self.llm:
            self.load_model()
        
        question = question.strip()
        context = (context or "").strip()
        
        if len(question) < 3:
            yield "Please ask a clearer question."
            return
        
        # Detect type and tokens
        qtype, max_tokens = self._detect_question_type(question)
        
        # Build prompt
        prompt = self._build_prompt(question, context)
        
        try:
            # Stream with adaptive settings
            for chunk in self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=0.5,
                top_p=0.9,
                repeat_penalty=1.1,
                stop=["</s>", "\n\nQuestion:", "\nQuestion:", "\n\n\n"],
                echo=False,
                stream=True
            ):
                if chunk and "choices" in chunk:
                    if len(chunk["choices"]) > 0:
                        text = chunk["choices"][0].get("text", "")
                        if text:
                            yield text
                            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield "Error generating answer."
    
    def _extract_text(self, response) -> str:
        """Extract text from llama-cpp-python response."""
        if not response:
            return ""
        
        try:
            if isinstance(response, dict):
                if "choices" in response and len(response["choices"]) > 0:
                    choice = response["choices"][0]
                    return choice.get("text", "").strip()
            elif isinstance(response, str):
                return response.strip()
        except Exception as e:
            logger.error(f"Extract error: {e}")
        
        return ""
    
    def _clean_answer(self, answer: str) -> str:
        """Remove common artifacts and format issues."""
        if not answer:
            return ""
        
        # Remove common prefixes
        prefixes = ["Answer:", "A:", "answer:"]
        for prefix in prefixes:
            if answer.startswith(prefix):
                answer = answer[len(prefix):].strip()
        
        # Remove Q:/A: patterns
        answer = re.sub(r'^[QA]:\s*', '', answer, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove exercises/practice sections
        stop_markers = [
            "\n\nExercise:", "\n\nPractice:", "\n\nNow try",
            "\nExercise:", "\nPractice:", "\nNow try"
        ]
        for marker in stop_markers:
            if marker in answer:
                answer = answer.split(marker)[0]
        
        return answer.strip()
    
    def _ensure_complete(self, answer: str) -> str:
        """Ensure answer ends with complete sentence."""
        if not answer or len(answer) < 10:
            return answer
        
        # Check if ends with punctuation
        if answer[-1] not in '.!?':
            # Find last complete sentence
            for punct in ['.', '!', '?']:
                idx = answer.rfind(punct)
                if idx > len(answer) * 0.6:  # In last 40% of text
                    answer = answer[:idx+1]
                    logger.debug(f"Trimmed to last complete sentence")
                    return answer
            
            # No punctuation found - add period
            answer += "."
        
        return answer
    
    def _calculate_confidence(self, answer: str, context: str, qtype: str) -> float:
        """Calculate confidence based on answer quality."""
        if not answer or len(answer) < 10:
            return 0.2
        
        # Base confidence
        confidence = 0.65
        
        # Length appropriateness (not too short)
        word_count = len(answer.split())
        if word_count >= 20:
            confidence += 0.1
        elif word_count < 10:
            confidence -= 0.2
        
        # Has structure (multiple sentences)
        sentence_count = answer.count('.') + answer.count('!') + answer.count('?')
        if sentence_count >= 2:
            confidence += 0.1
        
        # Context availability
        if context and len(context.strip()) > 30:
            confidence += 0.15  # Context = more reliable
        
        return min(1.0, max(0.1, confidence))
    
    def get_hints(self, question: str, context: str = "") -> list[str]:
        """Generate 3 helpful hints."""
        if not self.llm:
            self.load_model()
        
        context = (context or "").strip()
        
        prompt = (
            f"Give 3 brief hints to help answer this question.\n\n"
            f"Question: {question}\n\n"
            f"Hints:\n1."
        )
        
        try:
            response = self.llm(
                prompt,
                max_tokens=100,
                temperature=0.4,
                stop=["\n4", "4.", "\n\n"],
                echo=False
            )
            
            text = self._extract_text(response)
            
            # Parse hints
            hints = []
            for line in text.split('\n'):
                line = line.strip()
                if line and line[0].isdigit():
                    # Remove number prefix
                    hint = re.sub(r'^\d+[\.)]\s*', '', line)
                    if len(hint) > 10:
                        hints.append(hint)
            
            if len(hints) >= 2:
                return hints[:3]
            else:
                return [
                    "Think about the key concepts in the question.",
                    "Consider what information would help explain this.",
                    "Break down the question into smaller parts."
                ]
                
        except Exception as e:
            logger.error(f"Hints error: {e}")
            return ["Review the question carefully.", "Think step-by-step.", "Connect to what you know."]
    
    def cleanup(self):
        """Free memory."""
        if self.llm:
            del self.llm
            self.llm = None
            logger.info("Cleaned up")