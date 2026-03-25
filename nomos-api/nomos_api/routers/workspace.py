"""Workspace endpoints — agent workspace info, mount/unmount collections."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from nomos_api.schemas import (
    WorkspaceInfoResponse,
    WorkspaceMountRequest,
    WorkspaceMountResponse,
)
from nomos_api.services.honcho import HonchoClient
from nomos_api.services.workspace import WorkspaceService

router = APIRouter(prefix="/api", tags=["workspace"])

_client = HonchoClient(base_url="http://localhost:5055")
_workspace_service = WorkspaceService(_client)


def get_workspace_service() -> WorkspaceService:
    """Return the workspace service singleton."""
    return _workspace_service


@router.get("/workspace/{agent_id}", response_model=WorkspaceInfoResponse)
async def get_workspace_info(agent_id: str) -> WorkspaceInfoResponse:
    """Return workspace info and mounted collections for an agent."""
    svc = get_workspace_service()
    collections = svc.get_mounted_collections(agent_id)
    is_active = svc.can_access(agent_id, agent_id, "read")
    ws_id = svc._agent_workspaces.get(agent_id)
    return WorkspaceInfoResponse(
        agent_id=agent_id,
        workspace_id=ws_id,
        mounted_collections=collections,
        is_active=is_active,
    )


@router.post("/workspace/mount", response_model=WorkspaceMountResponse)
async def mount_collection(request: WorkspaceMountRequest) -> WorkspaceMountResponse:
    """Mount a collection to an agent's workspace."""
    svc = get_workspace_service()
    if request.agent_id not in svc._agent_workspaces:
        svc.create_agent_workspace(request.agent_id)
    result = svc.mount_collection(request.agent_id, request.collection_name)
    if not result:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot mount collection for agent {request.agent_id}",
        )
    return WorkspaceMountResponse(
        agent_id=request.agent_id,
        collection_name=request.collection_name,
        mounted=True,
    )


@router.post("/workspace/unmount", response_model=WorkspaceMountResponse)
async def unmount_collection(request: WorkspaceMountRequest) -> WorkspaceMountResponse:
    """Unmount a collection from an agent's workspace."""
    svc = get_workspace_service()
    result = svc.unmount_collection(request.agent_id, request.collection_name)
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
