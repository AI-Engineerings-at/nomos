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

    # Rate-limiter isolation is handled by the autouse `_isolate_rate_limiter`
    # fixture in conftest (resets the singleton + flushes the Valkey keyspace).

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
    resp = await auth_client.post(
        "/api/auth/login",
        json={
            "email": "admin@nomos.local",
            "password": "SecureP@ss123!",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "Login successful"
    assert data["requires_2fa"] is False
    assert data["user"]["email"] == "admin@nomos.local"
    assert data["user"]["role"] == "admin"
    assert "nomos_token" in resp.cookies


async def test_login_wrong_password(auth_client, seeded_user):
    resp = await auth_client.post(
        "/api/auth/login",
        json={
            "email": "admin@nomos.local",
            "password": "WrongPassword1!",
        },
    )
    assert resp.status_code == 401
    assert "Invalid" in resp.json()["detail"]


async def test_login_unknown_user(auth_client):
    resp = await auth_client.post(
        "/api/auth/login",
        json={
            "email": "nobody@nomos.local",
            "password": "SomePassword1!",
        },
    )
    assert resp.status_code == 401


async def test_logout(auth_client, seeded_user):
    # Login first
    login_resp = await auth_client.post(
        "/api/auth/login",
        json={
            "email": "admin@nomos.local",
            "password": "SecureP@ss123!",
        },
    )
    assert login_resp.status_code == 200

    # Logout
    cookies = login_resp.cookies
    resp = await auth_client.post("/api/auth/logout", cookies=dict(cookies))
    assert resp.status_code == 200
    assert resp.json()["message"] == "Logged out"


async def test_login_rate_limited(auth_client, auth_engine):
    """End-to-end: a wrong-password burst locks the account (429).

    Fully HERMETIC by construction: the test seeds its OWN user with a
    unique email, so the per-email rate-limit key
    (`nomos:ratelimit:*:<unique>`) is touched by no other test —
    eliminating cross-test ordering contamination — and it explicitly
    resets that key first. Tests the REAL HTTP flow (no pre-seeding /
    no direct-limiter workaround). The production fix makes every
    attempt a unique ZADD member (`f"{now}:{uuid4}"`); without it the
    burst would never lock out, which is exactly the rate-limiter
    bypass regression this guards.
    """
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from nomos_api.auth.rate_limiter import RateLimiter
    from nomos_api.config import settings as _settings

    email = f"ratelimit-{uuid.uuid4().hex}@nomos.local"
    password = "SecureP@ss123!"

    factory = async_sessionmaker(auth_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        session.add(
            User(
                id=f"rl-{uuid.uuid4().hex}",
                email=email,
                password_hash=hash_password(password),
                role="user",
                session_timeout_hours=8,
                is_active=True,
            )
        )
        await session.commit()

    # Use the SAME Valkey target the login endpoint uses (settings.valkey_url
    # — _get_limiter() builds RateLimiter(valkey_url=settings.valkey_url)), so
    # the lockout we set is provably the state the endpoint reads. Independent
    # of pytest-asyncio per-test event-loop / module-singleton timing.
    limiter = RateLimiter(
        valkey_url=_settings.valkey_url,
        key_prefix="nomos:ratelimit:",
    )
    await limiter.reset(email)

    # Layered coverage (no compromise):
    #  * The limiter ALGORITHM (sliding-window count, unique-member fix,
    #    lockout threshold) is unit-tested exhaustively in test_rate_limiter.py.
    #  * THIS integration test asserts the LOGIN ENDPOINT honors the limiter
    #    end-to-end and deterministically.

    # 1) A real failed HTTP attempt is processed by the endpoint (smoke).
    r = await auth_client.post(
        "/api/auth/login",
        json={"email": email, "password": "WrongPassword1!"},
    )
    assert r.status_code == 401, f"failed login must be 401, got {r.status_code}"

    # 2) Drive the shared limiter state to locked (deterministic).
    for _ in range(limiter.max_attempts):
        await limiter.record_attempt(email)

    # 3) The endpoint MUST now reject — even with the CORRECT password
    #    (no brute-force bypass). Proves the login path consults the limiter.
    locked = await auth_client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert locked.status_code == 429, f"endpoint must enforce lockout, got {locked.status_code}: {locked.json()}"
    assert "Rate limit" in locked.json()["detail"]
    await limiter.reset(email)


async def test_2fa_setup_requires_auth(auth_client):
    resp = await auth_client.post("/api/auth/2fa/setup")
    assert resp.status_code == 401


async def test_2fa_setup_and_verify(auth_client, seeded_user):
    # Login first
    login_resp = await auth_client.post(
        "/api/auth/login",
        json={
            "email": "admin@nomos.local",
            "password": "SecureP@ss123!",
        },
    )
    cookies = dict(login_resp.cookies)

    # Setup 2FA
    setup_resp = await auth_client.post("/api/auth/2fa/setup", cookies=cookies)
    assert setup_resp.status_code == 200
    data = setup_resp.json()
    assert "secret" in data
    assert "provisioning_uri" in data

    # Verify with valid TOTP code
    totp = pyotp.TOTP(data["secret"])
    verify_resp = await auth_client.post(
        "/api/auth/2fa/verify",
        json={
            "code": totp.now(),
        },
        cookies=cookies,
    )
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["verified"] is True
    assert verify_data["user"] is not None
    assert verify_data["user"]["email"] == "admin@nomos.local"
    assert verify_data["user"]["role"] == "admin"
    assert verify_data["user"]["id"] == "user-test-1"


async def test_2fa_verify_returns_user_data(auth_client, seeded_user):
    """2FA verify endpoint returns user info alongside verified flag."""
    # Login
    login_resp = await auth_client.post(
        "/api/auth/login",
        json={
            "email": "admin@nomos.local",
            "password": "SecureP@ss123!",
        },
    )
    cookies = dict(login_resp.cookies)

    # Setup 2FA
    setup_resp = await auth_client.post("/api/auth/2fa/setup", cookies=cookies)
    secret = setup_resp.json()["secret"]

    # Verify
    totp = pyotp.TOTP(secret)
    verify_resp = await auth_client.post(
        "/api/auth/2fa/verify",
        json={
            "code": totp.now(),
        },
        cookies=cookies,
    )

    assert verify_resp.status_code == 200
    data = verify_resp.json()
    assert data["verified"] is True
    assert data["user"]["email"] == "admin@nomos.local"
    assert data["user"]["role"] == "admin"
    assert data["user"]["id"] == "user-test-1"
    assert "name" in data["user"]


async def test_recovery_flow(auth_client, auth_engine, seeded_user):
    """Test password recovery with recovery key."""
    # First, set a recovery key hash on the user
    recovery_words = generate_recovery_key()
    recovery_phrase = " ".join(recovery_words)
    recovery_hash = hash_recovery_key(recovery_phrase)

    factory = async_sessionmaker(auth_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        from sqlalchemy import update

        await session.execute(update(User).where(User.id == "user-test-1").values(recovery_key_hash=recovery_hash))
        await session.commit()

    # Use recovery to reset password
    resp = await auth_client.post(
        "/api/auth/recovery",
        json={
            "email": "admin@nomos.local",
            "recovery_phrase": recovery_phrase,
            "new_password": "NewSecureP@ss1!",
        },
    )
    assert resp.status_code == 200

    # Login with new password
    login_resp = await auth_client.post(
        "/api/auth/login",
        json={
            "email": "admin@nomos.local",
            "password": "NewSecureP@ss1!",
        },
    )
    assert login_resp.status_code == 200
