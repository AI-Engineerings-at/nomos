"""Tests for the approval service — DB-backed via async endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def _create_agent(client: AsyncClient, name: str, email: str) -> str:
    r = await client.post(
        "/api/agents",
        json={
            "name": name,
            "role": "test",
            "company": "TestCo",
            "email": email,
            "risk_class": "limited",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def test_create_approval(client: AsyncClient) -> None:
    agent_id = await _create_agent(client, "ApprovalBot", "approve@test.local")
    r = await client.post(
        "/api/approvals",
        json={
            "agent_id": agent_id,
            "action": "external_api_call",
            "description": "Call CRM API",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "pending"
    assert "id" in body
    assert body["agent_id"] == agent_id
    assert body["action"] == "external_api_call"


async def test_approve(client: AsyncClient) -> None:
    agent_id = await _create_agent(client, "ApproveBot", "appbot@test.local")
    r = await client.post(
        "/api/approvals",
        json={
            "agent_id": agent_id,
            "action": "file_deletion",
            "description": "Delete temp.txt",
        },
    )
    approval_id = r.json()["id"]

    r2 = await client.post(
        f"/api/approvals/{approval_id}/approve",
        json={"resolved_by": "admin@nomos.local"},
    )
    assert r2.status_code == 200
    body = r2.json()
    assert body["status"] == "approved"
    assert body["resolved_by"] == "admin@nomos.local"
    assert body["resolved_at"] is not None


async def test_reject(client: AsyncClient) -> None:
    agent_id = await _create_agent(client, "RejectBot", "rejbot@test.local")
    r = await client.post(
        "/api/approvals",
        json={
            "agent_id": agent_id,
            "action": "data_export",
            "description": "Export CSV",
        },
    )
    approval_id = r.json()["id"]

    r2 = await client.post(
        f"/api/approvals/{approval_id}/reject",
        json={"resolved_by": "admin@nomos.local"},
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "denied"


async def test_list_pending(client: AsyncClient) -> None:
    agent_id = await _create_agent(client, "ListBot", "listbot@test.local")
    await client.post(
        "/api/approvals",
        json={"agent_id": agent_id, "action": "a", "description": "A"},
    )
    await client.post(
        "/api/approvals",
        json={"agent_id": agent_id, "action": "b", "description": "B"},
    )

    r = await client.get("/api/approvals")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 2
    for item in body["approvals"]:
        assert item["status"] == "pending"


async def test_approve_unknown_returns_404(client: AsyncClient) -> None:
    r = await client.post(
        "/api/approvals/99999/approve",
        json={"resolved_by": "admin@nomos.local"},
    )
    assert r.status_code == 404


async def test_list_by_agent(client: AsyncClient) -> None:
    agent_a = await _create_agent(client, "AgentA", "agenta@test.local")
    agent_b = await _create_agent(client, "AgentB", "agentb@test.local")

    await client.post(
        "/api/approvals",
        json={"agent_id": agent_a, "action": "x", "description": "X"},
    )
    await client.post(
        "/api/approvals",
        json={"agent_id": agent_b, "action": "y", "description": "Y"},
    )
    await client.post(
        "/api/approvals",
        json={"agent_id": agent_a, "action": "z", "description": "Z"},
    )

    r = await client.get(f"/api/approvals?agent_id={agent_a}")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    for item in body["approvals"]:
        assert item["agent_id"] == agent_a
