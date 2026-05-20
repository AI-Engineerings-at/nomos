"""Audit trail endpoints."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.auth.rbac import require_admin, require_agent_actor
from nomos_api.config import settings
from nomos_api.database import get_db
from nomos_api.models import AuditLog, User
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


@router.get("/audit", response_model=AuditResponse)
async def get_global_audit(
    limit: int = 100,
    offset: int = 0,
    agent_id: str | None = None,
    event_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> AuditResponse:
    """Global audit trail -- aggregates all agents with optional filters.

    AuthZ (post-judgment-day-2): admin-only. A non-admin user must not be
    able to enumerate the audit trails of agents they do not own.
    """
    query = select(AuditLog).order_by(AuditLog.id.desc())
    count_query = select(func.count()).select_from(AuditLog)

    if agent_id:
        query = query.where(AuditLog.agent_id == agent_id)
        count_query = count_query.where(AuditLog.agent_id == agent_id)
    if event_type:
        query = query.where(AuditLog.event_type == event_type)
        count_query = count_query.where(AuditLog.event_type == event_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(query.offset(offset).limit(limit))
    entries = result.scalars().all()

    return AuditResponse(
        agent_id="*",
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
        total=total,
    )


@router.get("/agents/{agent_id}/audit", response_model=AuditResponse)
async def get_agent_audit(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    _agent=Depends(require_agent_actor),
) -> AuditResponse:
    """AuthZ: service principal (plugin) OR the agent's owning user OR admin
    — same pattern as heartbeat. Closes the IDOR vector where any logged-in
    user could read every agent's audit trail."""
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
    _agent=Depends(require_agent_actor),
) -> PlainTextResponse:
    """Export audit trail as downloadable JSONL file.

    AuthZ: owner-or-service-or-admin (require_agent_actor). The chain file
    contains the full event history including data payloads — exporting it
    must be gated by agent ownership."""
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
        headers={"Content-Disposition": f'attachment; filename="{agent_id}-audit-chain.jsonl"'},
    )


@router.get("/audit/verify/{agent_id}", response_model=AuditVerifyResponse)
async def verify_agent_audit(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    _agent=Depends(require_agent_actor),
) -> AuditVerifyResponse:
    agent = await get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    agent_dir = Path(agent.agents_dir).resolve()
    safe_base = settings.agents_dir.resolve()
    if not agent_dir.is_relative_to(safe_base):
        raise HTTPException(status_code=400, detail="Invalid agent directory")
    result = verify_chain(agent_dir / "audit")

    # Phase-A5: locate the most recent external anchor for this agent so the
    # caller can confirm the live chain head matches the anchored head.
    last_anchored_at: str | None = None
    last_anchored_head_hash: str | None = None
    head_matches_anchor: bool | None = None
    try:
        anchors_path = settings.audit_anchors_path
        if anchors_path.exists():
            for raw_line in reversed(anchors_path.read_text(encoding="utf-8").splitlines()):
                if not raw_line.strip():
                    continue
                rec = json.loads(raw_line)
                if rec.get("agent_id") == agent_id:
                    last_anchored_at = rec.get("anchored_at")
                    last_anchored_head_hash = rec.get("head_hash")
                    break
        if last_anchored_head_hash is not None:
            chain_file = agent_dir / "audit" / "chain.jsonl"
            if chain_file.exists():
                lines = [ln for ln in chain_file.read_text(encoding="utf-8").splitlines() if ln]
                if lines:
                    current_head = json.loads(lines[-1]).get("hash")
                    head_matches_anchor = current_head == last_anchored_head_hash
    except Exception:
        # Anchor info is advisory; never block verify on a read error.
        pass

    return AuditVerifyResponse(
        agent_id=agent_id,
        valid=result.valid,
        entries_checked=result.entries_checked,
        errors=result.errors,
        last_anchored_at=last_anchored_at,
        last_anchored_head_hash=last_anchored_head_hash,
        head_matches_anchor=head_matches_anchor,
    )


@router.post("/audit/entry", response_model=AuditEntryCreateResponse, status_code=201)
async def create_audit_entry(
    request: AuditEntryCreateRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
) -> AuditEntryCreateResponse:
    """Add a new audit hash chain entry for an agent.

    Used by the NomOS Plugin to log events from OpenClaw Gateway hooks.
    Validates the event_type against the canonical NomOS event types.

    AuthZ (post-judgment-day-2): the principal MUST be the service
    (Plugin API key) OR the owning user OR an admin. Closes the tampering
    vector where any authenticated user could append arbitrary audit
    entries to any agent's chain (defeating both integrity and
    provenance). The check is inline because agent_id lives in the body,
    so the path-param-based require_agent_actor cannot be reused here.
    """
    principal = getattr(http_request.state, "user", None)
    if not principal:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not validate_event_type(request.event_type):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid event_type {request.event_type!r}. Must be a valid NomOS event type.",
        )

    agent = await get_agent(db, request.agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {request.agent_id!r} not found")

    # AuthZ check: service principal OR the agent's owning user OR admin.
    role = principal.get("role")
    if role != "service":
        from nomos_api.auth.rbac import check_agent_access

        class _P:
            pass

        actor = _P()
        actor.role = role or "user"
        actor.email = principal.get("email") or ""
        check_agent_access(actor, agent, "write audit entry")

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
