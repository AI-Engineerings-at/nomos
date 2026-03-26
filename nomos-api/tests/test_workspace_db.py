"""Tests for DB-backed workspace endpoints."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_workspace_get_unknown_agent(client):
    """GET /api/workspace/{agent_id} for non-existent agent returns inactive workspace."""
    resp = await client.get("/api/workspace/unknown-agent")
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_id"] == "unknown-agent"
    assert data["workspace_id"] is None
    assert data["mounted_collections"] == []
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_workspace_get_existing_agent(client, db_session):
    """GET /api/workspace/{agent_id} for existing agent returns active workspace."""
    from nomos_api.models import Agent

    agent = Agent(
        id="ws-test-agent",
        name="Test Agent",
        role="secretary",
        company="TestCo",
        email="test@test.com",
        risk_class="limited",
        status="running",
        manifest_hash="a" * 64,
        manifest_data={},
        compliance_status="compliant",
        agents_dir="/tmp/agents",
    )
    db_session.add(agent)
    await db_session.commit()

    resp = await client.get("/api/workspace/ws-test-agent")
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_id"] == "ws-test-agent"
    assert data["workspace_id"] == "ws-test-agent"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_workspace_mount(client, db_session):
    """POST /api/workspace/mount creates a mount entry and returns success."""
    from nomos_api.models import Agent

    agent = Agent(
        id="mount-agent",
        name="Mount Agent",
        role="secretary",
        company="TestCo",
        email="mount@test.com",
        risk_class="limited",
        status="running",
        manifest_hash="b" * 64,
        manifest_data={},
        compliance_status="compliant",
        agents_dir="/tmp/agents",
    )
    db_session.add(agent)
    await db_session.commit()

    resp = await client.post(
        "/api/workspace/mount",
        json={"agent_id": "mount-agent", "collection_name": "brand-guidelines"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_id"] == "mount-agent"
    assert data["collection_name"] == "brand-guidelines"
    assert data["mounted"] is True

    # Verify it shows up in GET
    resp2 = await client.get("/api/workspace/mount-agent")
    data2 = resp2.json()
    assert "brand-guidelines" in data2["mounted_collections"]


@pytest.mark.asyncio
async def test_workspace_mount_idempotent(client, db_session):
    """Mounting the same collection twice does not create duplicates."""
    from nomos_api.models import Agent

    agent = Agent(
        id="idemp-agent",
        name="Idempotent Agent",
        role="secretary",
        company="TestCo",
        email="idemp@test.com",
        risk_class="limited",
        status="running",
        manifest_hash="c" * 64,
        manifest_data={},
        compliance_status="compliant",
        agents_dir="/tmp/agents",
    )
    db_session.add(agent)
    await db_session.commit()

    await client.post(
        "/api/workspace/mount",
        json={"agent_id": "idemp-agent", "collection_name": "docs"},
    )
    await client.post(
        "/api/workspace/mount",
        json={"agent_id": "idemp-agent", "collection_name": "docs"},
    )

    resp = await client.get("/api/workspace/idemp-agent")
    data = resp.json()
    assert data["mounted_collections"].count("docs") == 1


@pytest.mark.asyncio
async def test_workspace_unmount_not_found(client):
    """POST /api/workspace/unmount without prior mount returns 404."""
    resp = await client.post(
        "/api/workspace/unmount",
        json={"agent_id": "unknown", "collection_name": "nothing"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_workspace_mount_unmount_cycle(client, db_session):
    """Mount then unmount a collection successfully."""
    from nomos_api.models import Agent

    agent = Agent(
        id="cycle-agent",
        name="Cycle Agent",
        role="secretary",
        company="TestCo",
        email="cycle@test.com",
        risk_class="limited",
        status="running",
        manifest_hash="d" * 64,
        manifest_data={},
        compliance_status="compliant",
        agents_dir="/tmp/agents",
    )
    db_session.add(agent)
    await db_session.commit()

    # Mount
    await client.post(
        "/api/workspace/mount",
        json={"agent_id": "cycle-agent", "collection_name": "brand"},
    )

    # Unmount
    resp = await client.post(
        "/api/workspace/unmount",
        json={"agent_id": "cycle-agent", "collection_name": "brand"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["mounted"] is False

    # Verify removed
    resp2 = await client.get("/api/workspace/cycle-agent")
    data2 = resp2.json()
    assert "brand" not in data2["mounted_collections"]
