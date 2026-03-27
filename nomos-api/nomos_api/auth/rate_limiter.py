"""Distributed rate limiter backed by Valkey (Redis-compatible).

Uses sorted sets for sliding window rate limiting.
State persists across restarts and is shared across API instances.
"""
from __future__ import annotations
import time
import valkey.asyncio as valkey


class RateLimiter:
    def __init__(self, max_attempts: int = 5, window_seconds: int = 900, lockout_seconds: int = 900,
                 valkey_url: str = "redis://valkey:6379", key_prefix: str = "nomos:ratelimit:") -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._prefix = key_prefix
        self._client = valkey.from_url(valkey_url, decode_responses=True)

    def _attempts_key(self, key: str) -> str:
        return f"{self._prefix}attempts:{key}"

    def _lockout_key(self, key: str) -> str:
        return f"{self._prefix}lockout:{key}"

    async def is_allowed(self, key: str) -> bool:
        locked = await self._client.get(self._lockout_key(key))
        if locked:
            return False
        now = time.time()
        window_start = now - self.window_seconds
        await self._client.zremrangebyscore(self._attempts_key(key), "-inf", window_start)
        count = await self._client.zcard(self._attempts_key(key))
        return count < self.max_attempts

    async def record_attempt(self, key: str) -> None:
        now = time.time()
        attempts_key = self._attempts_key(key)
        await self._client.zadd(attempts_key, {str(now): now})
        await self._client.expire(attempts_key, self.window_seconds + self.lockout_seconds)
        window_start = now - self.window_seconds
        await self._client.zremrangebyscore(attempts_key, "-inf", window_start)
        count = await self._client.zcard(attempts_key)
        if count >= self.max_attempts:
            await self._client.setex(self._lockout_key(key), self.lockout_seconds, "locked")

    async def reset(self, key: str) -> None:
        await self._client.delete(self._attempts_key(key), self._lockout_key(key))
