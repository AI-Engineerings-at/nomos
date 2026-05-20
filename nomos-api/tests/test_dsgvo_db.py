"""Tests for DSGVO Art. 17 forget + Art. 15 export — DB-backed via memory service."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.services.memory import store_message


pytestmark = pytest.mark.anyio


async def _create_agent(admin_client: AsyncClient) -> dict:
    """Helper: create an agent via HTTP and return the response body."""
    resp = await admin_client.post(
        "/api/agents",
        json={
            "name": "DSGVO Test Agent",
            "role": "test-agent",
            "company": "Test Corp",
            "email": "max@example.com",
            "risk_class": "limited",
        },
    )
    assert resp.status_code == 201
    return resp.json()


async def _seed_messages(db: AsyncSession, agent_id: str) -> None:
    """Helper: seed some messages containing PII into agent_memory."""
    await store_message(db, agent_id, "sess-1", "user", "My email is max@example.com")
    await store_message(db, agent_id, "sess-1", "assistant", "Hello Max!")
    await store_message(db, agent_id, "sess-2", "user", "Contact me at max@example.com please")


async def test_forget_deletes_from_db(admin_client: AsyncClient, db_session: AsyncSession) -> None:
    """POST /api/dsgvo/forget deletes messages containing the email from the DB."""
    agent = await _create_agent(admin_client)
    await _seed_messages(db_session, agent["id"])

    resp = await admin_client.post("/api/dsgvo/forget", json={"email": "max@example.com"})
    assert resp.status_code == 200

    body = resp.json()
    assert body["deleted_messages"] == 2  # 2 messages contain max@example.com
    assert body["search_term"] == "max@example.com"
    assert body["audit_event"] == "data.erased"
    assert body["audit_preserved"] is True


async def test_forget_requires_admin(client: AsyncClient) -> None:
    """L035 / A-C1: non-admin (service principal via API-key header)
    must NOT be able to trigger a cross-tenant DSGVO deletion."""
    resp = await client.post("/api/dsgvo/forget", json={"email": "anyone@example.com"})
    # 401/403 depending on principal class — both are correct refusals.
    assert resp.status_code in (401, 403)


async def test_export_requires_admin(client: AsyncClient) -> None:
    """L035 / A-C1: cross-tenant DSGVO export must reject non-admins."""
    resp = await client.post("/api/dsgvo/export", json={"email": "anyone@example.com"})
    assert resp.status_code in (401, 403)


async def test_forget_unknown_email(admin_client: AsyncClient) -> None:
    """Forget with unknown email returns deleted_messages=0."""
    resp = await admin_client.post("/api/dsgvo/forget", json={"email": "nobody@example.com"})
    assert resp.status_code == 200

    body = resp.json()
    assert body["deleted_messages"] == 0
    assert body["audit_event"] == ""


async def test_export_returns_matching(admin_client: AsyncClient, db_session: AsyncSession) -> None:
    """POST /api/dsgvo/export returns messages matching the email."""
    agent = await _create_agent(admin_client)
    await _seed_messages(db_session, agent["id"])

    resp = await admin_client.post("/api/dsgvo/export", json={"email": "max@example.com"})
    assert resp.status_code == 200

    body = resp.json()
    assert body["email"] == "max@example.com"
    assert body["total"] == 2  # 2 messages contain max@example.com
    assert len(body["messages"]) == 2
    # Verify structure of returned messages
    for msg in body["messages"]:
        assert "agent_id" in msg
        assert "session_id" in msg
        assert "role" in msg
        assert "content" in msg
        assert "max@example.com" in msg["content"]


async def test_export_empty(admin_client: AsyncClient) -> None:
    """Export without matching messages returns total=0."""
    resp = await admin_client.post("/api/dsgvo/export", json={"email": "nobody@example.com"})
    assert resp.status_code == 200

    body = resp.json()
    assert body["total"] == 0
    assert body["messages"] == []
