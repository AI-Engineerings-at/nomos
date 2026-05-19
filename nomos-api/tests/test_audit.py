"""Tests for audit trail endpoints."""

from __future__ import annotations


class TestAudit:
    async def test_audit_trail_for_created_agent(self, client) -> None:
        create_resp = await client.post(
            "/api/agents",
            json={
                "name": "Audit Test",
                "role": "test",
                "company": "Co",
                "email": "t@t.com",
            },
        )
        agent_id = create_resp.json()["id"]
        response = await client.get(f"/api/agents/{agent_id}/audit")
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == agent_id
        assert data["total"] >= 1
        assert data["entries"][0]["event_type"] == "agent.created"

    async def test_audit_verify_for_created_agent(self, client) -> None:
        create_resp = await client.post(
            "/api/agents",
            json={
                "name": "Verify Test",
                "role": "test",
                "company": "Co",
                "email": "t@t.com",
            },
        )
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


class TestGlobalAudit:
    async def test_global_audit_endpoint(self, admin_client) -> None:
        response = await admin_client.get("/api/audit")
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert "total" in data
        assert isinstance(data["entries"], list)
        assert data["agent_id"] == "*"

    async def test_global_audit_returns_all_agents(self, admin_client) -> None:
        await admin_client.post(
            "/api/agents",
            json={
                "name": "Global A",
                "role": "test",
                "company": "Co",
                "email": "a@t.com",
            },
        )
        await admin_client.post(
            "/api/agents",
            json={
                "name": "Global B",
                "role": "test",
                "company": "Co",
                "email": "b@t.com",
            },
        )
        response = await admin_client.get("/api/audit")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        agent_ids = {e["agent_id"] for e in data["entries"]}
        assert len(agent_ids) >= 2

    async def test_global_audit_filter_by_agent(self, admin_client) -> None:
        response = await admin_client.get("/api/audit?agent_id=nonexistent")
        assert response.status_code == 200
        assert response.json()["total"] == 0

    async def test_global_audit_filter_by_event_type(self, admin_client) -> None:
        await admin_client.post(
            "/api/agents",
            json={
                "name": "Event Filter",
                "role": "test",
                "company": "Co",
                "email": "ef@t.com",
            },
        )
        response = await admin_client.get("/api/audit?event_type=agent.created")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert all(e["event_type"] == "agent.created" for e in data["entries"])

    async def test_global_audit_pagination(self, admin_client) -> None:
        response = await admin_client.get("/api/audit?limit=1&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) <= 1


class TestAuditExport:
    async def test_export_returns_jsonl(self, client) -> None:
        create_resp = await client.post(
            "/api/agents",
            json={
                "name": "Export Test",
                "role": "test",
                "company": "Co",
                "email": "t@t.com",
            },
        )
        agent_id = create_resp.json()["id"]
        resp = await client.get(f"/api/agents/{agent_id}/audit/export")
        assert resp.status_code == 200
        assert "agent.created" in resp.text

    async def test_export_nonexistent(self, client) -> None:
        resp = await client.get("/api/agents/nonexistent/audit/export")
        assert resp.status_code == 404
