#!/usr/bin/env python3
"""
Simple RAG Cache Implementation

Caches RAG retrieval results to avoid repeated ChromaDB queries.
Uses in-memory LRU cache with TTL support.
"""

import time
import hashlib
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from functools import lru_cache

class RAGCache:
    """
    Simple in-memory cache for RAG retrieval results.
    
    Features:
    - LRU eviction (max 100 entries)
    - TTL support (default 1 hour)
    - Query normalization
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
        Get cached RAG results.
        
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

    def find_similar(self, embedding: np.ndarray, subject: str, grade: str, threshold: float = 0.92) -> Optional[Dict[str, Any]]:
        """
        Find semantically similar cached query.
        """
        if embedding is None:
            return None
            
        best_score = -1.0
        best_result = None
        
        # Norm of query embedding
        query_norm = np.linalg.norm(embedding)
        if query_norm == 0:
            return None
            
        for key, (val, timestamp, cached_emb, meta) in self.cache.items():
            # Check TTL
            if time.time() - timestamp > self.ttl_seconds:
                continue
                
            # strict filter on subject/grade
            if meta.get('subject') != subject or meta.get('grade') != grade:
                continue
                
            if cached_emb is None:
                continue
                
            # Cosine Similarity
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
    
    def set(self, query: str, subject: str, grade: str, results: Dict[str, Any], embedding: Optional[np.ndarray] = None) -> None:
        """
        Cache RAG results with optional embedding for semantic search.
        """
        key = self._normalize_query(query, subject, grade)
        
        # LRU eviction if cache is full
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        metadata = {"subject": subject, "grade": grade, "query": query}
        self.cache[key] = (results, time.time(), embedding, metadata)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
    
    def stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds
        }
