"""Agent service — create agents via forge + persist to DB.

Also provides FCL (Fair Core License) enforcement: max 3 agents on the
free tier, with clear messaging when the limit is reached.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.config import settings
from nomos_api.models import Agent, AuditLog
from nomos.core.forge import forge_agent, _slugify
from nomos.core.hash_chain import HashChain
from nomos.core.compliance_engine import check_compliance
from nomos.core.manifest_validator import load_manifest

# ---------------------------------------------------------------------------
# FCL (Fair Core License) enforcement — 3 agents free
# ---------------------------------------------------------------------------

FCL_MAX_AGENTS = 3


def check_fcl_limit(active_count: int) -> bool:
    """Return True if adding one more agent is allowed under the FCL free tier."""
    return active_count < FCL_MAX_AGENTS


def check_fcl_limit_with_message(active_count: int) -> tuple[bool, str]:
    """Check FCL limit and return (allowed, human-readable message)."""
    allowed = check_fcl_limit(active_count)
    if allowed:
        return True, f"FCL: {active_count}/{FCL_MAX_AGENTS} agents active. You can add more."
    return False, (
        f"FCL: {active_count}/{FCL_MAX_AGENTS} agents active. "
        f"Free license limit reached. Upgrade to add more agents."
    )


@dataclass
class CreateAgentResult:
    """Result of agent creation."""

    success: bool
    agent: Agent | None = None
    error: str = ""


async def create_agent(
    db: AsyncSession,
    name: str,
    role: str,
    company: str,
    email: str,
    risk_class: str = "limited",
) -> CreateAgentResult:
    """Create a new agent: forge directory, check compliance, persist to DB."""
    agents_dir = settings.agents_dir
    agents_dir.mkdir(parents=True, exist_ok=True)

    safe_name = _slugify(name)
    if not safe_name:
        return CreateAgentResult(success=False, error=f"Cannot create safe directory name from: {name!r}")

    forge_result = forge_agent(
        agent_name=name,
        agent_role=role,
        company=company,
        email=email,
        output_dir=agents_dir / safe_name,
        risk_class=risk_class,
    )

    if not forge_result.success:
        return CreateAgentResult(success=False, error=forge_result.error)

    manifest = load_manifest(forge_result.output_dir / "manifest.yaml")
    compliance_result = check_compliance(manifest, forge_result.output_dir / "compliance")

    agent = Agent(
        id=manifest.agent.id,
        name=name,
        role=role,
        company=company,
        email=email,
        risk_class=risk_class,
        status="created",
        manifest_hash=forge_result.manifest_hash,
        manifest_data=manifest.model_dump(mode="json"),
        compliance_status=compliance_result.status.value,
        agents_dir=str(forge_result.output_dir),
    )
    db.add(agent)

    chain = HashChain(storage_dir=forge_result.output_dir / "audit")
    for entry in chain.entries:
        audit_log = AuditLog(
            agent_id=entry.agent_id,
            sequence=entry.sequence,
            event_type=entry.event_type,
            data=entry.data,
            chain_hash=entry.hash,
            timestamp=entry.timestamp,
        )
        db.add(audit_log)

    try:
        await db.commit()
        await db.refresh(agent)
    except Exception as exc:
        await db.rollback()
        return CreateAgentResult(success=False, error=f"Database error: {exc}")

    return CreateAgentResult(success=True, agent=agent)
