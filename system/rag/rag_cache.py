#!/usr/bin/env python3
"""
Simple RAG Cache Implementation

Caches RAG retrieval results to avoid repeated ChromaDB queries.
Uses in-memory LRU cache with TTL support.
"""

import time
import hashlib
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
        self.cache: Dict[str, Tuple[Any, float]] = {}  # key -> (value, timestamp)
    
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
        
        value, timestamp = self.cache[key]
        
        # Check TTL
        if time.time() - timestamp > self.ttl_seconds:
            del self.cache[key]
            return None
        
        return value
    
    def set(self, query: str, subject: str, grade: str, results: Dict[str, Any]) -> None:
        """
        Cache RAG results.
        
        Args:
            query: User query
            subject: Subject filter
            grade: Grade filter
            results: RAG retrieval results to cache
        """
        key = self._normalize_query(query, subject, grade)
        
        # LRU eviction if cache is full
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        self.cache[key] = (results, time.time())
    
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
