"""CORS tests — verify that unknown origins are not allowed."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from nomos_api.main import app


@pytest.mark.asyncio
async def test_cors_rejects_unknown_origin():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options(
            "/health",
            headers={"Origin": "http://evil.example.com", "Access-Control-Request-Method": "GET"},
        )
        assert "access-control-allow-origin" not in response.headers or \
               response.headers.get("access-control-allow-origin") != "http://evil.example.com"
