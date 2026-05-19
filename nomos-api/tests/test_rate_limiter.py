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

    @pytest.mark.asyncio
    async def test_concurrent_burst_does_not_undercount(self, limiter):
        """REGRESSION: under a same-tick concurrent burst the limiter MUST
        count every attempt and lock at max_attempts.

        Before the uuid-suffixed ZADD member fix, multiple record_attempt
        calls in the same time.time() tick produced identical
        ``{str(now): now}`` pairs, which Valkey treats as the SAME sorted-set
        member (updates score, doesn't add a new row). zcard then
        undercounts and the lockout key is never written — a real
        rate-limit bypass. This test fires ``max_attempts`` recordings
        concurrently via asyncio.gather (no awaits between them, so they
        share the same wall-clock tick), then asserts that is_allowed
        returns False — proving the lockout actually engaged.
        """
        import asyncio

        await limiter.reset("burst-key")
        # Fire exactly max_attempts concurrent recordings.
        await asyncio.gather(*[limiter.record_attempt("burst-key") for _ in range(3)])
        # zcard must be 3 (with the fix) — not 1 (which the old bug produced).
        members = await limiter._client.zcard(limiter._attempts_key("burst-key"))
        assert members == 3, f"unique-member fix broken: zcard={members} (expected 3)"
        assert await limiter.is_allowed("burst-key") is False, "burst exceeded max_attempts but limiter did NOT lock"
        await limiter.reset("burst-key")
