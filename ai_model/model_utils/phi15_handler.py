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
    
    STOP_SEQUENCES = ["</s>", "\n\nQuestion:", "\n\nQ:", "Exercise", "Instructions:", "Reference material:"]  # Added to prevent hallucinations
    
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
        if self.llm is not None:
            return
        
        logger.info("Loading Phi 1.5 (CPU-optimized)...")
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=2048,       # Full context window support
            n_batch=96,
            n_threads=4,      
            use_mmap=True,
            use_mlock=False,
            f16_kv=False,
            verbose=False
        )
        logger.info("Model loaded!")
    
    def _build_prompt(self, question: str, context: str) -> str:
        context = (context or "").strip()
        
        # Prompt for RAG Use
        base_instruction = (
            "Instruct: You are Satya, an expert tutor. Use the Reference Material to write a specific, technical answer. "
            "Use scientific terms and details from the text. Explain functions and processes clearly. "
            "Avoid generic definitions.\n"
            "Output:"
        )
        
        if context:
            # I have trimmed the context to 300.
            if len(context) > 300:
                context = context[:300].rsplit('.', 1)[0] + '.'
            return f"{base_instruction}\nReference material:\n{context}\n\nQuestion: {question}\nAnswer:"
        
        return f"{base_instruction}\nQuestion: {question}\nAnswer:"
    
    def _clean_answer(self, answer: str) -> str:
        if not answer:
            return ""
        
        answer = answer.strip()
        
  
        answer = re.sub(r'^(Q:|A:)\s*', '', answer, flags=re.I)
        answer = re.sub(r'\n(Q:|A:)\s*', '\n', answer, flags=re.I)
        

        off_markers = ["Exercise:", "Practice:", "Try this:", "Use Case:", "Real-world"]
        for marker in off_markers:
            if marker in answer:
                answer = answer.split(marker)[0].strip()
        

        answer = re.sub(r'\s+', ' ', answer)
        

        if answer and not answer[-1] in ".!?":
            answer += '.'
        
        return answer
    
    def _calculate_confidence(self, answer: str, question: str) -> float:
        if not answer or len(answer.split()) < 5:
            return 0.3
        
        q_words = set(w.lower() for w in question.split() if len(w) > 3)
        a_words = set(w.lower() for w in answer.split())
        relevance = len(q_words & a_words) / max(1, len(q_words))
        
        return min(1.0, 0.5 + relevance * 0.5)
    
    def get_answer_stream(self, question: str, context: str = "") -> Iterator[str]:
        if not self.llm:
            self.load_model()
        
        if not question or len(question.strip()) < 3:
            yield "Please provide a proper question."
            return
        
        prompt = self._build_prompt(question, context)
        
        try:

            for chunk in self.llm(
                prompt,
                max_tokens=512,  # Increased to 512 to allow for detailed, complete answers
                temperature=0.6,
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
        if not self.llm:
            self.load_model()
        
        if not question or len(question.strip()) < 3:
            return "Please provide a proper question.", 0.1
        
        prompt = self._build_prompt(question, context)
        
        try:
            response = self.llm(
                prompt,
                max_tokens=512,  
                temperature=0.6,
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
        if self.llm:
            del self.llm
            self.llm = None
            logger.info("Model cleaned up")