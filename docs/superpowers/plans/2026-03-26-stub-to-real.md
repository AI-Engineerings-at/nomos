# Stub-Services zu echtem Code — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Alle 7 In-Memory-Fake-Services auf echte DB-backed Implementierungen umstellen. Kein Dict, kein Singleton, kein Reset bei Restart.

**Architecture:** Jeder Service bekommt `db: AsyncSession` als Dependency (FastAPI `Depends(get_db)`). Alle Writes gehen in die bestehenden ORM Models (Agent, Approval, Task, ConfigRevision, AuditLog). Fuer Agent-Memory wird ein neues Model `AgentMemory` erstellt. Pattern: exakt wie `create_agent()` in `agent_service.py` und `pause_agent()` in `routers/agents.py`.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 async, Pydantic v2, pytest + pytest-asyncio, aiosqlite (Tests)

**Konvention:** Jeder Service ist eine Sammlung von async Funktionen (kein Class mit `self._dict`). Router injiziert `db: AsyncSession = Depends(get_db)`.

---

## Referenz: Das korrekte DB-Pattern

Bevor du irgendetwas schreibst, lies diese Dateien — sie zeigen wie es richtig geht:

- `nomos-api/nomos_api/services/agent_service.py` — `create_agent(db, ...)` Pattern
- `nomos-api/nomos_api/routers/agents.py:pause_agent()` — Router mit `db: AsyncSession = Depends(get_db)`
- `nomos-api/nomos_api/routers/agents.py:_write_audit_event()` — Audit Trail schreiben
- `nomos-api/tests/conftest.py` — Test-Fixture mit async SQLite in-memory DB
- `nomos-api/nomos_api/models.py` — Alle ORM Models
- `nomos-api/nomos_api/schemas.py` — Alle Pydantic Schemas

---

## File Map

### Neue Dateien
| Datei | Verantwortung |
|---|---|
| `nomos-api/nomos_api/models.py` (modify) | Neues Model `AgentMemory` hinzufuegen (Task 4) |
| `nomos-api/nomos_api/schemas.py` (modify) | `BudgetTrackRequest`, `BudgetTrackResponse` hinzufuegen (Task 1) |
| `nomos-api/nomos_api/services/audit.py` (create) | `_write_audit_event` aus `routers/agents.py` extrahieren (Task 0) |

### Zu aendernde Dateien (Service → DB)
| Datei | Alt (Fake) | Neu (Echt) |
|---|---|---|
| `services/budget.py` | In-memory `_costs` dict | Async Funktionen, liest/schreibt `Agent.budget_used_eur` |
| `services/heartbeat.py` | In-memory `_last_seen` dict | Async Funktionen, schreibt `Agent.heartbeat_at` |
| `services/approval.py` | In-memory `_approvals` dict | Async Funktionen, nutzt `Approval` ORM Model |
| `services/honcho.py` | In-memory fake HonchoClient | Async Funktionen, nutzt neues `AgentMemory` Model |
| `services/forget.py` | Wrapper um fake HonchoClient | Async Funktionen, loescht aus DB + schreibt Audit |

### Zu aendernde Dateien (Router → DB Dependency)
| Datei | Aenderung |
|---|---|
| `routers/budget.py` | `db: AsyncSession = Depends(get_db)` statt Singleton |
| `routers/costs.py` | Query `Agent.budget_used_eur` aus DB |
| `routers/approvals.py` | `db: AsyncSession = Depends(get_db)` statt Singleton |
| `routers/dsgvo.py` | `db: AsyncSession = Depends(get_db)` statt Singleton |
| `routers/agents.py` | Heartbeat-Endpoint: `db` nutzen statt HeartbeatService |

### Zu aendernde Tests
| Datei | Aenderung |
|---|---|
| `tests/test_budget.py` | Von Unit-Test auf Integration-Test (`client` Fixture) |
| `tests/test_heartbeat.py` | Von Unit-Test auf Integration-Test |
| `tests/test_approvals.py` | Von Unit-Test auf Integration-Test |
| `tests/test_honcho_client.py` | Von Unit-Test auf Integration-Test (neues Model) |
| `tests/test_forget.py` | Von Unit-Test auf Integration-Test |
| `tests/test_workspace.py` | Anpassen an neuen Memory-Service |

---

## Task 0: Vorbereitungen — Schemas + Audit-Extraktion

**Ziel:** Fehlende Schemas anlegen und `_write_audit_event` aus `routers/agents.py` in eigenen Service extrahieren (verhindert Circular Imports wenn andere Router es brauchen).

**Files:**
- Modify: `nomos-api/nomos_api/schemas.py`
- Create: `nomos-api/nomos_api/services/audit.py`
- Modify: `nomos-api/nomos_api/routers/agents.py` (import umbiegen)

- [ ] **Step 1: Schemas in schemas.py hinzufuegen**

```python
# Am Ende von schemas.py hinzufuegen:

class BudgetTrackRequest(BaseModel):
    agent_id: str
    cost: float

class BudgetTrackResponse(BaseModel):
    agent_id: str
    budget_used_eur: float
    budget_limit_eur: float
```

- [ ] **Step 2: `_write_audit_event` aus agents.py extrahieren nach services/audit.py**

```python
# nomos-api/nomos_api/services/audit.py
"""Audit service — extracted from routers/agents.py for reuse."""
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from nomos_api.models import Agent, AuditLog
from nomos_api.settings import settings
# Importiere HashChain aus nomos-cli
from nomos.core.hash_chain import HashChain


async def write_audit_event(
    db: AsyncSession, agent: Agent, agent_id: str, event_type: str, data: dict | None = None
) -> None:
    """Write audit event to hash chain on disk + AuditLog in DB."""
    chain_dir = Path(settings.agents_dir) / agent_id
    chain_dir.mkdir(parents=True, exist_ok=True)
    chain = HashChain(str(chain_dir / "audit.jsonl"))
    entry = chain.append(event_type=event_type, data=data or {})

    audit_log = AuditLog(
        agent_id=agent_id,
        sequence=entry.sequence,
        event_type=event_type,
        data=data,
        chain_hash=entry.hash,
        timestamp=entry.timestamp,
    )
    db.add(audit_log)
    await db.commit()
```

- [ ] **Step 3: In agents.py den Import umbiegen**

Ersetze `_write_audit_event` Definition durch:
```python
from nomos_api.services.audit import write_audit_event as _write_audit_event
```

- [ ] **Step 4: Alle bestehenden Tests ausfuehren — muessen weiterhin PASS**

Run: `cd nomos-api && python -m pytest tests/ -v --tb=short`

- [ ] **Step 5: Commit**

```bash
git add nomos-api/nomos_api/schemas.py nomos-api/nomos_api/services/audit.py \
       nomos-api/nomos_api/routers/agents.py
git commit -m "refactor: extract audit service, add budget schemas"
```

---

## Task 1: Budget Service — DB-backed

**Ziel:** Budget-Tracking liest/schreibt `Agent.budget_used_eur` und `Agent.budget_limit_eur` aus der DB. Kein In-Memory Dict.

**Files:**
- Rewrite: `nomos-api/nomos_api/services/budget.py`
- Rewrite: `nomos-api/nomos_api/routers/budget.py`
- Rewrite: `nomos-api/nomos_api/routers/costs.py`
- Rewrite: `nomos-api/tests/test_budget.py`

- [ ] **Step 1: Test schreiben — budget check liest aus DB**

```python
# tests/test_budget_db.py
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio

async def test_budget_check_reads_from_db(client: AsyncClient):
    """Budget check should read agent's budget_used_eur and budget_limit_eur from DB."""
    # Create agent (budget_limit_eur defaults to 50.0 in model)
    r = await client.post("/api/agents", json={
        "name": "budget-test", "role": "test", "company": "TestCo",
        "email": "b@test.de", "risk_class": "limited"
    })
    assert r.status_code == 201
    agent_id = r.json()["id"]

    # Check budget — should be allowed (0 of 50 used)
    r = await client.post("/api/budget/check", json={
        "agent_id": agent_id, "estimated_cost": 10.0
    })
    assert r.status_code == 200
    data = r.json()
    assert data["allowed"] is True
    assert data["remaining"] == 50.0
    assert data["status"] == "normal"


async def test_budget_check_exceeded(client: AsyncClient):
    """Budget check should deny when usage exceeds limit."""
    r = await client.post("/api/agents", json={
        "name": "budget-exceed", "role": "test", "company": "TestCo",
        "email": "be@test.de", "risk_class": "limited"
    })
    agent_id = r.json()["id"]

    # Exceed: estimated 60 > limit 50
    r = await client.post("/api/budget/check", json={
        "agent_id": agent_id, "estimated_cost": 60.0
    })
    data = r.json()
    assert data["allowed"] is False
    assert data["status"] == "exceeded"


async def test_budget_check_warning(client: AsyncClient):
    """Budget check should warn at 80% threshold."""
    r = await client.post("/api/agents", json={
        "name": "budget-warn", "role": "test", "company": "TestCo",
        "email": "bw@test.de", "risk_class": "limited"
    })
    agent_id = r.json()["id"]

    # Set agent budget_used to 42 (84% of 50) via DB
    # We test this through the track endpoint
    r = await client.post("/api/budget/track", json={
        "agent_id": agent_id, "cost": 42.0
    })
    assert r.status_code == 200

    r = await client.post("/api/budget/check", json={
        "agent_id": agent_id, "estimated_cost": 1.0
    })
    data = r.json()
    assert data["allowed"] is True
    assert data["status"] == "warning"


async def test_budget_check_unknown_agent(client: AsyncClient):
    """Budget check for unknown agent returns 404."""
    r = await client.post("/api/budget/check", json={
        "agent_id": "nonexistent", "estimated_cost": 10.0
    })
    assert r.status_code == 404


async def test_budget_track_persists(client: AsyncClient):
    """Tracked costs should persist in Agent.budget_used_eur."""
    r = await client.post("/api/agents", json={
        "name": "budget-track", "role": "test", "company": "TestCo",
        "email": "bt@test.de", "risk_class": "limited"
    })
    agent_id = r.json()["id"]

    # Track 25 EUR
    r = await client.post("/api/budget/track", json={
        "agent_id": agent_id, "cost": 25.0
    })
    assert r.status_code == 200
    assert r.json()["budget_used_eur"] == 25.0

    # Track another 10 EUR
    r = await client.post("/api/budget/track", json={
        "agent_id": agent_id, "cost": 10.0
    })
    assert r.json()["budget_used_eur"] == 35.0
```

- [ ] **Step 2: Test ausfuehren — muss FAIL**

Run: `cd nomos-api && python -m pytest tests/test_budget_db.py -v`
Expected: FAIL (alte Endpoints geben kein 404 fuer unbekannte Agents, kein /api/budget/track)

- [ ] **Step 3: Service umschreiben — async Funktionen mit DB**

```python
# nomos-api/nomos_api/services/budget.py
"""Budget service — DB-backed, reads/writes Agent.budget_used_eur."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.models import Agent


async def check_budget(
    db: AsyncSession, agent_id: str, estimated_cost: float, warn_at: float = 80.0
) -> dict:
    """Check if agent can spend estimated_cost within their budget."""
    agent = await db.get(Agent, agent_id)
    if agent is None:
        return None  # Router handles 404

    current = agent.budget_used_eur or 0.0
    limit = agent.budget_limit_eur or 50.0
    projected = current + estimated_cost
    percent_used = (projected / limit * 100) if limit > 0 else 100.0

    if projected >= limit:
        status = "exceeded"
        allowed = False
    elif percent_used >= warn_at:
        status = "warning"
        allowed = True
    else:
        status = "normal"
        allowed = True

    return {
        "allowed": allowed,
        "status": status,
        "remaining": max(0.0, limit - current),
        "percent_used": round(min(percent_used, 100.0), 1),
        "current": current,
        "limit": limit,
        "agent_id": agent_id,
    }


async def track_cost(db: AsyncSession, agent_id: str, cost: float) -> dict | None:
    """Add cost to agent's budget_used_eur. Returns updated values or None if not found."""
    agent = await db.get(Agent, agent_id)
    if agent is None:
        return None

    agent.budget_used_eur = (agent.budget_used_eur or 0.0) + cost
    await db.commit()
    await db.refresh(agent)

    return {
        "agent_id": agent_id,
        "budget_used_eur": agent.budget_used_eur,
        "budget_limit_eur": agent.budget_limit_eur,
    }


async def get_all_costs(db: AsyncSession) -> list[dict]:
    """Get budget overview for all agents."""
    result = await db.execute(select(Agent))
    agents = result.scalars().all()

    costs = []
    for agent in agents:
        current = agent.budget_used_eur or 0.0
        limit = agent.budget_limit_eur or 50.0
        percent = (current / limit * 100) if limit > 0 else 0.0
        if percent >= 100:
            status = "exceeded"
        elif percent >= 80:
            status = "warning"
        else:
            status = "normal"

        costs.append({
            "agent_id": agent.id,
            "total_cost_eur": current,
            "budget_limit_eur": limit,
            "budget_status": status,
            "percent_used": round(min(percent, 100.0), 1),
        })

    return costs
```

- [ ] **Step 4: Router umschreiben**

```python
# nomos-api/nomos_api/routers/budget.py
"""Budget router — DB-backed."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.database import get_db
from nomos_api.schemas import BudgetCheckRequest, BudgetCheckResponse
from nomos_api.services.budget import check_budget, track_cost

router = APIRouter(tags=["budget"])


@router.post("/api/budget/check")
async def budget_check(request: BudgetCheckRequest, db: AsyncSession = Depends(get_db)):
    result = await check_budget(db, request.agent_id, request.estimated_cost)
    if result is None:
        raise HTTPException(404, detail="Agent not found")
    return result


@router.post("/api/budget/track")
async def budget_track(request: dict, db: AsyncSession = Depends(get_db)):
    result = await track_cost(db, request["agent_id"], request["cost"])
    if result is None:
        raise HTTPException(404, detail="Agent not found")
    return result
```

```python
# nomos-api/nomos_api/routers/costs.py
"""Costs router — reads from DB."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.database import get_db
from nomos_api.models import Agent
from nomos_api.schemas import CostResponse, CostOverviewResponse
from nomos_api.services.budget import get_all_costs

router = APIRouter(tags=["costs"])


@router.get("/api/costs", response_model=CostOverviewResponse)
async def get_costs(db: AsyncSession = Depends(get_db)):
    costs = await get_all_costs(db)
    return CostOverviewResponse(
        costs=[CostResponse(**c) for c in costs],
        total=len(costs),
    )


@router.get("/api/costs/{agent_id}")
async def get_agent_cost(agent_id: str, db: AsyncSession = Depends(get_db)):
    agent = await db.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(404, detail="Agent not found")
    return CostResponse(
        agent_id=agent.id,
        total_cost_eur=agent.budget_used_eur or 0.0,
        budget_limit_eur=agent.budget_limit_eur or 50.0,
        budget_status="normal",
        percent_used=round(
            ((agent.budget_used_eur or 0.0) / (agent.budget_limit_eur or 50.0)) * 100, 1
        ),
    )
```

- [ ] **Step 5: Tests ausfuehren — muessen PASS**

Run: `cd nomos-api && python -m pytest tests/test_budget_db.py -v`
Expected: All PASS

- [ ] **Step 6: Alte Test-Datei loeschen + Commit**

```bash
rm nomos-api/tests/test_budget.py
git add nomos-api/nomos_api/services/budget.py nomos-api/nomos_api/routers/budget.py \
       nomos-api/nomos_api/routers/costs.py nomos-api/tests/test_budget_db.py
git commit -m "feat(budget): DB-backed budget tracking, replace in-memory service"
```

---

## Task 2: Heartbeat — DB-backed

**Ziel:** Heartbeat schreibt `Agent.heartbeat_at` in die DB. Status wird aus dem Timestamp abgeleitet. Kein In-Memory Dict.

**Files:**
- Rewrite: `nomos-api/nomos_api/services/heartbeat.py`
- Modify: `nomos-api/nomos_api/routers/agents.py` (heartbeat endpoint)
- Rewrite: `nomos-api/tests/test_heartbeat.py`

- [ ] **Step 1: Test schreiben**

```python
# tests/test_heartbeat_db.py
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_heartbeat_updates_agent(client: AsyncClient):
    """Heartbeat should update Agent.heartbeat_at in DB."""
    r = await client.post("/api/agents", json={
        "name": "hb-test", "role": "test", "company": "TestCo",
        "email": "hb@test.de", "risk_class": "limited"
    })
    agent_id = r.json()["id"]

    r = await client.post(f"/api/agents/{agent_id}/heartbeat", json={"metrics": {"cpu": 42}})
    assert r.status_code == 200
    assert r.json()["status"] == "online"
    assert r.json()["agent_id"] == agent_id


async def test_heartbeat_unknown_agent(client: AsyncClient):
    """Heartbeat for unknown agent returns 404."""
    r = await client.post("/api/agents/nonexistent/heartbeat", json={"metrics": {}})
    assert r.status_code == 404


async def test_fleet_shows_heartbeat_status(client: AsyncClient):
    """Fleet endpoint should reflect heartbeat status."""
    r = await client.post("/api/agents", json={
        "name": "hb-fleet", "role": "test", "company": "TestCo",
        "email": "hbf@test.de", "risk_class": "limited"
    })
    agent_id = r.json()["id"]

    # Before heartbeat — no heartbeat_at means offline
    r = await client.get(f"/api/fleet/{agent_id}")
    assert r.status_code == 200
    # heartbeat_at should be None initially

    # Send heartbeat
    await client.post(f"/api/agents/{agent_id}/heartbeat", json={"metrics": {}})

    # After heartbeat — should be recent
    r = await client.get(f"/api/fleet/{agent_id}")
    assert r.json()["heartbeat_at"] is not None
```

- [ ] **Step 2: Test ausfuehren — muss FAIL**

Run: `cd nomos-api && python -m pytest tests/test_heartbeat_db.py -v`

- [ ] **Step 3: Service umschreiben**

```python
# nomos-api/nomos_api/services/heartbeat.py
"""Heartbeat service — DB-backed, writes Agent.heartbeat_at."""
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.models import Agent

_STALE_SECONDS = 300      # 5 min
_OFFLINE_SECONDS = 600    # 10 min


async def record_heartbeat(db: AsyncSession, agent_id: str, metrics: dict | None = None) -> dict | None:
    """Record heartbeat for agent. Returns status dict or None if agent not found."""
    agent = await db.get(Agent, agent_id)
    if agent is None:
        return None

    agent.heartbeat_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(agent)

    return {
        "agent_id": agent_id,
        "status": "online",
        "heartbeat_at": agent.heartbeat_at.isoformat(),
    }


def derive_status(heartbeat_at: datetime | None) -> str:
    """Derive agent status from last heartbeat timestamp."""
    if heartbeat_at is None:
        return "offline"
    elapsed = (datetime.now(timezone.utc) - heartbeat_at).total_seconds()
    if elapsed > _OFFLINE_SECONDS:
        return "offline"
    if elapsed > _STALE_SECONDS:
        return "stale"
    return "online"
```

- [ ] **Step 4: Router-Endpoint anpassen**

In `routers/agents.py`, den `record_heartbeat` Endpoint aendern:

```python
# Ersetze den bestehenden record_heartbeat endpoint:
@router.post("/api/agents/{agent_id}/heartbeat", response_model=HeartbeatResponse)
async def record_heartbeat_endpoint(
    agent_id: str, request: HeartbeatRequest, db: AsyncSession = Depends(get_db)
):
    from nomos_api.services.heartbeat import record_heartbeat
    result = await record_heartbeat(db, agent_id, request.metrics)
    if result is None:
        raise HTTPException(404, detail="Agent not found")
    return HeartbeatResponse(agent_id=agent_id, status=result["status"])
```

Entferne: `get_heartbeat_service()` Singleton und den Import von `HeartbeatService`.

- [ ] **Step 5: Tests ausfuehren — muessen PASS**

Run: `cd nomos-api && python -m pytest tests/test_heartbeat_db.py -v`

- [ ] **Step 6: Alte Tests loeschen + Commit**

```bash
rm nomos-api/tests/test_heartbeat.py
git add nomos-api/nomos_api/services/heartbeat.py nomos-api/nomos_api/routers/agents.py \
       nomos-api/tests/test_heartbeat_db.py
git commit -m "feat(heartbeat): DB-backed heartbeat, write Agent.heartbeat_at"
```

---

## Task 3: Approval Service — DB-backed

**Ziel:** Approvals nutzen das existierende `Approval` ORM Model. Kein In-Memory Dict.

**Files:**
- Rewrite: `nomos-api/nomos_api/services/approval.py`
- Rewrite: `nomos-api/nomos_api/routers/approvals.py`
- Rewrite: `nomos-api/tests/test_approvals.py`

- [ ] **Step 1: Test schreiben**

```python
# tests/test_approvals_db.py
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def _create_agent(client: AsyncClient, name: str, email: str) -> str:
    r = await client.post("/api/agents", json={
        "name": name, "role": "test", "company": "TestCo",
        "email": email, "risk_class": "limited"
    })
    return r.json()["id"]


async def test_create_approval(client: AsyncClient):
    agent_id = await _create_agent(client, "appr-test", "ap@test.de")
    r = await client.post("/api/approvals", json={
        "agent_id": agent_id, "action": "deploy", "description": "Deploy to prod"
    })
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "pending"
    assert data["agent_id"] == agent_id
    assert data["action"] == "deploy"
    assert "id" in data


async def test_approve(client: AsyncClient):
    agent_id = await _create_agent(client, "appr-ok", "aok@test.de")
    r = await client.post("/api/approvals", json={
        "agent_id": agent_id, "action": "deploy", "description": "Deploy"
    })
    approval_id = r.json()["id"]

    r = await client.post(f"/api/approvals/{approval_id}/approve", json={
        "resolved_by": "admin@nomos.local"
    })
    assert r.status_code == 200
    assert r.json()["status"] == "approved"
    assert r.json()["resolved_by"] == "admin@nomos.local"


async def test_reject(client: AsyncClient):
    agent_id = await _create_agent(client, "appr-no", "ano@test.de")
    r = await client.post("/api/approvals", json={
        "agent_id": agent_id, "action": "deploy", "description": "Deploy"
    })
    approval_id = r.json()["id"]

    r = await client.post(f"/api/approvals/{approval_id}/reject", json={
        "resolved_by": "admin@nomos.local"
    })
    assert r.status_code == 200
    assert r.json()["status"] == "denied"


async def test_list_pending(client: AsyncClient):
    agent_id = await _create_agent(client, "appr-list", "al@test.de")
    await client.post("/api/approvals", json={
        "agent_id": agent_id, "action": "a1", "description": "D1"
    })
    await client.post("/api/approvals", json={
        "agent_id": agent_id, "action": "a2", "description": "D2"
    })

    r = await client.get("/api/approvals")
    assert r.status_code == 200
    assert len(r.json()["items"]) >= 2


async def test_approve_unknown_returns_404(client: AsyncClient):
    r = await client.post("/api/approvals/99999/approve", json={
        "resolved_by": "admin"
    })
    assert r.status_code == 404


async def test_list_by_agent(client: AsyncClient):
    agent_id = await _create_agent(client, "appr-filter", "af@test.de")
    await client.post("/api/approvals", json={
        "agent_id": agent_id, "action": "x", "description": "X"
    })

    r = await client.get(f"/api/approvals?agent_id={agent_id}")
    assert r.status_code == 200
    for item in r.json()["items"]:
        assert item["agent_id"] == agent_id
```

- [ ] **Step 2: Test ausfuehren — muss FAIL**

Run: `cd nomos-api && python -m pytest tests/test_approvals_db.py -v`

- [ ] **Step 3: Service umschreiben**

```python
# nomos-api/nomos_api/services/approval.py
"""Approval service — DB-backed, uses Approval ORM model."""
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.models import Approval


async def create_approval(
    db: AsyncSession, agent_id: str, action: str, description: str,
    timeout_minutes: int = 60
) -> Approval:
    approval = Approval(
        agent_id=agent_id,
        action=action,
        description=description,
        status="pending",
        timeout_minutes=timeout_minutes,
        requested_at=datetime.now(timezone.utc).isoformat(),
    )
    db.add(approval)
    await db.commit()
    await db.refresh(approval)
    return approval


async def resolve_approval(
    db: AsyncSession, approval_id: int, resolution: str, resolved_by: str
) -> Approval | None:
    approval = await db.get(Approval, approval_id)
    if approval is None:
        return None
    if resolution not in ("approved", "denied"):
        raise ValueError(f"Invalid resolution: {resolution}")
    approval.status = resolution
    approval.resolved_by = resolved_by
    approval.resolved_at = datetime.now(timezone.utc).isoformat()
    await db.commit()
    await db.refresh(approval)
    return approval


async def list_approvals(
    db: AsyncSession, agent_id: str | None = None, status: str | None = "pending"
) -> list[Approval]:
    stmt = select(Approval)
    if agent_id:
        stmt = stmt.where(Approval.agent_id == agent_id)
    if status:
        stmt = stmt.where(Approval.status == status)
    stmt = stmt.order_by(Approval.id.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_approval(db: AsyncSession, approval_id: int) -> Approval | None:
    return await db.get(Approval, approval_id)
```

- [ ] **Step 4: Router umschreiben**

```python
# nomos-api/nomos_api/routers/approvals.py
"""Approvals router — DB-backed."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.database import get_db
from nomos_api.schemas import ApprovalRequestCreate, ApprovalResponse, ApprovalListResponse
from nomos_api.services.approval import (
    create_approval, resolve_approval, list_approvals, get_approval,
)

router = APIRouter(tags=["approvals"])


@router.post("/api/approvals", status_code=201)
async def create(request: ApprovalRequestCreate, db: AsyncSession = Depends(get_db)):
    approval = await create_approval(
        db, request.agent_id, request.action, request.description
    )
    return ApprovalResponse.model_validate(approval, from_attributes=True)


@router.get("/api/approvals", response_model=ApprovalListResponse)
async def list_all(
    agent_id: str | None = None, db: AsyncSession = Depends(get_db)
):
    # If agent_id filter provided, list all statuses for that agent
    status_filter = None if agent_id else "pending"
    items = await list_approvals(db, agent_id=agent_id, status=status_filter)
    return ApprovalListResponse(
        items=[ApprovalResponse.model_validate(a, from_attributes=True) for a in items],
        total=len(items),
    )


@router.post("/api/approvals/{approval_id}/approve")
async def approve(approval_id: int, request: dict, db: AsyncSession = Depends(get_db)):
    resolved_by = request.get("resolved_by", "system")
    approval = await resolve_approval(db, approval_id, "approved", resolved_by)
    if approval is None:
        raise HTTPException(404, detail="Approval not found")
    return ApprovalResponse.model_validate(approval, from_attributes=True)


@router.post("/api/approvals/{approval_id}/reject")
async def reject(approval_id: int, request: dict, db: AsyncSession = Depends(get_db)):
    resolved_by = request.get("resolved_by", "system")
    approval = await resolve_approval(db, approval_id, "denied", resolved_by)
    if approval is None:
        raise HTTPException(404, detail="Approval not found")
    return ApprovalResponse.model_validate(approval, from_attributes=True)
```

- [ ] **Step 5: Tests ausfuehren — muessen PASS**

Run: `cd nomos-api && python -m pytest tests/test_approvals_db.py -v`

- [ ] **Step 6: Alte Tests loeschen + Commit**

```bash
rm nomos-api/tests/test_approvals.py
git add nomos-api/nomos_api/services/approval.py nomos-api/nomos_api/routers/approvals.py \
       nomos-api/tests/test_approvals_db.py
git commit -m "feat(approvals): DB-backed approval workflow, replace in-memory service"
```

---

## Task 4: Agent Memory — neues DB Model (ersetzt fake HonchoClient)

**Ziel:** HonchoClient war ein Fake. Ersetze durch echtes `AgentMemory` Model in PostgreSQL. Firmenwissen und Agent-Nachrichten werden persistent gespeichert.

**Files:**
- Modify: `nomos-api/nomos_api/models.py` (neues Model `AgentMemory`)
- Rewrite: `nomos-api/nomos_api/services/honcho.py` → `memory.py`
- Rewrite: `nomos-api/tests/test_honcho_client.py` → `test_memory_db.py`

- [ ] **Step 1: Model definieren**

Fuege in `models.py` hinzu:

```python
class AgentMemory(Base):
    """Persistent memory store — replaces fake HonchoClient."""
    __tablename__ = "agent_memory"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(String(128), index=True)
    session_id: Mapped[str] = mapped_column(String(128), index=True)
    role: Mapped[str] = mapped_column(String(32))  # "user", "assistant", "system"
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

- [ ] **Step 2: Test schreiben**

```python
# tests/test_memory_db.py
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def _create_agent(client, name, email):
    r = await client.post("/api/agents", json={
        "name": name, "role": "test", "company": "TestCo",
        "email": email, "risk_class": "limited"
    })
    return r.json()["id"]


async def test_store_and_retrieve_memory(client: AsyncClient):
    """Memory service should persist messages to DB."""
    from nomos_api.services.memory import store_message, list_messages
    from nomos_api.database import async_session

    async with async_session() as db:
        await store_message(db, "agent-1", "sess-1", "user", "Hallo Welt")
        await store_message(db, "agent-1", "sess-1", "assistant", "Hallo!")
        messages = await list_messages(db, "agent-1", "sess-1")

    assert len(messages) == 2
    assert messages[0].content == "Hallo Welt"
    assert messages[1].role == "assistant"


async def test_delete_by_agent(client: AsyncClient):
    """Delete all memory for an agent (DSGVO forget)."""
    from nomos_api.services.memory import store_message, delete_by_agent, list_messages
    from nomos_api.database import async_session

    async with async_session() as db:
        await store_message(db, "agent-del", "s1", "user", "secret@email.com")
        await store_message(db, "agent-del", "s1", "assistant", "OK")
        count = await delete_by_agent(db, "agent-del")

    assert count == 2

    async with async_session() as db:
        messages = await list_messages(db, "agent-del", "s1")
    assert len(messages) == 0


async def test_delete_by_content(client: AsyncClient):
    """Delete messages matching search term (PII removal)."""
    from nomos_api.services.memory import store_message, delete_by_content
    from nomos_api.database import async_session

    async with async_session() as db:
        await store_message(db, "a1", "s1", "user", "Mail: joe@firma.de")
        await store_message(db, "a1", "s1", "assistant", "Notiert.")
        count = await delete_by_content(db, "joe@firma.de")

    assert count == 1  # Only the message containing the email


async def test_search_messages(client: AsyncClient):
    """Search across all messages for a term."""
    from nomos_api.services.memory import store_message, search_messages
    from nomos_api.database import async_session

    async with async_session() as db:
        await store_message(db, "a2", "s2", "user", "IBAN AT611904300234573201")
        await store_message(db, "a2", "s2", "assistant", "Gespeichert")
        results = await search_messages(db, "AT611904300234573201")

    assert len(results) == 1
    assert "IBAN" in results[0].content
```

- [ ] **Step 3: Test ausfuehren — muss FAIL**

Run: `cd nomos-api && python -m pytest tests/test_memory_db.py -v`

- [ ] **Step 4: Service implementieren**

```python
# nomos-api/nomos_api/services/memory.py
"""Agent memory service — DB-backed, replaces fake HonchoClient."""
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.models import AgentMemory


async def store_message(
    db: AsyncSession, agent_id: str, session_id: str, role: str, content: str
) -> AgentMemory:
    msg = AgentMemory(
        agent_id=agent_id, session_id=session_id, role=role, content=content
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def list_messages(
    db: AsyncSession, agent_id: str, session_id: str
) -> list[AgentMemory]:
    stmt = (
        select(AgentMemory)
        .where(AgentMemory.agent_id == agent_id, AgentMemory.session_id == session_id)
        .order_by(AgentMemory.id)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def delete_by_agent(db: AsyncSession, agent_id: str) -> int:
    """Delete ALL messages for an agent. Returns count deleted."""
    stmt = delete(AgentMemory).where(AgentMemory.agent_id == agent_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount


async def delete_by_content(db: AsyncSession, search_term: str) -> int:
    """Delete messages containing search_term (PII removal). Returns count deleted."""
    stmt = delete(AgentMemory).where(AgentMemory.content.contains(search_term))
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount


async def search_messages(db: AsyncSession, search_term: str) -> list[AgentMemory]:
    """Search all messages for a term (DSGVO export)."""
    stmt = select(AgentMemory).where(AgentMemory.content.contains(search_term))
    result = await db.execute(stmt)
    return list(result.scalars().all())
```

- [ ] **Step 5: Tests ausfuehren — muessen PASS**

Run: `cd nomos-api && python -m pytest tests/test_memory_db.py -v`

- [ ] **Step 6: Commit**

```bash
git add nomos-api/nomos_api/models.py nomos-api/nomos_api/services/memory.py \
       nomos-api/tests/test_memory_db.py
git commit -m "feat(memory): DB-backed AgentMemory model, replaces fake HonchoClient"
```

---

## Task 5: Forget/DSGVO — echte Loeschung + Audit Trail

**Ziel:** DSGVO Art. 17 (Forget) loescht echt aus der DB. Art. 15 (Export) liefert echte Daten. Jede Aktion schreibt Audit Trail.

**Files:**
- Rewrite: `nomos-api/nomos_api/services/forget.py`
- Rewrite: `nomos-api/nomos_api/routers/dsgvo.py`
- Rewrite: `nomos-api/tests/test_forget.py`

**Abhaengigkeit:** Task 4 (AgentMemory) muss fertig sein.

- [ ] **Step 1: Test schreiben**

```python
# tests/test_dsgvo_db.py
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def _create_agent(client, name, email):
    r = await client.post("/api/agents", json={
        "name": name, "role": "test", "company": "TestCo",
        "email": email, "risk_class": "limited"
    })
    return r.json()["id"]


async def test_forget_deletes_from_db(client: AsyncClient):
    """DSGVO forget should delete matching messages from DB and write audit."""
    agent_id = await _create_agent(client, "dsgvo-forget", "df@test.de")

    # Store some memory with PII
    from nomos_api.services.memory import store_message
    from nomos_api.database import async_session
    async with async_session() as db:
        await store_message(db, agent_id, "s1", "user", "Kontakt: df@test.de")
        await store_message(db, agent_id, "s1", "assistant", "Gespeichert")

    # Forget
    r = await client.post("/api/dsgvo/forget", json={"email": "df@test.de"})
    assert r.status_code == 200
    data = r.json()
    assert data["deleted_messages"] >= 1
    assert data["audit_event"] == "data.erased"

    # Verify messages are gone
    from nomos_api.services.memory import search_messages
    async with async_session() as db:
        remaining = await search_messages(db, "df@test.de")
    assert len(remaining) == 0


async def test_forget_creates_audit_entry(client: AsyncClient):
    """DSGVO forget must write audit trail."""
    agent_id = await _create_agent(client, "dsgvo-audit", "da@test.de")

    from nomos_api.services.memory import store_message
    from nomos_api.database import async_session
    async with async_session() as db:
        await store_message(db, agent_id, "s1", "user", "Info: da@test.de")

    r = await client.post("/api/dsgvo/forget", json={"email": "da@test.de"})
    assert r.status_code == 200
    assert r.json()["audit_preserved"] is True

    # Check audit trail exists
    r = await client.get(f"/api/agents/{agent_id}/audit")
    events = r.json()["entries"]
    assert any(e["event_type"] == "dsgvo.forget" for e in events)


async def test_forget_unknown_email(client: AsyncClient):
    """Forget with no matching messages returns 0 deleted."""
    r = await client.post("/api/dsgvo/forget", json={"email": "nobody@nowhere.de"})
    assert r.status_code == 200
    assert r.json()["deleted_messages"] == 0


async def test_export_returns_matching_messages(client: AsyncClient):
    """DSGVO export returns all messages containing the email."""
    agent_id = await _create_agent(client, "dsgvo-export", "de@test.de")

    from nomos_api.services.memory import store_message
    from nomos_api.database import async_session
    async with async_session() as db:
        await store_message(db, agent_id, "s1", "user", "Kontakt: de@test.de")
        await store_message(db, agent_id, "s1", "user", "Kein PII hier")

    r = await client.post("/api/dsgvo/export", json={"email": "de@test.de"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert len(data["messages"]) == 1
```

- [ ] **Step 2: Test ausfuehren — muss FAIL**

Run: `cd nomos-api && python -m pytest tests/test_dsgvo_db.py -v`

- [ ] **Step 3: Service implementieren**

```python
# nomos-api/nomos_api/services/forget.py
"""DSGVO forget service — DB-backed deletion with audit trail."""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.services.memory import delete_by_content, search_messages


async def forget(db: AsyncSession, search_term: str) -> dict:
    """DSGVO Art. 17: Delete all messages containing search_term."""
    count = await delete_by_content(db, search_term)
    return {
        "deleted_messages": count,
        "search_term": search_term,
        "audit_event": "data.erased" if count > 0 else "",
        "audit_preserved": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def export(db: AsyncSession, search_term: str) -> dict:
    """DSGVO Art. 15: Export all messages containing search_term."""
    messages = await search_messages(db, search_term)
    return {
        "email": search_term,
        "messages": [
            {"agent_id": m.agent_id, "role": m.role, "content": m.content,
             "created_at": m.created_at.isoformat() if m.created_at else None}
            for m in messages
        ],
        "total": len(messages),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
```

- [ ] **Step 4: Router umschreiben**

```python
# nomos-api/nomos_api/routers/dsgvo.py
"""DSGVO router — DB-backed forget + export with audit trail."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.database import get_db
from nomos_api.models import Agent, AgentMemory
from nomos_api.schemas import DSGVOForgetRequest, DSGVOForgetResponse, DSGVOExportRequest, DSGVOExportResponse
from nomos_api.services.forget import forget, export

router = APIRouter(tags=["dsgvo"])


@router.post("/api/dsgvo/forget", response_model=DSGVOForgetResponse)
async def dsgvo_forget(request: DSGVOForgetRequest, db: AsyncSession = Depends(get_db)):
    result = await forget(db, request.email)

    # Write audit trail for each affected agent
    if result["deleted_messages"] > 0:
        # Find agents that had messages with this email
        stmt = select(Agent).where(Agent.email == request.email)
        agents_result = await db.execute(stmt)
        for agent in agents_result.scalars().all():
            from nomos_api.routers.agents import _write_audit_event
            await _write_audit_event(
                db, agent, agent.id, "dsgvo.forget",
                {"search_term": request.email, "deleted": result["deleted_messages"]}
            )

    return DSGVOForgetResponse(**result)


@router.post("/api/dsgvo/export", response_model=DSGVOExportResponse)
async def dsgvo_export(request: DSGVOExportRequest, db: AsyncSession = Depends(get_db)):
    result = await export(db, request.email)
    return DSGVOExportResponse(**result)
```

- [ ] **Step 5: Tests ausfuehren — muessen PASS**

Run: `cd nomos-api && python -m pytest tests/test_dsgvo_db.py -v`

- [ ] **Step 6: Alte Tests loeschen + Commit**

```bash
rm nomos-api/tests/test_forget.py nomos-api/tests/test_honcho_client.py
git add nomos-api/nomos_api/services/forget.py nomos-api/nomos_api/services/memory.py \
       nomos-api/nomos_api/routers/dsgvo.py nomos-api/tests/test_dsgvo_db.py
git commit -m "feat(dsgvo): real DB deletion + audit trail for DSGVO forget/export"
```

---

## Task 6: Workspace Service — DB-backed (Bonus)

**Ziel:** WorkspaceService nutzt die echte Memory-DB statt den fake HonchoClient.

**Files:**
- Rewrite: `nomos-api/nomos_api/services/workspace.py`
- Rewrite: `nomos-api/tests/test_workspace.py`

**Abhaengigkeit:** Task 4 (AgentMemory) muss fertig sein.

- [ ] **Step 1: Test schreiben**

Tests fuer Workspace-Isolation: Agent kann nur eigene Messages lesen, nicht die eines anderen Agents.

```python
# tests/test_workspace_db.py
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_workspace_info(client: AsyncClient):
    """GET workspace returns agent info."""
    r = await client.post("/api/agents", json={
        "name": "ws-test", "role": "test", "company": "TestCo",
        "email": "ws@test.de", "risk_class": "limited"
    })
    agent_id = r.json()["id"]

    r = await client.get(f"/api/workspace/{agent_id}")
    assert r.status_code == 200
    assert r.json()["agent_id"] == agent_id
```

- [ ] **Step 2-5: Implement + Test + Commit**

Pattern wie Task 3-5. WorkspaceService braucht `db: AsyncSession`, nutzt `AgentMemory` fuer Message-Isolation.

```bash
git commit -m "feat(workspace): DB-backed workspace with agent isolation"
```

---

## Task 7: Aufraeumen — Singletons + tote Imports entfernen

**Ziel:** Alle `_service = Service()` Singletons aus Routern entfernen. `get_heartbeat_service()`, `get_budget_service()` etc. loeschen. Ungenutzter Code weg.

**Files:**
- Modify: alle geaenderten Router (entferne Singleton-Initialisierung)
- Delete: `scripts/gateway-entrypoint.sh` (nicht mehr gebraucht)

- [ ] **Step 1: grep nach verbleibenden Singletons**

```bash
cd nomos-api && grep -rn "_service = " nomos_api/routers/
```

- [ ] **Step 2: Jeden Singleton entfernen, durch `Depends(get_db)` ersetzen**

- [ ] **Step 3: Alle Tests ausfuehren**

```bash
cd nomos-api && python -m pytest tests/ -v --tb=short
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: remove all in-memory singletons, clean dead code"
```

---

## Task 8: Integration Smoke Test — E2E im Docker

**Ziel:** Stack neu bauen, einloggen, Budget tracken, Approval erstellen, DSGVO Forget ausfuehren — alles im Browser verifizieren.

- [ ] **Step 1: Stack neu bauen**

```bash
docker compose up -d --build
```

- [ ] **Step 2: Warten bis healthy**

```bash
docker compose ps
```

- [ ] **Step 3: API-Smoke via curl**

```bash
# Login
curl -s http://localhost:8060/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@nomos.local","password":"NomOSAdmin2026!"}'

# Budget check
curl -s http://localhost:8060/api/budget/check \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"<ID>","estimated_cost":10}'

# Create approval
curl -s http://localhost:8060/api/approvals \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"<ID>","action":"deploy","description":"Prod deploy"}'

# DSGVO forget
curl -s http://localhost:8060/api/dsgvo/forget \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'
```

- [ ] **Step 4: Alles verifiziert → Final Commit**

```bash
git commit -m "test: E2E smoke test passed — all services DB-backed"
```

---

## Abhaengigkeiten

```
Task 0 (Schemas+Audit) ──── ZUERST, alle anderen haengen davon ab
Task 1 (Budget)     ──┐
Task 2 (Heartbeat)  ──┤── unabhaengig, parallel moeglich (nach Task 0)
Task 3 (Approval)   ──┘
Task 4 (Memory)     ──── nach Task 0, muss vor Task 5 + 6 fertig sein
Task 5 (DSGVO)      ──── abhaengig von Task 4
Task 6 (Workspace)  ──── abhaengig von Task 4
Task 7 (Cleanup)    ──── nach Task 1-6
Task 8 (Smoke)      ──── nach Task 7
```

**Parallele Ausfuehrung:**
- Task 0 zuerst (allein)
- Tasks 1, 2, 3 koennen gleichzeitig als Subagents laufen
- Task 4 danach (allein)
- Tasks 5+6 parallel nach Task 4
- Task 7+8 sequentiell am Ende
