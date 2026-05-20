"""Workspace endpoints — agent workspace info, mount/unmount collections."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.auth.rbac import authorize_agent_action, require_agent_actor
from nomos_api.database import get_db
from nomos_api.models import Agent
from nomos_api.schemas import (
    WorkspaceInfoResponse,
    WorkspaceMountRequest,
    WorkspaceMountResponse,
)
from nomos_api.services import workspace as workspace_svc

router = APIRouter(prefix="/api", tags=["workspace"])


@router.get("/workspace/{agent_id}", response_model=WorkspaceInfoResponse)
async def get_workspace_info(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    _agent: Agent = Depends(require_agent_actor),
) -> WorkspaceInfoResponse:
    """Workspace info for an agent. Caller must own the agent or be admin
    (L035 audit A-C4 — was unguarded)."""
    """Return workspace info and mounted collections for an agent."""
    exists = await workspace_svc.agent_exists(db, agent_id)
    collections = await workspace_svc.get_mounted_collections(db, agent_id)
    return WorkspaceInfoResponse(
        agent_id=agent_id,
        workspace_id=agent_id if exists else None,
        mounted_collections=collections,
        is_active=exists,
    )


@router.post("/workspace/mount", response_model=WorkspaceMountResponse)
async def mount_collection(
    request: WorkspaceMountRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> WorkspaceMountResponse:
    """Mount a collection to an agent's workspace. Caller must own the
    target agent or be admin — otherwise RAG isolation between tenants
    can be broken (L035 audit A-C4)."""
    await authorize_agent_action(db=db, request=http_request, agent_id=request.agent_id, action="workspace_mount")
    result = await workspace_svc.mount_collection(db, request.agent_id, request.collection_name)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Agent {request.agent_id!r} not found")
    return WorkspaceMountResponse(
        agent_id=request.agent_id,
        collection_name=request.collection_name,
        mounted=True,
    )


@router.post("/workspace/unmount", response_model=WorkspaceMountResponse)
async def unmount_collection(
    request: WorkspaceMountRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> WorkspaceMountResponse:
    """Unmount a collection from an agent's workspace. Caller must own
    the target agent or be admin (L035 audit A-C4)."""
    await authorize_agent_action(db=db, request=http_request, agent_id=request.agent_id, action="workspace_unmount")
    result = await workspace_svc.unmount_collection(db, request.agent_id, request.collection_name)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Collection {request.collection_name} not mounted for agent {request.agent_id}",
        )
    return WorkspaceMountResponse(
        agent_id=request.agent_id,
        collection_name=request.collection_name,
        mounted=False,
    )
