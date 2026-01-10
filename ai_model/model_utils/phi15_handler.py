#!/usr/bin/env python3
"""
Simple Phi Handler for Satya Learning System
CPU-first, single-call implementation
"""

import re
import logging
from typing import Iterator, Tuple
from llama_cpp import Llama

logger = logging.getLogger(__name__)

class SimplePhiHandler:
    """Lightweight single-phase handler for i3 processors."""
    
    STOP_SEQUENCES = ["\n\nQ:", "\n\nQuestion:", "</s>", "\nQuestion:", "\nQ:"]
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.llm = None
        self.system_prompt = (
            "You are Satya, a clear and patient educational tutor.\n"
            "Explain concepts to high-school students.\n"
            "Provide clear, concise, and complete answers.\n"
            "Do not include exercises, Q/A echoes, or lists."
        )
    
    def load_model(self):
        """Load model with i3-optimized settings."""
        if self.llm is not None:
            return
        
        logger.info("Loading Phi 1.5 (CPU-optimized)...")
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=384,
            n_batch=96,
            n_threads=4,      # i3 cores
            use_mmap=True,
            use_mlock=False,
            f16_kv=False,
            verbose=False
        )
        logger.info("Model loaded!")
    
    def _build_prompt(self, question: str, context: str) -> str:
        """Build educational prompt with optional context."""
        context = (context or "").strip()
        if context:
            # Trim context to 200 chars for i3 performance
            if len(context) > 200:
                context = context[:200].rsplit('.', 1)[0] + '.'
            return f"{self.system_prompt}\n\nStudy material:\n{context}\n\nQ: {question}\nA:"
        
        return f"{self.system_prompt}\n\nQ: {question}\nA:"
    
    def _clean_answer(self, answer: str) -> str:
        """Clean answer output."""
        if not answer:
            return ""
        
        answer = answer.strip()
        
        # Remove Q/A echoes
        answer = re.sub(r'^(Q:|A:)\s*', '', answer, flags=re.I)
        answer = re.sub(r'\n(Q:|A:)\s*', '\n', answer, flags=re.I)
        
        # Remove off-topic markers
        off_markers = ["Exercise:", "Practice:", "Try this:", "Use Case:", "Real-world"]
        for marker in off_markers:
            if marker in answer:
                answer = answer.split(marker)[0].strip()
        
        # Collapse multiple spaces
        answer = re.sub(r'\s+', ' ', answer)
        
        # Ensure ends with proper punctuation
        if answer and not answer[-1] in ".!?":
            answer += '.'
        
        return answer
    
    def _calculate_confidence(self, answer: str, question: str) -> float:
        """Calculate confidence based on answer quality."""
        if not answer or len(answer.split()) < 5:
            return 0.3
        
        q_words = set(w.lower() for w in question.split() if len(w) > 3)
        a_words = set(w.lower() for w in answer.split())
        relevance = len(q_words & a_words) / max(1, len(q_words))
        
        return min(1.0, 0.5 + relevance * 0.5)
    
    def get_answer_stream(self, question: str, context: str = "") -> Iterator[str]:
        """Stream answer tokens in real-time."""
        if not self.llm:
            self.load_model()
        
        if not question or len(question.strip()) < 3:
            yield "Please provide a proper question."
            return
        
        prompt = self._build_prompt(question, context)
        
        try:
            # Stream directly from LLM
            for chunk in self.llm(
                prompt,
                max_tokens=200,
                temperature=0.5,
                top_p=0.9,
                repeat_penalty=1.08,
                stop=self.STOP_SEQUENCES,
                stream=True
            ):
                if chunk and "choices" in chunk:
                    if len(chunk["choices"]) > 0:
                        text = chunk["choices"][0].get("text", "")
                        if text:
                            yield text
        
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield "Error generating answer. Please try again."
    
    def get_answer(self, question: str, context: str = "") -> Tuple[str, float]:
        """Get complete answer (non-streaming)."""
        if not self.llm:
            self.load_model()
        
        if not question or len(question.strip()) < 3:
            return "Please provide a proper question.", 0.1
        
        prompt = self._build_prompt(question, context)
        
        try:
            response = self.llm(
                prompt,
                max_tokens=200,
                temperature=0.5,
                top_p=0.9,
                repeat_penalty=1.08,
                stop=self.STOP_SEQUENCES,
                stream=False
            )
            
            raw = response["choices"][0]["text"].strip()
            answer_clean = self._clean_answer(raw)
            confidence = self._calculate_confidence(answer_clean, question)
            
            return answer_clean, confidence
        
        except Exception as e:
            logger.error(f"Answer generation error: {e}")
            return "Error generating answer.", 0.1
    
    def cleanup(self):
        """Free memory."""
        if self.llm:
            del self.llm
            self.llm = None
            logger.info("Model cleaned up")