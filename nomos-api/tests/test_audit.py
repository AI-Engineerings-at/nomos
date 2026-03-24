"""Tests for audit trail endpoints."""

from __future__ import annotations

import pytest


class TestAudit:
    async def test_audit_trail_for_created_agent(self, client) -> None:
        create_resp = await client.post("/api/agents", json={
            "name": "Audit Test",
            "role": "test",
            "company": "Co",
            "email": "t@t.com",
        })
        agent_id = create_resp.json()["id"]
        response = await client.get(f"/api/agents/{agent_id}/audit")
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == agent_id
        assert data["total"] >= 1
        assert data["entries"][0]["event_type"] == "agent.created"

    async def test_audit_verify_for_created_agent(self, client) -> None:
        create_resp = await client.post("/api/agents", json={
            "name": "Verify Test",
            "role": "test",
            "company": "Co",
            "email": "t@t.com",
        })
        agent_id = create_resp.json()["id"]
        response = await client.get(f"/api/audit/verify/{agent_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == agent_id
        assert data["valid"] is True
        assert data["entries_checked"] >= 1

    async def test_audit_nonexistent_agent(self, client) -> None:
        response = await client.get("/api/agents/nonexistent/audit")
        assert response.status_code == 404

    async def test_verify_nonexistent_agent(self, client) -> None:
        response = await client.get("/api/audit/verify/nonexistent")
        assert response.status_code == 404


class TestAuditExport:
    async def test_export_returns_jsonl(self, client) -> None:
        create_resp = await client.post("/api/agents", json={
            "name": "Export Test", "role": "test", "company": "Co", "email": "t@t.com",
        })
        agent_id = create_resp.json()["id"]
        resp = await client.get(f"/api/agents/{agent_id}/audit/export")
        assert resp.status_code == 200
        assert "agent.created" in resp.text

    async def test_export_nonexistent(self, client) -> None:
        resp = await client.get("/api/agents/nonexistent/audit/export")
        assert resp.status_code == 404
