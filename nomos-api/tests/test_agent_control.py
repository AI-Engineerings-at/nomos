"""Tests for agent control endpoints — pause, resume, retire."""

from __future__ import annotations

import pytest


async def _create_agent(client, name: str = "Control Test Agent") -> str:
    """Helper: create an agent and return its ID."""
    resp = await client.post("/api/agents", json={
        "name": name,
        "role": "test-role",
        "company": "Test Co",
        "email": "test@test.com",
    })
    assert resp.status_code == 201
    return resp.json()["id"]


class TestPauseAgent:
    async def test_pause_running_agent(self, client) -> None:
        agent_id = await _create_agent(client, "Pause Test")
        resp = await client.post(f"/api/agents/{agent_id}/pause")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "paused"
        assert data["id"] == agent_id

    async def test_pause_creates_audit_entry(self, client) -> None:
        agent_id = await _create_agent(client, "Pause Audit Test")
        await client.post(f"/api/agents/{agent_id}/pause")
        audit_resp = await client.get(f"/api/agents/{agent_id}/audit")
        events = [e["event_type"] for e in audit_resp.json()["entries"]]
        assert "kill_switch.user_pause" in events

    async def test_pause_nonexistent_agent(self, client) -> None:
        resp = await client.post("/api/agents/nonexistent/pause")
        assert resp.status_code == 404


class TestResumeAgent:
    async def test_resume_paused_agent(self, client) -> None:
        agent_id = await _create_agent(client, "Resume Test")
        await client.post(f"/api/agents/{agent_id}/pause")
        resp = await client.post(f"/api/agents/{agent_id}/resume")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "running"

    async def test_resume_non_paused_agent_rejected(self, client) -> None:
        agent_id = await _create_agent(client, "Resume Reject Test")
        resp = await client.post(f"/api/agents/{agent_id}/resume")
        assert resp.status_code == 409

    async def test_resume_nonexistent_agent(self, client) -> None:
        resp = await client.post("/api/agents/nonexistent/resume")
        assert resp.status_code == 404


class TestRetireAgent:
    async def test_retire_agent(self, client) -> None:
        agent_id = await _create_agent(client, "Retire Test")
        resp = await client.post(f"/api/agents/{agent_id}/retire")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "retired"

    async def test_retire_creates_audit_entry(self, client) -> None:
        agent_id = await _create_agent(client, "Retire Audit Test")
        await client.post(f"/api/agents/{agent_id}/retire")
        audit_resp = await client.get(f"/api/agents/{agent_id}/audit")
        events = [e["event_type"] for e in audit_resp.json()["entries"]]
        assert "agent.retired" in events

    async def test_retire_nonexistent_agent(self, client) -> None:
        resp = await client.post("/api/agents/nonexistent/retire")
        assert resp.status_code == 404
