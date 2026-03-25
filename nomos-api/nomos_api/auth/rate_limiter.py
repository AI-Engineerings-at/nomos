import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_attempts: int = 5, window_seconds: int = 900, lockout_seconds: int = 900):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._attempts: dict[str, list[float]] = defaultdict(list)
        self._lockouts: dict[str, float] = {}

    def is_allowed(self, key: str) -> bool:
        now = time.monotonic()

        if key in self._lockouts:
            if now < self._lockouts[key]:
                return False
            del self._lockouts[key]
            self._attempts[key] = []

        self._attempts[key] = [t for t in self._attempts[key] if now - t < self.window_seconds]
        return len(self._attempts[key]) < self.max_attempts

    def record_attempt(self, key: str) -> None:
        now = time.monotonic()
        self._attempts[key].append(now)

        recent = [t for t in self._attempts[key] if now - t < self.window_seconds]
        self._attempts[key] = recent

        if len(recent) >= self.max_attempts:
            self._lockouts[key] = now + self.lockout_seconds

    def reset(self, key: str) -> None:
        self._attempts.pop(key, None)
        self._lockouts.pop(key, None)
