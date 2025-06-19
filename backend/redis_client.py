import redis.asyncio as redis
import json
import pickle
from typing import Any, Optional
from config import settings


class RedisClient:
    def __init__(self):
        self.redis = redis.from_url(settings.redis_url, decode_responses=False)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        try:
            value = await self.redis.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, expire: int = 300) -> bool:
        """Set value in Redis cache with expiration"""
        try:
            serialized_value = pickle.dumps(value)
            await self.redis.set(key, serialized_value, ex=expire)
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis cache"""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> bool:
        """Clear all keys matching pattern"""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
            return True
        except Exception as e:
            print(f"Redis clear pattern error: {e}")
            return False


# Global Redis client instance
redis_client = RedisClient() 