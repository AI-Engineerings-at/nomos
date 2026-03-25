"""Tests for the TaskService — in-memory task dispatch with status machine."""

from __future__ import annotations

import pytest

from nomos_api.services.task_dispatch import TaskService


def test_create_task():
    svc = TaskService()
    task = svc.create(agent_id="agent-1", description="Write blog post", priority="normal")
    assert task["status"] == "queued"
    assert task["agent_id"] == "agent-1"
    assert task["description"] == "Write blog post"
    assert task["priority"] == "normal"
    assert "id" in task


def test_task_lifecycle():
    svc = TaskService()
    task = svc.create(agent_id="agent-1", description="Test task")
    task_id = task["id"]
    svc.update_status(task_id, "assigned")
    assert svc.get(task_id)["status"] == "assigned"
    svc.update_status(task_id, "running")
    assert svc.get(task_id)["status"] == "running"
    svc.update_status(task_id, "done")
    assert svc.get(task_id)["status"] == "done"


def test_invalid_status_transition():
    svc = TaskService()
    task = svc.create(agent_id="agent-1", description="Test")
    with pytest.raises(ValueError, match="Invalid"):
        svc.update_status(task["id"], "done")  # Can't go from queued to done


def test_list_tasks_by_agent():
    svc = TaskService()
    svc.create(agent_id="agent-1", description="Task A")
    svc.create(agent_id="agent-2", description="Task B")
    svc.create(agent_id="agent-1", description="Task C")
    tasks = svc.list_by_agent("agent-1")
    assert len(tasks) == 2


def test_get_unknown_task():
    svc = TaskService()
    with pytest.raises(KeyError):
        svc.get("nonexistent")


def test_update_unknown_task():
    svc = TaskService()
    with pytest.raises(KeyError):
        svc.update_status("nonexistent", "assigned")


def test_running_to_failed():
    svc = TaskService()
    task = svc.create(agent_id="agent-1", description="Fail task")
    svc.update_status(task["id"], "assigned")
    svc.update_status(task["id"], "running")
    svc.update_status(task["id"], "failed")
    assert svc.get(task["id"])["status"] == "failed"


def test_running_to_review_to_done():
    svc = TaskService()
    task = svc.create(agent_id="agent-1", description="Review task")
    svc.update_status(task["id"], "assigned")
    svc.update_status(task["id"], "running")
    svc.update_status(task["id"], "review")
    svc.update_status(task["id"], "done")
    assert svc.get(task["id"])["status"] == "done"


def test_assigned_to_queued_requeue():
    svc = TaskService()
    task = svc.create(agent_id="agent-1", description="Requeue task")
    svc.update_status(task["id"], "assigned")
    svc.update_status(task["id"], "queued")
    assert svc.get(task["id"])["status"] == "queued"


def test_list_all_tasks():
    svc = TaskService()
    svc.create(agent_id="agent-1", description="A")
    svc.create(agent_id="agent-2", description="B")
    all_tasks = svc.list_all()
    assert len(all_tasks) == 2
