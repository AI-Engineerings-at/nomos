import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from nomos_api.auth.jwt import TokenPayload, create_token
from nomos_api.auth.password import hash_password
from nomos_api.config import settings
from nomos_api.models import User

_JWT = "test-jwt-secret-at-least-32-chars-long-123"
_PLUGIN = "test-plugin-key-at-least-32-characters"


@pytest.fixture
async def admin_client(db_engine, monkeypatch):
    """Authenticated ADMIN cookie client (for settings PATCH SSRF tests)."""
    from nomos_api.database import get_db
    from nomos_api.main import app

    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(settings, "jwt_secret", _JWT)
    monkeypatch.setattr(settings, "plugin_api_key", _PLUGIN)

    uid = str(uuid.uuid4())
    async with factory() as s:
        s.add(
            User(
                id=uid,
                email="admin@nomos.local",
                password_hash=hash_password("Str0ngP@ss!1"),
                role="admin",
                is_active=True,
                session_timeout_hours=8,
            )
        )
        await s.commit()
    token = create_token(TokenPayload(user_id=uid, email="admin@nomos.local", role="admin"), _JWT)

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-NomOS-API-Key": _PLUGIN},
        cookies={"nomos_token": token},
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_settings_patch_requires_admin(client: AsyncClient):
    """Non-admin cannot update settings."""
    # Note: client fixture in conftest.py uses a service key which acts as service, not admin
    # So this should fail with 401/403 if it expects a user session
    response = await client.patch("/api/settings", json={"retention_days": 30})
    # Since the client uses X-NomOS-API-Key which maps to role=service
    # And settings router uses _require_admin which checks nomos_token cookie
    assert response.status_code == 401  # No cookie


@pytest.mark.asyncio
async def test_get_settings_requires_auth(client: AsyncClient):
    """H4: GET /api/settings now requires an authenticated user cookie."""
    response = await client.get("/api/settings")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_settings_works_for_authed_user(authed_client: AsyncClient):
    """GET /api/settings returns settings for an authenticated user."""
    response = await authed_client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert "retention_days" in data
    assert "openai_api_key_set" in data


@pytest.mark.asyncio
async def test_get_settings_redacts_gateway_url_for_non_admin(authed_client: AsyncClient):
    """H4: non-admin users must not see the cleartext (SSRF-relevant) gateway_url."""
    response = await authed_client.get("/api/settings")
    assert response.status_code == 200
    # authed_client is role=user → gateway_url is redacted.
    assert response.json()["gateway_url"] == "***"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad_url",
    [
        "file:///etc/passwd",
        "gopher://127.0.0.1:6379/_FLUSHALL",
        "ftp://internal/secret",
        "unix:///var/run/docker.sock",
        "javascript:alert(1)",
        "not-a-url",
    ],
)
async def test_patch_gateway_url_rejects_unsafe_scheme(admin_client: AsyncClient, bad_url: str):
    """H4 SSRF: PATCH gateway_url must reject non-http(s) schemes with 422.

    Runs before the Vault-availability check, so it is deterministic without
    a connected Vault.
    """
    resp = await admin_client.patch("/api/settings", json={"gateway_url": bad_url})
    assert resp.status_code == 422, resp.text
    assert "gateway_url" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_patch_gateway_url_accepts_https(admin_client: AsyncClient):
    """A valid https URL passes validation (then fails on Vault unavailable)."""
    resp = await admin_client.patch("/api/settings", json={"gateway_url": "https://gateway.example.com:18789"})
    # Validation passed; without Vault the handler returns 503 (not 422).
    assert resp.status_code != 422
