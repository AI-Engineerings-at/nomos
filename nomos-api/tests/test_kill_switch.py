"""Tests for Kill Switch endpoint — POST /api/agents/{id}/kill."""

from __future__ import annotations


class TestKillSwitch:
    async def test_kill_switch_changes_status(self, client) -> None:
        # Create agent first
        create_resp = await client.post("/api/agents", json={
            "name": "Kill Test Agent",
            "role": "test-role",
            "company": "Test Co",
            "email": "test@test.com",
        })
        assert create_resp.status_code == 201
        agent_id = create_resp.json()["id"]

        # Kill it
        kill_resp = await client.post(f"/api/agents/{agent_id}/kill")
        assert kill_resp.status_code == 200
        data = kill_resp.json()
        assert data["status"] == "killed"
        assert data["id"] == agent_id

    async def test_kill_nonexistent_agent_returns_404(self, client) -> None:
        response = await client.post("/api/agents/nonexistent-agent/kill")
        assert response.status_code == 404

    async def test_kill_already_killed_agent(self, client) -> None:
        # Create and kill
        create_resp = await client.post("/api/agents", json={
            "name": "Double Kill Agent",
            "role": "test-role",
            "company": "Test Co",
            "email": "test@test.com",
        })
        agent_id = create_resp.json()["id"]
        await client.post(f"/api/agents/{agent_id}/kill")

        # Kill again - should still work (idempotent)
        kill_resp = await client.post(f"/api/agents/{agent_id}/kill")
        assert kill_resp.status_code == 200
        assert kill_resp.json()["status"] == "killed"

    async def test_kill_creates_audit_entry(self, client) -> None:
        create_resp = await client.post("/api/agents", json={
            "name": "Audit Kill Agent",
            "role": "test-role",
            "company": "Test Co",
            "email": "test@test.com",
        })
        agent_id = create_resp.json()["id"]

        await client.post(f"/api/agents/{agent_id}/kill")

        # Check audit trail includes kill switch event
        audit_resp = await client.get(f"/api/agents/{agent_id}/audit")
        assert audit_resp.status_code == 200
        events = audit_resp.json()["entries"]
        event_types = [e["event_type"] for e in events]
        assert "kill_switch.activated" in event_types
