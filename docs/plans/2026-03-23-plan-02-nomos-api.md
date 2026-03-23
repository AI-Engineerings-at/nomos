# Plan 2: NomOS API — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI backend that exposes NomOS core functionality (fleet registry, agent creation, compliance checks, audit trail) as a REST API with PostgreSQL persistence.

**Architecture:** The API is a thin HTTP layer over nomos-core. It does NOT duplicate core logic — it imports and calls manifest, forge, compliance_engine, hash_chain, and events. PostgreSQL stores fleet state (which agents exist, their status, manifests). The hash chain JSONL files remain on disk (filesystem = source of truth for audit, DB = index for queries).

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), asyncpg, PostgreSQL 16 + pgvector, Alembic (migrations), pytest + httpx (testing), Docker Compose (API + Postgres)

---

## Prerequisite

Plan 1 must be complete. The following modules must exist and pass all tests:
- `nomos.core.manifest` (AgentManifest, 11 Pydantic models)
- `nomos.core.manifest_validator` (load, validate, hash)
- `nomos.core.hash_chain` (HashChain, verify_chain)
- `nomos.core.events` (EventType, NomOSEvent)
- `nomos.core.compliance_engine` (check_compliance, ComplianceStatus)
- `nomos.core.forge` (forge_agent, ForgeResult)

---

## File Structure

### Files to CREATE

```
nomos-api/
├── pyproject.toml                     # FastAPI + SQLAlchemy + asyncpg deps
├── nomos_api/
│   ├── __init__.py
│   ├── main.py                        # FastAPI app, lifespan, CORS
│   ├── config.py                      # Settings from env vars (Pydantic BaseSettings)
│   ├── database.py                    # SQLAlchemy async engine + session
│   ├── models.py                      # SQLAlchemy ORM models (Agent, AuditEntry)
│   ├── schemas.py                     # Pydantic request/response models (API layer)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py                  # GET /health, GET /readiness
│   │   ├── fleet.py                   # GET /api/fleet, GET /api/fleet/{id}
│   │   ├── agents.py                  # POST /api/agents (create via forge)
│   │   ├── compliance.py              # GET /api/agents/{id}/compliance
│   │   └── audit.py                   # GET /api/agents/{id}/audit, GET /api/audit/verify
│   └── services/
│       ├── __init__.py
│       ├── fleet_service.py           # Fleet CRUD (DB operations)
│       └── agent_service.py           # Agent creation (forge + DB + chain)
├── alembic/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│       └── 001_initial_schema.py      # Initial migration
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Test DB fixtures, async client
│   ├── test_health.py                 # Health endpoint tests
│   ├── test_fleet.py                  # Fleet API tests
│   ├── test_agents.py                 # Agent creation tests
│   ├── test_compliance.py             # Compliance endpoint tests
│   └── test_audit.py                  # Audit endpoint tests
├── Dockerfile                         # Python 3.12 slim, uvicorn
└── docker-compose.yml                 # API + PostgreSQL + Redis (standalone)
```

### Files to MODIFY

```
.github/workflows/ci.yml              # Add test-api job
```

---

## Task 1: Project Setup + Config

**Why:** Every FastAPI project needs proper project config, settings management, and dependency declaration before any code.

**Files:**
- Create: `nomos-api/pyproject.toml`
- Create: `nomos-api/nomos_api/__init__.py`
- Create: `nomos-api/nomos_api/config.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "nomos-api"
version = "0.1.0"
description = "NomOS Fleet API — Agent Lifecycle Management"
requires-python = ">=3.11"
license = {text = "Fair Source"}
authors = [{name = "AI Engineering", email = "kontakt@ai-engineering.at"}]
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.30",
    "alembic>=1.14",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "pyyaml>=6.0",
    "httpx>=0.27",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "httpx>=0.27",
    "aiosqlite>=0.20",
    "ruff>=0.8",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["nomos_api"]

[tool.ruff]
target-version = "py311"
line-length = 120

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 2: Create __init__.py**

```python
"""NomOS Fleet API."""
```

- [ ] **Step 3: Create config.py**

```python
"""NomOS API configuration — all settings from environment variables."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """API settings loaded from environment variables.

    For local dev: set in .env file or docker-compose environment.
    For production: set via Docker secrets or orchestrator.
    """

    # Database
    database_url: str = "postgresql+asyncpg://nomos:nomos@localhost:5432/nomos"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "NomOS Fleet API"
    api_version: str = "0.1.0"
    cors_origins: list[str] = ["http://localhost:3040"]

    # Storage
    agents_dir: Path = Path("./data/agents")

    model_config = {"env_prefix": "NOMOS_", "env_file": ".env", "extra": "ignore"}


settings = Settings()
```

- [ ] **Step 4: Commit**

```bash
cd C:\Users\Legion\Documents\nomos
git add nomos-api/
git commit -m "feat(api): project setup — pyproject.toml, config from env vars

FastAPI + SQLAlchemy async + asyncpg + Alembic.
All settings via NOMOS_ prefixed env vars.
No hardcoded credentials, no internal IPs."
```

---

## Task 2: Database Models + Migration

**Why:** The fleet registry needs persistent storage. SQLAlchemy 2.0 async with proper models and Alembic migrations.

**Files:**
- Create: `nomos-api/nomos_api/database.py`
- Create: `nomos-api/nomos_api/models.py`

- [ ] **Step 1: Create database.py**

```python
"""Database engine and session management."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from nomos_api.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """FastAPI dependency: yield an async database session."""
    async with async_session() as session:
        yield session
```

- [ ] **Step 2: Create models.py**

```python
"""SQLAlchemy ORM models for the NomOS fleet registry."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Agent(Base):
    """An AI agent registered in the NomOS fleet."""

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(256), nullable=False)
    company: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str] = mapped_column(String(256), nullable=False)
    risk_class: Mapped[str] = mapped_column(String(32), nullable=False, default="limited")
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="created",
        comment="created | deployed | stopped | retired",
    )
    manifest_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    manifest_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    compliance_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending",
        comment="pending | passed | warning | blocked",
    )
    agents_dir: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="Path to agent directory on disk (manifest, audit chain, compliance docs)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now(),
    )


class AuditLog(Base):
    """Indexed audit entries for fast queries. Source of truth remains the JSONL chain on disk."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    sequence: Mapped[int] = mapped_column(nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=True)
    chain_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

- [ ] **Step 3: Commit**

```bash
git add nomos-api/nomos_api/database.py nomos-api/nomos_api/models.py
git commit -m "feat(api): database models — Agent + AuditLog with SQLAlchemy 2.0

Agent: fleet registry (id, name, role, status, manifest_hash, compliance_status)
AuditLog: indexed audit entries (source of truth = JSONL chain on disk)
Async engine with asyncpg. No hardcoded credentials."
```

---

## Task 3: API Schemas (Request/Response Models)

**Why:** Clean separation between ORM models (database) and API schemas (HTTP layer). Pydantic models for request validation and response serialization.

**Files:**
- Create: `nomos-api/nomos_api/schemas.py`

- [ ] **Step 1: Create schemas.py**

```python
"""Pydantic schemas for API request/response models.

These are SEPARATE from the ORM models (models.py) and from
nomos-core manifest models. Each layer has its own models.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# --- Requests ---

class AgentCreateRequest(BaseModel):
    """POST /api/agents — create a new agent."""

    name: str = Field(..., min_length=1, max_length=256, examples=["Mani Ruf"])
    role: str = Field(..., min_length=1, max_length=256, examples=["external-secretary"])
    company: str = Field(..., min_length=1, max_length=256, examples=["AI Engineering"])
    email: str = Field(..., examples=["mani@ai-engineering.at"])
    risk_class: str = Field(default="limited", pattern="^(minimal|limited|high)$")


# --- Responses ---

class AgentResponse(BaseModel):
    """Single agent in API responses."""

    id: str
    name: str
    role: str
    company: str
    email: str
    risk_class: str
    status: str
    manifest_hash: str
    compliance_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FleetResponse(BaseModel):
    """GET /api/fleet response."""

    agents: list[AgentResponse]
    total: int


class ComplianceResponse(BaseModel):
    """GET /api/agents/{id}/compliance response."""

    agent_id: str
    status: str
    missing_documents: list[str]
    errors: list[str]
    warnings: list[str]


class AuditEntryResponse(BaseModel):
    """Single audit entry."""

    sequence: int
    event_type: str
    agent_id: str
    data: dict
    chain_hash: str
    timestamp: datetime


class AuditResponse(BaseModel):
    """GET /api/agents/{id}/audit response."""

    agent_id: str
    entries: list[AuditEntryResponse]
    total: int


class AuditVerifyResponse(BaseModel):
    """GET /api/audit/verify/{agent_id} response."""

    agent_id: str
    valid: bool
    entries_checked: int
    errors: list[str]


class HealthResponse(BaseModel):
    """GET /health response."""

    status: str
    service: str
    version: str


class ErrorResponse(BaseModel):
    """Error response body."""

    detail: str
```

- [ ] **Step 2: Commit**

```bash
git add nomos-api/nomos_api/schemas.py
git commit -m "feat(api): request/response schemas — clean API contract

AgentCreateRequest, AgentResponse, FleetResponse, ComplianceResponse,
AuditResponse, AuditVerifyResponse, HealthResponse, ErrorResponse.
Separate from ORM models and nomos-core manifest models."
```

---

## Task 4: Service Layer (Fleet + Agent)

**Why:** Business logic lives in services, not routers. Routers handle HTTP, services handle domain logic + DB operations.

**Files:**
- Create: `nomos-api/nomos_api/services/__init__.py`
- Create: `nomos-api/nomos_api/services/fleet_service.py`
- Create: `nomos-api/nomos_api/services/agent_service.py`

- [ ] **Step 1: Create fleet_service.py**

```python
"""Fleet service — CRUD operations for agent registry."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.models import Agent


async def list_agents(db: AsyncSession) -> list[Agent]:
    """List all agents in the fleet."""
    result = await db.execute(select(Agent).order_by(Agent.created_at.desc()))
    return list(result.scalars().all())


async def get_agent(db: AsyncSession, agent_id: str) -> Agent | None:
    """Get a single agent by ID."""
    return await db.get(Agent, agent_id)


async def update_agent_status(db: AsyncSession, agent_id: str, status: str) -> Agent | None:
    """Update an agent's status."""
    agent = await db.get(Agent, agent_id)
    if agent is None:
        return None
    agent.status = status
    await db.commit()
    await db.refresh(agent)
    return agent
```

- [ ] **Step 2: Create agent_service.py**

```python
"""Agent service — create agents via forge + persist to DB."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.config import settings
from nomos_api.models import Agent, AuditLog

# Import nomos-core (installed as sibling package or via path)
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "nomos-cli"))

from nomos.core.forge import forge_agent, ForgeResult
from nomos.core.hash_chain import HashChain
from nomos.core.compliance_engine import check_compliance, ComplianceStatus
from nomos.core.manifest_validator import load_manifest


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
    # Forge the agent directory
    agents_dir = settings.agents_dir
    agents_dir.mkdir(parents=True, exist_ok=True)

    forge_result = forge_agent(
        agent_name=name,
        agent_role=role,
        company=company,
        email=email,
        output_dir=agents_dir / name.lower().replace(" ", "-"),
        risk_class=risk_class,
    )

    if not forge_result.success:
        return CreateAgentResult(success=False, error=forge_result.error)

    # Load the generated manifest
    manifest = load_manifest(forge_result.output_dir / "manifest.yaml")

    # Check compliance
    compliance_result = check_compliance(manifest, forge_result.output_dir / "compliance")

    # Persist to database
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

    # Index the audit chain entry in DB
    chain = HashChain(storage_dir=forge_result.output_dir / "audit")
    for entry in chain._entries:
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
    await db.refresh(agent)

    return CreateAgentResult(success=True, agent=agent)
```

- [ ] **Step 3: Commit**

```bash
git add nomos-api/nomos_api/services/
git commit -m "feat(api): service layer — fleet CRUD + agent creation via forge

fleet_service: list, get, update_status
agent_service: create_agent() calls forge → compliance check → DB persist
Source of truth: JSONL chain on disk, DB = index for queries."
```

---

## Task 5: Routers (HTTP Endpoints)

**Why:** Thin HTTP handlers that delegate to services. Each router handles one resource.

**Files:**
- Create: `nomos-api/nomos_api/routers/__init__.py`
- Create: `nomos-api/nomos_api/routers/health.py`
- Create: `nomos-api/nomos_api/routers/fleet.py`
- Create: `nomos-api/nomos_api/routers/agents.py`
- Create: `nomos-api/nomos_api/routers/compliance.py`
- Create: `nomos-api/nomos_api/routers/audit.py`

- [ ] **Step 1: Create health.py**

```python
"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from nomos_api.config import settings
from nomos_api.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.api_title,
        version=settings.api_version,
    )
```

- [ ] **Step 2: Create fleet.py**

```python
"""Fleet endpoints — list and get agents."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.database import get_db
from nomos_api.schemas import AgentResponse, FleetResponse
from nomos_api.services.fleet_service import get_agent, list_agents

router = APIRouter(prefix="/api", tags=["fleet"])


@router.get("/fleet", response_model=FleetResponse)
async def get_fleet(db: AsyncSession = Depends(get_db)) -> FleetResponse:
    agents = await list_agents(db)
    return FleetResponse(
        agents=[AgentResponse.model_validate(a) for a in agents],
        total=len(agents),
    )


@router.get("/fleet/{agent_id}", response_model=AgentResponse)
async def get_fleet_agent(agent_id: str, db: AsyncSession = Depends(get_db)) -> AgentResponse:
    agent = await get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    return AgentResponse.model_validate(agent)
```

- [ ] **Step 3: Create agents.py**

```python
"""Agent creation endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.database import get_db
from nomos_api.schemas import AgentCreateRequest, AgentResponse
from nomos_api.services.agent_service import create_agent

router = APIRouter(prefix="/api", tags=["agents"])


@router.post("/agents", response_model=AgentResponse, status_code=201)
async def create_new_agent(
    request: AgentCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    result = await create_agent(
        db=db,
        name=request.name,
        role=request.role,
        company=request.company,
        email=request.email,
        risk_class=request.risk_class,
    )
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return AgentResponse.model_validate(result.agent)
```

- [ ] **Step 4: Create compliance.py**

```python
"""Compliance check endpoint."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.database import get_db
from nomos_api.schemas import ComplianceResponse
from nomos_api.services.fleet_service import get_agent

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "nomos-cli"))

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
```

- [ ] **Step 5: Create audit.py**

```python
"""Audit trail endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.database import get_db
from nomos_api.models import AuditLog
from nomos_api.schemas import AuditEntryResponse, AuditResponse, AuditVerifyResponse
from nomos_api.services.fleet_service import get_agent

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "nomos-cli"))

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

    result = await db.execute(
        select(AuditLog).where(AuditLog.agent_id == agent_id).order_by(AuditLog.sequence)
    )
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


@router.get("/audit/verify/{agent_id}", response_model=AuditVerifyResponse)
async def verify_agent_audit(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
) -> AuditVerifyResponse:
    agent = await get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")

    agent_dir = Path(agent.agents_dir)
    result = verify_chain(agent_dir / "audit")

    return AuditVerifyResponse(
        agent_id=agent_id,
        valid=result.valid,
        entries_checked=result.entries_checked,
        errors=result.errors,
    )
```

- [ ] **Step 6: Commit**

```bash
git add nomos-api/nomos_api/routers/
git commit -m "feat(api): routers — health, fleet, agents, compliance, audit

GET /health — service status
GET /api/fleet — all agents
GET /api/fleet/{id} — single agent
POST /api/agents — create via forge
GET /api/agents/{id}/compliance — compliance check
GET /api/agents/{id}/audit — audit trail
GET /api/audit/verify/{id} — cryptographic chain verification"
```

---

## Task 6: FastAPI App + CORS + Lifespan

**Why:** Wire everything together. Lifespan creates DB tables on startup.

**Files:**
- Create: `nomos-api/nomos_api/main.py`

- [ ] **Step 1: Create main.py**

```python
"""NomOS Fleet API — FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from nomos_api.config import settings
from nomos_api.database import engine
from nomos_api.models import Base
from nomos_api.routers import agents, audit, compliance, fleet, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup, dispose engine on shutdown."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(fleet.router)
app.include_router(agents.router)
app.include_router(compliance.router)
app.include_router(audit.router)
```

- [ ] **Step 2: Commit**

```bash
git add nomos-api/nomos_api/main.py
git commit -m "feat(api): FastAPI app — lifespan, CORS, all routers wired

Creates DB tables on startup, disposes engine on shutdown.
CORS configured for console at localhost:3040."
```

---

## Task 7: Docker Compose (Standalone)

**Why:** `docker compose up` must work for customers. API + PostgreSQL + Redis, no internal dependencies.

**Files:**
- Create: `nomos-api/Dockerfile`
- Create: `nomos-api/docker-compose.yml`

- [ ] **Step 1: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy and install dependencies
COPY pyproject.toml ./
RUN uv pip install --system -e ".[dev]"

# Copy nomos-core (needed by API)
COPY ../nomos-cli /app/nomos-cli
ENV PYTHONPATH="/app/nomos-cli:${PYTHONPATH}"

# Copy API code
COPY nomos_api/ ./nomos_api/

EXPOSE 8000

CMD ["uvicorn", "nomos_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Create docker-compose.yml**

```yaml
services:
  nomos-api:
    build:
      context: ..
      dockerfile: nomos-api/Dockerfile
    ports:
      - "${NOMOS_API_PORT:-8060}:8000"
    environment:
      - NOMOS_DATABASE_URL=postgresql+asyncpg://nomos:${NOMOS_DB_PASSWORD:-nomos}@postgres:5432/nomos
      - NOMOS_AGENTS_DIR=/data/agents
    volumes:
      - nomos-agents:/data/agents
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"]
      interval: 10s
      timeout: 5s
      retries: 3

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_DB=nomos
      - POSTGRES_USER=nomos
      - POSTGRES_PASSWORD=${NOMOS_DB_PASSWORD:-nomos}
    volumes:
      - nomos-pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nomos"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:8-alpine
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  nomos-pgdata:
  nomos-agents:
```

- [ ] **Step 3: Create .env.example**

```bash
# NomOS API Configuration
NOMOS_DB_PASSWORD=change-me-in-production
NOMOS_API_PORT=8060
NOMOS_CORS_ORIGINS=["http://localhost:3040"]
```

- [ ] **Step 4: Verify no internal IPs (R12)**

```bash
grep -r "10.40.10" nomos-api/ || echo "R12: CLEAN"
```

- [ ] **Step 5: Commit**

```bash
git add nomos-api/Dockerfile nomos-api/docker-compose.yml nomos-api/.env.example
git commit -m "feat(api): Docker Compose — standalone API + PostgreSQL + Redis

docker compose up starts everything. No internal IP dependencies.
DB password via env var (default for dev, change for production).
Volumes for persistent data (agents + postgres)."
```

---

## Task 8: Tests (conftest + all endpoints)

**Why:** A senior dev tests every endpoint. Integration tests against a real (SQLite async) database.

**Files:**
- Create: `nomos-api/tests/__init__.py`
- Create: `nomos-api/tests/conftest.py`
- Create: `nomos-api/tests/test_health.py`
- Create: `nomos-api/tests/test_fleet.py`
- Create: `nomos-api/tests/test_agents.py`

- [ ] **Step 1: Create conftest.py**

```python
"""Test fixtures — async SQLite database + HTTPX test client."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from nomos_api.models import Base

# Use SQLite for tests (no PostgreSQL dependency in CI)
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(db_engine, tmp_path):
    """HTTPX async test client with patched DB and agents_dir."""
    from nomos_api.database import get_db
    from nomos_api.main import app

    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with patch("nomos_api.config.settings.agents_dir", tmp_path / "agents"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac

    app.dependency_overrides.clear()
```

- [ ] **Step 2: Create test_health.py**

```python
"""Tests for health endpoint."""

from __future__ import annotations

import pytest


class TestHealth:
    async def test_health_returns_ok(self, client) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "NomOS Fleet API"
        assert "version" in data
```

- [ ] **Step 3: Create test_fleet.py**

```python
"""Tests for fleet endpoints."""

from __future__ import annotations

import pytest


class TestFleet:
    async def test_empty_fleet(self, client) -> None:
        response = await client.get("/api/fleet")
        assert response.status_code == 200
        data = response.json()
        assert data["agents"] == []
        assert data["total"] == 0

    async def test_fleet_after_agent_created(self, client) -> None:
        # Create an agent first
        await client.post("/api/agents", json={
            "name": "Test Agent",
            "role": "test-role",
            "company": "Test Co",
            "email": "test@test.com",
        })
        response = await client.get("/api/fleet")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["agents"][0]["name"] == "Test Agent"

    async def test_get_nonexistent_agent(self, client) -> None:
        response = await client.get("/api/fleet/nonexistent")
        assert response.status_code == 404
```

- [ ] **Step 4: Create test_agents.py**

```python
"""Tests for agent creation endpoint."""

from __future__ import annotations

import pytest


class TestCreateAgent:
    async def test_create_agent_success(self, client) -> None:
        response = await client.post("/api/agents", json={
            "name": "Mani Ruf",
            "role": "external-secretary",
            "company": "AI Engineering",
            "email": "mani@ai-engineering.at",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Mani Ruf"
        assert data["role"] == "external-secretary"
        assert data["status"] == "created"
        assert len(data["manifest_hash"]) == 64

    async def test_create_agent_invalid_name(self, client) -> None:
        response = await client.post("/api/agents", json={
            "name": "",
            "role": "test",
            "company": "Co",
            "email": "t@t.com",
        })
        assert response.status_code == 422  # Pydantic validation error

    async def test_create_duplicate_agent(self, client) -> None:
        agent_data = {
            "name": "Duplicate",
            "role": "test",
            "company": "Co",
            "email": "t@t.com",
        }
        await client.post("/api/agents", json=agent_data)
        response = await client.post("/api/agents", json=agent_data)
        assert response.status_code == 400  # Directory already exists

    async def test_create_agent_returns_in_fleet(self, client) -> None:
        await client.post("/api/agents", json={
            "name": "Fleet Agent",
            "role": "test",
            "company": "Co",
            "email": "t@t.com",
        })
        response = await client.get("/api/fleet")
        assert response.json()["total"] == 1
        assert response.json()["agents"][0]["id"] == "fleet-agent"
```

- [ ] **Step 5: Run tests**

Run: `cd C:\Users\Legion\Documents\nomos\nomos-api && uv sync && uv run pytest -v --tb=short`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add nomos-api/tests/
git commit -m "test(api): integration tests — health, fleet, agents

conftest: async SQLite + HTTPX test client with patched DB
test_health: status, service name, version
test_fleet: empty fleet, fleet after creation, 404
test_agents: create success, invalid name, duplicate, fleet integration"
```

---

## Task 9: CI Update + Final Verification

**Why:** CI must include the API tests. Push everything.

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Add test-api job to CI**

Add after test-cli:
```yaml
  test-api:
    name: Test API
    runs-on: ubuntu-latest
    needs: lint-python
    defaults:
      run:
        working-directory: nomos-api
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          python-version: "3.12"
      - run: uv sync --extra dev
      - run: PYTHONPATH="../nomos-cli:$PYTHONPATH" uv run pytest -v --tb=short
```

Also add lint for nomos-api in the lint job.

- [ ] **Step 2: Run ALL tests (both packages)**

```bash
cd C:\Users\Legion\Documents\nomos\nomos-cli && uv run pytest -v --tb=short
cd C:\Users\Legion\Documents\nomos\nomos-api && uv run pytest -v --tb=short
```

- [ ] **Step 3: R12 + S9 checks**

```bash
grep -r "10.40.10" nomos-api/ nomos-cli/ || echo "R12: CLEAN"
grep -r "coming soon\|TODO\|FIXME\|placeholder" nomos-api/nomos_api/ || echo "S9: CLEAN"
```

- [ ] **Step 4: Commit + Push**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add test-api job — lint + integration tests for API

PYTHONPATH includes nomos-cli for core imports.
SQLite async for test DB (no PostgreSQL in CI)."
git push origin main
```

---

## Summary

After Plan 2 completion:

| Component | Endpoints | Tests |
|-----------|-----------|-------|
| Health | GET /health | 1 |
| Fleet | GET /api/fleet, GET /api/fleet/{id} | 3 |
| Agents | POST /api/agents | 4 |
| Compliance | GET /api/agents/{id}/compliance | (Plan 3) |
| Audit | GET /api/agents/{id}/audit, GET /api/audit/verify/{id} | (Plan 3) |
| **nomos-core** | (from Plan 1) | 61 |

**What's next:** Plan 3 (NomOS Compliance Gate) builds on this API to provide the Streamlit wizard.
