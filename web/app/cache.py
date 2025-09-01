"""
Simple in-memory caching system for the IT-Kurs application.

This module provides a lightweight caching layer for frequently accessed
data like courses and content to improve performance.
"""

import time
import logging
from typing import Any, Optional, Callable
from functools import wraps

logger = logging.getLogger(__name__)


class SimpleCache:
    """Simple in-memory cache with TTL (Time To Live) support."""
    
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
    
    def get(self, key: str, default_ttl: int = 300) -> Optional[Any]:
        """
        Get item from cache.
        
        Args:
            key: Cache key
            default_ttl: Default TTL in seconds (5 minutes)
            
        Returns:
            Cached value or None if expired/not found
        """
        if key not in self._cache:
            return None
            
        # Check if expired
        if time.time() - self._timestamps[key] > default_ttl:
            self.delete(key)
            return None
            
        return self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """
        Set item in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = value
        self._timestamps[key] = time.time()
    
    def delete(self, key: str) -> None:
        """Delete item from cache."""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._timestamps.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)
    
    def keys(self) -> list:
        """Get all cache keys."""
        return list(self._cache.keys())


# Global cache instance
cache = SimpleCache()


def cached(key_func: Optional[Callable] = None, ttl: int = 300):
    """
    Decorator for caching function results.
    
    Args:
        key_func: Function to generate cache key from args
        ttl: Time to live in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key, ttl)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            logger.debug(f"Cache miss for {cache_key} - stored result")
            
            return result
        return wrapper
    return decorator


def cache_courses_key(*args, **kwargs):
    """Generate cache key for courses."""
    return "courses:all"


def cache_course_detail_key(slug, *args, **kwargs):
    """Generate cache key for course details."""
    return f"course_detail:{slug}"


def cache_lessons_key(course_slug, *args, **kwargs):
    """Generate cache key for lessons."""
    return f"lessons:{course_slug}"


def get_cache_stats() -> dict:
    """Get cache statistics."""
    return {
        "size": cache.size(),
        "keys": cache.keys(),
        "hit_rate": "Not implemented in simple cache"
    }
