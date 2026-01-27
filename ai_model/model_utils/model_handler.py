#!/usr/bin/env python3
# Copyright (C) 2026 Aashik
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Model Handler for Satya Learning System
CPU-first with Simple Handler interface
"""

import os
import logging
from typing import Dict, Any, List, Tuple, Iterator, Optional

from .phi15_handler import SimplePhiHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleHandler:
    """Lightweight single-phase interface for RAG queries."""
    
    
    def __init__(self, phi_handler):
        self.phi_handler = phi_handler
    
    def get_answer(self, query_text: str, context_text: str) -> Tuple[str, float]:
        """Single-step answer generation."""
        try:
            return self.phi_handler.get_answer(query_text, context_text)
        except Exception as e:
            logger.error(f"SimpleHandler error: {e}")
            return "Error generating answer.", 0.0


class ModelHandler:
    """Model handler with Simple Phi Handler interface for i3 optimization."""
    
    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            model_path = os.path.join("satya_data", "models", "phi15")
        
        from pathlib import Path
        model_dir = Path(model_path)
        gguf_files = list(model_dir.glob("*.gguf"))
        
        if not gguf_files:
            raise FileNotFoundError(f"No .gguf file found in {model_path}")
        
        model_file = str(gguf_files[0])
        logger.info(f"Using model: {model_file}")
        
        self.model_path = model_path
        self.handler = SimplePhiHandler(model_file)
        
        try:
            logger.info("Loading Phi 1.5...")
            self.handler.load_model()
            self.handler.warm_up()
            logger.info("Model ready!")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
        
        self.simple_handler = SimpleHandler(self.handler)
    
    def get_answer(self, question: str, context: str = "", answer_length: str = "medium") -> Tuple[str, float]:
        try:
            return self.handler.get_answer(question, context)
        except Exception as e:
            logger.error(f"Error: {e}")
            return "I'm having trouble with your question. Please try again.", 0.1
    
    def get_answer_stream(self, question: str, context: str = "", answer_length: str = "medium") -> Iterator[str]:
        try:
            yield from self.handler.get_answer_stream(question, context)
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield "I'm having trouble with your question. Please try again."
            
    def generate_response(self, prompt: str, max_tokens: int = 512) -> str:
        """Video passthrough for raw prompt generation."""
        try:
             return self.handler.generate_response(prompt, max_tokens)
        except Exception as e:
             logger.error(f"Gen Error: {e}")
             return ""
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": "Phi 1.5",
            "version": "1.5",
            "format": "GGUF",
            "backend": "llama-cpp-python",
            "optimized_for": "i3_cpu",
            "context_size": "384 tokens"
        }
    
    def cleanup(self):
        try:
            self.handler.cleanup()
            logger.info("Model cleaned up")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")