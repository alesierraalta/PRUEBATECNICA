"""
Redis-based caching service using aiocache.

Provides high-performance caching for summary results using Redis
with aiocache library for elegant async caching operations.
Includes connection pooling, serialization, and comprehensive error handling.
"""

import hashlib
import json
import time
from typing import Any, Optional, Union

from aiocache import Cache
from aiocache.serializers import PickleSerializer

from app.core.constants import (
    CACHE_NAMESPACE,
    CACHE_KEY_PREFIX,
    DEFAULT_CACHE_TTL,
)
from app.core.exceptions import CacheError


class CacheService:
    """
    Redis-based caching service using aiocache.
    
    Provides high-performance caching for summary results with
    automatic serialization, connection pooling, and comprehensive
    error handling. Uses aiocache for elegant async operations.
    
    Features:
    - Automatic serialization with PickleSerializer
    - Connection pooling for Redis
    - Deterministic cache key generation
    - Configurable TTL and namespace
    - Comprehensive error handling
    - Cache statistics and monitoring
    - Graceful degradation on cache failures
    
    Attributes:
        cache: aiocache Cache instance
        ttl_seconds: Time-to-live for cached entries
        namespace: Cache namespace for key isolation
    """
    
    def __init__(
        self,
        redis_url: str,
        ttl_seconds: int = DEFAULT_CACHE_TTL,
        namespace: str = CACHE_NAMESPACE,
        max_connections: int = 50
    ):
        """
        Initialize cache service.
        
        Sets up Redis cache with aiocache, configuring connection
        pooling, serialization, and error handling.
        
        Args:
            redis_url: Redis connection URL
            ttl_seconds: Time-to-live for cached entries
            namespace: Cache namespace for key isolation
            max_connections: Maximum Redis connection pool size
            
        Raises:
            CacheError: If cache initialization fails
            
        Example:
            ```python
            cache_service = CacheService(
                redis_url="redis://localhost:6379",
                ttl_seconds=3600,
                namespace="summaries"
            )
            ```
        """
        try:
            # Initialize aiocache with Redis backend
            self.cache = Cache.from_url(
                redis_url,
                serializer=PickleSerializer(),  # For Python objects
                namespace=namespace,
                pool_max_connections=max_connections
            )
            
            self.ttl_seconds = ttl_seconds
            self.namespace = namespace
            
        except Exception as e:
            raise CacheError(
                f"Failed to initialize cache service / Error al inicializar servicio de cache: {str(e)}",
                operation="init",
                details={"redis_url": redis_url, "namespace": namespace}
            )
    
    def _create_cache_key(
        self,
        text: str,
        params: dict[str, Any]
    ) -> str:
        """
        Create deterministic cache key.
        
        Generates a consistent cache key based on text content
        and parameters using SHA256 hashing for security and
        consistency across different requests.
        
        Args:
            text: Input text content
            params: Summarization parameters
            
        Returns:
            SHA256 hash of text + params as cache key
            
        Example:
            ```python
            key = cache_service._create_cache_key(
                "Hello world",
                {"max_tokens": 100, "lang": "en"}
            )
            print(key)  # "sha256_hash_here"
            ```
        """
        try:
            # Sort params for consistent hashing
            params_str = json.dumps(params, sort_keys=True, separators=(',', ':'))
            
            # Create hash from text and params
            content = f"{text}|{params_str}"
            hash_obj = hashlib.sha256(content.encode('utf-8'))
            
            # Add prefix and return hex digest
            cache_key = f"{CACHE_KEY_PREFIX}:{hash_obj.hexdigest()}"
            
            return cache_key
            
        except Exception as e:
            # Fallback to simple hash if JSON serialization fails
            content = f"{text}|{str(params)}"
            hash_obj = hashlib.sha256(content.encode('utf-8'))
            return f"{CACHE_KEY_PREFIX}:{hash_obj.hexdigest()}"
    
    async def get(
        self,
        text: str,
        params: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """
        Get cached summary result.
        
        Retrieves cached summary result if available, returning
        None if not found or if cache operation fails.
        
        Args:
            text: Input text used for summarization
            params: Summarization parameters
            
        Returns:
            Cached result dictionary or None if not found
            
        Example:
            ```python
            result = await cache_service.get(
                text="Hello world",
                params={"max_tokens": 100, "lang": "en"}
            )
            if result:
                print(f"Cached summary: {result['summary']}")
            ```
        """
        try:
            key = self._create_cache_key(text, params)
            result = await self.cache.get(key)
            
            if result:
                # Add cache metadata
                result["cached"] = True
                result["cache_timestamp"] = time.time()
            
            return result
            
        except Exception as e:
            # Cache miss or error - return None without failing request
            return None
    
    async def set(
        self,
        text: str,
        params: dict[str, Any],
        result: dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache summary result.
        
        Stores summary result in cache with specified TTL.
        Returns True if successful, False if caching fails.
        
        Args:
            text: Input text used for summarization
            params: Summarization parameters
            result: Summary result to cache
            ttl: Time-to-live override (uses default if None)
            
        Returns:
            True if cached successfully, False otherwise
            
        Example:
            ```python
            success = await cache_service.set(
                text="Hello world",
                params={"max_tokens": 100, "lang": "en"},
                result={"summary": "Hello", "usage": {...}}
            )
            print(f"Cached: {success}")
            ```
        """
        try:
            key = self._create_cache_key(text, params)
            
            # Add cache metadata
            result["cached"] = False  # Mark as not cached (will be True when retrieved)
            result["cache_timestamp"] = time.time()
            
            # Use provided TTL or default
            cache_ttl = ttl if ttl is not None else self.ttl_seconds
            
            await self.cache.set(key, result, ttl=cache_ttl)
            return True
            
        except Exception as e:
            # Cache error - don't fail the request
            return False
    
    async def delete(
        self,
        text: str,
        params: dict[str, Any]
    ) -> bool:
        """
        Delete cached summary result.
        
        Removes cached result from cache if it exists.
        
        Args:
            text: Input text used for summarization
            params: Summarization parameters
            
        Returns:
            True if deleted successfully, False otherwise
            
        Example:
            ```python
            success = await cache_service.delete(
                text="Hello world",
                params={"max_tokens": 100, "lang": "en"}
            )
            print(f"Deleted: {success}")
            ```
        """
        try:
            key = self._create_cache_key(text, params)
            await self.cache.delete(key)
            return True
            
        except Exception:
            return False
    
    async def clear_all(self) -> bool:
        """
        Clear all cached entries in this namespace.
        
        Removes all cached entries within the configured namespace.
        Use with caution as this affects all cached summaries.
        
        Returns:
            True if cleared successfully, False otherwise
            
        Example:
            ```python
            success = await cache_service.clear_all()
            print(f"Cache cleared: {success}")
            ```
        """
        try:
            await self.cache.clear()
            return True
            
        except Exception:
            return False
    
    async def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics and health information.
        
        Retrieves information about cache performance and health
        for monitoring and debugging purposes.
        
        Returns:
            Dictionary with cache statistics
            
        Example:
            ```python
            stats = await cache_service.get_stats()
            print(f"Cache namespace: {stats['namespace']}")
            ```
        """
        try:
            # Basic cache information
            stats = {
                "namespace": self.namespace,
                "ttl_seconds": self.ttl_seconds,
                "cache_type": "redis",
                "serializer": "pickle",
                "status": "healthy"
            }
            
            # Try to get Redis info if available
            try:
                # This might not be available in all aiocache versions
                redis_info = await self.cache.raw("INFO", "memory")
                if redis_info:
                    stats["redis_memory"] = redis_info
            except Exception:
                pass
            
            return stats
            
        except Exception as e:
            return {
                "namespace": self.namespace,
                "ttl_seconds": self.ttl_seconds,
                "status": "error",
                "error": str(e)
            }
    
    async def health_check(self) -> bool:
        """
        Perform cache health check.
        
        Tests cache connectivity and basic operations to ensure
        the cache service is functioning properly.
        
        Returns:
            True if cache is healthy, False otherwise
            
        Example:
            ```python
            is_healthy = await cache_service.health_check()
            print(f"Cache healthy: {is_healthy}")
            ```
        """
        try:
            # Test basic operations
            test_key = f"{CACHE_KEY_PREFIX}:health_check"
            test_value = {"test": True, "timestamp": time.time()}
            
            # Set test value
            await self.cache.set(test_key, test_value, ttl=10)
            
            # Get test value
            retrieved = await self.cache.get(test_key)
            
            # Clean up
            await self.cache.delete(test_key)
            
            # Verify value was stored and retrieved correctly
            return retrieved is not None and retrieved.get("test") is True
            
        except Exception:
            return False
    
    async def close(self) -> None:
        """
        Close cache connections.
        
        Properly closes Redis connections and cleans up resources.
        Should be called during application shutdown.
        
        Example:
            ```python
            await cache_service.close()
            ```
        """
        try:
            await self.cache.close()
        except Exception:
            # Ignore errors during shutdown
            pass
    
    def __repr__(self) -> str:
        """
        String representation of the cache service.
        
        Returns:
            String representation with cache details
        """
        return (
            f"CacheService("
            f"namespace={self.namespace}, "
            f"ttl={self.ttl_seconds}s, "
            f"backend=redis"
            f")"
        )


# Export for easy importing
__all__ = ["CacheService"]
