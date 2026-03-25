"""Audit trail endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.config import settings
from nomos_api.database import get_db
from nomos_api.models import AuditLog
from nomos_api.schemas import (
    AuditEntryCreateRequest,
    AuditEntryCreateResponse,
    AuditEntryResponse,
    AuditResponse,
    AuditVerifyResponse,
)
from nomos_api.services.fleet_service import get_agent
from nomos.core.events import validate_event_type
from nomos.core.hash_chain import HashChain, verify_chain

router = APIRouter(prefix="/api", tags=["audit"])


@router.get("/agents/{agent_id}/audit", response_model=AuditResponse)
async def get_agent_audit(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
) -> AuditResponse:
    agent = await get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    result = await db.execute(select(AuditLog).where(AuditLog.agent_id == agent_id).order_by(AuditLog.sequence))
    entries = result.scalars().all()
    return AuditResponse(
        agent_id=agent_id,
        entries=[
            AuditEntryResponse(
                sequence=e.sequence,
                event_type=e.event_type,
                agent_id=e.agent_id,
                data=e.data or {},
                chain_hash=e.chain_hash,
                timestamp=e.timestamp,
            )
            for e in entries
        ],
        total=len(entries),
    )


@router.get("/agents/{agent_id}/audit/export")
async def export_agent_audit(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
) -> PlainTextResponse:
    """Export audit trail as downloadable JSONL file."""
    agent = await get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")

    agent_dir = Path(agent.agents_dir).resolve()
    safe_base = settings.agents_dir.resolve()
    if not agent_dir.is_relative_to(safe_base):
        raise HTTPException(status_code=400, detail="Invalid agent directory")

    chain_file = agent_dir / "audit" / "chain.jsonl"
    if not chain_file.exists():
        return PlainTextResponse("", media_type="application/jsonl")

    content = chain_file.read_text(encoding="utf-8")
    return PlainTextResponse(
        content,
        media_type="application/jsonl",
        headers={
            "Content-Disposition": f'attachment; filename="{agent_id}-audit-chain.jsonl"'
        },
    )


@router.get("/audit/verify/{agent_id}", response_model=AuditVerifyResponse)
async def verify_agent_audit(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
) -> AuditVerifyResponse:
    agent = await get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    agent_dir = Path(agent.agents_dir).resolve()
    safe_base = settings.agents_dir.resolve()
    if not agent_dir.is_relative_to(safe_base):
        raise HTTPException(status_code=400, detail="Invalid agent directory")
    result = verify_chain(agent_dir / "audit")
    return AuditVerifyResponse(
        agent_id=agent_id,
        valid=result.valid,
        entries_checked=result.entries_checked,
        errors=result.errors,
    )


@router.post("/audit/entry", response_model=AuditEntryCreateResponse, status_code=201)
async def create_audit_entry(
    request: AuditEntryCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> AuditEntryCreateResponse:
    """Add a new audit hash chain entry for an agent.

    Used by the NomOS Plugin to log events from OpenClaw Gateway hooks.
    Validates the event_type against the canonical NomOS event types.
    """
    if not validate_event_type(request.event_type):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid event_type {request.event_type!r}. Must be a valid NomOS event type.",
        )

    agent = await get_agent(db, request.agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {request.agent_id!r} not found")

    agent_dir = Path(agent.agents_dir).resolve()
    safe_base = settings.agents_dir.resolve()
    if not agent_dir.is_relative_to(safe_base):
        raise HTTPException(status_code=400, detail="Invalid agent directory")

    audit_dir = agent_dir / "audit"
    if not audit_dir.exists():
        raise HTTPException(status_code=400, detail="Agent audit directory not found")

    chain = HashChain(storage_dir=audit_dir)
    entry = chain.append(
        event_type=request.event_type,
        agent_id=request.agent_id,
        data=request.payload,
    )

    audit_log = AuditLog(
        agent_id=entry.agent_id,
        sequence=entry.sequence,
        event_type=entry.event_type,
        data=entry.data,
        chain_hash=entry.hash,
        timestamp=entry.timestamp,
    )
    db.add(audit_log)
    await db.commit()
    await db.refresh(audit_log)

    return AuditEntryCreateResponse(hash=entry.hash, id=audit_log.id)
