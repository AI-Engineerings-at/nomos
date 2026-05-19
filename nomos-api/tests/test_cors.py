"""CORS tests — verify that unknown origins are not allowed (in-process via ASGITransport)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from nomos_api.main import app


@pytest.mark.asyncio
async def test_cors_rejects_unknown_origin():
    """An unknown origin must NOT receive a permissive Access-Control-Allow-Origin header."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://evil.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
    # ACAO must not echo the evil origin back, and must not be the wildcard "*"
    acao = response.headers.get("access-control-allow-origin", "")
    assert acao != "http://evil.example.com", "Server must not reflect unknown origin in ACAO header"
    assert acao != "*", "Server must not use wildcard ACAO with credentials=True"


@pytest.mark.asyncio
async def test_cors_allows_known_origin():
    """An origin from cors_origins must receive a matching ACAO header on preflight."""
    transport = ASGITransport(app=app)
    # dev_mode=True appends http://localhost:3040 (see main.py cors_origins building)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3040",
                "Access-Control-Request-Method": "GET",
            },
        )
    acao = response.headers.get("access-control-allow-origin", "")
    assert acao == "http://localhost:3040", f"Known origin should be reflected in ACAO, got: {acao!r}"


@pytest.mark.asyncio
async def test_cors_unknown_origin_simple_request():
    """A simple (non-preflight) request from an unknown origin must not get a reflective ACAO."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/health",
            headers={"Origin": "http://attacker.example.com"},
        )
    acao = response.headers.get("access-control-allow-origin", "")
    assert acao != "http://attacker.example.com", "Simple request from unknown origin must not receive reflective ACAO"
    assert acao != "*", "Wildcard ACAO must not be used"
