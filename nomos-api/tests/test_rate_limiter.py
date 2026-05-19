import pytest
from nomos_api.auth.rate_limiter import RateLimiter


@pytest.fixture
async def limiter():
    rl = RateLimiter(max_attempts=3, window_seconds=10, lockout_seconds=10, valkey_url="redis://localhost:6379")
    await rl.reset("test-key")
    yield rl
    await rl.reset("test-key")


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_allows_under_limit(self, limiter):
        assert await limiter.is_allowed("test-key") is True

    @pytest.mark.asyncio
    async def test_blocks_after_max_attempts(self, limiter):
        for _ in range(3):
            await limiter.record_attempt("test-key")
        assert await limiter.is_allowed("test-key") is False

    @pytest.mark.asyncio
    async def test_reset_clears_state(self, limiter):
        for _ in range(3):
            await limiter.record_attempt("test-key")
        await limiter.reset("test-key")
        assert await limiter.is_allowed("test-key") is True

    @pytest.mark.asyncio
    async def test_independent_keys(self, limiter):
        for _ in range(3):
            await limiter.record_attempt("key-a")
        assert await limiter.is_allowed("key-b") is True
        await limiter.reset("key-a")
