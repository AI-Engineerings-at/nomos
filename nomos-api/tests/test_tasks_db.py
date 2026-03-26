"""Tests for the task dispatch service — DB-backed via async endpoints."""

from __future__ import annotations

from httpx import AsyncClient


async def _create_agent(client: AsyncClient, name: str, email: str) -> str:
    r = await client.post(
        "/api/agents",
        json={
            "name": name,
            "role": "test",
            "company": "TestCo",
            "email": email,
            "risk_class": "limited",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def test_create_task(client: AsyncClient) -> None:
    agent_id = await _create_agent(client, "TaskBot", "taskbot@test.local")
    r = await client.post(
        "/api/tasks",
        json={
            "agent_id": agent_id,
            "description": "Write blog post",
            "priority": "high",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "queued"
    assert body["agent_id"] == agent_id
    assert body["description"] == "Write blog post"
    assert body["priority"] == "high"
    assert "id" in body
    assert body["cost_eur"] == 0.0


async def test_task_lifecycle(client: AsyncClient) -> None:
    """Full lifecycle: queued -> assigned -> running -> done."""
    agent_id = await _create_agent(client, "LifecycleBot", "lifecycle@test.local")
    r = await client.post(
        "/api/tasks",
        json={"agent_id": agent_id, "description": "Lifecycle test"},
    )
    task_id = r.json()["id"]

    # queued -> assigned
    r = await client.patch(f"/api/tasks/{task_id}", json={"status": "assigned"})
    assert r.status_code == 200
    assert r.json()["status"] == "assigned"

    # assigned -> running
    r = await client.patch(f"/api/tasks/{task_id}", json={"status": "running"})
    assert r.status_code == 200
    assert r.json()["status"] == "running"

    # running -> done
    r = await client.patch(f"/api/tasks/{task_id}", json={"status": "done"})
    assert r.status_code == 200
    assert r.json()["status"] == "done"


async def test_invalid_transition(client: AsyncClient) -> None:
    """Cannot jump from queued directly to done."""
    agent_id = await _create_agent(client, "InvalidBot", "invalid@test.local")
    r = await client.post(
        "/api/tasks",
        json={"agent_id": agent_id, "description": "Invalid transition"},
    )
    task_id = r.json()["id"]

    r = await client.patch(f"/api/tasks/{task_id}", json={"status": "done"})
    assert r.status_code == 400
    assert "Invalid transition" in r.json()["detail"]


async def test_list_tasks(client: AsyncClient) -> None:
    agent_a = await _create_agent(client, "ListA", "lista@test.local")
    agent_b = await _create_agent(client, "ListB", "listb@test.local")

    await client.post("/api/tasks", json={"agent_id": agent_a, "description": "A1"})
    await client.post("/api/tasks", json={"agent_id": agent_b, "description": "B1"})
    await client.post("/api/tasks", json={"agent_id": agent_a, "description": "A2"})

    # List all
    r = await client.get("/api/tasks")
    assert r.status_code == 200
    assert r.json()["total"] >= 3

    # Filter by agent
    r = await client.get(f"/api/tasks?agent_id={agent_a}")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    for task in body["tasks"]:
        assert task["agent_id"] == agent_a


async def test_get_task_not_found(client: AsyncClient) -> None:
    r = await client.get("/api/tasks/nonexistent-id")
    assert r.status_code == 404


async def test_update_task_not_found(client: AsyncClient) -> None:
    r = await client.patch("/api/tasks/nonexistent-id", json={"status": "assigned"})
    assert r.status_code == 404


async def test_running_to_failed(client: AsyncClient) -> None:
    agent_id = await _create_agent(client, "FailBot", "failbot@test.local")
    r = await client.post(
        "/api/tasks",
        json={"agent_id": agent_id, "description": "Fail task"},
    )
    task_id = r.json()["id"]

    await client.patch(f"/api/tasks/{task_id}", json={"status": "assigned"})
    await client.patch(f"/api/tasks/{task_id}", json={"status": "running"})
    r = await client.patch(f"/api/tasks/{task_id}", json={"status": "failed"})
    assert r.status_code == 200
    assert r.json()["status"] == "failed"


async def test_running_to_review_to_done(client: AsyncClient) -> None:
    agent_id = await _create_agent(client, "ReviewBot", "reviewbot@test.local")
    r = await client.post(
        "/api/tasks",
        json={"agent_id": agent_id, "description": "Review task"},
    )
    task_id = r.json()["id"]

    await client.patch(f"/api/tasks/{task_id}", json={"status": "assigned"})
    await client.patch(f"/api/tasks/{task_id}", json={"status": "running"})
    await client.patch(f"/api/tasks/{task_id}", json={"status": "review"})
    r = await client.patch(f"/api/tasks/{task_id}", json={"status": "done"})
    assert r.status_code == 200
    assert r.json()["status"] == "done"


async def test_assigned_to_queued_requeue(client: AsyncClient) -> None:
    agent_id = await _create_agent(client, "RequeueBot", "requeue@test.local")
    r = await client.post(
        "/api/tasks",
        json={"agent_id": agent_id, "description": "Requeue task"},
    )
    task_id = r.json()["id"]

    await client.patch(f"/api/tasks/{task_id}", json={"status": "assigned"})
    r = await client.patch(f"/api/tasks/{task_id}", json={"status": "queued"})
    assert r.status_code == 200
    assert r.json()["status"] == "queued"
