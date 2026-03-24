"""Compliance check endpoint."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.config import settings
from nomos_api.database import get_db
from nomos_api.schemas import ComplianceResponse
from nomos_api.services.fleet_service import get_agent
from nomos.core.compliance_engine import check_compliance
from nomos.core.manifest_validator import load_manifest

router = APIRouter(prefix="/api", tags=["compliance"])


@router.get("/agents/{agent_id}/compliance", response_model=ComplianceResponse)
async def check_agent_compliance(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
) -> ComplianceResponse:
    agent = await get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    agent_dir = Path(agent.agents_dir).resolve()
    safe_base = settings.agents_dir.resolve()
    if not agent_dir.is_relative_to(safe_base):
        raise HTTPException(status_code=400, detail="Invalid agent directory")
    manifest = load_manifest(agent_dir / "manifest.yaml")
    result = check_compliance(manifest, agent_dir / "compliance")
    return ComplianceResponse(
        agent_id=agent_id,
        status=result.status.value,
        missing_documents=result.missing_documents,
        errors=result.errors,
        warnings=result.warnings,
    )


@router.post("/agents/{agent_id}/gate", response_model=ComplianceResponse)
async def run_compliance_gate(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
) -> ComplianceResponse:
    """Generate compliance documents for an agent and re-check compliance."""
    agent = await get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")

    agent_dir = Path(agent.agents_dir).resolve()
    safe_base = settings.agents_dir.resolve()
    if not agent_dir.is_relative_to(safe_base):
        raise HTTPException(status_code=400, detail="Invalid agent directory")

    manifest = load_manifest(agent_dir / "manifest.yaml")

    # Generate compliance documents
    from nomos.core.gate import generate_compliance_docs
    generate_compliance_docs(manifest, agent_dir / "compliance")

    # Re-check compliance (should now pass)
    result = check_compliance(manifest, agent_dir / "compliance")

    # Update compliance status in DB
    agent.compliance_status = result.status.value
    await db.commit()
    await db.refresh(agent)

    return ComplianceResponse(
        agent_id=agent_id,
        status=result.status.value,
        missing_documents=result.missing_documents,
        errors=result.errors,
        warnings=result.warnings,
    )
