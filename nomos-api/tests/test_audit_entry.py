"""Tests for POST /api/audit/entry — used by the NomOS Plugin to log hash chain entries."""

from __future__ import annotations

import pytest


async def _create_agent(client, name: str = "Audit Entry Test") -> str:
    resp = await client.post("/api/agents", json={
        "name": name,
        "role": "test-role",
        "company": "Test Co",
        "email": "test@test.com",
    })
    assert resp.status_code == 201
    return resp.json()["id"]


class TestAuditEntry:
    async def test_create_audit_entry_success(self, client) -> None:
        agent_id = await _create_agent(client, "Audit Entry Agent")
        resp = await client.post("/api/audit/entry", json={
            "agent_id": agent_id,
            "event_type": "governance.hook.triggered",
            "payload": {"hook": "before_tool_call", "tool": "bash"},
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "hash" in data
        assert len(data["hash"]) == 64
        assert "id" in data

    async def test_create_audit_entry_appears_in_trail(self, client) -> None:
        agent_id = await _create_agent(client, "Audit Trail Check")
        await client.post("/api/audit/entry", json={
            "agent_id": agent_id,
            "event_type": "governance.hook.triggered",
            "payload": {"hook": "test"},
        })
        audit_resp = await client.get(f"/api/agents/{agent_id}/audit")
        events = [e["event_type"] for e in audit_resp.json()["entries"]]
        assert "governance.hook.triggered" in events

    async def test_create_audit_entry_nonexistent_agent(self, client) -> None:
        resp = await client.post("/api/audit/entry", json={
            "agent_id": "nonexistent",
            "event_type": "governance.hook.triggered",
            "payload": {},
        })
        assert resp.status_code == 404

    async def test_create_audit_entry_invalid_event_type(self, client) -> None:
        agent_id = await _create_agent(client, "Invalid Event Type")
        resp = await client.post("/api/audit/entry", json={
            "agent_id": agent_id,
            "event_type": "not.a.valid.event",
            "payload": {},
        })
        assert resp.status_code == 422
