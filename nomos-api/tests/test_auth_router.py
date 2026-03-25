"""Tests for the auth router endpoints."""

import pytest
import pyotp
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from nomos_api.models import Base, User
from nomos_api.auth.password import hash_password
from nomos_api.auth.recovery import generate_recovery_key, hash_recovery_key


@pytest.fixture
async def auth_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def auth_session(auth_engine):
    factory = async_sessionmaker(auth_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
async def auth_client(auth_engine, tmp_path, monkeypatch):
    from nomos_api.config import settings
    from nomos_api.database import get_db
    from nomos_api.main import app
    from nomos_api.routers.auth import _login_limiter

    # Reset rate limiter between tests
    _login_limiter._attempts.clear()
    _login_limiter._lockouts.clear()

    factory = async_sessionmaker(auth_engine, class_=AsyncSession, expire_on_commit=False)

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
async def seeded_user(auth_engine):
    """Create a test user in the database."""
    factory = async_sessionmaker(auth_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        user = User(
            id="user-test-1",
            email="admin@nomos.local",
            password_hash=hash_password("SecureP@ss123!"),
            role="admin",
            session_timeout_hours=8,
            is_active=True,
        )
        session.add(user)
        await session.commit()
    return user


async def test_login_success(auth_client, seeded_user):
    resp = await auth_client.post("/api/auth/login", json={
        "email": "admin@nomos.local",
        "password": "SecureP@ss123!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "Login successful"
    assert "nomos_token" in resp.cookies


async def test_login_wrong_password(auth_client, seeded_user):
    resp = await auth_client.post("/api/auth/login", json={
        "email": "admin@nomos.local",
        "password": "WrongPassword1!",
    })
    assert resp.status_code == 401
    assert "Invalid" in resp.json()["detail"]


async def test_login_unknown_user(auth_client):
    resp = await auth_client.post("/api/auth/login", json={
        "email": "nobody@nomos.local",
        "password": "SomePassword1!",
    })
    assert resp.status_code == 401


async def test_logout(auth_client, seeded_user):
    # Login first
    login_resp = await auth_client.post("/api/auth/login", json={
        "email": "admin@nomos.local",
        "password": "SecureP@ss123!",
    })
    assert login_resp.status_code == 200

    # Logout
    cookies = login_resp.cookies
    resp = await auth_client.post("/api/auth/logout", cookies=dict(cookies))
    assert resp.status_code == 200
    assert resp.json()["message"] == "Logged out"


async def test_login_rate_limited(auth_client, seeded_user):
    """After 5 failed attempts, login is blocked."""
    for _ in range(5):
        await auth_client.post("/api/auth/login", json={
            "email": "admin@nomos.local",
            "password": "WrongPassword1!",
        })
    resp = await auth_client.post("/api/auth/login", json={
        "email": "admin@nomos.local",
        "password": "SecureP@ss123!",
    })
    assert resp.status_code == 429
    assert "Rate limit" in resp.json()["detail"]


async def test_2fa_setup_requires_auth(auth_client):
    resp = await auth_client.post("/api/auth/2fa/setup")
    assert resp.status_code == 401


async def test_2fa_setup_and_verify(auth_client, seeded_user):
    # Login first
    login_resp = await auth_client.post("/api/auth/login", json={
        "email": "admin@nomos.local",
        "password": "SecureP@ss123!",
    })
    cookies = dict(login_resp.cookies)

    # Setup 2FA
    setup_resp = await auth_client.post("/api/auth/2fa/setup", cookies=cookies)
    assert setup_resp.status_code == 200
    data = setup_resp.json()
    assert "secret" in data
    assert "provisioning_uri" in data

    # Verify with valid TOTP code
    totp = pyotp.TOTP(data["secret"])
    verify_resp = await auth_client.post("/api/auth/2fa/verify", json={
        "code": totp.now(),
    }, cookies=cookies)
    assert verify_resp.status_code == 200


async def test_recovery_flow(auth_client, auth_engine, seeded_user):
    """Test password recovery with recovery key."""
    # First, set a recovery key hash on the user
    recovery_words = generate_recovery_key()
    recovery_phrase = " ".join(recovery_words)
    recovery_hash = hash_recovery_key(recovery_phrase)

    factory = async_sessionmaker(auth_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        from sqlalchemy import update
        await session.execute(
            update(User).where(User.id == "user-test-1").values(recovery_key_hash=recovery_hash)
        )
        await session.commit()

    # Use recovery to reset password
    resp = await auth_client.post("/api/auth/recovery", json={
        "email": "admin@nomos.local",
        "recovery_phrase": recovery_phrase,
        "new_password": "NewSecureP@ss1!",
    })
    assert resp.status_code == 200

    # Login with new password
    login_resp = await auth_client.post("/api/auth/login", json={
        "email": "admin@nomos.local",
        "password": "NewSecureP@ss1!",
    })
    assert login_resp.status_code == 200
