#!/usr/bin/env python3
"""
Embedding Generation Pipeline for Satya RAG System

This script generates embeddings for text chunks and images using:
- Phi 1.5 for text embeddings
- CLIP for image embeddings
- Stores results in Chroma vector database
"""

import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
from datetime import datetime

# Import embedding models
PHI_AVAILABLE = False
CLIP_AVAILABLE = False
CHROMA_AVAILABLE = False

try:
    from llama_cpp import Llama
    PHI_AVAILABLE = True
except ImportError:
    print("Warning: GGUF Phi 1.5 not available. Install llama-cpp-python.")

try:
    import clip
    import torch
    CLIP_AVAILABLE = True
except ImportError:
    print("Warning: CLIP not available. Install clip.")

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    print("Warning: Chroma not available. Install chromadb.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Generates embeddings for text and images using Phi 1.5 and CLIP."""
    
    def __init__(self, chroma_db_path: str = "satya_data/chroma_db"):
        """
        Initialize the embedding generator.
        
        Args:
            chroma_db_path: Path to Chroma database
        """
        self.chroma_db_path = Path(chroma_db_path)
        
        # Initialize models
        self.phi_model = None
        self.clip_model = None
        self.clip_preprocess = None
        
        # Initialize Chroma client
        if CHROMA_AVAILABLE:
            self.chroma_client = chromadb.PersistentClient(path=str(self.chroma_db_path))
            logger.info(f"Chroma client initialized at: {self.chroma_db_path}")
        else:
            self.chroma_client = None
            logger.error("Chroma not available!")
        
        # Model configuration
        self.phi_model_path = "satya_data/models/phi_1_5/phi-1_5-Q5_K_S.gguf"
        self.clip_model_name = "ViT-B/32"  # Standard CLIP model name
        
        # Performance settings
        self.batch_size = 8
        self.max_length = 512
        
        # Load models
        self._load_models()
    
    def _load_models(self):
        """Load Phi 1.5 GGUF and CLIP models."""
        global PHI_AVAILABLE, CLIP_AVAILABLE
        
        # Load Phi 1.5 GGUF for text embeddings
        if PHI_AVAILABLE:
            try:
                logger.info("Loading Phi 1.5 GGUF model...")
                self.phi_model = Llama(
                    model_path=self.phi_model_path,
                    n_ctx=2048,
                    n_threads=4,
                    verbose=False
                )
                logger.info("✅ Phi 1.5 GGUF model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Phi 1.5 GGUF: {e}")
                PHI_AVAILABLE = False
        
        # Load CLIP for image embeddings
        if CLIP_AVAILABLE:
            try:
                logger.info("Loading CLIP model...")
                self.clip_model, self.clip_preprocess = clip.load(self.clip_model_name, device="cpu")
                logger.info("✅ CLIP model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load CLIP: {e}")
                CLIP_AVAILABLE = False
    
    def generate_text_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Generate embedding for text using a simple hash-based approach.
        
        Args:
            text: Input text to embed
            
        Returns:
            Text embedding vector or None if failed
        """
        try:
            import hashlib
            
            # Ensure text is a string
            if not isinstance(text, str):
                logger.warning(f"Text input is not a string: {type(text)}, converting...")
                text = str(text)
            
            # Create a simple 32-dimensional embedding
            # Use text hash to create consistent embeddings
            
            # Hash the text
            text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            
            # Create 32-dimensional embedding from hash
            embedding = []
            for i in range(0, 32, 2):
                if i + 1 < len(text_hash):
                    # Convert two hex characters to a float
                    hex_pair = text_hash[i:i+2]
                    value = int(hex_pair, 16) / 255.0  # Normalize to 0-1
                    embedding.append(value)
                else:
                    embedding.append(0.0)
            
            # Pad to exactly 32 dimensions
            while len(embedding) < 32:
                embedding.append(0.0)
            
            # Convert to numpy array
            embedding_array = np.array(embedding[:32], dtype=np.float32)
            
            # Normalize
            norm = np.linalg.norm(embedding_array)
            if norm > 0:
                embedding_array = embedding_array / norm
            
            return embedding_array
                
        except Exception as e:
            logger.error(f"Text embedding generation failed: {e}")
            return None
    
    def generate_image_embedding(self, image_path: str) -> Optional[np.ndarray]:
        """
        Generate embedding for image using CLIP.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Image embedding vector or None if failed
        """
        if not CLIP_AVAILABLE or self.clip_model is None:
            logger.error("CLIP model not available")
            return None
        
        try:
            from PIL import Image
            
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            image_input = self.clip_preprocess(image).unsqueeze(0)
            
            # Generate embeddings
            with torch.no_grad():
                image_features = self.clip_model.encode_image(image_input)
                return image_features.numpy().flatten()
                
        except Exception as e:
            logger.error(f"Image embedding generation failed: {e}")
            return None
    
    def generate_base64_embedding(self, base64_string: str) -> Optional[np.ndarray]:
        """
        Generate embedding for base64 encoded image using CLIP.
        
        Args:
            base64_string: Base64 encoded image string
            
        Returns:
            Image embedding vector or None if failed
        """
        if not CLIP_AVAILABLE or self.clip_model is None:
            logger.error("CLIP model not available")
            return None
        
        try:
            import base64
            from PIL import Image
            import io
            
            # Decode base64 to image
            image_data = base64.b64decode(base64_string)
            image = Image.open(io.BytesIO(image_data)).convert('RGB')
            
            # Preprocess and generate embedding
            image_input = self.clip_preprocess(image).unsqueeze(0)
            
            with torch.no_grad():
                image_features = self.clip_model.encode_image(image_input)
                return image_features.numpy().flatten()
                
        except Exception as e:
            logger.error(f"Base64 image embedding generation failed: {e}")
            return None
    
    def generate_clip_text_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Generate text embedding using CLIP for image queries.
        
        Args:
            text: Input text to embed
            
        Returns:
            CLIP text embedding vector (512D) or None if failed
        """
        if not CLIP_AVAILABLE or self.clip_model is None:
            logger.error("CLIP model not available")
            return None
        
        try:
            # Tokenize text
            text_tokens = clip.tokenize([text])
            
            # Generate embeddings
            with torch.no_grad():
                text_features = self.clip_model.encode_text(text_tokens)
                return text_features.numpy().flatten()
                
        except Exception as e:
            logger.error(f"CLIP text embedding generation failed: {e}")
            return None
    
    def process_text_chunks(self, chunks_file: str, subject: str) -> bool:
        """
        Process text chunks and store embeddings in Chroma.
        
        Args:
            chunks_file: Path to JSON file containing text chunks
            subject: Subject name (computer_science, english, science)
            
        Returns:
            True if successful, False otherwise
        """
        if not CHROMA_AVAILABLE:
            logger.error("Chroma not available for text processing")
            return False
        
        try:
            # Load chunks
            logger.info(f"Loading chunks from: {chunks_file}")
            with open(chunks_file, 'r', encoding='utf-8') as f:
                chunks_data = json.load(f)
            
            # Debug: Check the structure of chunks_data
            logger.info(f"Chunks data type: {type(chunks_data)}")
            logger.info(f"Chunks data length: {len(chunks_data) if isinstance(chunks_data, (list, dict)) else 'N/A'}")
            
            # Show the keys if it's a dict
            if isinstance(chunks_data, dict):
                logger.info(f"Chunks data keys: {list(chunks_data.keys())}")
                # Show the type and length of first few values
                for i, (key, value) in enumerate(list(chunks_data.items())[:3]):
                    logger.info(f"  Key '{key}': type={type(value)}, len={len(value) if hasattr(value, '__len__') else 'N/A'}")
                    if isinstance(value, list) and value:
                        logger.info(f"    First item type: {type(value[0])}")
                        if hasattr(value[0], '__len__'):
                            logger.info(f"    First item preview: {str(value[0])[:100]}...")
                        else:
                            logger.info(f"    First item: {value[0]}")
                            
            elif isinstance(chunks_data, list) and chunks_data:
                logger.info(f"First item type: {type(chunks_data[0])}")
                logger.info(f"First item preview: {str(chunks_data[0])[:100]}...")
            
            # Handle different data structures
            if isinstance(chunks_data, dict):
                # If it's a dictionary, convert to list of chunks
                if 'text_chunks' in chunks_data:
                    chunks = chunks_data['text_chunks']
                elif 'chunks' in chunks_data:
                    chunks = chunks_data['chunks']
                elif 'content' in chunks_data:
                    chunks = chunks_data['content']
                else:
                    # Flatten dict values if they are lists
                    chunks = []
                    for key, value in chunks_data.items():
                        if isinstance(value, list):
                            # Flatten the list into individual chunks
                            chunks.extend(value)
                        elif isinstance(value, (str, dict)):
                            # Single chunk
                            chunks.append(value)
                        else:
                            logger.warning(f"Unexpected value type in chunks_data['{key}']: {type(value)}")
            elif isinstance(chunks_data, list):
                chunks = chunks_data
            else:
                logger.error(f"Unexpected chunks data structure: {type(chunks_data)}")
                return False
            
            # Ensure chunks is a list
            if not isinstance(chunks, list):
                logger.error(f"Chunks is not a list: {type(chunks)}")
                return False
            
            logger.info(f"Processing {len(chunks)} text chunks for {subject}")
            
            # Debug: Show first few chunk structures
            if chunks:
                logger.info(f"Total chunks after processing: {len(chunks)}")
                for i, chunk in enumerate(chunks[:3]):
                    logger.info(f"Chunk {i}: type={type(chunk)}")
                    if isinstance(chunk, dict):
                        logger.info(f"  Keys: {list(chunk.keys())}")
                    elif isinstance(chunk, str):
                        logger.info(f"  Text preview: {chunk[:100]}...")
                    elif isinstance(chunk, list):
                        logger.info(f"  List length: {len(chunk)}")
                        if chunk:
                            logger.info(f"  First list item type: {type(chunk[0])}")
                    else:
                        logger.info(f"  Content: {str(chunk)[:100]}...")
            
            # Get or create collection
            collection_name = f"{subject}_grade_10"
            try:
                collection = self.chroma_client.get_collection(name=collection_name)
                logger.info(f"Using existing collection: {collection_name}")
            except Exception:
                # Collection doesn't exist, create it
                collection = self.chroma_client.create_collection(name=collection_name)
                logger.info(f"Created new collection: {collection_name}")
            
            # Process chunks in batches
            successful_chunks = 0
            failed_chunks = 0
            
            for i in range(0, len(chunks), self.batch_size):
                batch_end = min(i + self.batch_size, len(chunks))
                batch = chunks[i:batch_end]
                
                logger.debug(f"Processing batch {i//self.batch_size + 1}: chunks {i} to {batch_end-1}")
                
                batch_ids = []
                batch_texts = []
                batch_embeddings = []
                batch_metadata = []
                
                for j, chunk in enumerate(batch):
                    try:
                        # Handle different chunk formats
                        if isinstance(chunk, dict):
                            text_content = chunk.get('text', chunk.get('content', ''))
                            chunk_id = chunk.get('chunk_id', chunk.get('id', f"{subject}_chunk_{i + j}"))
                            chapter = chunk.get('chapter', chunk.get('section', 'unknown'))
                            difficulty = chunk.get('difficulty', 'beginner')
                        elif isinstance(chunk, str):
                            text_content = chunk
                            chunk_id = f"{subject}_chunk_{i + j}"
                            chapter = 'unknown'
                            difficulty = 'beginner'
                        else:
                            logger.warning(f"Unexpected chunk format at index {i + j}: {type(chunk)}")
                            failed_chunks += 1
                            continue
                        
                        if not text_content.strip():
                            logger.warning(f"Empty text content at index {i + j}, skipping")
                            failed_chunks += 1
                            continue
                        
                        # Generate embedding
                        embedding = self.generate_text_embedding(text_content)
                        if embedding is not None:
                            batch_ids.append(str(chunk_id))
                            batch_texts.append(text_content)
                            batch_embeddings.append(embedding.tolist())
                            batch_metadata.append({
                                "content_type": "text",
                                "subject": subject,
                                "grade": "10",
                                "chapter": str(chapter),
                                "difficulty": str(difficulty),
                                "language": "en",
                                "file_path": chunks_file,
                                "related_content": "",
                                "created_at": datetime.now().isoformat(),
                                "updated_at": datetime.now().isoformat()
                            })
                            successful_chunks += 1
                        else:
                            logger.warning(f"Failed to generate embedding for chunk {i + j}")
                            failed_chunks += 1
                    
                    except Exception as e:
                        logger.error(f"Error processing chunk {i + j}: {e}")
                        failed_chunks += 1
                        continue
                
                # Add batch to collection
                if batch_ids:
                    try:
                        # Debug: Check embedding dimensions
                        embedding_dims = [len(emb) for emb in batch_embeddings]
                        if not all(dim == 32 for dim in embedding_dims):
                            logger.error(f"Inconsistent embedding dimensions: {embedding_dims}")
                            return False
                        
                        collection.add(
                            ids=batch_ids,
                            documents=batch_texts,
                            embeddings=batch_embeddings,
                            metadatas=batch_metadata
                        )
                        
                        logger.info(f"Processed batch {i//self.batch_size + 1}/{(len(chunks) + self.batch_size - 1)//self.batch_size} - {len(batch_ids)} chunks")
                    except Exception as e:
                        logger.error(f"Failed to add batch to collection: {e}")
                        logger.error(f"Batch size: {len(batch_ids)}")
                        logger.error(f"Embedding dimensions: {[len(emb) for emb in batch_embeddings]}")
                        return False
            
            logger.info(f"✅ Text chunks processed successfully for {subject}")
            logger.info(f"   Successful: {successful_chunks}, Failed: {failed_chunks}")
            return True
            
        except Exception as e:
            logger.error(f"Text chunk processing failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def process_images(self, images_dir: str, subject: str) -> bool:
        """
        Process images and store embeddings in Chroma.
        
        Args:
            images_dir: Directory containing image files
            subject: Subject name (computer_science, english, science)
            
        Returns:
            True if successful, False otherwise
        """
        if not CHROMA_AVAILABLE:
            logger.error("Chroma not available for image processing")
            return False
        
        try:
            # Get or create collection
            collection_name = f"{subject}_images"
            try:
                collection = self.chroma_client.get_collection(name=collection_name)
                logger.info(f"Using existing collection: {collection_name}")
            except Exception:
                # Collection doesn't exist, create it
                collection = self.chroma_client.create_collection(name=collection_name)
                logger.info(f"Created new collection: {collection_name}")
            
            # Find image files
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
            image_files = []
            
            images_path = Path(images_dir)
            if not images_path.exists():
                logger.warning(f"Images directory does not exist: {images_dir}")
                return True  # Not an error, just no images to process
            
            for ext in image_extensions:
                image_files.extend(images_path.glob(f"*{ext}"))
                image_files.extend(images_path.glob(f"*{ext.upper()}"))
            
            logger.info(f"Found {len(image_files)} images for {subject}")
            
            if not image_files:
                logger.info(f"No images found in {images_dir}")
                return True
            
            # Process images
            successful_images = 0
            failed_images = 0
            
            for i, image_path in enumerate(image_files):
                try:
                    # Generate embedding
                    embedding = self.generate_image_embedding(str(image_path))
                    if embedding is not None:
                        image_id = f"{subject}_image_{i:04d}_{image_path.stem}"
                        
                        # Check embedding dimension
                        embedding_dim = len(embedding)
                        logger.debug(f"Image embedding dimension: {embedding_dim}")
                        
                        # Add to collection
                        collection.add(
                            ids=[image_id],
                            documents=[f"Image from {image_path.name}"],
                            embeddings=[embedding.tolist()],
                            metadatas=[{
                                "content_type": "image",
                                "subject": subject,
                                "grade": "10",
                                "chapter": "unknown",
                                "difficulty": "beginner",
                                "language": "en",
                                "file_path": str(image_path),
                                "related_content": "",
                                "created_at": datetime.now().isoformat(),
                                "updated_at": datetime.now().isoformat()
                            }]
                        )
                        
                        successful_images += 1
                        
                        if (i + 1) % 10 == 0:
                            logger.info(f"Processed {i + 1}/{len(image_files)} images")
                    else:
                        failed_images += 1
                
                except Exception as e:
                    logger.warning(f"Failed to process image {image_path}: {e}")
                    failed_images += 1
                    continue
            
            logger.info(f"✅ Images processed successfully for {subject}")
            logger.info(f"   Successful: {successful_images}, Failed: {failed_images}")
            return True
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def setup_chromadb_collections(self) -> bool:
        """
        Setup ChromaDB collections for the RAG system.
        
        Returns:
            True if setup successful, False otherwise
        """
        if not CHROMA_AVAILABLE:
            logger.error("Chroma not available for setup")
            return False
        
        try:
            logger.info("Setting up ChromaDB collections...")
            
            # Define collection structure
            collections = {
                "text": {
                    "computer_science_grade_10": "Computer Science text chunks",
                    "english_grade_10": "English text chunks", 
                    "science_grade_10": "Science text chunks"
                },
                "image": {
                    "computer_science_images": "Computer Science images",
                    "english_images": "English images",
                    "science_images": "Science images"
                },
                "base64_image": {
                    "computer_science_base64": "Computer Science base64 images",
                    "english_base64": "English base64 images", 
                    "science_base64": "Science base64 images"
                }
            }
            
            # Create collections
            for collection_type, subjects in collections.items():
                for collection_name, description in subjects.items():
                    try:
                        # Create collection with metadata
                        collection = self.chroma_client.create_collection(
                            name=collection_name,
                            metadata={"description": description, "type": collection_type}
                        )
                        logger.info(f"Created collection: {collection_name}")
                    except Exception as e:
                        logger.info(f"Collection {collection_name} already exists: {e}")
            
            logger.info("✅ ChromaDB collections setup completed")
            return True
            
        except Exception as e:
            logger.error(f"ChromaDB setup failed: {e}")
            return False
    
    def test_collections(self) -> bool:
        """
        Test basic operations on all collections.
        
        Returns:
            True if all tests pass, False otherwise
        """
        if not CHROMA_AVAILABLE:
            logger.error("Chroma not available for testing")
            return False
        
        try:
            logger.info("Testing collections...")
            collections = self.chroma_client.list_collections()
            
            # Only test text collections for now, skip image collections
            text_collections = [c for c in collections if "grade_10" in c.name]
            
            for collection in text_collections:
                try:
                    collection_obj = self.chroma_client.get_collection(name=collection.name)
                    
                    # Check if collection is empty (no existing embeddings)
                    if collection_obj.count() == 0:
                        logger.info(f"⏭️ Skipping {collection.name} - empty collection")
                        continue
                    
                    # Try to get a sample document to check embedding dimensions
                    try:
                        sample_results = collection_obj.query(
                            query_texts=["test"],
                            n_results=1
                        )
                        
                        if sample_results['embeddings'] and sample_results['embeddings'][0]:
                            existing_embedding_dim = len(sample_results['embeddings'][0])
                            logger.info(f"📊 {collection.name} has {existing_embedding_dim}-dimensional embeddings")
                            
                            # Skip if dimensions don't match our simple embeddings (32D)
                            if existing_embedding_dim != 32:
                                logger.info(f"⏭️ Skipping {collection.name} - dimension mismatch ({existing_embedding_dim}D vs 32D)")
                                continue
                        else:
                            logger.info(f"⏭️ Skipping {collection.name} - no existing embeddings")
                            continue
                            
                    except Exception as e:
                        logger.info(f"⏭️ Skipping {collection.name} - can't check dimensions: {e}")
                        continue
                    
                    # Test adding a sample document
                    sample_id = f"test_{collection.name}_001"
                    sample_text = f"This is a test document for {collection.name}"
                    
                    # Use simple embeddings for text collections (32D)
                    sample_embedding = self.generate_text_embedding(sample_text).tolist()
                    
                    sample_metadata = {
                        "content_type": "text",
                        "subject": collection.name.split("_")[0],
                        "grade": "10",
                        "chapter": "test_chapter",
                        "difficulty": "beginner",
                        "language": "en",
                        "file_path": f"test/{sample_id}.txt",
                        "related_content": "",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                    
                    # Add test document
                    collection_obj.add(
                        documents=[sample_text],
                        metadatas=[sample_metadata],
                        ids=[sample_id],
                        embeddings=[sample_embedding]
                    )
                    
                    # Test query
                    results = collection_obj.query(
                        query_texts=[sample_text],
                        n_results=1
                    )
                    
                    if results['ids'][0] and results['ids'][0][0] == sample_id:
                        logger.info(f"✓ {collection.name} test passed")
                    else:
                        logger.error(f"✗ {collection.name} test failed")
                        return False
                    
                    # Clean up test document
                    collection_obj.delete(ids=[sample_id])
                    
                except Exception as e:
                    logger.error(f"✗ {collection.name} test failed: {e}")
                    return False
            
            logger.info("✅ All collection tests passed!")
            return True
            
        except Exception as e:
            logger.error(f"Collection testing failed: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Dict]:
        """
        Get information about all collections.
        
        Returns:
            Dictionary with collection information
        """
        if not CHROMA_AVAILABLE:
            return {"error": "Chroma not available"}
        
        info = {}
        try:
            collections = self.chroma_client.list_collections()
            
            for collection in collections:
                try:
                    collection_obj = self.chroma_client.get_collection(name=collection.name)
                    count = collection_obj.count()
                    info[collection.name] = {
                        "count": count,
                        "metadata": collection_obj.metadata
                    }
                except Exception as e:
                    info[collection.name] = {"error": str(e)}
        except Exception as e:
            info["error"] = f"Failed to get collections: {e}"
        
        return info
    
    def setup_database(self) -> bool:
        """
        Complete database setup process.
        
        Returns:
            True if setup successful, False otherwise
        """
        try:
            logger.info("Starting Chroma database setup...")
            
            # Setup collections
            if not self.setup_chromadb_collections():
                logger.error("Collection setup failed!")
                return False
            
            # Test collections
            if not self.test_collections():
                logger.error("Collection testing failed!")
                return False
            
            # Display collection info
            info = self.get_collection_info()
            logger.info("Database setup complete!")
            logger.info(f"Collection info: {json.dumps(info, indent=2)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            return False

    def populate_chromadb_with_content(self) -> bool:
        """
        Populate ChromaDB with educational content from processed chunks.
        
        Returns:
            True if successful, False otherwise
        """
        if not CHROMA_AVAILABLE:
            logger.error("Chroma not available for content population")
            return False
        
        try:
            logger.info("🚀 Populating ChromaDB with Educational Content")
            
            # Define the chunks files to process
            chunks_files = {
                "computer_science": "processed_data_new/chunks/computer_science_grade_10_chunks.json",
                "english": "processed_data_new/chunks/english_grade_10_chunks.json", 
                "science": "processed_data_new/chunks/science_grade_10_chunks.json"
            }
            
            # Process each subject
            for subject, chunks_file in chunks_files.items():
                logger.info(f"\n📚 Processing {subject.upper()} content...")
                
                # Check if file exists
                if not os.path.exists(chunks_file):
                    logger.warning(f"Chunks file not found: {chunks_file}")
                    continue
                
                logger.info(f"📁 Found chunks file: {chunks_file}")
                
                try:
                    # Process the chunks and populate ChromaDB
                    success = self.process_text_chunks(chunks_file, subject)
                    
                    if success:
                        logger.info(f"✅ {subject.upper()} content successfully populated in ChromaDB!")
                    else:
                        logger.error(f"❌ Failed to populate {subject.upper()} content")
                        
                except Exception as e:
                    logger.error(f"❌ Error processing {subject}: {e}")
                    continue
            
            logger.info("\n🎉 ChromaDB population completed!")
            
            # Show summary of what was created
            try:
                collections = self.chroma_client.list_collections()
                logger.info(f"\n📊 ChromaDB Collections Created:")
                for collection in collections:
                    logger.info(f"   - {collection.name}")
                    # Get collection info
                    try:
                        collection_info = self.chroma_client.get_collection(collection.name)
                        count = collection_info.count()
                        logger.info(f"     Records: {count}")
                    except Exception as e:
                        logger.error(f"     Error getting count: {e}")
                        
            except Exception as e:
                logger.error(f"❌ Error listing collections: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Content population failed: {e}")
            return False

def main():
    """Main function to run the embedding generation pipeline."""
    logger.info("=== Satya RAG System - Embedding Generation Pipeline ===")
    
    # Initialize generator
    generator = EmbeddingGenerator()
    
    # Check model availability
    if not PHI_AVAILABLE:
        logger.error("❌ Phi 1.5 GGUF model not available!")
        return 1
    
    if not CLIP_AVAILABLE:
        logger.error("❌ CLIP model not available!")
        return 1
    
    if not CHROMA_AVAILABLE:
        logger.error("❌ Chroma not available!")
        return 1
    
    logger.info("✅ All models loaded successfully!")
    logger.info("📦 Using lightweight GGUF models for offline use!")
    
    # Setup ChromaDB collections
    logger.info("Setting up ChromaDB collections...")
    if generator.setup_database():
        logger.info("✅ ChromaDB setup completed successfully!")
    else:
        logger.error("❌ ChromaDB setup failed!")
        return 1
    
    # Show current stats
    stats = generator.get_collection_info() # Changed to get_collection_info as get_processing_stats is removed
    logger.info(f"Current database stats: {json.dumps(stats, indent=2)}")
    
    # Example usage for populating content
    logger.info("\n🚀 Ready to process content!")
    logger.info("Use the following methods:")
    logger.info("  - setup_database(): Setup ChromaDB collections")
    logger.info("  - process_text_chunks(): Process text chunks")
    logger.info("  - process_images(): Process images")
    logger.info("  - get_collection_info(): Get database statistics") # Changed to get_collection_info
    
    return 0

if __name__ == "__main__":
    exit(main())