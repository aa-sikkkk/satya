import os
from typing import Tuple, Any, Dict
from transformers import AutoTokenizer, AutoModelForQuestionAnswering, pipeline
import torch

class QnAHandler:
    """
    Handler for DistilBERT Q&A model using Hugging Face Transformers.
    """
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.qa_pipeline = None

    def load_model(self) -> None:
        if self.model is None or self.tokenizer is None:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForQuestionAnswering.from_pretrained(self.model_path)
            self.qa_pipeline = pipeline('question-answering', model=self.model, tokenizer=self.tokenizer, device=-1)

    def get_answer(self, question: str, context: str) -> Tuple[str, float]:
        if self.qa_pipeline is None:
            self.load_model()
        try:
            result = self.qa_pipeline({'question': question, 'context': context})
            answer = result['answer']
            score = result['score']  # This is the probability/confidence
            # Heuristic: if answer is empty or very short, lower confidence
            if not answer or len(answer.strip()) < 2:
                return '', 0.0
            confidence = float(score)
            return answer, confidence
        except Exception:
            return '', 0.0

    def get_model_info(self) -> Dict[str, Any]:
        return {
            'name': 'DistilBERT QnA',
            'version': '1.0',
            'quantization': 'None',
            'max_length': 512,
            'temperature': 0.0,
            'top_p': 0.0,
            'num_beams': 0
        } 