"""Integration tests for DB-backed budget service — check, track, costs."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.anyio


async def _create_agent(client, name: str = "Budget Agent") -> str:
    """Helper: create an agent and return its ID."""
    resp = await client.post(
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


async def test_budget_check_reads_from_db(client) -> None:
    """Fresh agent: 0/50 used, check with small cost -> allowed, normal."""
    agent_id = await _create_agent(client)
    resp = await client.post(
        "/api/budget/check",
        json={
            "agent_id": agent_id,
            "estimated_cost": 5.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["allowed"] is True
    assert data["status"] == "normal"
    assert data["remaining"] == pytest.approx(45.0)
    assert data["current"] == pytest.approx(0.0)
    assert data["limit"] == pytest.approx(50.0)
    assert data["agent_id"] == agent_id


async def test_budget_check_exceeded(client) -> None:
    """Estimated cost > limit -> not allowed, exceeded."""
    agent_id = await _create_agent(client)
    resp = await client.post(
        "/api/budget/check",
        json={
            "agent_id": agent_id,
            "estimated_cost": 60.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["allowed"] is False
    assert data["status"] == "exceeded"


async def test_budget_check_warning(client) -> None:
    """Track 42 EUR, then check 1 EUR -> 86% used -> warning."""
    agent_id = await _create_agent(client)

    # Track 42 EUR first
    track_resp = await client.post(
        "/api/budget/track",
        json={
            "agent_id": agent_id,
            "cost": 42.0,
        },
    )
    assert track_resp.status_code == 200

    # Now check with 1 EUR additional
    resp = await client.post(
        "/api/budget/check",
        json={
            "agent_id": agent_id,
            "estimated_cost": 1.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["allowed"] is True
    assert data["status"] == "warning"
    assert data["percent_used"] == pytest.approx(86.0)


async def test_budget_check_unknown_agent(client) -> None:
    """Unknown agent -> restrictive default (fail-closed), not 404."""
    resp = await client.post(
        "/api/budget/check",
        json={
            "agent_id": "nonexistent-agent-xyz",
            "estimated_cost": 1.0,
        },
    )
    assert resp.status_code == 200  # Not 404 — fail-closed, not error
    data = resp.json()
    assert data["allowed"] is False
    assert data["status"] == "unknown_agent"
    assert "reason" in data


async def test_budget_check_unknown_agent_returns_restrictive(client) -> None:
    """Unknown agent returns fail-closed response with correct fields."""
    resp = await client.post(
        "/api/budget/check",
        json={
            "agent_id": "nonexistent-agent",
            "estimated_cost": 0.01,
        },
    )
    assert resp.status_code == 200  # Not 404
    data = resp.json()
    assert data["allowed"] is False
    assert data["status"] == "unknown_agent"
    assert "reason" in data


async def test_budget_track_persists(client) -> None:
    """Track 25, then 10 -> budget_used_eur == 35."""
    agent_id = await _create_agent(client)

    resp1 = await client.post(
        "/api/budget/track",
        json={
            "agent_id": agent_id,
            "cost": 25.0,
        },
    )
    assert resp1.status_code == 200
    assert resp1.json()["budget_used_eur"] == pytest.approx(25.0)

    resp2 = await client.post(
        "/api/budget/track",
        json={
            "agent_id": agent_id,
            "cost": 10.0,
        },
    )
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["budget_used_eur"] == pytest.approx(35.0)
    assert data["budget_limit_eur"] == pytest.approx(50.0)


async def test_costs_overview(client, admin_client) -> None:
    """GET /api/costs returns all agents with budget info.

    L035 / audit A-C7: cross-tenant cost list is admin-only as of 0.2.1.
    Service principal (client) creates + tracks the agent; admin_client
    reads the cross-tenant list.
    """
    agent_id = await _create_agent(client, name="Costs Agent")

    await client.post(
        "/api/budget/track",
        json={
            "agent_id": agent_id,
            "cost": 15.0,
        },
    )

    resp = await admin_client.get("/api/costs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    agent_cost = next(c for c in data["costs"] if c["agent_id"] == agent_id)
    assert agent_cost["total_cost_eur"] == pytest.approx(15.0)
    assert agent_cost["budget_limit_eur"] == pytest.approx(50.0)


async def test_costs_overview_rejects_non_admin(client) -> None:
    """L035 / A-C7: service principal must not be able to list
    cross-tenant costs."""
    resp = await client.get("/api/costs")
    assert resp.status_code in (401, 403)
