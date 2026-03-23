"""Compliance check endpoint."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

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
    agent_dir = Path(agent.agents_dir)
    manifest = load_manifest(agent_dir / "manifest.yaml")
    result = check_compliance(manifest, agent_dir / "compliance")
    return ComplianceResponse(
        agent_id=agent_id,
        status=result.status.value,
        missing_documents=result.missing_documents,
        errors=result.errors,
        warnings=result.warnings,
    )
