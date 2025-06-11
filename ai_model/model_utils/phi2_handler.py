import os
import json
import logging
import time
from typing import Tuple, Optional, List, Dict, Any
from llama_cpp import Llama

logger = logging.getLogger(__name__)

class Phi2Handler:
    """
    Handler for Microsoft's Phi-2 model using GGUF format and llama.cpp backend.
    Optimized for CPU usage on low-resource hardware.
    """
    
    def __init__(self, model_path: str):
        """
        Initialize the Phi-2 model handler.
        
        Args:
            model_path (str): Path to the model directory containing GGUF file
        """
        self.model_path = model_path
        self.llm = None
        self.config = self._load_config()
        self.model_file = self._find_gguf_file()
        
    def _find_gguf_file(self) -> str:
        """Find the GGUF model file in the directory"""
        for file in os.listdir(self.model_path):
            if file.endswith(".gguf"):
                return os.path.join(self.model_path, file)
        raise FileNotFoundError("No GGUF model file found in directory")
    
    def _load_config(self) -> dict:
        """Load model configuration from config.json if exists, else defaults"""
        config_path = os.path.join(self.model_path, 'config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {str(e)}")
        
        # Default configuration optimized for low-resource hardware
        return {
            'n_ctx': 2048,          # Context window size
            'n_threads': 4,          # Number of CPU threads
            'n_gpu_layers': 0,       # Run on CPU only
            'max_tokens': 150,       # Maximum tokens to generate
            'temperature': 0.7,      # Creativity level
            'top_p': 0.9,            # Nucleus sampling
            'stop': ["\n", "###"]    # Stop sequences
        }
            
    def load_model(self) -> None:
        """Load the GGUF model using llama.cpp backend"""
        if self.llm is None:
            try:
                logger.info(f"Loading Phi-2 model from: {self.model_file}")
                start_time = time.time()
                
                self.llm = Llama(
                    model_path=self.model_file,
                    n_ctx=self.config.get('n_ctx', 2048),
                    n_threads=self.config.get('n_threads', 4),
                    n_gpu_layers=self.config.get('n_gpu_layers', 0),
                    verbose=False
                )
                
                load_time = time.time() - start_time
                logger.info(f"Phi-2 model loaded in {load_time:.2f} seconds")
            except Exception as e:
                logger.error(f"Error loading model: {str(e)}")
                raise
                
    def get_answer(self, question: str, context: str) -> Tuple[str, float]:
        """
        Generate an answer for the given question using the provided context.
        
        Args:
            question (str): The question to answer
            context (str): The context to use for answering
            
        Returns:
            Tuple[str, float]: The generated answer and confidence score
        """
        if self.llm is None:
            self.load_model()
            
        try:
            # Prepare input with better formatting for Phi-2
            prompt = (
                "You are a helpful educational assistant. Answer the following question "
                "based on the provided context. Be clear, concise, and accurate.\n\n"
                f"Context:\n{context}\n\n"
                f"Question: {question}\n\n"
                "Answer:"
            )
            
            # Generate response with adjusted parameters
            response = self.llm(
                prompt,
                max_tokens=self.config.get('max_tokens', 150),
                temperature=self.config.get('temperature', 0.7),
                top_p=self.config.get('top_p', 0.9),
                stop=self.config.get('stop', ["\n\n", "###"]),  # Changed stop sequences
                echo=False,
                stream=False
            )
            
            # Extract answer
            answer = response['choices'][0]['text'].strip()
            
            # Clean up the answer
            if not answer:
                # Try again with a simpler prompt
                simple_prompt = f"Question: {question}\nAnswer:"
                response = self.llm(
                    simple_prompt,
                    max_tokens=self.config.get('max_tokens', 150),
                    temperature=0.5,  # Lower temperature for more focused response
                    top_p=0.9,
                    stop=["\n\n", "###"],
                    echo=False,
                    stream=False
                )
                answer = response['choices'][0]['text'].strip()
            
            # If still no answer, provide a fallback
            if not answer:
                answer = "I couldn't generate a proper answer. Please try rephrasing your question."
            
            # Calculate confidence based on response characteristics
            confidence = self._calculate_confidence(answer, response)
            
            return answer, confidence
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return "I'm having trouble processing your question. Please try again.", 0.1
            
    def _calculate_confidence(self, answer: str, response: dict) -> float:
        """Calculate confidence score based on answer characteristics"""
        # Base confidence
        confidence = 0.7
        
        # Adjust based on answer length
        word_count = len(answer.split())
        if word_count < 3:  # Very short answers
            confidence *= 0.6
        elif word_count > 50:  # Very long answers
            confidence *= 0.8
        else:
            confidence += min(0.2, word_count * 0.02)  # Longer answers get slight boost
            
        # Adjust based on content
        low_confidence_phrases = [
            "i don't know", "cannot answer", "not sure", "unclear", 
            "sorry", "i'm not certain", "no information"
        ]
        
        if any(phrase in answer.lower() for phrase in low_confidence_phrases):
            confidence *= 0.5
            
        # Adjust based on token probabilities if available
        if 'logprobs' in response['choices'][0]:
            try:
                # Calculate average token probability
                logprobs = response['choices'][0]['logprobs']['token_logprobs']
                if logprobs:
                    avg_prob = sum(logprobs) / len(logprobs)
                    confidence = min(0.9, max(0.1, confidence * (1 + avg_prob)))
            except:
                pass
        
        # Ensure confidence is within bounds
        return max(0.1, min(0.95, confidence))
            
    def get_hints(self, question: str, context: str) -> List[str]:
        """
        Generate hints for the given question.
        
        Args:
            question (str): The question to generate hints for
            context (str): The context to use for generating hints
            
        Returns:
            List[str]: List of hints
        """
        if self.llm is None:
            self.load_model()
            
        try:
            # Prepare input for hint generation
            prompt = (
                f"### Context:\n{context}\n\n"
                f"### Question:\n{question}\n\n"
                "### Task:\nGenerate 3 concise hints to help answer the question. "
                "Each hint should be one sentence.\n\n"
                "### Hints:\n1."
            )
            
            # Generate hints with higher temperature
            response = self.llm(
                prompt,
                max_tokens=200,
                temperature=0.85,  # Higher temperature for creativity
                top_p=0.95,
                stop=["\n4", "###"],
                echo=False,
                stream=False
            )
            
            # Extract and parse hints
            hints_text = response['choices'][0]['text'].strip()
            hints = []
            
            # Split into lines and clean
            for line in hints_text.split('\n'):
                line = line.strip()
                if line and line[0].isdigit() and '.' in line:
                    # Remove numbering
                    hint = line.split('.', 1)[1].strip()
                    if hint:
                        hints.append(hint)
            
            # Ensure we have exactly 3 hints
            if len(hints) > 3:
                hints = hints[:3]
            elif len(hints) < 3:
                # Add default hints if we didn't get enough
                default_hints = [
                    "Look for key terms in the context related to the question.",
                    "Consider how different concepts in the context connect to each other.",
                    "Identify the main idea or purpose mentioned in the context."
                ]
                for i in range(3 - len(hints)):
                    hints.append(default_hints[i])
            
            return hints
            
        except Exception as e:
            logger.error(f"Error generating hints: {str(e)}")
            return [
                "Identify key terms in the question and find them in the context.",
                "Look for cause-and-effect relationships in the material.",
                "Try to summarize the main points of the context."
            ]

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dict[str, Any]: Model information
        """
        info = {
            "model_path": self.model_file,
            "context_size": self.config.get('n_ctx', 2048),
            "threads": self.config.get('n_threads', 4),
            "max_tokens": self.config.get('max_tokens', 150),
            "temperature": self.config.get('temperature', 0.7),
            "format": "GGUF"
        }
        
        # Try to get model metadata
        try:
            if self.llm:
                params = self.llm.params
                info.update({
                    "model_size": f"{params.n_gqa}G",  # Approximation
                    "quantization": getattr(params, 'quantization', "Unknown")
                })
        except:
            pass
            
        return info

    def cleanup(self):
        """Clean up model resources"""
        if self.llm is not None:
            del self.llm
            self.llm = None