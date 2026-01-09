#!/usr/bin/env python3
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
        """
        Initialize the embedding generator.
        
        Args:
            model_name: Name of sentence-transformer model
            device: 'cpu', 'cuda', or None (auto-detect)
            batch_size: Batch size for encoding
            cache_dir: Directory to cache model files
        """
        self.model_name = model_name
        self.batch_size = batch_size
        
        # Optimize for i3 (Low core count)
        torch.set_num_threads(2)
        self.model_name = model_name
        self.batch_size = batch_size
        
        # Auto-detect device if not specified
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"🔄 Initializing Embedding Generator...")
        logger.info(f"   Model: {model_name}")
        logger.info(f"   Device: {self.device}")
        
        try:
            self.model = SentenceTransformer(
                model_name,
                device=self.device,
                cache_folder=cache_dir
            )
            logger.info("✅ Model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise
            
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"   Dimensions: {self.embedding_dim}")

    def generate_embeddings(
        self,
        texts: Union[str, List[str]],
        show_progress: bool = False
    ) -> Union[np.ndarray, List[np.ndarray]]:
        """
        Generate embeddings for a text or list of texts.
        
        Args:
            texts: Single string or list of strings
            show_progress: Whether to show progress bar
            
        Returns:
            Numpy array of embeddings
        """
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]
            
        try:
            # Filter out empty strings to prevent errors/useless computations
            valid_indices = [i for i, t in enumerate(texts) if t and t.strip()]
            valid_texts = [texts[i] for i in valid_indices]
            
            if not valid_texts:
                return np.array([]) if not is_single else np.zeros(self.embedding_dim)

            embeddings = self.model.encode(
                valid_texts,
                batch_size=self.batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
                normalize_embeddings=True  # Important for cosine similarity
            )
            
            # Map back to original list (preserving order, keeping empty for empty inputs)
            if len(valid_texts) < len(texts):
                full_embeddings = np.zeros((len(texts), self.embedding_dim))
                for i, valid_idx in enumerate(valid_indices):
                    full_embeddings[valid_idx] = embeddings[i]
                result = full_embeddings
            else:
                result = embeddings
                
            return result[0] if is_single else result
            
        except Exception as e:
            logger.error(f"❌ Encoding failed: {e}")
            raise

    def process_chunk_file(
        self,
        input_file: str,
        output_file: str = None
    ) -> Dict:
        """
        Process a JSON chunk file and add embeddings.
        
        Args:
            input_file: Path to input JSON file with chunks
            output_file: Path to save result (defaults to input_file)
            
        Returns:
            Dictionary with processing stats
        """
        if output_file is None:
            output_file = input_file
            
        logger.info(f"📖 Processing chunks from: {input_file}")
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Handle different formats (list vs dict wrapper)
            if isinstance(data, list):
                chunks = data
            elif isinstance(data, dict) and 'chunks' in data:
                chunks = data['chunks']
            else:
                chunks = []
                # Try finding any list value that looks like chunks
                for k, v in data.items():
                    if isinstance(v, list) and len(v) > 0 and 'text' in v[0]:
                        chunks = v
                        break
            
            if not chunks:
                logger.warning("No chunks found in file")
                return {'processed': 0, 'error': "No chunks found"}
                
            # Extract texts
            texts = [c.get('text', '') for c in chunks]
            
            # Generate embeddings
            logger.info(f"⚡ Generating embeddings for {len(texts)} chunks...")
            embeddings = self.generate_embeddings(texts, show_progress=True)
            
            # Add to chunks
            for i, chunk in enumerate(chunks):
                if i < len(embeddings):
                    # Convert numpy array to list for JSON serialization
                    chunk['embedding'] = embeddings[i].tolist()
            
            # Save back
            output_data = {'chunks': chunks} if isinstance(data, list) else data
            if isinstance(data, dict) and 'chunks' not in data:
                 # If we found chunks in a subkey, updated them in place, so just save data
                 pass

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False) # No indent to save space? Or indent=2?
                # indent=None is better for large files, but indent=1 helps debugging.
                # Let's check size. If these are final processed files, smaller is better.
            
            logger.info(f"💾 Saved updated chunks to {output_file}")
            
            return {
                'processed': len(chunks),
                'model': self.model_name,
                'dimension': self.embedding_dim
            }
            
        except Exception as e:
            logger.error(f"❌ Processing failed: {e}")
            return {'processed': 0, 'error': str(e)}

def main():
    """CLI Interface"""
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
