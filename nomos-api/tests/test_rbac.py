"""Tests for RBAC — check_agent_access."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from nomos_api.auth.rbac import check_agent_access


class _FakeUser:
    def __init__(self, email: str, role: str) -> None:
        self.email = email
        self.role = role


class _FakeAgent:
    def __init__(self, id: str, email: str) -> None:
        self.id = id
        self.email = email


class TestCheckAgentAccess:
    def test_admin_can_access_any_agent(self) -> None:
        user = _FakeUser(email="admin@co.com", role="admin")
        agent = _FakeAgent(id="agent-1", email="other@co.com")
        # Should not raise
        check_agent_access(user, agent, "kill")

    def test_user_can_access_own_agent(self) -> None:
        user = _FakeUser(email="owner@co.com", role="user")
        agent = _FakeAgent(id="agent-1", email="owner@co.com")
        # Should not raise
        check_agent_access(user, agent, "pause")

    def test_user_cannot_access_foreign_agent(self) -> None:
        user = _FakeUser(email="owner@co.com", role="user")
        agent = _FakeAgent(id="agent-1", email="other@co.com")
        with pytest.raises(HTTPException) as exc_info:
            check_agent_access(user, agent, "retire")
        assert exc_info.value.status_code == 403
        assert "retire" in exc_info.value.detail

    def test_officer_can_access_own_agent(self) -> None:
        user = _FakeUser(email="officer@co.com", role="officer")
        agent = _FakeAgent(id="agent-1", email="officer@co.com")
        # Should not raise
        check_agent_access(user, agent, "resume")

    def test_officer_cannot_access_foreign_agent(self) -> None:
        user = _FakeUser(email="officer@co.com", role="officer")
        agent = _FakeAgent(id="agent-1", email="other@co.com")
        with pytest.raises(HTTPException) as exc_info:
            check_agent_access(user, agent, "kill")
        assert exc_info.value.status_code == 403
