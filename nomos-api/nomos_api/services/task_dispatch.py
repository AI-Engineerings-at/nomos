"""Task dispatch service — DB-backed CRUD and lifecycle management for agent tasks.

Implements a status machine with valid transitions:
    queued -> assigned -> running -> review -> done
                      -> failed
    assigned -> queued (requeue)
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.models import Task

# Valid status transitions: from_status -> set of allowed to_statuses
_TRANSITIONS: dict[str, set[str]] = {
    "queued": {"assigned"},
    "assigned": {"running", "queued"},
    "running": {"review", "done", "failed"},
    "review": {"done", "failed"},
    "done": set(),
    "failed": set(),
}


async def create_task(
    db: AsyncSession,
    agent_id: str,
    description: str,
    priority: str = "normal",
    created_by: str | None = None,
    timeout_minutes: int = 60,
    cost_eur: float = 0.0,
) -> Task:
    """Create a new task in 'queued' status."""
    task = Task(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        description=description,
        priority=priority,
        status="queued",
        created_by=created_by,
        timeout_minutes=timeout_minutes,
        cost_eur=cost_eur,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def get_task(
    db: AsyncSession,
    task_id: str,
) -> Task | None:
    """Get a task by ID. Returns None if not found."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def update_task_status(
    db: AsyncSession,
    task_id: str,
    new_status: str,
) -> Task | None:
    """Transition a task to a new status. Validates the transition.

    Returns None if task not found.
    Raises ValueError if the transition is invalid.
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        return None

    current = task.status
    allowed = _TRANSITIONS.get(current, set())

    if new_status not in allowed:
        raise ValueError(f"Invalid transition: {current!r} -> {new_status!r}. Allowed: {sorted(allowed)}")

    task.status = new_status
    await db.commit()
    await db.refresh(task)
    return task


async def list_tasks(
    db: AsyncSession,
    agent_id: str | None = None,
) -> list[Task]:
    """List tasks, optionally filtered by agent_id."""
    stmt = select(Task)
    if agent_id is not None:
        stmt = stmt.where(Task.agent_id == agent_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())
