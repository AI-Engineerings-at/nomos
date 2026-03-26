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

# Module-level instance — will be replaced by DB-backed service
_task_service = TaskService()


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(agent_id: str | None = None) -> TaskListResponse:
    if agent_id:
        tasks = _task_service.list_by_agent(agent_id)
    else:
        tasks = _task_service.list_all()
    return TaskListResponse(
        tasks=[TaskResponse(**t) for t in tasks],
        total=len(tasks),
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str) -> TaskResponse:
    try:
        task = _task_service.get(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Task {task_id!r} not found")
    return TaskResponse(**task)


@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(request: TaskCreateRequest) -> TaskResponse:
    task = _task_service.create(
        agent_id=request.agent_id,
        description=request.description,
        priority=request.priority,
        timeout_minutes=request.timeout_minutes,
    )
    return TaskResponse(**task)


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task_status(task_id: str, request: TaskUpdateRequest) -> TaskResponse:
    try:
        task = _task_service.update_status(task_id, request.status)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Task {task_id!r} not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return TaskResponse(**task)
