"""HTTP tests for GET /api/costs/{agent_id} — per-agent cost endpoint.

GET /api/costs (fleet overview) is already tested in test_budget_db.py.
This file adds focused tests for the per-agent endpoint that was not covered.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def _create_agent(client: AsyncClient, name: str, email: str) -> str:
    r = await client.post(
        "/api/agents",
        json={
            "name": name,
            "role": "worker",
            "company": "TestCo",
            "email": email,
            "risk_class": "limited",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def test_get_agent_cost_returns_correct_fields(client: AsyncClient) -> None:
    """GET /api/costs/{agent_id} returns budget fields for a known agent."""
    agent_id = await _create_agent(client, "CostBot", "costbot@test.local")

    resp = await client.get(f"/api/costs/{agent_id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["agent_id"] == agent_id
    assert isinstance(body["total_cost_eur"], float)
    assert isinstance(body["budget_limit_eur"], float)
    assert body["budget_status"] in {"normal", "warning", "exceeded"}
    assert isinstance(body["percent_used"], float)


async def test_get_agent_cost_normal_status_at_zero(client: AsyncClient) -> None:
    """Fresh agent with 0 cost has status=normal and percent_used=0.0."""
    agent_id = await _create_agent(client, "ZeroCostBot", "zerocost@test.local")

    resp = await client.get(f"/api/costs/{agent_id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total_cost_eur"] == 0.0
    assert body["budget_status"] == "normal"
    assert body["percent_used"] == 0.0


async def test_get_agent_cost_warning_status_after_80_percent(client: AsyncClient) -> None:
    """Agent with budget_used >= 80% of limit has status=warning."""
    agent_id = await _create_agent(client, "WarningBot", "warning@test.local")

    # Default budget_limit_eur is 50.0 — spend 41 EUR (82%) to trigger warning
    await client.post("/api/budget/track", json={"agent_id": agent_id, "cost": 41.0})

    resp = await client.get(f"/api/costs/{agent_id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["budget_status"] == "warning", f"Expected 'warning' at 82% budget use, got: {body['budget_status']!r}"
    assert body["percent_used"] >= 80.0


async def test_get_agent_cost_exceeded_status_at_limit(client: AsyncClient) -> None:
    """Agent with budget_used >= budget_limit has status=exceeded."""
    agent_id = await _create_agent(client, "ExceededBot", "exceeded@test.local")

    # Default limit is 50.0 — spend exactly 50 EUR
    await client.post("/api/budget/track", json={"agent_id": agent_id, "cost": 50.0})

    resp = await client.get(f"/api/costs/{agent_id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["budget_status"] == "exceeded", (
        f"Expected 'exceeded' at 100% budget use, got: {body['budget_status']!r}"
    )
    assert body["percent_used"] == pytest.approx(100.0)


async def test_get_agent_cost_unknown_agent_returns_404(client: AsyncClient) -> None:
    """GET /api/costs/{agent_id} with a non-existent agent_id returns 404."""
    resp = await client.get("/api/costs/nonexistent-agent-xyz")

    assert resp.status_code == 404
    assert "nonexistent-agent-xyz" in resp.json()["detail"]
