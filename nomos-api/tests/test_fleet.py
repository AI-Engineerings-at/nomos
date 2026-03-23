"""Tests for fleet endpoints."""

from __future__ import annotations

import pytest


class TestFleet:
    async def test_empty_fleet(self, client) -> None:
        response = await client.get("/api/fleet")
        assert response.status_code == 200
        data = response.json()
        assert data["agents"] == []
        assert data["total"] == 0

    async def test_fleet_after_agent_created(self, client) -> None:
        await client.post("/api/agents", json={
            "name": "Test Agent",
            "role": "test-role",
            "company": "Test Co",
            "email": "test@test.com",
        })
        response = await client.get("/api/fleet")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["agents"][0]["name"] == "Test Agent"

    async def test_get_nonexistent_agent(self, client) -> None:
        response = await client.get("/api/fleet/nonexistent")
        assert response.status_code == 404

    async def test_get_created_agent(self, client) -> None:
        create_resp = await client.post("/api/agents", json={
            "name": "Lookup Agent",
            "role": "test",
            "company": "Co",
            "email": "t@t.com",
        })
        agent_id = create_resp.json()["id"]
        response = await client.get(f"/api/fleet/{agent_id}")
        assert response.status_code == 200
        assert response.json()["id"] == agent_id
