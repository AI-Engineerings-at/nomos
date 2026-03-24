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
from nomos_api.schemas import AuditEntryResponse, AuditResponse, AuditVerifyResponse
from nomos_api.services.fleet_service import get_agent
from nomos.core.hash_chain import verify_chain

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
