"""Tests for compliance endpoint."""

from __future__ import annotations

import pytest


class TestCompliance:
    async def test_compliance_check_for_created_agent(self, client) -> None:
        create_resp = await client.post("/api/agents", json={
            "name": "Compliance Test",
            "role": "test",
            "company": "Co",
            "email": "t@t.com",
        })
        agent_id = create_resp.json()["id"]
        response = await client.get(f"/api/agents/{agent_id}/compliance")
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == agent_id
        assert data["status"] in ("passed", "warning", "blocked")
        assert isinstance(data["missing_documents"], list)

    async def test_compliance_nonexistent_agent(self, client) -> None:
        response = await client.get("/api/agents/nonexistent/compliance")
        assert response.status_code == 404


class TestGate:
    async def test_gate_generates_docs_and_passes(self, client) -> None:
        # Create agent (starts as blocked)
        create_resp = await client.post("/api/agents", json={
            "name": "Gate Test",
            "role": "test",
            "company": "Co",
            "email": "t@t.com",
        })
        agent_id = create_resp.json()["id"]

        # Verify blocked before gate
        comp_resp = await client.get(f"/api/agents/{agent_id}/compliance")
        assert comp_resp.json()["status"] == "blocked"

        # Run gate
        gate_resp = await client.post(f"/api/agents/{agent_id}/gate")
        assert gate_resp.status_code == 200
        data = gate_resp.json()
        assert data["status"] == "passed"
        assert len(data["missing_documents"]) == 0

        # Verify passed after gate
        comp_resp2 = await client.get(f"/api/agents/{agent_id}/compliance")
        assert comp_resp2.json()["status"] == "passed"

    async def test_gate_nonexistent_agent(self, client) -> None:
        resp = await client.post("/api/agents/nonexistent/gate")
        assert resp.status_code == 404

    async def test_gate_creates_audit_entry(self, client) -> None:
        create_resp = await client.post("/api/agents", json={
            "name": "Audit Gate Test", "role": "test", "company": "Co", "email": "t@t.com",
        })
        agent_id = create_resp.json()["id"]
        await client.post(f"/api/agents/{agent_id}/gate")
        audit_resp = await client.get(f"/api/agents/{agent_id}/audit")
        entries = audit_resp.json()["entries"]
        assert len(entries) >= 2
        event_types = [e["event_type"] for e in entries]
        assert "agent.created" in event_types
        assert "compliance.check.passed" in event_types
