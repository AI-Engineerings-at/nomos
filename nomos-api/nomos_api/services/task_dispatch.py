"""Task dispatch service — CRUD and lifecycle management for agent tasks.

Implements a status machine with valid transitions:
    queued -> assigned -> running -> review -> done
                      -> failed
    assigned -> queued (requeue)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


# Valid status transitions: from_status -> set of allowed to_statuses
_TRANSITIONS: dict[str, set[str]] = {
    "queued": {"assigned"},
    "assigned": {"running", "queued"},
    "running": {"review", "done", "failed"},
    "review": {"done", "failed"},
    "done": set(),
    "failed": set(),
}


class TaskService:
    """In-memory task dispatch with status machine enforcement."""

    def __init__(self) -> None:
        self._tasks: dict[str, dict] = {}

    def create(
        self,
        agent_id: str,
        description: str,
        priority: str = "normal",
        created_by: str | None = None,
        timeout_minutes: int = 60,
    ) -> dict:
        """Create a new task in 'queued' status."""
        task_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        task = {
            "id": task_id,
            "agent_id": agent_id,
            "description": description,
            "priority": priority,
            "status": "queued",
            "created_by": created_by,
            "timeout_minutes": timeout_minutes,
            "cost_eur": 0.0,
            "created_at": now,
            "updated_at": now,
        }
        self._tasks[task_id] = task
        return dict(task)

    def get(self, task_id: str) -> dict:
        """Get a task by ID. Raises KeyError if not found."""
        if task_id not in self._tasks:
            raise KeyError(f"Task {task_id!r} not found")
        return dict(self._tasks[task_id])

    def update_status(self, task_id: str, new_status: str) -> dict:
        """Transition a task to a new status. Validates the transition."""
        if task_id not in self._tasks:
            raise KeyError(f"Task {task_id!r} not found")

        task = self._tasks[task_id]
        current = task["status"]
        allowed = _TRANSITIONS.get(current, set())

        if new_status not in allowed:
            raise ValueError(
                f"Invalid transition: {current!r} -> {new_status!r}. "
                f"Allowed: {sorted(allowed)}"
            )

        task["status"] = new_status
        task["updated_at"] = datetime.now(timezone.utc).isoformat()
        return dict(task)

    def list_by_agent(self, agent_id: str) -> list[dict]:
        """List all tasks for a specific agent."""
        return [dict(t) for t in self._tasks.values() if t["agent_id"] == agent_id]

    def list_all(self) -> list[dict]:
        """List all tasks across all agents."""
        return [dict(t) for t in self._tasks.values()]
