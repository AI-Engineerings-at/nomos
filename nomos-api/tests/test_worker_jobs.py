"""Tests for ARQ background worker jobs.

All tests use in-memory SQLite — no Valkey required.
Jobs are called as plain async functions (ARQ context is mocked).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

from nomos_api.models import Agent, AgentMemory, Approval, Base, IncidentRecord


@pytest.fixture
async def worker_engine():
    """In-memory SQLite engine for worker job tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def worker_session_factory(worker_engine):
    """Session factory for worker tests."""
    return async_sessionmaker(worker_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def worker_session(worker_session_factory):
    """Single session for assertions."""
    async with worker_session_factory() as session:
        yield session


def _make_agent(
    agent_id: str = "agent-001",
    status: str = "running",
    heartbeat_at: datetime | None = None,
) -> Agent:
    """Create an Agent ORM instance for testing."""
    return Agent(
        id=agent_id,
        name="Test Agent",
        role="assistant",
        company="TestCo",
        email="test@test.com",
        risk_class="limited",
        status=status,
        manifest_hash="a" * 64,
        manifest_data={"name": "test"},
        compliance_status="passed",
        agents_dir="/data/agents/test",
        budget_used_eur=0.0,
        budget_limit_eur=50.0,
        heartbeat_at=heartbeat_at,
    )


def _make_memory(
    agent_id: str = "agent-001",
    created_at: datetime | None = None,
) -> AgentMemory:
    """Create an AgentMemory ORM instance for testing."""
    return AgentMemory(
        agent_id=agent_id,
        session_id="sess-001",
        role="user",
        content="Hello, world!",
        created_at=created_at or datetime.now(timezone.utc),
    )


def _make_incident(
    agent_id: str = "agent-001",
    status: str = "detected",
    report_deadline: str | None = None,
) -> IncidentRecord:
    """Create an IncidentRecord ORM instance for testing."""
    if report_deadline is None:
        deadline = datetime.now(timezone.utc) + timedelta(hours=72)
        report_deadline = deadline.isoformat()
    return IncidentRecord(
        agent_id=agent_id,
        incident_type="data_breach",
        description="Test incident",
        severity="high",
        status=status,
        detected_at=datetime.now(timezone.utc).isoformat(),
        report_deadline=report_deadline,
    )


def _make_approval(
    agent_id: str = "agent-001",
    status: str = "pending",
    requested_at: datetime | None = None,
    timeout_minutes: int = 60,
) -> Approval:
    """Create an Approval ORM instance for testing."""
    return Approval(
        id=f"appr-{agent_id}-{timeout_minutes}",
        agent_id=agent_id,
        action="deploy",
        description="Test approval",
        status=status,
        requested_at=requested_at or datetime.now(timezone.utc),
        timeout_minutes=timeout_minutes,
    )


# ─── Job 1: Retention ────────────────────────────────────────────


async def test_retention_deletes_old_messages(worker_session_factory: async_sessionmaker) -> None:
    """Messages older than retention_days are deleted."""
    from nomos_api.worker.jobs.retention import retention_cleanup

    old_date = datetime.now(timezone.utc) - timedelta(days=400)
    async with worker_session_factory() as session:
        session.add(_make_memory(created_at=old_date))
        await session.commit()

    await retention_cleanup(None, session_factory=worker_session_factory, retention_days=365)

    async with worker_session_factory() as session:
        result = await session.execute(select(AgentMemory))
        remaining = result.scalars().all()
    assert len(remaining) == 0


async def test_retention_keeps_recent_messages(worker_session_factory: async_sessionmaker) -> None:
    """Messages within retention window are kept."""
    from nomos_api.worker.jobs.retention import retention_cleanup

    recent_date = datetime.now(timezone.utc) - timedelta(days=100)
    async with worker_session_factory() as session:
        session.add(_make_memory(created_at=recent_date))
        await session.commit()

    await retention_cleanup(None, session_factory=worker_session_factory, retention_days=365)

    async with worker_session_factory() as session:
        result = await session.execute(select(AgentMemory))
        remaining = result.scalars().all()
    assert len(remaining) == 1


# ─── Job 2: Heartbeat / Stale Detection ─────────────────────────


async def test_stale_detection_marks_agent(worker_session_factory: async_sessionmaker) -> None:
    """Agent with old heartbeat is marked stale."""
    from nomos_api.worker.jobs.heartbeat import detect_stale_agents

    old_heartbeat = datetime.now(timezone.utc) - timedelta(minutes=15)
    async with worker_session_factory() as session:
        session.add(_make_agent(heartbeat_at=old_heartbeat))
        await session.commit()

    await detect_stale_agents(None, session_factory=worker_session_factory, stale_threshold_minutes=10)

    async with worker_session_factory() as session:
        result = await session.execute(select(Agent).where(Agent.id == "agent-001"))
        agent = result.scalar_one()
    assert agent.status == "stale"


async def test_stale_detection_ignores_active(worker_session_factory: async_sessionmaker) -> None:
    """Agent with fresh heartbeat stays running."""
    from nomos_api.worker.jobs.heartbeat import detect_stale_agents

    fresh_heartbeat = datetime.now(timezone.utc) - timedelta(minutes=2)
    async with worker_session_factory() as session:
        session.add(_make_agent(heartbeat_at=fresh_heartbeat))
        await session.commit()

    await detect_stale_agents(None, session_factory=worker_session_factory, stale_threshold_minutes=10)

    async with worker_session_factory() as session:
        result = await session.execute(select(Agent).where(Agent.id == "agent-001"))
        agent = result.scalar_one()
    assert agent.status == "running"


# ─── Job 3: Incident Escalation ─────────────────────────────────


async def test_incident_escalation(worker_session_factory: async_sessionmaker) -> None:
    """Incident near deadline is escalated."""
    from nomos_api.worker.jobs.incidents import check_incident_deadlines

    # Deadline in 3 hours (< 4h threshold)
    near_deadline = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
    async with worker_session_factory() as session:
        session.add(_make_incident(report_deadline=near_deadline))
        await session.commit()

    await check_incident_deadlines(None, session_factory=worker_session_factory)

    async with worker_session_factory() as session:
        result = await session.execute(select(IncidentRecord))
        incident = result.scalar_one()
    assert incident.status == "escalated"


async def test_incident_overdue(worker_session_factory: async_sessionmaker) -> None:
    """Incident past deadline is marked overdue."""
    from nomos_api.worker.jobs.incidents import check_incident_deadlines

    past_deadline = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    async with worker_session_factory() as session:
        session.add(_make_incident(report_deadline=past_deadline))
        await session.commit()

    await check_incident_deadlines(None, session_factory=worker_session_factory)

    async with worker_session_factory() as session:
        result = await session.execute(select(IncidentRecord))
        incident = result.scalar_one()
    assert incident.status == "overdue"


# ─── Job 4: Approval Expiry ─────────────────────────────────────


async def test_approval_expiry(worker_session_factory: async_sessionmaker) -> None:
    """Pending approval past timeout is expired."""
    from nomos_api.worker.jobs.approvals import expire_approvals

    old_request = datetime.now(timezone.utc) - timedelta(minutes=120)
    async with worker_session_factory() as session:
        session.add(_make_approval(requested_at=old_request, timeout_minutes=60))
        await session.commit()

    await expire_approvals(None, session_factory=worker_session_factory)

    async with worker_session_factory() as session:
        result = await session.execute(select(Approval))
        approval = result.scalar_one()
    assert approval.status == "expired"


async def test_approval_keeps_recent(worker_session_factory: async_sessionmaker) -> None:
    """Fresh pending approval stays pending."""
    from nomos_api.worker.jobs.approvals import expire_approvals

    recent_request = datetime.now(timezone.utc) - timedelta(minutes=10)
    async with worker_session_factory() as session:
        session.add(_make_approval(requested_at=recent_request, timeout_minutes=60))
        await session.commit()

    await expire_approvals(None, session_factory=worker_session_factory)

    async with worker_session_factory() as session:
        result = await session.execute(select(Approval))
        approval = result.scalar_one()
    assert approval.status == "pending"


# ─── Idempotency ─────────────────────────────────────────────────


async def test_all_jobs_idempotent(worker_session_factory: async_sessionmaker) -> None:
    """Running each job twice produces no errors and correct final state."""
    from nomos_api.worker.jobs.approvals import expire_approvals
    from nomos_api.worker.jobs.heartbeat import detect_stale_agents
    from nomos_api.worker.jobs.incidents import check_incident_deadlines
    from nomos_api.worker.jobs.retention import retention_cleanup

    old_date = datetime.now(timezone.utc) - timedelta(days=400)
    old_heartbeat = datetime.now(timezone.utc) - timedelta(minutes=15)
    past_deadline = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    old_request = datetime.now(timezone.utc) - timedelta(minutes=120)

    async with worker_session_factory() as session:
        session.add(_make_memory(created_at=old_date))
        session.add(_make_agent(agent_id="agent-idem", heartbeat_at=old_heartbeat))
        session.add(_make_incident(agent_id="agent-idem", report_deadline=past_deadline))
        session.add(_make_approval(agent_id="agent-idem", requested_at=old_request, timeout_minutes=60))
        await session.commit()

    # Run each job twice
    for _ in range(2):
        await retention_cleanup(None, session_factory=worker_session_factory, retention_days=365)
        await detect_stale_agents(None, session_factory=worker_session_factory, stale_threshold_minutes=10)
        await check_incident_deadlines(None, session_factory=worker_session_factory)
        await expire_approvals(None, session_factory=worker_session_factory)

    async with worker_session_factory() as session:
        memories = (await session.execute(select(AgentMemory))).scalars().all()
        agent = (await session.execute(select(Agent).where(Agent.id == "agent-idem"))).scalar_one()
        incident = (await session.execute(select(IncidentRecord))).scalar_one()
        approval = (await session.execute(select(Approval))).scalar_one()

    assert len(memories) == 0
    assert agent.status == "stale"
    assert incident.status == "overdue"
    assert approval.status == "expired"
