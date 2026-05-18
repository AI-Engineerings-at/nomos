"""H1 regression: monitoring router must require an admin user.

Before the fix every /api/monitoring endpoint had zero authZ. These tests
assert that:
- a non-admin authenticated user is rejected (403),
- an unauthenticated/plugin-only caller is rejected (401/403),
- an admin user is allowed through (not 401/403).
"""

from __future__ import annotations

import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from nomos_api.auth.jwt import TokenPayload, create_token
from nomos_api.auth.password import hash_password
from nomos_api.models import User

_JWT = "test-jwt-secret-at-least-32-chars-long-123"
_PLUGIN = "test-plugin-key-at-least-32-characters"


async def _client_for(db_engine, monkeypatch, *, role: str | None):
    from nomos_api.config import settings
    from nomos_api.database import get_db
    from nomos_api.main import app

    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(settings, "plugin_api_key", _PLUGIN)
    monkeypatch.setattr(settings, "jwt_secret", _JWT)

    cookies = {}
    if role is not None:
        uid = str(uuid.uuid4())
        async with factory() as s:
            s.add(
                User(
                    id=uid,
                    email=f"{role}@nomos.local",
                    password_hash=hash_password("Str0ngP@ss!1"),
                    role=role,
                    is_active=True,
                    session_timeout_hours=8,
                )
            )
            await s.commit()
        token = create_token(TokenPayload(user_id=uid, email=f"{role}@nomos.local", role=role), _JWT)
        cookies["nomos_token"] = token

    transport = ASGITransport(app=app)
    return AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-NomOS-API-Key": _PLUGIN},
        cookies=cookies,
    )


async def test_metrics_rejects_non_admin_user(db_engine, monkeypatch):
    client = await _client_for(db_engine, monkeypatch, role="user")
    async with client:
        resp = await client.get("/api/monitoring/metrics")
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Admin access required"


async def test_metrics_rejects_plugin_only_no_cookie(db_engine, monkeypatch):
    client = await _client_for(db_engine, monkeypatch, role=None)
    async with client:
        resp = await client.get("/api/monitoring/metrics")
    # Plugin passes the global middleware but require_admin has no cookie.
    assert resp.status_code == 401


async def test_create_alert_rule_rejects_non_admin(db_engine, monkeypatch):
    client = await _client_for(db_engine, monkeypatch, role="user")
    async with client:
        resp = await client.post(
            "/api/monitoring/alert-rules",
            json={
                "metric_name": "api.latency",
                "threshold_type": "above",
                "threshold_value": 1.0,
                "comparison_window": 5,
                "severity": "warning",
                "notification_channels": {"email": []},
                "description": "x",
                "is_active": True,
            },
        )
    assert resp.status_code == 403


async def test_delete_alert_rule_rejects_non_admin(db_engine, monkeypatch):
    client = await _client_for(db_engine, monkeypatch, role="user")
    async with client:
        resp = await client.delete("/api/monitoring/alert-rules/1")
    assert resp.status_code == 403


async def test_admin_is_allowed_through(db_engine, monkeypatch):
    client = await _client_for(db_engine, monkeypatch, role="admin")
    async with client:
        resp = await client.get("/api/monitoring/metrics")
    # Admin must NOT be blocked by authZ (200 with empty metrics on fresh DB).
    assert resp.status_code == 200
    body = resp.json()
    assert "api" in body and "agents" in body and "system" in body
