import os
from typing import Tuple, Any, Dict
from transformers import AutoTokenizer, AutoModelForQuestionAnswering, pipeline
import torch
import time

try:
    import onnxruntime as ort
    import numpy as np
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

class QnAHandler:
    """
    Handler for DistilBERT Q&A model using Hugging Face Transformers or ONNXRuntime.
    """
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.qa_pipeline = None
        self.onnx_session = None
        self.onnx_active = False
        self.onnx_model_path = os.path.join(model_path, "qna_quantized.onnx")

    def load_model(self) -> None:
        # Try ONNX first if available
        if ONNX_AVAILABLE and os.path.exists(self.onnx_model_path):
            if self.tokenizer is None:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            if self.onnx_session is None:
                self.onnx_session = ort.InferenceSession(self.onnx_model_path, providers=["CPUExecutionProvider"])
            self.onnx_active = True
            return
        # Fallback to Transformers pipeline
        if self.model is None or self.tokenizer is None:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForQuestionAnswering.from_pretrained(self.model_path)
            self.qa_pipeline = pipeline(
                "question-answering",
                model=self.model,
                tokenizer=self.tokenizer,
                device=-1,
                max_length=64
            )
        self.onnx_active = False

    def get_answer(self, question: str, context: str) -> tuple:
        start = time.time()
        self.load_model()
        if self.onnx_active:
            # ONNX inference logic
            inputs = self.tokenizer(
                question,
                context,
                return_tensors="np",
                max_length=512,
                truncation=True,
                padding="max_length"
            )
            input_ids = inputs["input_ids"]
            attention_mask = inputs["attention_mask"]
            outputs = self.onnx_session.run(None, {"input_ids": input_ids, "attention_mask": attention_mask})
            start_logits, end_logits = outputs
            # Find the most probable start and end logits
            start_idx = int(np.argmax(start_logits, axis=1)[0])
            end_idx = int(np.argmax(end_logits, axis=1)[0])
            if end_idx < start_idx:
                end_idx = start_idx
            tokens = input_ids[0][start_idx:end_idx+1]
            answer = self.tokenizer.decode(tokens, skip_special_tokens=True)
            # Confidence: use softmax of max logit as a proxy
            import scipy.special
            start_conf = float(scipy.special.softmax(start_logits[0])[start_idx])
            end_conf = float(scipy.special.softmax(end_logits[0])[end_idx])
            score = (start_conf + end_conf) / 2
            end = time.time()
            print(f"[QnAHandler:ONNX] Inference time: {end-start:.2f}s")
            return answer, score
        else:
            result = self.qa_pipeline({"question": question, "context": context})
            end = time.time()
            print(f"[QnAHandler] Inference time: {end-start:.2f}s")
            answer = result['answer']
            score = result.get('score', 0.0)
            return answer, score

    def get_model_info(self) -> Dict[str, Any]:
        if self.onnx_active:
            quant = 'ONNX Quantized'
        else:
            quant = 'None'
        return {
            'name': 'DistilBERT QnA',
            'version': '1.0',
            'quantization': quant,
            'max_length': 512,
            'temperature': 0.0,
            'top_p': 0.0,
            'num_beams': 0
        } 