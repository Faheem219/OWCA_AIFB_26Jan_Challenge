"""
Redis connection and caching utilities.
"""
import redis.asyncio as redis
from app.core.config import settings
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache manager."""
    
    def __init__(self):
        self.redis_client: redis.Redis = None
    
    async def connect_to_redis(self):
        """Create Redis connection."""
        logger.info("Connecting to Redis...")
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            # Test the connection
            await self.redis_client.ping()
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def close_redis_connection(self):
        """Close Redis connection."""
        logger.info("Closing Redis connection...")
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis_client:
            return None
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting key {key} from Redis: {e}")
            return None
    
    async def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in cache with expiration."""
        if not self.redis_client:
            return False
        try:
            serialized_value = json.dumps(value, default=str)
            await self.redis_client.setex(key, expire, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Error setting key {key} in Redis: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis_client:
            return False
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting key {key} from Redis: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.redis_client:
            return False
        try:
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking key {key} in Redis: {e}")
            return False
    
    async def set_session(self, session_id: str, user_data: dict, expire: int = 86400) -> bool:
        """Set user session data."""
        return await self.set(f"session:{session_id}", user_data, expire)
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get user session data."""
        return await self.get(f"session:{session_id}")
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete user session."""
        return await self.delete(f"session:{session_id}")
    
    async def cache_translation(self, text_hash: str, translation_data: dict, expire: int = 86400) -> bool:
        """Cache translation result."""
        return await self.set(f"translation:{text_hash}", translation_data, expire)
    
    async def get_cached_translation(self, text_hash: str) -> Optional[dict]:
        """Get cached translation."""
        return await self.get(f"translation:{text_hash}")
    
    async def cache_price_data(self, commodity: str, location: str, price_data: dict, expire: int = 300) -> bool:
        """Cache price data (5 minutes expiration)."""
        key = f"price:{commodity}:{location}"
        return await self.set(key, price_data, expire)
    
    async def get_cached_price_data(self, commodity: str, location: str) -> Optional[dict]:
        """Get cached price data."""
        key = f"price:{commodity}:{location}"
        return await self.get(key)


# Global Redis instance
redis_cache = RedisCache()


async def get_redis() -> RedisCache:
    """Dependency to get Redis instance."""
    return redis_cache