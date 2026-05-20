"""Tests for GET /api/tasks/{task_id} — single task detail endpoint."""

from __future__ import annotations


class TestTaskDetail:
    async def test_get_task_detail(self, client) -> None:
        # L035 / audit A-C2: POST /api/tasks now resolves the target
        # agent before accepting the task. Create the agent first, then
        # the task. Previously this test relied on the unguarded path.
        agent_resp = await client.post(
            "/api/agents",
            json={
                "name": "Task Detail Agent",
                "role": "test",
                "company": "TestCo",
                "email": "td@test.local",
                "risk_class": "limited",
            },
        )
        assert agent_resp.status_code == 201
        agent_id = agent_resp.json()["id"]

        create_resp = await client.post(
            "/api/tasks",
            json={
                "agent_id": agent_id,
                "description": "Write blog post",
                "priority": "high",
            },
        )
        assert create_resp.status_code == 201
        task_id = create_resp.json()["id"]

        resp = await client.get(f"/api/tasks/{task_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == task_id
        assert data["agent_id"] == agent_id
        assert data["description"] == "Write blog post"
        assert data["priority"] == "high"
        assert data["status"] == "queued"

    async def test_get_task_detail_not_found(self, client) -> None:
        resp = await client.get("/api/tasks/nonexistent-task-id")
        assert resp.status_code == 404
