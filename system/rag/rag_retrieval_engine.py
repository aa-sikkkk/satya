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
from collections import OrderedDict

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
    
    def __init__(self, chroma_db_path: str = "satya_data/chroma_db", cache_size: int = 128):
        """
        Initialize the RAG retrieval engine.

        Args:
            chroma_db_path: Path to ChromaDB database
            cache_size: Max entries for query and embedding caches.
        """
        self.chroma_db_path = Path(chroma_db_path)
        self.chroma_client = None
        self.collections = {}
        self.cache_size = cache_size
        self._query_cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._embedding_cache: OrderedDict[str, np.ndarray] = OrderedDict()
        
        # Initialize ChromaDB
        self._initialize_chromadb()
        
        # Initialize embedding model
        self.embedding_model = None
        self._initialize_embedding_model()
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB client and load collections."""
        try:
            self.chroma_client = chromadb.PersistentClient(path=str(self.chroma_db_path))

            
            # Get available collections - store names only, retrieve fresh when needed
            collections = self.chroma_client.list_collections()
            for collection in collections:
                # Store collection name for later retrieval
                self.collections[collection.name] = collection.name
                logger.debug(f"Found collection: {collection.name}")

            if not self.collections:
                logger.warning("No collections found in ChromaDB")
            else:
                logger.info(f"Initialized {len(self.collections)} ChromaDB collections")
                
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
        cached = self._embedding_cache.get(text)
        if cached is not None:
            return cached

        embedding = self._generate_hash_embedding(text)
        self._remember(self._embedding_cache, text, embedding)
        return embedding
    
    def _prepare_query_embeddings(self, embedding: Any) -> List[List[float]]:
        """Normalize a single or batched embedding into the format Chroma expects.
        
        - If a 1D numpy array/list of floats is provided, wrap it as [[...]].
        - If a 2D numpy array/list of lists is provided, return as [[...], [...]].
        - Ensure all values are Python floats.
        """
        import numpy as _np
        # Convert numpy arrays to lists
        if isinstance(embedding, _np.ndarray):
            if embedding.ndim == 1:
                return [[float(x) for x in embedding.tolist()]]
            if embedding.ndim == 2:
                return [[float(x) for x in row.tolist()] for row in embedding]
        # Python list inputs
        if isinstance(embedding, list):
            if len(embedding) == 0:
                return [[]]
            first = embedding[0]
            # Already batched: [[...], [...]]
            if isinstance(first, (list, tuple, _np.ndarray)):
                return [[float(x) for x in (row.tolist() if isinstance(row, _np.ndarray) else row)] for row in embedding]
            # Single vector: [...]
            return [[float(x) for x in embedding]]
        # Fallback: try to cast to list and wrap
        try:
            as_list = list(embedding)
            return [[float(x) for x in as_list]]
        except Exception:
            # Last resort: stringify and hash-embed to avoid crashing
            vec = self._generate_hash_embedding(str(embedding))
            return [[float(x) for x in vec.tolist()]]
    
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
                        query_embeddings=self._prepare_query_embeddings(query_embedding),
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
                query_embeddings=self._prepare_query_embeddings(np.zeros(32, dtype=np.float32)),  # Dummy query
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
            cached = self._query_cache.get(query)
            if cached:
                return cached

            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            all_results = []
            
            # Optimize: Limit to first 3 collections to speed up search
            # Prioritize most common subjects (Computer Science, English, etc.)
            all_collection_names = list(self.collections.keys())
            logger.debug(f"RAG: Available collections: {all_collection_names}")
            
            collections_to_search = [
                name for name in all_collection_names 
                if "grade_10" in name
            ][:3]  # Limit to 3 collections max
            
            # If no grade_10 collections, try all collections (fallback)
            if not collections_to_search:
                logger.warning(f"No 'grade_10' collections found in {all_collection_names}, searching all available collections")
                collections_to_search = all_collection_names[:3]
            
            # If still no collections, return empty
            if not collections_to_search:
                logger.warning(f"No collections available for RAG search. Available: {all_collection_names}")
                empty = {'chunks': [], 'total_found': 0, 'query': query, 'error': 'No collections available'}
                self._remember(self._query_cache, query, empty)
                return empty
            
            logger.debug(f"RAG: Searching collections: {collections_to_search}")
            
            # Search across limited text collections
            for collection_name in collections_to_search:
                try:
                    # Get fresh collection reference from ChromaDB
                    collection = self.chroma_client.get_collection(name=collection_name)
                    logger.debug(f"RAG: querying collection '{collection_name}' for '{query}'")
                    # Query the collection with reduced results for speed
                    results = collection.query(
                        query_embeddings=self._prepare_query_embeddings(query_embedding),
                        n_results=max_results,  # Reduced from max_results * 2
                        include=['documents', 'metadatas', 'distances']
                    )
                    hit_count = len(results['documents'][0]) if results.get('documents') and results['documents'] and results['documents'][0] else 0
                    logger.debug(f"RAG: '{collection_name}' vector hits: {hit_count}")
                    
                    if results['documents']:
                        for i, doc in enumerate(results['documents'][0]):
                            distance = results['distances'][0][i] if results['distances'] else 1.0
                            # Filter aggressive distance to reduce noisy context
                            if distance is None or distance > 0.65:
                                continue
                            result = {
                                'content': doc,
                                'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                                'distance': distance,
                                'collection': collection_name
                            }
                            all_results.append(result)
                    
                    # If no vector hits here, try keyword fallback per collection
                    if hit_count == 0:
                        # Get collection again for fallback search
                        collection = self.chroma_client.get_collection(name=collection_name)
                        fallback = self._keyword_fallback_search(collection, query, max_results=max_results)
                        logger.debug(f"RAG: '{collection_name}' keyword-fallback hits: {len(fallback)}")
                        for f in fallback:
                            f['collection'] = collection_name
                            all_results.append({
                                'content': f['content'],
                                'metadata': f.get('metadata', {}),
                                'distance': f.get('distance', 0.75),
                                'collection': collection_name
                            })
                            
                except Exception as e:
                    logger.warning(f"Error querying collection {collection_name}: {e}")
                    continue
            
            # Sort by distance (lower is better) and take top results
            all_results.sort(key=lambda x: x['distance'])
            # Backstop: if nothing found (or distances missing), try a lenient include
            if not all_results:
                logger.info("RAG: no results from vector or keyword fallback across collections")
                empty = {'chunks': [], 'total_found': 0, 'query': query}
                self._remember(self._query_cache, query, empty)
                return empty

            top_results = all_results[:max_results]
            
            # Convert to chunks format
            chunks = []
            for result in top_results:
                chunk = {
                    'content': result['content'],
                    'metadata': result['metadata'],
                    'source': result['collection'],
                    'distance': result['distance'],
                    'relevance_score': 1.0 - result['distance']  # Convert distance to relevance
                }
                chunks.append(chunk)
            logger.debug(f"RAG: returning {len(chunks)} chunks (max_results={max_results})")
            response = {
                'chunks': chunks,
                'total_found': len(chunks),
                'query': query
            }
            self._remember(self._query_cache, query, response)
            return response
            
        except Exception as e:
            logger.error(f"Error in retrieve_relevant_content: {e}")
            return {'chunks': [], 'total_found': 0, 'query': query, 'error': str(e)}

    def _remember(self, cache: OrderedDict, key: str, value: Any) -> None:
        """LRU helper for small in-memory caches."""
        cache[key] = value
        cache.move_to_end(key)
        if len(cache) > self.cache_size:
            cache.popitem(last=False)
    
    def get_statistics(self) -> Dict:
        """Get RAG system statistics."""
        try:
            stats = {
                "total_collections": len(self.collections),
                "collections": {},
                "total_documents": 0
            }
            
            for collection_name in self.collections.keys():
                try:
                    collection = self.chroma_client.get_collection(name=collection_name)
                    count = collection.count()
                    stats["collections"][collection_name] = {
                        "count": count,
                        "metadata": collection.metadata
                    }
                    stats["total_documents"] += count
                except Exception as e:
                    stats["collections"][collection_name] = {"error": str(e)}
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {"error": str(e)} 

    def _keyword_fallback_search(self, collection, query: str, max_results: int) -> List[Dict]:
        """Data-driven fallback using simple BM25-style scoring without hardcoded synonyms."""
        import math
        import re
        try:
            def _tokenize(text: str) -> List[str]:
                text = text.lower()
                text = re.sub(r"[^a-z0-9\s]", " ", text)
                text = re.sub(r"\s+", " ", text).strip()
                return text.split() if text else []
            
            def _normalize(tokens: List[str]) -> List[str]:
                normalized = []
                for t in tokens:
                    if len(t) > 4 and t.endswith("ing"):
                        t = t[:-3]
                    elif len(t) > 3 and t.endswith("ed"):
                        t = t[:-2]
                    elif len(t) > 3 and t.endswith("es"):
                        t = t[:-2]
                    elif len(t) > 2 and t.endswith("s"):
                        t = t[:-1]
                    normalized.append(t)
                return normalized
            
            # Load docs
            results = collection.get(include=['documents', 'metadatas'])
            docs = results.get('documents') or []
            metas = results.get('metadatas') or []
            if not docs:
                return []
            
            # Prepare tokens
            doc_tokens: List[List[str]] = []
            doc_lengths: List[int] = []
            df: Dict[str, int] = {}
            for doc in docs:
                if not isinstance(doc, str):
                    doc_tokens.append([])
                    doc_lengths.append(0)
                    continue
                toks = _normalize(_tokenize(doc))
                doc_tokens.append(toks)
                doc_lengths.append(len(toks))
                seen = set()
                for tok in toks:
                    if tok and tok not in seen:
                        df[tok] = df.get(tok, 0) + 1
                        seen.add(tok)
            N = max(1, len(docs))
            avgdl = sum(doc_lengths) / N
            
            # Query tokens
            q_tokens = _normalize(_tokenize(query))
            if not q_tokens:
                return []
            
            # IDF
            idf: Dict[str, float] = {}
            for tok in set(q_tokens):
                dfi = df.get(tok, 0)
                idf[tok] = math.log((N - dfi + 0.5) / (dfi + 0.5) + 1.0)
            
            # BM25-lite scoring
            k1 = 1.5
            b = 0.75
            scores: List[Tuple[float, int]] = []
            for idx, toks in enumerate(doc_tokens):
                if not toks:
                    continue
                score = 0.0
                tf: Dict[str, int] = {}
                for t in toks:
                    tf[t] = tf.get(t, 0) + 1
                dl = max(1, doc_lengths[idx])
                for q in q_tokens:
                    if q not in idf:
                        continue
                    f = tf.get(q, 0)
                    if f == 0:
                        continue
                    denom = f + k1 * (1 - b + b * dl / avgdl)
                    score += idf[q] * (f * (k1 + 1)) / denom
                if score > 0:
                    scores.append((score, idx))
            scores.sort(key=lambda x: x[0], reverse=True)
            top = scores[:max_results]
            fallback: List[Dict] = []
            for score, idx in top:
                fallback.append({
                    'content': docs[idx],
                    'metadata': metas[idx] if idx < len(metas) and metas[idx] else {},
                    'distance': max(0.0, 1.0 - min(score / 10.0, 1.0)),  # map score to pseudo-distance
                })
            return fallback
        except Exception as e:
            logger.warning(f"Keyword fallback failed: {e}")
            return [] 