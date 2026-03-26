"""Tests for DB-backed heartbeat service — agent liveness via PostgreSQL."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from nomos_api.services.heartbeat import derive_status

pytestmark = pytest.mark.anyio

_AGENT_PAYLOAD = {
    "name": "Heartbeat Test Agent",
    "role": "test-runner",
    "company": "TestCo",
    "email": "hb@test.local",
    "risk_class": "limited",
}


async def _create_agent(client: AsyncClient) -> str:
    """Helper: create an agent and return its id."""
    resp = await client.post("/api/agents", json=_AGENT_PAYLOAD)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def test_heartbeat_updates_agent(client: AsyncClient) -> None:
    """POST /api/agents/{id}/heartbeat returns 200 with status online."""
    agent_id = await _create_agent(client)
    resp = await client.post(
        f"/api/agents/{agent_id}/heartbeat",
        json={"metrics": {"cpu": 42}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["agent_id"] == agent_id
    assert body["status"] == "online"


async def test_heartbeat_unknown_agent(client: AsyncClient) -> None:
    """POST /api/agents/nonexistent/heartbeat returns 404."""
    resp = await client.post(
        "/api/agents/nonexistent-agent-xyz/heartbeat",
        json={"metrics": {}},
    )
    assert resp.status_code == 404


async def test_heartbeat_persists_in_fleet(client: AsyncClient) -> None:
    """After heartbeat, GET /api/fleet/{id} shows heartbeat_at is set."""
    agent_id = await _create_agent(client)

    # Before heartbeat — heartbeat_at should be None
    resp = await client.get(f"/api/fleet/{agent_id}")
    assert resp.status_code == 200
    assert resp.json()["heartbeat_at"] is None

    # Send heartbeat
    hb_resp = await client.post(
        f"/api/agents/{agent_id}/heartbeat",
        json={"metrics": {}},
    )
    assert hb_resp.status_code == 200

    # After heartbeat — heartbeat_at should be set
    resp = await client.get(f"/api/fleet/{agent_id}")
    assert resp.status_code == 200
    assert resp.json()["heartbeat_at"] is not None


def test_derive_status_none() -> None:
    """None heartbeat_at means offline."""
    assert derive_status(None) == "offline"


def test_derive_status_recent() -> None:
    """Recent heartbeat means online."""
    recent = datetime.now(timezone.utc) - timedelta(seconds=30)
    assert derive_status(recent) == "online"


def test_derive_status_stale() -> None:
    """Heartbeat 6 minutes ago means stale."""
    stale = datetime.now(timezone.utc) - timedelta(minutes=6)
    assert derive_status(stale) == "stale"


def test_derive_status_offline() -> None:
    """Heartbeat 11 minutes ago means offline."""
    old = datetime.now(timezone.utc) - timedelta(minutes=11)
    assert derive_status(old) == "offline"
