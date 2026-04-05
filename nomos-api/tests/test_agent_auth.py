"""Tests for auth on state-change endpoints — 401/403/200 scenarios."""

from __future__ import annotations

import uuid

import pytest

from nomos_api.auth.jwt import TokenPayload, create_token
from nomos_api.auth.password import hash_password
from nomos_api.models import User


async def _seed_user(db_session, email: str, role: str = "user") -> User:
    """Insert a user into the test DB and return it."""
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        password_hash=hash_password("Str0ngP@ssword!"),
        role=role,
        is_active=True,
        session_timeout_hours=24 if role != "admin" else 8,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def _make_cookie(user: User) -> str:
    """Create a valid JWT token for a user."""
    payload = TokenPayload(user_id=user.id, email=user.email, role=user.role)
    return create_token(payload, "test-jwt-secret-at-least-32-chars-long-123")


async def _create_agent(client, email: str = "owner@test.com") -> str:
    """Create an agent owned by the given email, return agent ID."""
    resp = await client.post(
        "/api/agents",
        json={
            "name": "Auth Test Agent",
            "role": "test-role",
            "company": "Test Co",
            "email": email,
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


class TestNoAuthReturns401:
    """State-change endpoints without a cookie must return 401."""

    @pytest.mark.parametrize("action", ["pause", "resume", "kill", "retire"])
    async def test_no_cookie_returns_401(self, client, action: str) -> None:
        # Create an agent first (create endpoint does not require user auth)
        agent_id = await _create_agent(client)
        # Remove any cookies on the client
        client.cookies.clear()
        resp = await client.post(f"/api/agents/{agent_id}/{action}")
        assert resp.status_code == 401


class TestUserCannotAccessForeignAgent:
    """A regular user must get 403 when acting on another user's agent."""

    @pytest.mark.parametrize("action", ["pause", "kill", "retire"])
    async def test_foreign_agent_returns_403(self, client, db_session, action: str) -> None:
        # Agent owned by "owner@test.com"
        agent_id = await _create_agent(client, email="owner@test.com")
        # User is "other@test.com"
        other_user = await _seed_user(db_session, "other@test.com", role="user")
        token = _make_cookie(other_user)
        client.cookies.set("nomos_token", token)
        resp = await client.post(f"/api/agents/{agent_id}/{action}")
        assert resp.status_code == 403


class TestUserCanAccessOwnAgent:
    async def test_pause_own_agent(self, client, db_session) -> None:
        owner_email = "owner@test.com"
        owner = await _seed_user(db_session, owner_email, role="user")
        token = _make_cookie(owner)
        agent_id = await _create_agent(client, email=owner_email)
        client.cookies.set("nomos_token", token)
        resp = await client.post(f"/api/agents/{agent_id}/pause")
        assert resp.status_code == 200
        assert resp.json()["status"] == "paused"


class TestAdminCanAccessForeignAgent:
    async def test_retire_foreign_agent_as_admin(self, client, db_session) -> None:
        # Agent owned by someone else
        agent_id = await _create_agent(client, email="owner@test.com")
        # Admin user
        admin = await _seed_user(db_session, "admin@test.com", role="admin")
        token = _make_cookie(admin)
        client.cookies.set("nomos_token", token)
        resp = await client.post(f"/api/agents/{agent_id}/retire")
        assert resp.status_code == 200
        assert resp.json()["status"] == "retired"

    async def test_admin_action_creates_audit_event(self, client, db_session) -> None:
        """When an admin acts on another user's agent, an admin.action audit event is created."""
        agent_id = await _create_agent(client, email="owner@test.com")
        admin = await _seed_user(db_session, "admin@test.com", role="admin")
        token = _make_cookie(admin)
        client.cookies.set("nomos_token", token)
        await client.post(f"/api/agents/{agent_id}/kill")
        # Check audit trail for admin.action event
        audit_resp = await client.get(f"/api/agents/{agent_id}/audit")
        assert audit_resp.status_code == 200
        events = [e["event_type"] for e in audit_resp.json()["entries"]]
        assert "admin.action" in events
