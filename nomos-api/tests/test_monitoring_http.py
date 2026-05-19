"""Functional HTTP tests for /api/monitoring/* endpoints.

Covers: GET /metrics shape, POST/GET/PATCH /alerts create→list→ack→resolve
roundtrip, GET/POST/DELETE /alert-rules CRUD roundtrip, and error paths
(404 unknown alert/rule, 422 validation).

All endpoints require admin auth. Tests create an admin user + JWT cookie
using the same pattern as test_monitoring_authz.py.
Real SQLite in-process DB via the shared db_engine conftest fixture.
"""

from __future__ import annotations

import copy
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from nomos_api.auth.jwt import TokenPayload, create_token
from nomos_api.auth.password import hash_password
from nomos_api.models import User

_JWT = "test-jwt-secret-at-least-32-chars-long-123"
_PLUGIN = "test-plugin-key-at-least-32-characters"

pytestmark = pytest.mark.anyio


# ---------------------------------------------------------------------------
# Shared helper — build an admin client bound to the test DB engine
# ---------------------------------------------------------------------------


async def _admin_client(db_engine, monkeypatch) -> AsyncClient:
    """Return an AsyncClient authenticated as an admin user."""
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

    uid = str(uuid.uuid4())
    async with factory() as s:
        s.add(
            User(
                id=uid,
                email=f"admin-monitoring-{uid[:8]}@nomos.local",
                password_hash=hash_password("Str0ngP@ss!1"),
                role="admin",
                is_active=True,
                session_timeout_hours=8,
            )
        )
        await s.commit()

    token = create_token(
        TokenPayload(user_id=uid, email=f"admin-monitoring-{uid[:8]}@nomos.local", role="admin"),
        _JWT,
    )
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-NomOS-API-Key": _PLUGIN},
        cookies={"nomos_token": token},
    )


# ---------------------------------------------------------------------------
# GET /api/monitoring/metrics — shape
# ---------------------------------------------------------------------------


async def test_metrics_returns_correct_shape(db_engine, monkeypatch) -> None:
    """GET /api/monitoring/metrics returns the three metric groups + timestamp."""
    async with await _admin_client(db_engine, monkeypatch) as client:
        resp = await client.get("/api/monitoring/metrics")

    assert resp.status_code == 200
    body = resp.json()
    assert "api" in body, "Response must contain 'api' key"
    assert "agents" in body, "Response must contain 'agents' key"
    assert "system" in body, "Response must contain 'system' key"
    assert "timestamp" in body, "Response must contain 'timestamp' key"
    # On a fresh DB all groups are empty dicts (no metrics seeded)
    assert isinstance(body["api"], dict)
    assert isinstance(body["agents"], dict)
    assert isinstance(body["system"], dict)
    # timestamp is a non-empty ISO string
    assert len(body["timestamp"]) > 0


# ---------------------------------------------------------------------------
# POST /api/monitoring/alerts — create
# ---------------------------------------------------------------------------


async def test_create_alert_returns_201_with_correct_fields(db_engine, monkeypatch) -> None:
    """POST /api/monitoring/alerts creates an alert and returns 201 with payload."""
    async with await _admin_client(db_engine, monkeypatch) as client:
        resp = await client.post(
            "/api/monitoring/alerts",
            json={
                "severity": "warning",
                "metric_name": "api.latency",
                "current_value": 1.5,
                "threshold_value": 1.0,
            },
        )

    assert resp.status_code == 201
    body = resp.json()
    assert body["severity"] == "warning"
    assert body["metric_name"] == "api.latency"
    assert body["current_value"] == 1.5
    assert body["threshold_value"] == 1.0
    assert body["status"] == "triggered"
    assert isinstance(body["id"], str) and len(body["id"]) > 0


async def test_create_alert_accepts_explicit_id(db_engine, monkeypatch) -> None:
    """POST /api/monitoring/alerts accepts a caller-supplied id."""
    async with await _admin_client(db_engine, monkeypatch) as client:
        resp = await client.post(
            "/api/monitoring/alerts",
            json={
                "id": "my-custom-alert-id",
                "severity": "critical",
                "metric_name": "api.error_rate",
                "current_value": 0.25,
                "threshold_value": 0.10,
            },
        )

    assert resp.status_code == 201
    assert resp.json()["id"] == "my-custom-alert-id"


async def test_create_alert_invalid_severity_returns_422(db_engine, monkeypatch) -> None:
    """POST /api/monitoring/alerts with severity not in (critical|warning|info) → 422."""
    async with await _admin_client(db_engine, monkeypatch) as client:
        resp = await client.post(
            "/api/monitoring/alerts",
            json={
                "severity": "extreme",  # not in pattern ^(critical|warning|info)$
                "metric_name": "api.latency",
                "current_value": 1.0,
                "threshold_value": 0.5,
            },
        )

    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/monitoring/alerts — list
# ---------------------------------------------------------------------------


async def test_list_alerts_returns_created_alert(db_engine, monkeypatch) -> None:
    """GET /api/monitoring/alerts lists active (non-resolved) alerts."""
    async with await _admin_client(db_engine, monkeypatch) as client:
        create_resp = await client.post(
            "/api/monitoring/alerts",
            json={
                "id": "list-test-alert-001",
                "severity": "critical",
                "metric_name": "api.error_rate",
                "current_value": 0.25,
                "threshold_value": 0.10,
            },
        )
        assert create_resp.status_code == 201

        list_resp = await client.get("/api/monitoring/alerts")

    assert list_resp.status_code == 200
    alerts = list_resp.json()
    assert isinstance(alerts, list)
    ids = [a["id"] for a in alerts]
    assert "list-test-alert-001" in ids, f"Created alert not found in list: {ids}"


async def test_list_alerts_empty_on_fresh_db(db_engine, monkeypatch) -> None:
    """GET /api/monitoring/alerts returns empty list when no alerts exist."""
    async with await _admin_client(db_engine, monkeypatch) as client:
        resp = await client.get("/api/monitoring/alerts")

    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# PATCH /api/monitoring/alerts/{id} — acknowledge / resolve
# ---------------------------------------------------------------------------


async def test_acknowledge_alert_changes_status(db_engine, monkeypatch) -> None:
    """PATCH …/alerts/{id} with status=acknowledged updates the status field."""
    async with await _admin_client(db_engine, monkeypatch) as client:
        create_resp = await client.post(
            "/api/monitoring/alerts",
            json={
                "id": "ack-test-alert-001",
                "severity": "info",
                "metric_name": "system.cpu",
                "current_value": 90.0,
                "threshold_value": 80.0,
            },
        )
        assert create_resp.status_code == 201

        patch_resp = await client.patch(
            "/api/monitoring/alerts/ack-test-alert-001",
            json={"status": "acknowledged"},
        )

    assert patch_resp.status_code == 200
    body = patch_resp.json()
    assert body["status"] == "acknowledged"
    assert body["id"] == "ack-test-alert-001"
    # acknowledged is not resolved — resolved_at must still be None
    assert body["resolved_at"] is None


async def test_resolve_alert_sets_resolved_at(db_engine, monkeypatch) -> None:
    """PATCH …/alerts/{id} with status=resolved sets resolved_at to a timestamp."""
    async with await _admin_client(db_engine, monkeypatch) as client:
        await client.post(
            "/api/monitoring/alerts",
            json={
                "id": "resolve-test-alert-001",
                "severity": "warning",
                "metric_name": "agent.stale",
                "current_value": 3.0,
                "threshold_value": 2.0,
            },
        )

        patch_resp = await client.patch(
            "/api/monitoring/alerts/resolve-test-alert-001",
            json={"status": "resolved"},
        )

    assert patch_resp.status_code == 200
    body = patch_resp.json()
    assert body["status"] == "resolved"
    assert body["resolved_at"] is not None, "resolved_at must be set after resolving"


async def test_patch_unknown_alert_returns_404(db_engine, monkeypatch) -> None:
    """PATCH …/alerts/{id} with a non-existent ID returns 404."""
    async with await _admin_client(db_engine, monkeypatch) as client:
        resp = await client.patch(
            "/api/monitoring/alerts/completely-nonexistent-xyz",
            json={"status": "acknowledged"},
        )

    assert resp.status_code == 404
    assert "Alert not found" in resp.json()["detail"]


async def test_patch_alert_invalid_status_returns_422(db_engine, monkeypatch) -> None:
    """PATCH …/alerts/{id} with status not in pattern → 422."""
    async with await _admin_client(db_engine, monkeypatch) as client:
        await client.post(
            "/api/monitoring/alerts",
            json={
                "id": "patch-invalid-status-001",
                "severity": "info",
                "metric_name": "system.cpu",
                "current_value": 1.0,
                "threshold_value": 0.5,
            },
        )

        resp = await client.patch(
            "/api/monitoring/alerts/patch-invalid-status-001",
            json={"status": "bogus"},
        )

    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Alert CRUD roundtrip: create → list → acknowledge → resolve
# ---------------------------------------------------------------------------


async def test_full_alert_roundtrip(db_engine, monkeypatch) -> None:
    """Full roundtrip: create → appears in list → acknowledge → resolve → resolved_at set."""
    async with await _admin_client(db_engine, monkeypatch) as client:
        # Create
        create_resp = await client.post(
            "/api/monitoring/alerts",
            json={
                "id": "roundtrip-alert-001",
                "severity": "warning",
                "metric_name": "system.memory",
                "current_value": 92.0,
                "threshold_value": 85.0,
            },
        )
        assert create_resp.status_code == 201
        assert create_resp.json()["status"] == "triggered"

        # List — appears as active
        list_resp = await client.get("/api/monitoring/alerts")
        assert list_resp.status_code == 200
        assert any(a["id"] == "roundtrip-alert-001" for a in list_resp.json())

        # Acknowledge
        ack_resp = await client.patch(
            "/api/monitoring/alerts/roundtrip-alert-001",
            json={"status": "acknowledged"},
        )
        assert ack_resp.status_code == 200
        assert ack_resp.json()["status"] == "acknowledged"
        assert ack_resp.json()["resolved_at"] is None

        # Resolve
        resolve_resp = await client.patch(
            "/api/monitoring/alerts/roundtrip-alert-001",
            json={"status": "resolved"},
        )
        assert resolve_resp.status_code == 200
        assert resolve_resp.json()["status"] == "resolved"
        assert resolve_resp.json()["resolved_at"] is not None


# ---------------------------------------------------------------------------
# GET /api/monitoring/alert-rules — list
# ---------------------------------------------------------------------------

_RULE_PAYLOAD: dict = {
    "metric_name": "api.error_rate",
    "threshold_type": "above",
    "threshold_value": 0.05,
    "comparison_window": "5m",
    "severity": "warning",
    "notification_channels": {"email": ["admin@nomos.local"]},
    "description": "Alert when error rate exceeds 5%",
    "is_active": True,
}


async def test_create_alert_rule_returns_201(db_engine, monkeypatch) -> None:
    """POST /api/monitoring/alert-rules creates a rule and returns 201."""
    async with await _admin_client(db_engine, monkeypatch) as client:
        resp = await client.post("/api/monitoring/alert-rules", json=copy.deepcopy(_RULE_PAYLOAD))

    assert resp.status_code == 201
    body = resp.json()
    assert body["metric_name"] == "api.error_rate"
    assert body["threshold_type"] == "above"
    assert body["threshold_value"] == 0.05
    assert body["severity"] == "warning"
    assert body["is_active"] is True
    assert isinstance(body["id"], int)


async def test_list_alert_rules_contains_created_rule(db_engine, monkeypatch) -> None:
    """GET /api/monitoring/alert-rules returns the rule created in the same session."""
    async with await _admin_client(db_engine, monkeypatch) as client:
        create_resp = await client.post("/api/monitoring/alert-rules", json=copy.deepcopy(_RULE_PAYLOAD))
        assert create_resp.status_code == 201
        rule_id = create_resp.json()["id"]

        list_resp = await client.get("/api/monitoring/alert-rules")

    assert list_resp.status_code == 200
    rules = list_resp.json()
    assert isinstance(rules, list)
    rule_ids = [r["id"] for r in rules]
    assert rule_id in rule_ids, f"Created rule id {rule_id} not found in list: {rule_ids}"


async def test_list_alert_rules_empty_on_fresh_db(db_engine, monkeypatch) -> None:
    """GET /api/monitoring/alert-rules returns empty list when no rules exist."""
    async with await _admin_client(db_engine, monkeypatch) as client:
        resp = await client.get("/api/monitoring/alert-rules")

    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# DELETE /api/monitoring/alert-rules/{id}
# ---------------------------------------------------------------------------


async def test_delete_alert_rule_returns_204(db_engine, monkeypatch) -> None:
    """DELETE /api/monitoring/alert-rules/{id} returns 204 No Content."""
    async with await _admin_client(db_engine, monkeypatch) as client:
        create_resp = await client.post("/api/monitoring/alert-rules", json=copy.deepcopy(_RULE_PAYLOAD))
        assert create_resp.status_code == 201
        rule_id = create_resp.json()["id"]

        delete_resp = await client.delete(f"/api/monitoring/alert-rules/{rule_id}")

    assert delete_resp.status_code == 204


async def test_delete_alert_rule_removes_from_list(db_engine, monkeypatch) -> None:
    """After DELETE the rule must not appear in GET /api/monitoring/alert-rules."""
    async with await _admin_client(db_engine, monkeypatch) as client:
        create_resp = await client.post("/api/monitoring/alert-rules", json=copy.deepcopy(_RULE_PAYLOAD))
        assert create_resp.status_code == 201
        rule_id = create_resp.json()["id"]

        del_resp = await client.delete(f"/api/monitoring/alert-rules/{rule_id}")
        assert del_resp.status_code == 204

        list_resp = await client.get("/api/monitoring/alert-rules")

    assert list_resp.status_code == 200
    rule_ids = [r["id"] for r in list_resp.json()]
    assert rule_id not in rule_ids, f"Deleted rule {rule_id} still appears in list: {rule_ids}"


async def test_delete_nonexistent_alert_rule_returns_404(db_engine, monkeypatch) -> None:
    """DELETE /api/monitoring/alert-rules/{id} with unknown ID returns 404."""
    async with await _admin_client(db_engine, monkeypatch) as client:
        resp = await client.delete("/api/monitoring/alert-rules/999999")

    assert resp.status_code == 404
    assert "Alert rule not found" in resp.json()["detail"]


async def test_create_alert_rule_invalid_threshold_type_returns_422(db_engine, monkeypatch) -> None:
    """POST /api/monitoring/alert-rules with threshold_type not in (above|below|change) → 422."""
    payload = copy.deepcopy(_RULE_PAYLOAD)
    payload["threshold_type"] = "invalid_type"

    async with await _admin_client(db_engine, monkeypatch) as client:
        resp = await client.post("/api/monitoring/alert-rules", json=payload)

    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Alert-rule CRUD roundtrip: create → list → delete → gone
# ---------------------------------------------------------------------------


async def test_full_alert_rule_roundtrip(db_engine, monkeypatch) -> None:
    """Full roundtrip: create → appears in list → delete → no longer in list."""
    async with await _admin_client(db_engine, monkeypatch) as client:
        # Create
        create_resp = await client.post("/api/monitoring/alert-rules", json=copy.deepcopy(_RULE_PAYLOAD))
        assert create_resp.status_code == 201
        rule_id = create_resp.json()["id"]
        assert isinstance(rule_id, int)

        # List — appears
        list_resp = await client.get("/api/monitoring/alert-rules")
        assert list_resp.status_code == 200
        assert any(r["id"] == rule_id for r in list_resp.json())

        # Delete
        del_resp = await client.delete(f"/api/monitoring/alert-rules/{rule_id}")
        assert del_resp.status_code == 204

        # List — gone
        list_resp2 = await client.get("/api/monitoring/alert-rules")
        assert list_resp2.status_code == 200
        assert not any(r["id"] == rule_id for r in list_resp2.json())
