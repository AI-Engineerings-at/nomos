"""Task dispatch endpoints — create, update, and list tasks."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from nomos_api.schemas import (
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskUpdateRequest,
)
from nomos_api.services.task_dispatch import TaskService

router = APIRouter(prefix="/api", tags=["tasks"])

# Singleton service instance for the application lifecycle
_task_service = TaskService()


def get_task_service() -> TaskService:
    """Return the shared TaskService instance."""
    return _task_service


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(agent_id: str | None = None) -> TaskListResponse:
    svc = get_task_service()
    if agent_id:
        tasks = svc.list_by_agent(agent_id)
    else:
        tasks = svc.list_all()
    return TaskListResponse(
        tasks=[TaskResponse(**t) for t in tasks],
        total=len(tasks),
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str) -> TaskResponse:
    svc = get_task_service()
    try:
        task = svc.get(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Task {task_id!r} not found")
    return TaskResponse(**task)


@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(request: TaskCreateRequest) -> TaskResponse:
    svc = get_task_service()
    task = svc.create(
        agent_id=request.agent_id,
        description=request.description,
        priority=request.priority,
        timeout_minutes=request.timeout_minutes,
    )
    return TaskResponse(**task)


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task_status(task_id: str, request: TaskUpdateRequest) -> TaskResponse:
    svc = get_task_service()
    try:
        task = svc.update_status(task_id, request.status)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Task {task_id!r} not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return TaskResponse(**task)
