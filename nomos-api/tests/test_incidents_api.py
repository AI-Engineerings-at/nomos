"""Tests for Incident API endpoints — Art. 33/34 DSGVO compliance."""

from __future__ import annotations


class TestCreateIncident:
    async def test_create_incident_with_pii(self, client) -> None:
        response = await client.post("/api/incidents", json={
            "log_entry": "User max@example.com logged in",
            "agent_id": "test-agent",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["incident_type"] == "pii_in_log"
        assert data["severity"] == "high"
        assert data["status"] == "detected"
        assert data["agent_id"] == "test-agent"

    async def test_create_incident_unknown_endpoint(self, client) -> None:
        response = await client.post("/api/incidents", json={
            "log_entry": "Agent sent data to https://evil.com/collect",
            "agent_id": "test-agent",
            "context": {"allowed_endpoints": ["https://api.anthropic.com"]},
        })
        assert response.status_code == 201
        data = response.json()
        assert data["incident_type"] == "unknown_endpoint"
        assert data["severity"] == "critical"

    async def test_no_incident_returns_204(self, client) -> None:
        response = await client.post("/api/incidents", json={
            "log_entry": "Normal operation completed",
            "agent_id": "test-agent",
        })
        assert response.status_code == 204

    async def test_incident_has_deadline(self, client) -> None:
        response = await client.post("/api/incidents", json={
            "log_entry": "PII leak: max@test.com",
            "agent_id": "test-agent",
        })
        data = response.json()
        assert "report_deadline" in data
        assert len(data["report_deadline"]) > 0


class TestListIncidents:
    async def test_list_empty(self, client) -> None:
        response = await client.get("/api/incidents")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["incidents"] == []

    async def test_list_after_creation(self, client) -> None:
        await client.post("/api/incidents", json={
            "log_entry": "max@test.com in log",
            "agent_id": "test-agent",
        })
        response = await client.get("/api/incidents")
        data = response.json()
        assert data["total"] == 1


class TestUpdateIncident:
    async def test_update_status_to_reported(self, client) -> None:
        create_resp = await client.post("/api/incidents", json={
            "log_entry": "max@test.com in log",
            "agent_id": "test-agent",
        })
        incident_id = create_resp.json()["id"]
        update_resp = await client.patch(f"/api/incidents/{incident_id}", json={
            "status": "reported",
        })
        assert update_resp.status_code == 200
        assert update_resp.json()["status"] == "reported"

    async def test_update_status_to_resolved(self, client) -> None:
        create_resp = await client.post("/api/incidents", json={
            "log_entry": "max@test.com in log",
            "agent_id": "test-agent",
        })
        incident_id = create_resp.json()["id"]
        update_resp = await client.patch(f"/api/incidents/{incident_id}", json={
            "status": "resolved",
        })
        assert update_resp.status_code == 200
        assert update_resp.json()["status"] == "resolved"

    async def test_update_nonexistent_returns_404(self, client) -> None:
        response = await client.patch("/api/incidents/9999", json={
            "status": "reported",
        })
        assert response.status_code == 404

    async def test_invalid_status_rejected(self, client) -> None:
        create_resp = await client.post("/api/incidents", json={
            "log_entry": "max@test.com in log",
            "agent_id": "test-agent",
        })
        incident_id = create_resp.json()["id"]
        response = await client.patch(f"/api/incidents/{incident_id}", json={
            "status": "invalid_status",
        })
        assert response.status_code == 422
