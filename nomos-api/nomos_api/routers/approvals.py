"""Approval endpoints — request, approve, deny, and list approvals."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.database import get_db
from nomos_api.schemas import (
    ApprovalListResponse,
    ApprovalRequestCreate,
    ApprovalResolveRequest,
    ApprovalResponse,
)
from nomos_api.models import Approval
from nomos_api.services.approval import (
    create_approval,
    list_approvals,
    resolve_approval,
)

router = APIRouter(prefix="/api", tags=["approvals"])


def _approval_to_response(approval: Approval) -> ApprovalResponse:
    """Convert an Approval ORM instance to an ApprovalResponse schema."""
    return ApprovalResponse(
        id=approval.id,
        agent_id=approval.agent_id,
        action=approval.action,
        description=approval.description,
        status=approval.status,
        requested_at=approval.requested_at.isoformat() if approval.requested_at else "",
        resolved_at=approval.resolved_at.isoformat() if approval.resolved_at else None,
        resolved_by=approval.resolved_by,
        timeout_minutes=approval.timeout_minutes,
    )


@router.get("/approvals", response_model=ApprovalListResponse)
async def list_approvals_endpoint(
    agent_id: str | None = None,
    status: str = "pending",
    db: AsyncSession = Depends(get_db),
) -> ApprovalListResponse:
    approvals = await list_approvals(db, agent_id=agent_id, status=status)
    items = [_approval_to_response(a) for a in approvals]
    return ApprovalListResponse(approvals=items, total=len(items))


@router.post("/approvals", response_model=ApprovalResponse, status_code=201)
async def create_approval_endpoint(
    request: ApprovalRequestCreate,
    db: AsyncSession = Depends(get_db),
) -> ApprovalResponse:
    approval = await create_approval(
        db,
        agent_id=request.agent_id,
        action=request.action,
        description=request.description,
        timeout_minutes=request.timeout_minutes,
    )
    return _approval_to_response(approval)


@router.post("/approvals/{approval_id}/approve", response_model=ApprovalResponse)
async def approve(
    approval_id: str,
    request: ApprovalResolveRequest,
    db: AsyncSession = Depends(get_db),
) -> ApprovalResponse:
    result = await resolve_approval(db, approval_id, "approved", resolved_by=request.resolved_by)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id!r} not found")
    return _approval_to_response(result)


@router.post("/approvals/{approval_id}/reject", response_model=ApprovalResponse)
async def reject(
    approval_id: str,
    request: ApprovalResolveRequest,
    db: AsyncSession = Depends(get_db),
) -> ApprovalResponse:
    result = await resolve_approval(db, approval_id, "denied", resolved_by=request.resolved_by)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id!r} not found")
    return _approval_to_response(result)
