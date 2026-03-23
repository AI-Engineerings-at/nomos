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
