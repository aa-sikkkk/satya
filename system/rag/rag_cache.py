#!/usr/bin/env python3
"""
Simple RAG Cache Implementation

Caches RAG retrieval results to avoid repeated ChromaDB queries.
Uses in-memory LRU cache with TTL support.
"""

import time
import hashlib
import numpy as np
from typing import Dict, Any, Optional, Tuple

class RAGCache:
    """
    Simple in-memory cache for RAG retrieval results.
    
    Features:
    - LRU eviction (max 100 entries)
    - TTL support (default 1 hour)
    - Query normalization
    - Semantic similarity search
    """
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Initialize RAG cache.
        
        Args:
            max_size: Maximum number of cached entries
            ttl_seconds: Time-to-live for cache entries (default 1 hour)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        # key -> (value, timestamp, embedding, metadata)
        self.cache: Dict[str, Tuple[Any, float, Optional[np.ndarray], Dict]] = {}
    
    def _normalize_query(self, query: str, subject: str, grade: str) -> str:
        """Normalize query for cache key."""
        normalized = f"{query.lower().strip()}|{subject.lower()}|{grade}"
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def get(self, query: str, subject: str, grade: str) -> Optional[Dict[str, Any]]:
        """
        Get cached RAG results (exact match).
        
        Args:
            query: User query
            subject: Subject filter
            grade: Grade filter
            
        Returns:
            Cached results or None if not found/expired
        """
        key = self._normalize_query(query, subject, grade)
        
        if key not in self.cache:
            return None
        
        value, timestamp, _, _ = self.cache[key]
        
        # Check TTL
        if time.time() - timestamp > self.ttl_seconds:
            del self.cache[key]
            return None
        
        return value

    def find_similar(
        self, 
        embedding: np.ndarray, 
        subject: str, 
        grade: str, 
        threshold: float = 0.92
    ) -> Optional[Dict[str, Any]]:
        """
        Find semantically similar cached query using cosine similarity.
        
        Args:
            embedding: Query embedding vector
            subject: Subject filter
            grade: Grade filter
            threshold: Minimum similarity score (0.92 = very similar)
            
        Returns:
            Cached results of most similar query, or None
        """
        if embedding is None:
            return None
        
        # Handle embedding shape
        if embedding.ndim > 1:
            embedding = embedding.flatten()
            
        best_score = -1.0
        best_result = None
        
        query_norm = np.linalg.norm(embedding)
        if query_norm == 0:
            return None
            
        for key, (val, timestamp, cached_emb, meta) in list(self.cache.items()):
            if time.time() - timestamp > self.ttl_seconds:
                del self.cache[key]
                continue
                
            # Filter by subject/grade
            if meta.get('subject') != subject or meta.get('grade') != grade:
                continue
                
            if cached_emb is None:
                continue
            
            if cached_emb.ndim > 1:
                cached_emb = cached_emb.flatten()
                
            if embedding.shape != cached_emb.shape:
                continue
                
            cached_norm = np.linalg.norm(cached_emb)
            if cached_norm == 0:
                continue
                
            score = np.dot(embedding, cached_emb) / (query_norm * cached_norm)
            
            if score > best_score:
                best_score = score
                best_result = val
                
        if best_score >= threshold:
            return best_result
        
        return None
    
    def set(
        self, 
        query: str, 
        subject: str, 
        grade: str, 
        results: Dict[str, Any], 
        embedding: Optional[np.ndarray] = None
    ) -> None:
        """
        Cache RAG results with optional embedding for semantic search.
        
        Args:
            query: User query
            subject: Subject filter
            grade: Grade filter
            results: RAG results to cache
            embedding: Optional query embedding for semantic search
        """
        key = self._normalize_query(query, subject, grade)
        
        # LRU eviction if cache is full
        if len(self.cache) >= self.max_size and key not in self.cache:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        # Store metadata for filtering
        metadata = {
            "subject": subject, 
            "grade": grade, 
            "query": query
        }
        
        # Flatten embedding if needed
        if embedding is not None and embedding.ndim > 1:
            embedding = embedding.flatten()
        
        self.cache[key] = (results, time.time(), embedding, metadata)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = time.time()
        expired_keys = [
            k for k, (_, timestamp, _, _) in self.cache.items() 
            if current_time - timestamp > self.ttl_seconds
        ]
        for k in expired_keys:
            del self.cache[k]
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "hit_rate": "N/A"  # Would need counters to track
        }