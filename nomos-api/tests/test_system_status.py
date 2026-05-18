"""Tests for GET /api/system/status and GET /api/system/unseal-key."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from nomos_api.auth.password import hash_password
from nomos_api.models import User


@pytest.mark.asyncio
async def test_status_before_setup(client: AsyncClient) -> None:
    """Before any admin exists and not initialized: setup_required is True."""
    with patch(
        "nomos_api.routers.system._get_init_file_path",
        return_value=Path("/nonexistent/path/initialized"),
    ):
        resp = await client.get("/api/system/status")

    assert resp.status_code == 200
    data = resp.json()
    assert data["initialized"] is False
    assert data["admin_exists"] is False
    assert data["setup_required"] is True
    assert "vault_status" in data


@pytest.mark.asyncio
async def test_status_after_bootstrap(client: AsyncClient, db_engine, tmp_path: Path) -> None:
    """After admin exists and initialized file present: setup_required is False."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    # Create admin user in test DB
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        admin = User(
            id="admin-001",
            email="admin@nomos.local",
            password_hash=hash_password("Str0ngP@ssword!"),
            role="admin",
            is_active=True,
            session_timeout_hours=8,
        )
        session.add(admin)
        await session.commit()

    # Create initialized marker file
    init_file = tmp_path / "initialized"
    init_file.write_text("1")

    with patch(
        "nomos_api.routers.system._get_init_file_path",
        return_value=init_file,
    ):
        resp = await client.get("/api/system/status")

    assert resp.status_code == 200
    data = resp.json()
    assert data["initialized"] is True
    assert data["admin_exists"] is True
    assert data["setup_required"] is False


@pytest.mark.asyncio
async def test_unseal_key_returns_key(client: AsyncClient, tmp_path: Path) -> None:
    """First call to unseal-key returns the key from file (no admin yet)."""
    key_file = tmp_path / "unseal-key"
    key_file.write_text("s.ABCDEF1234567890")
    marker = tmp_path / "served-marker"

    with patch(
        "nomos_api.routers.system._get_unseal_key_paths",
        return_value=[key_file],
    ), patch(
        "nomos_api.routers.system._get_served_marker_path",
        return_value=marker,
    ):
        resp = await client.get("/api/system/unseal-key")

    assert resp.status_code == 200
    data = resp.json()
    assert data["unseal_key"] == "s.ABCDEF1234567890"
    assert marker.exists()  # one-shot marker persisted


@pytest.mark.asyncio
async def test_unseal_key_returns_410_on_second_call(client: AsyncClient, tmp_path: Path) -> None:
    """Second call to unseal-key returns 410 Gone (persistent marker)."""
    key_file = tmp_path / "unseal-key"
    key_file.write_text("s.ABCDEF1234567890")
    marker = tmp_path / "served-marker"

    with patch(
        "nomos_api.routers.system._get_unseal_key_paths",
        return_value=[key_file],
    ), patch(
        "nomos_api.routers.system._get_served_marker_path",
        return_value=marker,
    ):
        # First call — succeeds
        resp1 = await client.get("/api/system/unseal-key")
        assert resp1.status_code == 200

        # Second call — 410 Gone (marker now exists on disk)
        resp2 = await client.get("/api/system/unseal-key")
        assert resp2.status_code == 410
        assert "already been served" in resp2.json()["detail"]


@pytest.mark.asyncio
async def test_unseal_key_returns_404_when_no_file(client: AsyncClient, tmp_path: Path) -> None:
    """When unseal key file does not exist, return 404."""
    marker = tmp_path / "served-marker"
    with patch(
        "nomos_api.routers.system._get_unseal_key_paths",
        return_value=[tmp_path / "nonexistent-key"],
    ), patch(
        "nomos_api.routers.system._get_served_marker_path",
        return_value=marker,
    ):
        resp = await client.get("/api/system/unseal-key")

    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()
    assert not marker.exists()  # nothing served -> no marker written


@pytest.mark.asyncio
async def test_unseal_key_reads_from_init_output_json(client: AsyncClient, tmp_path: Path) -> None:
    """Unseal key can be read from init-output.json as fallback."""
    # No plain unseal-key file, but init-output.json exists
    init_output = tmp_path / "init-output.json"
    init_output.write_text(json.dumps({"unseal_keys_b64": ["s.FROM-INIT-OUTPUT"], "root_token": "ignored"}))
    marker = tmp_path / "served-marker"

    with patch(
        "nomos_api.routers.system._get_unseal_key_paths",
        return_value=[tmp_path / "nonexistent-key", init_output],
    ), patch(
        "nomos_api.routers.system._get_served_marker_path",
        return_value=marker,
    ):
        resp = await client.get("/api/system/unseal-key")

    assert resp.status_code == 200
    assert resp.json()["unseal_key"] == "s.FROM-INIT-OUTPUT"


@pytest.mark.asyncio
async def test_unseal_key_forbidden_once_admin_exists(
    client: AsyncClient, db_engine, tmp_path: Path
) -> None:
    """Security: once an admin exists (setup complete), unseal-key is 403 forever."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            User(
                id="admin-sec-001",
                email="admin-sec@nomos.local",
                password_hash=hash_password("Str0ngP@ssword!"),
                role="admin",
                is_active=True,
                session_timeout_hours=8,
            )
        )
        await session.commit()

    key_file = tmp_path / "unseal-key"
    key_file.write_text("s.SHOULD-NEVER-BE-RETURNED")
    marker = tmp_path / "served-marker"

    with patch(
        "nomos_api.routers.system._get_unseal_key_paths",
        return_value=[key_file],
    ), patch(
        "nomos_api.routers.system._get_served_marker_path",
        return_value=marker,
    ):
        resp = await client.get("/api/system/unseal-key")

    assert resp.status_code == 403
    assert "permanently disabled" in resp.json()["detail"]
    assert not marker.exists()


@pytest.mark.asyncio
async def test_status_endpoint_is_public(db_engine, tmp_path, monkeypatch) -> None:
    """The /api/system/status endpoint must be accessible without auth."""
    from nomos_api.config import settings
    from nomos_api.database import get_db
    from nomos_api.main import app
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(settings, "agents_dir", tmp_path / "agents")
    monkeypatch.setattr(settings, "plugin_api_key", "test-plugin-key-at-least-32-characters")

    transport = ASGITransport(app=app)
    # No auth headers, no cookies — should still work
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        with patch(
            "nomos_api.routers.system._get_init_file_path",
            return_value=Path("/nonexistent/path/initialized"),
        ):
            resp = await ac.get("/api/system/status")

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert "setup_required" in data
