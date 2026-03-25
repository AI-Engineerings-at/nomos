import time
from nomos_api.auth.rate_limiter import RateLimiter

def test_allows_within_limit():
    limiter = RateLimiter(max_attempts=5, window_seconds=60, lockout_seconds=10)
    for _ in range(5):
        assert limiter.is_allowed("user-1") is True

def test_blocks_after_limit():
    limiter = RateLimiter(max_attempts=3, window_seconds=60, lockout_seconds=10)
    for _ in range(3):
        limiter.record_attempt("user-1")
    assert limiter.is_allowed("user-1") is False

def test_different_users_independent():
    limiter = RateLimiter(max_attempts=2, window_seconds=60, lockout_seconds=10)
    limiter.record_attempt("user-1")
    limiter.record_attempt("user-1")
    assert limiter.is_allowed("user-1") is False
    assert limiter.is_allowed("user-2") is True

def test_lockout_expires():
    limiter = RateLimiter(max_attempts=1, window_seconds=60, lockout_seconds=1)
    limiter.record_attempt("user-1")
    assert limiter.is_allowed("user-1") is False
    time.sleep(1.1)
    assert limiter.is_allowed("user-1") is True

def test_reset_clears_attempts():
    limiter = RateLimiter(max_attempts=2, window_seconds=60, lockout_seconds=10)
    limiter.record_attempt("user-1")
    limiter.record_attempt("user-1")
    assert limiter.is_allowed("user-1") is False
    limiter.reset("user-1")
    assert limiter.is_allowed("user-1") is True
