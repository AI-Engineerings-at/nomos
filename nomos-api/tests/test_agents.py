"""Tests for agent creation endpoint."""

from __future__ import annotations

import pytest


class TestCreateAgent:
    async def test_create_agent_success(self, client) -> None:
        response = await client.post("/api/agents", json={
            "name": "Mani Ruf",
            "role": "external-secretary",
            "company": "AI Engineering",
            "email": "mani@ai-engineering.at",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Mani Ruf"
        assert data["role"] == "external-secretary"
        assert data["status"] == "created"
        assert len(data["manifest_hash"]) == 64

    async def test_create_agent_invalid_name(self, client) -> None:
        response = await client.post("/api/agents", json={
            "name": "",
            "role": "test",
            "company": "Co",
            "email": "t@t.com",
        })
        assert response.status_code == 422

    async def test_create_duplicate_agent(self, client) -> None:
        agent_data = {
            "name": "Duplicate",
            "role": "test",
            "company": "Co",
            "email": "t@t.com",
        }
        resp1 = await client.post("/api/agents", json=agent_data)
        assert resp1.status_code == 201
        resp2 = await client.post("/api/agents", json=agent_data)
        assert resp2.status_code == 400
