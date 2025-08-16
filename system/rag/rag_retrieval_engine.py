"""
RAG Retrieval Engine for Satya Learning System

This module provides intelligent content retrieval using ChromaDB and
Phi 1.5 embeddings for enhanced question answering.
"""

import os
import json
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import chromadb
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGRetrievalEngine:
    """
    Intelligent content retrieval engine using ChromaDB and Phi 1.5.
    
    Attributes:
        chroma_client: ChromaDB client for vector search
        embedding_model: Phi 1.5 model for text embeddings
        collections: Available ChromaDB collections
    """
    
    def __init__(self, chroma_db_path: str = "satya_data/chroma_db"):
        """
        Initialize the RAG retrieval engine.
        
        Args:
            chroma_db_path: Path to ChromaDB database
        """
        self.chroma_db_path = Path(chroma_db_path)
        self.chroma_client = None
        self.collections = {}
        
        # Initialize ChromaDB
        self._initialize_chromadb()
        
        # Initialize embedding model
        self.embedding_model = None
        self._initialize_embedding_model()
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB client and load collections."""
        try:
            self.chroma_client = chromadb.PersistentClient(path=str(self.chroma_db_path))

            
            # Get available collections
            collections = self.chroma_client.list_collections()
            for collection in collections:
                self.collections[collection.name] = collection

                
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def _initialize_embedding_model(self):
        """Initialize Phi 1.5 embedding model."""
        try:
            # For now, use simple hash-based embeddings (32D)
            # This can be upgraded to actual Phi 1.5 later

            self.embedding_model = "hash_based"
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            # Fall back to hash-based embeddings
            self.embedding_model = "hash_based"
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for text using current model.
        
        Args:
            text: Input text to embed
            
        Returns:
            Text embedding vector
        """
        if self.embedding_model == "hash_based":
            return self._generate_hash_embedding(text)
        else:
            # Placeholder for Phi 1.5 embeddings
            return self._generate_hash_embedding(text)
    
    def _generate_hash_embedding(self, text: str) -> np.ndarray:
        """Generate 32-dimensional hash-based embedding."""
        import hashlib
        
        # Ensure text is a string
        if not isinstance(text, str):
            text = str(text)
        
        # Hash the text
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        
        # Create 32-dimensional embedding from hash
        embedding = []
        for i in range(0, 32, 2):
            if i + 1 < len(text_hash):
                hex_pair = text_hash[i:i+2]
                value = int(hex_pair, 16) / 255.0  # Normalize to 0-1
                embedding.append(value)
            else:
                embedding.append(0.0)
        
        # Pad to exactly 32 dimensions
        while len(embedding) < 32:
            embedding.append(0.0)
        
        # Convert to numpy array and normalize
        embedding_array = np.array(embedding[:32], dtype=np.float32)
        norm = np.linalg.norm(embedding_array)
        if norm > 0:
            embedding_array = embedding_array / norm
        
        return embedding_array
    
    def search_content(self, query: str, subject: str = None, n_results: int = 5) -> List[Dict]:
        """
        Search for relevant content using vector similarity.
        
        Args:
            query: Search query
            subject: Optional subject filter
            n_results: Number of results to return
            
        Returns:
            List of relevant content with metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Determine which collections to search
            search_collections = []
            if subject:
                # Search specific subject collection
                collection_name = f"{subject.lower().replace(' ', '_')}_grade_10"
                if collection_name in self.collections:
                    search_collections.append(collection_name)
            else:
                # Search all text collections
                for name in self.collections.keys():
                    if "grade_10" in name:
                        search_collections.append(name)
            
            if not search_collections:
                logger.warning("No text collections found for search")
                return []
            
            # Search each collection
            all_results = []
            for collection_name in search_collections:
                try:
                    collection = self.chroma_client.get_collection(name=collection_name)
                    
                    # Perform vector search
                    results = collection.query(
                        query_embeddings=[query_embedding.tolist()],
                        n_results=n_results,
                        include=['documents', 'metadatas', 'distances']
                    )
                    
                    # Process results
                    if results['documents'] and results['documents'][0]:
                        for i, doc in enumerate(results['documents'][0]):
                            metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {}
                            distance = results['distances'][0][i] if results['distances'] and results['distances'][0] else 1.0
                            
                            # Convert distance to similarity score (0-1)
                            similarity = 1.0 - min(distance, 1.0)
                            
                            result = {
                                'content': doc,
                                'metadata': metadata,
                                'similarity': similarity,
                                'collection': collection_name,
                                'subject': metadata.get('subject', 'unknown'),
                                'chapter': metadata.get('chapter', 'unknown'),
                                'difficulty': metadata.get('difficulty', 'beginner')
                            }
                            all_results.append(result)
                            
                except Exception as e:
                    logger.warning(f"Error searching collection {collection_name}: {e}")
                    continue
            
            # Sort by similarity and return top results
            all_results.sort(key=lambda x: x['similarity'], reverse=True)
            return all_results[:n_results]
            
        except Exception as e:
            logger.error(f"Error in search_content: {e}")
            return []
    
    def get_subject_overview(self, subject: str) -> Dict:
        """
        Get overview of available content for a subject.
        
        Args:
            subject: Subject name
            
        Returns:
            Dictionary with subject overview
        """
        try:
            collection_name = f"{subject.lower().replace(' ', '_')}_grade_10"
            if collection_name not in self.collections:
                return {"error": f"Subject {subject} not found"}
            
            collection = self.chroma_client.get_collection(name=collection_name)
            count = collection.count()
            
            # Get sample content for overview
            sample_results = collection.query(
                query_embeddings=[np.zeros(32).tolist()],  # Dummy query
                n_results=min(5, count)
            )
            
            overview = {
                "subject": subject,
                "total_chunks": count,
                "sample_content": sample_results['documents'][0] if sample_results['documents'] else [],
                "metadata": sample_results['metadatas'][0] if sample_results['metadatas'] else []
            }
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting subject overview: {e}")
            return {"error": str(e)}
    
    def get_available_subjects(self) -> List[str]:
        """Get list of available subjects."""
        subjects = []
        for collection_name in self.collections.keys():
            if "grade_10" in collection_name:
                # Extract subject name from collection name
                subject = collection_name.replace("_grade_10", "").replace("_", " ").title()
                subjects.append(subject)
        return subjects
    
    def get_chapter_content(self, subject: str, chapter: str) -> List[Dict]:
        """
        Get content for a specific chapter.
        
        Args:
            subject: Subject name
            chapter: Chapter name
            
        Returns:
            List of chapter content
        """
        try:
            collection_name = f"{subject.lower().replace(' ', '_')}_grade_10"
            if collection_name not in self.collections:
                return []
            
            collection = self.chroma_client.get_collection(name=collection_name)
            
            # Get all content and filter by chapter
            results = collection.get(
                include=['documents', 'metadatas']
            )
            
            chapter_content = []
            for i, metadata in enumerate(results['metadatas']):
                if metadata.get('chapter', '').lower() == chapter.lower():
                    content = {
                        'text': results['documents'][i],
                        'metadata': metadata
                    }
                    chapter_content.append(content)
            
            return chapter_content
            
        except Exception as e:
            logger.error(f"Error getting chapter content: {e}")
            return []
    
    def retrieve_relevant_content(self, query: str, max_results: int = 5) -> Dict:
        """
        Retrieve relevant content using semantic search.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with chunks and metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            all_results = []
            
            # Search across all text collections
            for collection_name, collection in self.collections.items():
                if "grade_10" in collection_name:  # Only text collections
                    try:
                        # Query the collection
                        results = collection.query(
                            query_embeddings=[query_embedding.tolist()],
                            n_results=max_results,
                            include=['documents', 'metadatas', 'distances']
                        )
                        
                        if results['documents']:
                            for i, doc in enumerate(results['documents'][0]):
                                result = {
                                    'content': doc,
                                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                                    'distance': results['distances'][0][i] if results['distances'] else 0.0,
                                    'collection': collection_name
                                }
                                all_results.append(result)
                                
                    except Exception as e:
                        logger.warning(f"Error querying collection {collection_name}: {e}")
                        continue
            
            # Sort by distance (lower is better) and take top results
            all_results.sort(key=lambda x: x['distance'])
            top_results = all_results[:max_results]
            
            # Convert to chunks format
            chunks = []
            for result in top_results:
                chunk = {
                    'content': result['content'],
                    'metadata': result['metadata'],
                    'source': result['collection'],
                    'relevance_score': 1.0 - result['distance']  # Convert distance to relevance
                }
                chunks.append(chunk)
            
            return {
                'chunks': chunks,
                'total_found': len(chunks),
                'query': query
            }
            
        except Exception as e:
            logger.error(f"Error in retrieve_relevant_content: {e}")
            return {'chunks': [], 'total_found': 0, 'query': query, 'error': str(e)}
    
    def get_statistics(self) -> Dict:
        """Get RAG system statistics."""
        try:
            stats = {
                "total_collections": len(self.collections),
                "collections": {},
                "total_documents": 0
            }
            
            for name, collection in self.collections.items():
                try:
                    count = collection.count()
                    stats["collections"][name] = {
                        "count": count,
                        "metadata": collection.metadata
                    }
                    stats["total_documents"] += count
                except Exception as e:
                    stats["collections"][name] = {"error": str(e)}
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {"error": str(e)} 