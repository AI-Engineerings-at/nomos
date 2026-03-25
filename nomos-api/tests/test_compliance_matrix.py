"""Tests for GET /api/compliance/matrix — all agents x compliance status."""

from __future__ import annotations

import pytest


class TestComplianceMatrix:
    async def test_compliance_matrix_empty(self, client) -> None:
        resp = await client.get("/api/compliance/matrix")
        assert resp.status_code == 200
        data = resp.json()
        assert data["matrix"] == []
        assert data["total"] == 0

    async def test_compliance_matrix_with_agents(self, client) -> None:
        await client.post("/api/agents", json={
            "name": "Matrix Agent 1",
            "role": "test",
            "company": "Co",
            "email": "a1@test.com",
        })
        await client.post("/api/agents", json={
            "name": "Matrix Agent 2",
            "role": "test",
            "company": "Co",
            "email": "a2@test.com",
            "risk_class": "high",
        })
        resp = await client.get("/api/compliance/matrix")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["matrix"]) == 2
        entry = data["matrix"][0]
        assert "agent_id" in entry
        assert "agent_name" in entry
        assert "status" in entry
        assert "risk_class" in entry

    async def test_compliance_matrix_reflects_gate_status(self, client) -> None:
        create_resp = await client.post("/api/agents", json={
            "name": "Gate Matrix Agent",
            "role": "test",
            "company": "Co",
            "email": "gm@test.com",
        })
        agent_id = create_resp.json()["id"]

        # Before gate: should be blocked/pending
        resp1 = await client.get("/api/compliance/matrix")
        statuses_before = {e["agent_id"]: e["status"] for e in resp1.json()["matrix"]}
        assert statuses_before[agent_id] in ("pending", "blocked")

        # Run gate
        await client.post(f"/api/agents/{agent_id}/gate")

        # After gate: should be passed
        resp2 = await client.get("/api/compliance/matrix")
        statuses_after = {e["agent_id"]: e["status"] for e in resp2.json()["matrix"]}
        assert statuses_after[agent_id] == "passed"
