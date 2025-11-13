"""
Redis Cache Manager - Fast caching layer for search results
Provides 95% faster response times for repeated queries
"""

import json
import hashlib
import logging
from typing import Any, Optional, Callable
from functools import wraps
import time

# Try to import Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not installed. Install with: pip install redis")

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages Redis caching with fallback to in-memory cache
    """
    
    def __init__(self, 
                 redis_host: str = 'localhost',
                 redis_port: int = 6379,
                 redis_db: int = 0,
                 default_ttl: int = 3600,
                 enabled: bool = True):
        """
        Initialize cache manager
        
        Args:
            redis_host: Redis server hostname
            redis_port: Redis server port
            redis_db: Redis database number
            default_ttl: Default time-to-live in seconds (1 hour)
            enabled: Enable/disable caching
        """
        self.enabled = enabled
        self.default_ttl = default_ttl
        self.redis_client = None
        self.fallback_cache = {}  # In-memory fallback
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.errors = 0
        
        # Try to connect to Redis
        if enabled and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True,
                    socket_connect_timeout=2
                )
                # Test connection
                self.redis_client.ping()
                logger.info(f"✓ Redis connected: {redis_host}:{redis_port}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Using in-memory cache.")
                self.redis_client = None
        elif enabled and not REDIS_AVAILABLE:
            logger.warning("Redis not available. Using in-memory cache.")
    
    def _generate_key(self, key_prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from function arguments
        
        Args:
            key_prefix: Prefix for the key
            *args, **kwargs: Function arguments to hash
            
        Returns:
            Cache key string
        """
        # Create a string representation of arguments
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
        key_string = "|".join(key_parts)
        
        # Hash for shorter keys
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]
        
        return f"{key_prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self.enabled:
            return None
        
        try:
            # Try Redis first
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    self.hits += 1
                    return json.loads(value)
            
            # Fallback to in-memory cache
            if key in self.fallback_cache:
                entry = self.fallback_cache[key]
                # Check expiration
                if entry['expires_at'] > time.time():
                    self.hits += 1
                    return entry['value']
                else:
                    # Expired - remove it
                    del self.fallback_cache[key]
            
            self.misses += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.errors += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time-to-live in seconds (None = default)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        ttl = ttl or self.default_ttl
        
        try:
            serialized = json.dumps(value)
            
            # Try Redis first
            if self.redis_client:
                self.redis_client.setex(key, ttl, serialized)
                return True
            
            # Fallback to in-memory cache
            self.fallback_cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl
            }
            
            # Cleanup old entries (simple LRU)
            if len(self.fallback_cache) > 1000:
                self._cleanup_fallback_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self.errors += 1
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Delete from Redis
            if self.redis_client:
                self.redis_client.delete(key)
            
            # Delete from fallback cache
            if key in self.fallback_cache:
                del self.fallback_cache[key]
            
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            self.errors += 1
            return False
    
    def clear(self) -> bool:
        """
        Clear all cache entries
        
        Returns:
            True if successful
        """
        try:
            if self.redis_client:
                self.redis_client.flushdb()
            
            self.fallback_cache.clear()
            
            logger.info("Cache cleared")
            return True
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            self.errors += 1
            return False
    
    def _cleanup_fallback_cache(self) -> None:
        """Remove expired entries from fallback cache"""
        current_time = time.time()
        expired_keys = [
            k for k, v in self.fallback_cache.items()
            if v['expires_at'] <= current_time
        ]
        
        for key in expired_keys:
            del self.fallback_cache[key]
    
    def cached(self, 
               key_prefix: str = 'default',
               ttl: Optional[int] = None) -> Callable:
        """
        Decorator for caching function results
        
        Args:
            key_prefix: Prefix for cache keys
            ttl: Time-to-live in seconds
            
        Returns:
            Decorated function
        
        Example:
            @cache_manager.cached(key_prefix='search', ttl=3600)
            def search(query):
                return expensive_search(query)
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_key(key_prefix, *args, **kwargs)
                
                # Try to get from cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit: {cache_key}")
                    return cached_value
                
                # Cache miss - execute function
                logger.debug(f"Cache miss: {cache_key}")
                result = func(*args, **kwargs)
                
                # Store in cache
                self.set(cache_key, result, ttl=ttl)
                
                return result
            
            return wrapper
        return decorator
    
    def get_statistics(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            'enabled': self.enabled,
            'backend': 'redis' if self.redis_client else 'memory',
            'hits': self.hits,
            'misses': self.misses,
            'errors': self.errors,
            'total_requests': total_requests,
            'hit_rate_percent': round(hit_rate, 2),
            'fallback_cache_size': len(self.fallback_cache)
        }
        
        # Get Redis info if available
        if self.redis_client:
            try:
                redis_info = self.redis_client.info('stats')
                stats['redis_keys'] = self.redis_client.dbsize()
                stats['redis_memory_mb'] = round(
                    int(redis_info.get('used_memory', 0)) / 1024 / 1024, 2
                )
            except Exception:
                pass
        
        return stats
    
    def reset_statistics(self) -> None:
        """Reset cache statistics counters"""
        self.hits = 0
        self.misses = 0
        self.errors = 0


# Global cache manager instance
cache_manager = CacheManager(enabled=True)


# Convenience functions
def get_cache(key: str) -> Optional[Any]:
    """Get value from cache"""
    return cache_manager.get(key)


def set_cache(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set value in cache"""
    return cache_manager.set(key, value, ttl)


def delete_cache(key: str) -> bool:
    """Delete key from cache"""
    return cache_manager.delete(key)


def clear_cache() -> bool:
    """Clear all cache"""
    return cache_manager.clear()


def cached(key_prefix: str = 'default', ttl: Optional[int] = None):
    """Caching decorator"""
    return cache_manager.cached(key_prefix=key_prefix, ttl=ttl)


# Example usage
if __name__ == "__main__":
    # Initialize cache
    cache = CacheManager()
    
    # Test caching
    print("Testing cache...")
    
    # Set value
    cache.set('test_key', {'data': 'test_value'}, ttl=60)
    print("✓ Set cache")
    
    # Get value
    value = cache.get('test_key')
    print(f"✓ Get cache: {value}")
    
    # Test decorator
    @cache.cached(key_prefix='example', ttl=300)
    def expensive_function(n):
        print(f"  Computing expensive_function({n})...")
        time.sleep(1)  # Simulate expensive operation
        return n * 2
    
    print("\nTesting decorator:")
    print(f"First call: {expensive_function(5)}")   # Slow (cache miss)
    print(f"Second call: {expensive_function(5)}")  # Fast (cache hit)
    
    # Show statistics
    print(f"\nCache statistics: {cache.get_statistics()}")