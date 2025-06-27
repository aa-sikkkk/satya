import os
from typing import List, Any, Dict
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch
import time

class HintHandler:
    """
    Handler for T5-small model for hint generation using Hugging Face Transformers.
    Falls back to Phi-2 for hints if T5 fails or outputs generic hints.
    """
    def __init__(self, model_path: str, phi2_handler=None):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.hint_pipeline = None
        self.phi2_handler = phi2_handler

    def load_model(self) -> None:
        if self.model is None or self.tokenizer is None:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_path)
            self.hint_pipeline = pipeline(
                "text2text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=-1,
                max_length=64
            )

    def get_hints(self, question: str, context: str) -> List[str]:
        default_hints = [
            "Break the question into smaller parts and look for clues in the context.",
            "Think about what you already know about this topic and connect it to the question.",
            "Don't worry if it's tricky—try to find the main idea or ask for help if you get stuck!"
        ]
        try:
            if self.hint_pipeline is None:
                try:
                    self.load_model()
                except Exception:
                    # T5 failed, try Phi-2 if available
                    if self.phi2_handler:
                        try:
                            hints = self.phi2_handler.get_hints(question, context)
                            if hints and not self._is_generic(hints):
                                return hints
                        except Exception:
                            pass
                    return default_hints
            start = time.time()
            prompt = f"Generate 3 short hints to help answer the following question.\nContext: {context}\nQuestion: {question}\nHints:"
            result = self.hint_pipeline(prompt, max_length=64, num_return_sequences=1, do_sample=False)
            end = time.time()
            print(f"[HintHandler] Inference time: {end-start:.2f}s")
            text = result[0]['generated_text'] if 'generated_text' in result[0] else result[0]['text']
            hints = [h.strip('-•. 1234567890') for h in text.split('\n') if h.strip()]
            if len(hints) < 3:
                hints = [h.strip('-•. 1234567890') for h in text.split('.') if h.strip()]
            hints = [h for h in hints if h]
            if self._is_generic(hints):
                # T5 output is generic, try Phi-2
                if self.phi2_handler:
                    try:
                        hints = self.phi2_handler.get_hints(question, context)
                        if hints and not self._is_generic(hints):
                            return hints
                    except Exception:
                        pass
                return default_hints
            return hints[:3]
        except Exception:
            # Both T5 and Phi-2 failed
            if self.phi2_handler:
                try:
                    hints = self.phi2_handler.get_hints(question, context)
                    if hints and not self._is_generic(hints):
                        return hints
                except Exception:
                    pass
            return default_hints

    def _is_generic(self, hints: List[str]) -> bool:
        generic_phrases = [
            "Context:", "Generate 3 short hints", "learning system for Grade 10 students", "Hints:", "question"
        ]
        return (
            not hints or
            any(any(phrase.lower() in h.lower() for phrase in generic_phrases) for h in hints) or
            sum(len(h) for h in hints) < 30
        )

    def get_model_info(self) -> Dict[str, Any]:
        return {
            'name': 'T5-small Hint',
            'version': '1.0',
            'quantization': 'None',
            'max_length': 128,
            'temperature': 0.0,
            'top_p': 0.0,
            'num_beams': 0
        } 