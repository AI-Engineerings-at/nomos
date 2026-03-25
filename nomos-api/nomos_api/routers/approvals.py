"""Approval endpoints — request, approve, deny, and list approvals."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from nomos_api.schemas import (
    ApprovalListResponse,
    ApprovalRequestCreate,
    ApprovalResolveRequest,
    ApprovalResponse,
)
from nomos_api.services.approval import ApprovalService

router = APIRouter(prefix="/api", tags=["approvals"])

# Singleton service instance for the application lifecycle
_approval_service = ApprovalService()


def get_approval_service() -> ApprovalService:
    """Return the shared ApprovalService instance."""
    return _approval_service


@router.get("/approvals", response_model=ApprovalListResponse)
async def list_approvals(agent_id: str | None = None) -> ApprovalListResponse:
    svc = get_approval_service()
    if agent_id:
        approvals = svc.list_by_agent(agent_id)
    else:
        approvals = svc.list_pending()
    return ApprovalListResponse(
        approvals=[ApprovalResponse(**a) for a in approvals],
        total=len(approvals),
    )


@router.post("/approvals", response_model=ApprovalResponse, status_code=201)
async def create_approval(request: ApprovalRequestCreate) -> ApprovalResponse:
    svc = get_approval_service()
    approval = svc.request(
        agent_id=request.agent_id,
        action=request.action,
        description=request.description,
        timeout_minutes=request.timeout_minutes,
    )
    return ApprovalResponse(**approval)


@router.post("/approvals/{approval_id}/approve", response_model=ApprovalResponse)
async def approve(approval_id: str, request: ApprovalResolveRequest) -> ApprovalResponse:
    svc = get_approval_service()
    try:
        result = svc.resolve(approval_id, "approved", resolved_by=request.resolved_by)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id!r} not found")
    return ApprovalResponse(**result)


@router.post("/approvals/{approval_id}/reject", response_model=ApprovalResponse)
async def reject(approval_id: str, request: ApprovalResolveRequest) -> ApprovalResponse:
    svc = get_approval_service()
    try:
        result = svc.resolve(approval_id, "denied", resolved_by=request.resolved_by)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id!r} not found")
    return ApprovalResponse(**result)
