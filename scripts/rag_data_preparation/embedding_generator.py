#!/usr/bin/env python3
# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
Semantic Embedding Generator for Satya Learning System

Generates high-quality semantic embeddings using Sentence Transformers.
Optimized for local execution on i3 processors.

Features:
- Uses `all-MiniLM-L6-v2` (small, fast, high accuracy)
- Batch processing for efficiency
- Caching of embeddings
- GPU support (if available, falls back to CPU)
- Standardized dimension (384D)
"""

import os
import json
import logging
import torch
from typing import List, Dict, Optional, Union, Any
from pathlib import Path
from tqdm import tqdm
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    logger.error("Missing dependency: sentence-transformers")
    logger.error("Install with: pip install sentence-transformers")
    raise


class EmbeddingGenerator:
    """
    Generates semantic embeddings using Sentence BERT.
    Default model: all-MiniLM-L6-v2 (384 dimensions, ~80MB)
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = None,
        batch_size: int = 16, # Reduced from 32 for i3 stability
        cache_dir: str = None
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        
        torch.set_num_threads(2)
        self.model_name = model_name
        self.batch_size = batch_size
        
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"Initializing Embedding Generator...")
        logger.info(f"   Model: {model_name}")
        logger.info(f"   Device: {self.device}")
        
        try:
            self.model = SentenceTransformer(
                model_name,
                device=self.device,
                cache_folder=cache_dir
            )
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
            
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"   Dimensions: {self.embedding_dim}")

    def generate_embeddings(
        self,
        texts: Union[str, List[str]],
        show_progress: bool = False
    ) -> Union[np.ndarray, List[np.ndarray]]:
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]
            
        try:
            valid_indices = [i for i, t in enumerate(texts) if t and t.strip()]
            valid_texts = [texts[i] for i in valid_indices]
            
            if not valid_texts:
                return np.array([]) if not is_single else np.zeros(self.embedding_dim)

            embeddings = self.model.encode(
                valid_texts,
                batch_size=self.batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            
            if len(valid_texts) < len(texts):
                full_embeddings = np.zeros((len(texts), self.embedding_dim))
                for i, valid_idx in enumerate(valid_indices):
                    full_embeddings[valid_idx] = embeddings[i]
                result = full_embeddings
            else:
                result = embeddings
                
            return result[0] if is_single else result
            
        except Exception as e:
            logger.error(f"Encoding failed: {e}")
            raise

    def process_chunk_file(
        self,
        input_file: str,
        output_file: str = None
    ) -> Dict:
        if output_file is None:
            output_file = input_file
            
        logger.info(f"Processing chunks from: {input_file}")
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if isinstance(data, list):
                chunks = data
            elif isinstance(data, dict) and 'chunks' in data:
                chunks = data['chunks']
            else:
                chunks = []
                for k, v in data.items():
                    if isinstance(v, list) and len(v) > 0 and 'text' in v[0]:
                        chunks = v
                        break
            
            if not chunks:
                logger.warning("No chunks found in file")
                return {'processed': 0, 'error': "No chunks found"}
                
            texts = [c.get('text', '') for c in chunks]
            
            logger.info(f"Generating embeddings for {len(texts)} chunks...")
            embeddings = self.generate_embeddings(texts, show_progress=True)
            
            for i, chunk in enumerate(chunks):
                if i < len(embeddings):
                    chunk['embedding'] = embeddings[i].tolist()
            
            output_data = {'chunks': chunks} if isinstance(data, list) else data

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False)
            
            logger.info(f"Saved updated chunks to {output_file}")
            
            return {
                'processed': len(chunks),
                'model': self.model_name,
                'dimension': self.embedding_dim
            }
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return {'processed': 0, 'error': str(e)}

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate semantic embeddings for text chunks")
    parser.add_argument("input", help="Input JSON file or directory containing chunks")
    parser.add_argument("--output", help="Output path (optional)")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--model", default="all-MiniLM-L6-v2", help="SentenceTransformer model name")
    
    args = parser.parse_args()
    
    generator = EmbeddingGenerator(
        model_name=args.model,
        batch_size=args.batch_size
    )
    
    if os.path.isfile(args.input):
        generator.process_chunk_file(args.input, args.output)
    elif os.path.isdir(args.input):
        input_path = Path(args.input)
        files = list(input_path.glob("*chunks*.json"))
        logger.info(f"📚 Found {len(files)} chunk files to process")
        
        for f in files:
            generator.process_chunk_file(str(f))

if __name__ == "__main__":
    main()