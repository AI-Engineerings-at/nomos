"""Test fixtures — async SQLite database + HTTPX test client."""

from __future__ import annotations

import os

# Set mandatory secrets for tests before any NomOS modules are imported
os.environ["NOMOS_JWT_SECRET"] = "test-jwt-secret-at-least-32-chars-long-123"
os.environ["NOMOS_PLUGIN_API_KEY"] = "test-plugin-key"
os.environ["NOMOS_GATEWAY_TOKEN"] = "test-gateway-token"
os.environ["NOMOS_DB_PASSWORD"] = "test-db-password"
os.environ["NOMOS_DEV_MODE"] = "true"

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from nomos_api.auth.jwt import TokenPayload, create_token
from nomos_api.auth.password import hash_password
from nomos_api.models import Base, User


@pytest.fixture
async def db_engine():
    """In-memory SQLite for tests — no PostgreSQL needed."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(db_engine, tmp_path, monkeypatch):
    """HTTPX async test client with patched DB and agents_dir."""
    from nomos_api.config import settings
    from nomos_api.database import get_db
    from nomos_api.main import app

    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(settings, "agents_dir", tmp_path / "agents")

    # Set a test plugin API key so all requests pass the auth middleware
    monkeypatch.setattr(settings, "plugin_api_key", "test-plugin-key")

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-NomOS-API-Key": "test-plugin-key"},
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def authed_client(db_engine, tmp_path, monkeypatch):
    """HTTPX test client with an authenticated user cookie (email=test@test.com, role=user).

    Use this fixture for tests that hit auth-protected endpoints.
    """
    from nomos_api.config import settings
    from nomos_api.database import get_db
    from nomos_api.main import app

    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(settings, "agents_dir", tmp_path / "agents")
    monkeypatch.setattr(settings, "plugin_api_key", "test-plugin-key")

    # Seed a user that matches the default test agent email
    user_id = str(uuid.uuid4())
    async with session_factory() as session:
        user = User(
            id=user_id,
            email="test@test.com",
            password_hash=hash_password("Str0ngP@ssword!"),
            role="user",
            is_active=True,
            session_timeout_hours=24,
        )
        session.add(user)
        await session.commit()

    # Create JWT cookie
    payload = TokenPayload(user_id=user_id, email="test@test.com", role="user")
    token = create_token(payload, "test-jwt-secret-at-least-32-chars-long-123")

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-NomOS-API-Key": "test-plugin-key"},
        cookies={"nomos_token": token},
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
