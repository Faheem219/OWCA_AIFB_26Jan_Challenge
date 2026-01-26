"""
Redis connection and caching utilities.

This module handles Redis connection setup and provides caching utilities
for the multilingual marketplace platform.
"""

import json
import logging
from typing import Any, Optional, Union
import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis client instance
redis_client: Optional[Redis] = None


async def connect_to_redis() -> None:
    """
    Create Redis connection.
    """
    global redis_client
    
    try:
        logger.info("Connecting to Redis...")
        
        # Create Redis client
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        
        # Test the connection
        await redis_client.ping()
        
        logger.info("Successfully connected to Redis")
        
    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to Redis: {e}")
        raise


async def close_redis_connection() -> None:
    """
    Close Redis connection.
    """
    global redis_client
    
    if redis_client:
        logger.info("Closing Redis connection...")
        await redis_client.close()
        redis_client = None
        logger.info("Redis connection closed")


async def get_redis() -> Redis:
    """
    Get Redis client instance.
    
    Returns:
        Redis: The Redis client instance
        
    Raises:
        RuntimeError: If Redis is not connected
    """
    if redis_client is None:
        raise RuntimeError("Redis is not connected. Call connect_to_redis() first.")
    return redis_client


async def check_redis_health() -> bool:
    """
    Check if Redis connection is healthy.
    
    Returns:
        bool: True if Redis is healthy, False otherwise
    """
    try:
        if redis_client is None:
            return False
        
        # Ping Redis
        await redis_client.ping()
        return True
        
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False


# Cache utility functions
class CacheManager:
    """Redis cache manager with utility methods."""
    
    def __init__(self):
        self.default_ttl = settings.REDIS_CACHE_TTL
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            client = await get_redis()
            value = await client.get(key)
            
            if value is None:
                return None
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error(f"Error getting cache key '{key}': {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await get_redis()
            
            # Serialize value if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value, default=str)
            
            ttl = ttl or self.default_ttl
            await client.setex(key, ttl, value)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache key '{key}': {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await get_redis()
            await client.delete(key)
            return True
            
        except Exception as e:
            logger.error(f"Error deleting cache key '{key}': {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            client = await get_redis()
            return bool(await client.exists(key))
            
        except Exception as e:
            logger.error(f"Error checking cache key '{key}': {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a numeric value in cache.
        
        Args:
            key: Cache key
            amount: Amount to increment by
            
        Returns:
            New value or None if error
        """
        try:
            client = await get_redis()
            return await client.incrby(key, amount)
            
        except Exception as e:
            logger.error(f"Error incrementing cache key '{key}': {e}")
            return None
    
    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for a key.
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await get_redis()
            return await client.expire(key, ttl)
            
        except Exception as e:
            logger.error(f"Error setting expiration for cache key '{key}': {e}")
            return False
    
    async def get_pattern(self, pattern: str) -> list:
        """
        Get all keys matching a pattern.
        
        Args:
            pattern: Key pattern (e.g., "user:*")
            
        Returns:
            List of matching keys
        """
        try:
            client = await get_redis()
            return await client.keys(pattern)
            
        except Exception as e:
            logger.error(f"Error getting keys with pattern '{pattern}': {e}")
            return []
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Key pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            client = await get_redis()
            keys = await client.keys(pattern)
            
            if keys:
                return await client.delete(*keys)
            return 0
            
        except Exception as e:
            logger.error(f"Error deleting keys with pattern '{pattern}': {e}")
            return 0


# Global cache manager instance
cache = CacheManager()


# Specialized cache functions for common use cases
async def cache_translation(
    text: str,
    source_lang: str,
    target_lang: str,
    translation: str
) -> bool:
    """
    Cache a translation result.
    
    Args:
        text: Original text
        source_lang: Source language code
        target_lang: Target language code
        translation: Translated text
        
    Returns:
        True if cached successfully
    """
    key = f"translation:{source_lang}:{target_lang}:{hash(text)}"
    return await cache.set(key, translation, settings.TRANSLATION_CACHE_TTL)


async def get_cached_translation(
    text: str,
    source_lang: str,
    target_lang: str
) -> Optional[str]:
    """
    Get cached translation.
    
    Args:
        text: Original text
        source_lang: Source language code
        target_lang: Target language code
        
    Returns:
        Cached translation or None
    """
    key = f"translation:{source_lang}:{target_lang}:{hash(text)}"
    return await cache.get(key)


async def cache_price_data(commodity: str, market: str, data: dict) -> bool:
    """
    Cache price data for a commodity and market.
    
    Args:
        commodity: Commodity name
        market: Market name
        data: Price data
        
    Returns:
        True if cached successfully
    """
    key = f"price:{commodity}:{market}"
    return await cache.set(key, data, settings.PRICE_CACHE_TTL)


async def get_cached_price_data(commodity: str, market: str) -> Optional[dict]:
    """
    Get cached price data.
    
    Args:
        commodity: Commodity name
        market: Market name
        
    Returns:
        Cached price data or None
    """
    key = f"price:{commodity}:{market}"
    return await cache.get(key)