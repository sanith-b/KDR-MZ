import json
from typing import Any, Optional
from shared.config.settings import settings
from logging_helper import LOGGER

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class CacheManager:
    def __init__(self):
        self._redis = None
        self._memory_cache = {}
        self._connected = False

    async def connect(self):
        if not REDIS_AVAILABLE:
            LOGGER.info("Redis package not installed. Using in-memory cache.")
            return

        try:
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=3
            )
            await self._redis.ping()
            self._connected = True
            LOGGER.info("✅ Redis connected successfully.")
        except Exception as e:
            LOGGER.warning(f"⚠️ Redis unavailable ({e}). Falling back to memory cache.")
            self._connected = False

    async def get(self, key: str) -> Optional[Any]:
        if self._connected and self._redis:
            try:
                val = await self._redis.get(key)
                if val:
                    try:
                        return json.loads(val)
                    except (json.JSONDecodeError, TypeError):
                        return val
                return None
            except Exception:
                pass
        return self._memory_cache.get(key)

    async def set(self, key: str, value: Any, ttl: int = 1800) -> bool:
        if self._connected and self._redis:
            try:
                serialized = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
                await self._redis.setex(key, ttl, serialized)
                return True
            except Exception:
                pass
        self._memory_cache[key] = value
        return True

    async def delete(self, key: str) -> bool:
        if self._connected and self._redis:
            try:
                await self._redis.delete(key)
                return True
            except Exception:
                pass
        self._memory_cache.pop(key, None)
        return True

cache = CacheManager()
