"""Tests for the users router endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from nomos_api.models import Base, User
from nomos_api.auth.password import hash_password


@pytest.fixture
async def users_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def users_client(users_engine, tmp_path, monkeypatch):
    from nomos_api.config import settings
    from nomos_api.database import get_db
    from nomos_api.main import app
    from nomos_api.routers.auth import _login_limiter

    _login_limiter._attempts.clear()
    _login_limiter._lockouts.clear()

    factory = async_sessionmaker(users_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(settings, "agents_dir", tmp_path / "agents")
    monkeypatch.setattr(settings, "jwt_secret", "test-secret-key")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def admin_user(users_engine):
    """Create an admin user for auth."""
    factory = async_sessionmaker(users_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        user = User(
            id="admin-1",
            email="admin@nomos.local",
            password_hash=hash_password("AdminP@ssword1!"),
            role="admin",
            session_timeout_hours=8,
            is_active=True,
        )
        session.add(user)
        await session.commit()
    return user


async def _login_as_admin(client):
    """Helper: login as admin and return cookies."""
    resp = await client.post("/api/auth/login", json={
        "email": "admin@nomos.local",
        "password": "AdminP@ssword1!",
    })
    assert resp.status_code == 200
    return dict(resp.cookies)


async def test_list_users_requires_auth(users_client):
    resp = await users_client.get("/api/users")
    assert resp.status_code == 401


async def test_list_users_as_admin(users_client, admin_user):
    cookies = await _login_as_admin(users_client)
    resp = await users_client.get("/api/users", cookies=cookies)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any(u["email"] == "admin@nomos.local" for u in data["users"])


async def test_create_user_returns_recovery_key(users_client, admin_user):
    cookies = await _login_as_admin(users_client)
    resp = await users_client.post("/api/users", json={
        "email": "newuser@nomos.local",
        "password": "NewUserP@ss12!",
        "role": "user",
    }, cookies=cookies)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newuser@nomos.local"
    assert data["role"] == "user"
    # Recovery key shown ONCE
    assert "recovery_key" in data
    words = data["recovery_key"].split()
    assert len(words) == 12


async def test_create_user_duplicate_email(users_client, admin_user):
    cookies = await _login_as_admin(users_client)
    # Create first user
    await users_client.post("/api/users", json={
        "email": "dup@nomos.local",
        "password": "DupUserP@ss12!!",
        "role": "user",
    }, cookies=cookies)
    # Try duplicate
    resp = await users_client.post("/api/users", json={
        "email": "dup@nomos.local",
        "password": "DupUserP@ss12!!",
        "role": "user",
    }, cookies=cookies)
    assert resp.status_code == 409


async def test_update_user(users_client, admin_user):
    cookies = await _login_as_admin(users_client)
    # Create a user first
    create_resp = await users_client.post("/api/users", json={
        "email": "patchme@nomos.local",
        "password": "PatchMeP@ss12!",
        "role": "user",
    }, cookies=cookies)
    user_id = create_resp.json()["id"]

    # Update role to officer
    resp = await users_client.patch(f"/api/users/{user_id}", json={
        "role": "officer",
    }, cookies=cookies)
    assert resp.status_code == 200
    assert resp.json()["role"] == "officer"


async def test_deactivate_user(users_client, admin_user):
    cookies = await _login_as_admin(users_client)
    # Create a user
    create_resp = await users_client.post("/api/users", json={
        "email": "delete-me@nomos.local",
        "password": "DeleteMeP@ss1!",
        "role": "user",
    }, cookies=cookies)
    user_id = create_resp.json()["id"]

    # Deactivate
    resp = await users_client.delete(f"/api/users/{user_id}", cookies=cookies)
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


async def test_non_admin_cannot_list_users(users_client, users_engine, admin_user):
    # Create a regular user
    cookies = await _login_as_admin(users_client)
    await users_client.post("/api/users", json={
        "email": "regular@nomos.local",
        "password": "RegularP@ss12!",
        "role": "user",
    }, cookies=cookies)

    # Login as regular user
    from nomos_api.routers.auth import _login_limiter
    _login_limiter._attempts.clear()
    _login_limiter._lockouts.clear()

    login_resp = await users_client.post("/api/auth/login", json={
        "email": "regular@nomos.local",
        "password": "RegularP@ss12!",
    })
    assert login_resp.status_code == 200
    user_cookies = dict(login_resp.cookies)

    # Try to list users — should be forbidden
    resp = await users_client.get("/api/users", cookies=user_cookies)
    assert resp.status_code == 403


async def test_create_user_weak_password(users_client, admin_user):
    cookies = await _login_as_admin(users_client)
    resp = await users_client.post("/api/users", json={
        "email": "weak@nomos.local",
        "password": "short",
        "role": "user",
    }, cookies=cookies)
    assert resp.status_code == 422
