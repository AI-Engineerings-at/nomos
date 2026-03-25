"""Tests for GET /api/tasks/{task_id} — single task detail endpoint."""

from __future__ import annotations

import pytest


class TestTaskDetail:
    async def test_get_task_detail(self, client) -> None:
        create_resp = await client.post("/api/tasks", json={
            "agent_id": "agent-1",
            "description": "Write blog post",
            "priority": "high",
        })
        assert create_resp.status_code == 201
        task_id = create_resp.json()["id"]

        resp = await client.get(f"/api/tasks/{task_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == task_id
        assert data["agent_id"] == "agent-1"
        assert data["description"] == "Write blog post"
        assert data["priority"] == "high"
        assert data["status"] == "queued"

    async def test_get_task_detail_not_found(self, client) -> None:
        resp = await client.get("/api/tasks/nonexistent-task-id")
        assert resp.status_code == 404
