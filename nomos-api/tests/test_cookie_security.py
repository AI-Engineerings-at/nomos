"""Tests for cookie security settings (secure flag, SameSite)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from nomos_api.models import Base, User
from nomos_api.auth.password import hash_password


@pytest.fixture
async def cookie_engine():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def cookie_client(cookie_engine, monkeypatch):
    from nomos_api.config import settings
    from nomos_api.database import get_db
    from nomos_api.main import app

    factory = async_sessionmaker(cookie_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with factory() as session:
            yield session

    # Seed a test user
    async with factory() as session:
        user = User(
            id=1,
            email="cookie@nomos.local",
            password_hash=hash_password("CookieP@ss12!"),
            role="admin",
        )
        session.add(user)
        await session.commit()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(settings, "jwt_secret", "test-secret-key-for-cookies-32ch")
    from unittest.mock import AsyncMock
    mock_limiter = AsyncMock()
    mock_limiter.is_allowed = AsyncMock(return_value=True)
    mock_limiter.record_attempt = AsyncMock()
    mock_limiter.reset = AsyncMock()
    monkeypatch.setattr("nomos_api.routers.auth._login_limiter", mock_limiter)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, settings

    app.dependency_overrides.clear()


class TestCookieSecure:
    async def test_secure_cookie_when_cookie_secure_true(self, cookie_client, monkeypatch):
        client, settings = cookie_client
        monkeypatch.setattr(settings, "cookie_secure", True)

        resp = await client.post("/api/auth/login", json={
            "email": "cookie@nomos.local",
            "password": "CookieP@ss12!",
        })
        assert resp.status_code == 200

        cookie_header = resp.headers.get("set-cookie", "").lower()
        assert "secure" in cookie_header
        assert "samesite=strict" in cookie_header

    async def test_no_secure_cookie_when_cookie_secure_false(self, cookie_client, monkeypatch):
        client, settings = cookie_client
        monkeypatch.setattr(settings, "cookie_secure", False)

        resp = await client.post("/api/auth/login", json={
            "email": "cookie@nomos.local",
            "password": "CookieP@ss12!",
        })
        assert resp.status_code == 200

        cookie_header = resp.headers.get("set-cookie", "")
        cookie_header = resp.headers.get("set-cookie", "").lower()
        assert "; secure" not in cookie_header
        assert "samesite=lax" in cookie_header

    async def test_logout_cookie_respects_settings(self, cookie_client, monkeypatch):
        client, settings = cookie_client
        monkeypatch.setattr(settings, "cookie_secure", True)

        # Login first
        login_resp = await client.post("/api/auth/login", json={
            "email": "cookie@nomos.local",
            "password": "CookieP@ss12!",
        })
        cookies = dict(login_resp.cookies)

        # Logout
        resp = await client.post("/api/auth/logout", cookies=cookies)
        assert resp.status_code == 200
