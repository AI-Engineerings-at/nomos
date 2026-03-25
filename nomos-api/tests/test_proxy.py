"""Tests for Gateway Proxy endpoints — POST /api/proxy/chat, GET /api/proxy/status."""

from __future__ import annotations

import pytest


class TestProxyStatus:
    async def test_proxy_status_returns_offline_when_gateway_unreachable(self, client) -> None:
        resp = await client.get("/api/proxy/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "offline"

    async def test_proxy_status_response_shape(self, client) -> None:
        resp = await client.get("/api/proxy/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert data["status"] in ("online", "offline")


class TestProxyChat:
    async def test_proxy_chat_returns_error_when_gateway_offline(self, client) -> None:
        resp = await client.post("/api/proxy/chat", json={
            "agent_id": "test-agent",
            "message": "Hello",
        })
        assert resp.status_code == 502
        data = resp.json()
        assert "detail" in data

    async def test_proxy_chat_with_session_id(self, client) -> None:
        resp = await client.post("/api/proxy/chat", json={
            "agent_id": "test-agent",
            "message": "Hello",
            "session_id": "sess-123",
        })
        assert resp.status_code == 502

    async def test_proxy_chat_missing_agent_id(self, client) -> None:
        resp = await client.post("/api/proxy/chat", json={
            "message": "Hello",
        })
        assert resp.status_code == 422

    async def test_proxy_chat_missing_message(self, client) -> None:
        resp = await client.post("/api/proxy/chat", json={
            "agent_id": "test-agent",
        })
        assert resp.status_code == 422
