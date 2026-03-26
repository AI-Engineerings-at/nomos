"""Task dispatch endpoints — create, update, and list tasks."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.database import get_db
from nomos_api.models import Task
from nomos_api.schemas import (
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskUpdateRequest,
)
from nomos_api.services.task_dispatch import (
    create_task,
    get_task,
    list_tasks,
    update_task_status,
)

router = APIRouter(prefix="/api", tags=["tasks"])


def _task_to_response(task: Task) -> TaskResponse:
    """Convert a Task ORM instance to a TaskResponse schema."""
    return TaskResponse(
        id=task.id,
        agent_id=task.agent_id,
        description=task.description,
        priority=task.priority,
        status=task.status,
        created_by=task.created_by,
        timeout_minutes=task.timeout_minutes,
        cost_eur=task.cost_eur,
        created_at=task.created_at.isoformat() if task.created_at else "",
        updated_at=task.updated_at.isoformat() if task.updated_at else "",
    )


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks_endpoint(
    agent_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> TaskListResponse:
    tasks = await list_tasks(db, agent_id=agent_id)
    items = [_task_to_response(t) for t in tasks]
    return TaskListResponse(tasks=items, total=len(items))


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_endpoint(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    task = await get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id!r} not found")
    return _task_to_response(task)


@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task_endpoint(
    request: TaskCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    task = await create_task(
        db,
        agent_id=request.agent_id,
        description=request.description,
        priority=request.priority,
        timeout_minutes=request.timeout_minutes,
    )
    return _task_to_response(task)


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task_status_endpoint(
    task_id: str,
    request: TaskUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    try:
        task = await update_task_status(db, task_id, request.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id!r} not found")
    return _task_to_response(task)
