"""Tests for Gateway Proxy endpoints — POST /api/proxy/chat, GET /api/proxy/status.

H2/H3 regression: proxy_chat now requires an authenticated user and
agent-ownership (IDOR fix). Outbound URLs are settings-only (SSRF guard).
"""

from __future__ import annotations

import uuid

from nomos_api.models import Agent


async def _create_owned_agent(authed_client, name: str = "Proxy Test Agent") -> str:
    """Create an agent owned by the authed_client user (test@test.com)."""
    resp = await authed_client.post(
        "/api/agents",
        json={
            "name": name,
            "role": "test-role",
            "company": "Test Co",
            "email": "test@test.com",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


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
    async def test_proxy_chat_returns_error_when_gateway_offline(self, authed_client) -> None:
        agent_id = await _create_owned_agent(authed_client)
        resp = await authed_client.post(
            "/api/proxy/chat",
            json={
                "agent_id": agent_id,
                "message": "Hello",
            },
        )
        assert resp.status_code == 502
        data = resp.json()
        assert "detail" in data

    async def test_proxy_chat_with_session_id(self, authed_client) -> None:
        agent_id = await _create_owned_agent(authed_client, "Proxy Session Agent")
        resp = await authed_client.post(
            "/api/proxy/chat",
            json={
                "agent_id": agent_id,
                "message": "Hello",
                "session_id": "sess-123",
            },
        )
        assert resp.status_code == 502

    async def test_proxy_chat_missing_agent_id(self, authed_client) -> None:
        resp = await authed_client.post(
            "/api/proxy/chat",
            json={
                "message": "Hello",
            },
        )
        assert resp.status_code == 422

    async def test_proxy_chat_missing_message(self, authed_client) -> None:
        resp = await authed_client.post(
            "/api/proxy/chat",
            json={
                "agent_id": "test-agent",
            },
        )
        assert resp.status_code == 422


class TestProxyChatAuthZ:
    """H3 IDOR: a caller may only chat as an agent they own."""

    async def test_unauthenticated_plugin_only_is_rejected(self, client) -> None:
        # `client` fixture has the plugin API key but NO user cookie.
        resp = await client.post(
            "/api/proxy/chat",
            json={
                "agent_id": "whatever",
                "message": "Hello",
            },
        )
        assert resp.status_code == 401

    async def test_chat_unknown_agent_is_404_not_silent(self, authed_client) -> None:
        resp = await authed_client.post(
            "/api/proxy/chat",
            json={
                "agent_id": "does-not-exist",
                "message": "Hello",
            },
        )
        assert resp.status_code == 404

    async def test_cannot_chat_as_other_users_agent(self, authed_client, db_session) -> None:
        # Seed an agent owned by a DIFFERENT user (not test@test.com).
        other_id = f"other-{uuid.uuid4().hex[:8]}"
        db_session.add(
            Agent(
                id=other_id,
                name="Foreign Agent",
                role="r",
                company="C",
                email="someone-else@evil.test",
                manifest_hash="0" * 64,
                manifest_data={},
                agents_dir="/tmp/x",
            )
        )
        await db_session.commit()
        resp = await authed_client.post(
            "/api/proxy/chat",
            json={
                "agent_id": other_id,
                "message": "Hello",
            },
        )
        assert resp.status_code == 403
        assert "Not authorized" in resp.json()["detail"]


class TestProxyChatNoSSRF:
    """H3 SSRF: outbound URLs must come only from settings, never the request."""

    async def test_outbound_urls_are_settings_only(self) -> None:
        import inspect

        from nomos_api.routers import proxy

        src = inspect.getsource(proxy._gateway_fetch) + inspect.getsource(proxy._direct_llm_chat)
        # URLs are built from settings.* exclusively.
        assert "settings.gateway_url" in src
        assert "settings.llm_base_url" in src
        # No request/agent-controlled value is interpolated into a URL.
        assert "request." not in src
        assert "agent." not in src
