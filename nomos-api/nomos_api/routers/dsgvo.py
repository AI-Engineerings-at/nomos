"""DSGVO endpoints — Art. 17 forget, Art. 15 export."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.auth.rbac import require_admin
from nomos_api.database import get_db
from nomos_api.models import Agent, User
from nomos_api.schemas import (
    DSGVOExportRequest,
    DSGVOExportResponse,
    DSGVOForgetRequest,
    DSGVOForgetResponse,
)
from nomos_api.services.audit import write_audit_event
from nomos_api.services.forget import export_data, forget
from nomos.core.events import EventType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["dsgvo"])


@router.post("/dsgvo/forget", response_model=DSGVOForgetResponse)
async def dsgvo_forget(
    request: DSGVOForgetRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> DSGVOForgetResponse:
    """Art. 17 DSGVO — delete all messages containing the email address.

    Admin-only: a substring-driven deletion across all tenants must never
    be reachable by a non-admin authenticated user (L035 audit finding A-C1).
    The requester's email is included in the audit event so the chain
    records WHO triggered the deletion, not only which agent it affected.
    """
    result = await forget(db, request.email)

    # Write audit trail if messages were deleted and an agent with this email exists
    if result["deleted_messages"] > 0:
        stmt = select(Agent).where(Agent.email == request.email)
        agent_row = await db.execute(stmt)
        agent = agent_row.scalar_one_or_none()
        if agent is not None:
            try:
                await write_audit_event(
                    db=db,
                    agent=agent,
                    agent_id=agent.id,
                    event_type=EventType.DATA_ERASED,
                    data={
                        "search_term": request.email,
                        "deleted_messages": result["deleted_messages"],
                        "requester_email": admin.email,
                    },
                )
            except Exception:
                logger.warning(
                    "Could not write audit event for DSGVO forget (agent=%s)",
                    agent.id,
                    exc_info=True,
                )

    return DSGVOForgetResponse(
        deleted_messages=result["deleted_messages"],
        search_term=result["search_term"],
        audit_event=result["audit_event"],
        audit_preserved=result["audit_preserved"],
        timestamp=result["timestamp"],
    )


@router.post("/dsgvo/export", response_model=DSGVOExportResponse)
async def dsgvo_export(
    request: DSGVOExportRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> DSGVOExportResponse:
    """Art. 15 DSGVO — export all data for an email address.

    Admin-only: substring-driven cross-tenant data exfiltration must never
    be reachable by a non-admin authenticated user (L035 audit finding A-C1).
    """
    result = await export_data(db, request.email)
    return DSGVOExportResponse(
        email=result["email"],
        messages=result["messages"],
        total=result["total"],
        timestamp=result["timestamp"],
    )
