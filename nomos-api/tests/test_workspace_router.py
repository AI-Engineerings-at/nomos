"""Tests for workspace and DSGVO API routers."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client(db_engine, tmp_path, monkeypatch):
    """HTTPX async test client with patched DB and agents_dir."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from nomos_api.config import settings
    from nomos_api.database import get_db
    from nomos_api.main import app

    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(settings, "agents_dir", tmp_path / "agents")
    monkeypatch.setattr(settings, "plugin_api_key", "test-plugin-key-at-least-32-characters")

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-NomOS-API-Key": "test-plugin-key-at-least-32-characters"},
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_workspace_get_unknown_agent(client):
    """L035 / A-C4: unknown agent -> 404 (no longer leaks existence)."""
    resp = await client.get("/api/workspace/unknown-agent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_workspace_mount_requires_existing_agent(client):
    """Mounting a collection for a non-existent agent returns 404."""
    resp = await client.post(
        "/api/workspace/mount",
        json={"agent_id": "nonexistent", "collection_name": "brand-guidelines"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_workspace_mount_creates_workspace(client, db_session):
    from nomos_api.models import Agent

    agent = Agent(
        id="mani",
        name="Mani Agent",
        role="secretary",
        company="TestCo",
        email="mani@test.com",
        risk_class="limited",
        status="running",
        manifest_hash="a" * 64,
        manifest_data={},
        compliance_status="compliant",
        agents_dir="/tmp/agents",
    )
    db_session.add(agent)
    await db_session.commit()

    resp = await client.post(
        "/api/workspace/mount",
        json={"agent_id": "mani", "collection_name": "brand-guidelines"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_id"] == "mani"
    assert data["collection_name"] == "brand-guidelines"
    assert data["mounted"] is True


@pytest.mark.asyncio
async def test_workspace_unmount_not_found(client):
    resp = await client.post(
        "/api/workspace/unmount",
        json={"agent_id": "unknown", "collection_name": "nothing"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_dsgvo_forget_rejects_non_admin(client):
    """L035 / A-C1: DSGVO endpoints are admin-only as of 0.2.1.
    The empty-data happy-path is exercised in test_dsgvo_db.py with
    admin_client; this test guards the AuthZ boundary on the same
    file that previously asserted the (insecure) 200."""
    resp = await client.post(
        "/api/dsgvo/forget",
        json={"email": "nobody@example.com"},
    )
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_dsgvo_export_rejects_non_admin(client):
    """L035 / A-C1: same as forget — admin-only since 0.2.1."""
    resp = await client.post(
        "/api/dsgvo/export",
        json={"email": "nobody@example.com"},
    )
    assert resp.status_code in (401, 403)
