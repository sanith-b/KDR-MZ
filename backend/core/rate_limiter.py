"""
Redis-backed Rate Limiter Dependency with in-memory fallback
Protects public and resource-intensive endpoints from abuse and DoS attacks.
"""
import time
from typing import Optional, Dict
from fastapi import Request, HTTPException, status
from shared.cache.redis_client import cache
from logging_helper import LOGGER

class RateLimiter:
    """
    FastAPI dependency implementing a fixed/sliding window rate limiter.
    Defaults to 60 requests per minute per IP address.
    """
    def __init__(self, requests_per_minute: int = 60, key_prefix: str = "rate"):
        self.requests_per_minute = requests_per_minute
        self.key_prefix = key_prefix
        self._local_buckets: Dict[str, list] = {}

    async def __call__(self, request: Request):
        # Identify caller by Authorization token subject or Client IP
        client_ip = request.client.host if request.client else "unknown"
        auth_header = request.headers.get("Authorization")
        identifier = client_ip
        if auth_header and auth_header.startswith("Bearer "):
            # Use hashed token snippet to rate-limit authenticated users individually
            identifier = f"user_{hash(auth_header[:30])}"

        now = int(time.time())
        key = f"{self.key_prefix}:{identifier}:{now // 60}"

        if cache._connected and cache._redis:
            try:
                current_count = await cache._redis.incr(key)
                if current_count == 1:
                    await cache._redis.expire(key, 65)
                if current_count > self.requests_per_minute:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded. Please wait a minute before retrying."
                    )
                return
            except HTTPException:
                raise
            except Exception as e:
                LOGGER.debug(f"Redis rate limiter failed: {e}. Falling back to in-memory.")

        # In-memory sliding window fallback
        timestamps = self._local_buckets.get(identifier, [])
        window_start = now - 60
        timestamps = [ts for ts in timestamps if ts > window_start]
        if len(timestamps) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait a minute before retrying."
            )
        timestamps.append(now)
        self._local_buckets[identifier] = timestamps
