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

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_workspace_get_unknown_agent(client):
    resp = await client.get("/api/workspace/unknown-agent")
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_id"] == "unknown-agent"
    assert data["mounted_collections"] == []
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_workspace_mount_creates_workspace(client):
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
async def test_dsgvo_forget_no_data(client):
    resp = await client.post(
        "/api/dsgvo/forget",
        json={"email": "nobody@example.com"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["deleted_messages"] == 0
    assert data["audit_preserved"] is True


@pytest.mark.asyncio
async def test_dsgvo_export_no_data(client):
    resp = await client.post(
        "/api/dsgvo/export",
        json={"email": "nobody@example.com"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["messages"] == []
