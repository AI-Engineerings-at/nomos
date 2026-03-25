# Sub-Projekt B: Control Plane — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Heartbeat-System, Task Dispatch, Approval Gates, Budget Enforcement und Config Revisioning — die Steuerungsschicht die NomOS zur echten Control Plane macht.

**Architecture:** Neue Services + Models + Routers in nomos-api. Erweitert bestehende Agent-Models und Core-Library (manifest.py, events.py). FCL Enforcement (3 Agents gratis) im Fleet Service.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Pydantic v2, pytest

**Design Spec:** `docs/superpowers/specs/2026-03-24-nomos-v2-design.md` Sektion 7
**Master Plan:** `docs/superpowers/plans/2026-03-24-nomos-v2-master-plan.md` Sub-Projekt B

---

## File Structure

```
Neue Dateien:
  nomos-api/nomos_api/services/heartbeat.py       # Heartbeat empfangen, STALE/OFFLINE
  nomos-api/nomos_api/services/task_dispatch.py    # Task CRUD + Lifecycle
  nomos-api/nomos_api/services/approval.py         # Approval Queue + Delegation
  nomos-api/nomos_api/services/budget.py           # Budget Tracking + Enforcement
  nomos-api/nomos_api/services/config_revision.py  # Config Versioning + Rollback
  nomos-api/nomos_api/routers/tasks.py             # REST /api/tasks/*
  nomos-api/nomos_api/routers/approvals.py         # REST /api/approvals/*
  nomos-api/nomos_api/routers/costs.py             # REST /api/costs/*

Erweitern:
  nomos-api/nomos_api/models.py                    # +Task, +Approval, +ConfigRevision
  nomos-api/nomos_api/schemas.py                   # +Task/Approval/Budget Schemas
  nomos-api/nomos_api/routers/agents.py            # +PATCH pause/resume/kill, +heartbeat
  nomos-api/nomos_api/services/agent_service.py    # +FCL check (max 3 agents)
  nomos-api/nomos_api/main.py                      # +neue Router registrieren
  nomos-cli/nomos/core/manifest.py                 # +BudgetConfig, +ApprovalConfig
  nomos-cli/nomos/core/events.py                   # +task.*, +approval.*, +budget.*, +config.*

Tests:
  nomos-api/tests/test_heartbeat.py
  nomos-api/tests/test_tasks.py
  nomos-api/tests/test_approvals.py
  nomos-api/tests/test_budget.py
  nomos-api/tests/test_config_revision.py
  nomos-api/tests/test_fcl.py
  nomos-cli/tests/test_manifest_v2.py
  nomos-cli/tests/test_events_v2.py
```

---

## Task 1: Extend Manifest + Events (Core Library)

**Files:**
- Modify: `nomos-cli/nomos/core/manifest.py`
- Modify: `nomos-cli/nomos/core/events.py`
- Test: `nomos-cli/tests/test_manifest_v2.py`
- Test: `nomos-cli/tests/test_events_v2.py`

- [ ] **Step 1: Write test for BudgetConfig + ApprovalConfig**

```python
# nomos-cli/tests/test_manifest_v2.py
from nomos.core.manifest import AgentManifest, BudgetConfig, ApprovalConfig

def test_budget_config_defaults():
    budget = BudgetConfig()
    assert budget.monthly_limit_eur == 50.0
    assert budget.warn_at_percent == 80
    assert budget.auto_pause is True

def test_approval_config():
    approval = ApprovalConfig(
        required_for=["external_api_calls", "file_deletion", "data_export"]
    )
    assert len(approval.required_for) == 3

def test_manifest_with_budget():
    data = _valid_manifest_data()
    data["budget"] = {"monthly_limit_eur": 100, "warn_at_percent": 90}
    manifest = AgentManifest(**data)
    assert manifest.budget.monthly_limit_eur == 100

def test_manifest_without_budget_gets_defaults():
    data = _valid_manifest_data()
    manifest = AgentManifest(**data)
    assert manifest.budget.monthly_limit_eur == 50.0
```

- [ ] **Step 2: Run test — FAIL**
- [ ] **Step 3: Extend manifest.py with BudgetConfig + ApprovalConfig**

Add to manifest.py:
```python
class BudgetConfig(BaseModel):
    monthly_limit_eur: float = 50.0
    warn_at_percent: int = 80
    auto_pause: bool = True

class ApprovalConfig(BaseModel):
    required_for: list[str] = Field(default_factory=lambda: [
        "external_api_calls", "file_deletion", "data_export", "budget_over_threshold"
    ])
    timeout_minutes: int = 60
```

Add to AgentManifest: `budget: BudgetConfig = Field(default_factory=BudgetConfig)` and `approval: ApprovalConfig = Field(default_factory=ApprovalConfig)`

- [ ] **Step 4: Write test for new event types**

```python
# nomos-cli/tests/test_events_v2.py
from nomos.core.events import EventType

def test_task_events_exist():
    assert hasattr(EventType, "TASK_CREATED")
    assert hasattr(EventType, "TASK_ASSIGNED")
    assert hasattr(EventType, "TASK_COMPLETED")

def test_budget_events_exist():
    assert hasattr(EventType, "BUDGET_WARNING")
    assert hasattr(EventType, "BUDGET_EXCEEDED")

def test_approval_events_exist():
    assert hasattr(EventType, "APPROVAL_REQUESTED")
    assert hasattr(EventType, "APPROVAL_GRANTED")
    assert hasattr(EventType, "APPROVAL_DENIED")

def test_config_events_exist():
    assert hasattr(EventType, "CONFIG_CHANGED")
    assert hasattr(EventType, "CONFIG_ROLLED_BACK")
```

- [ ] **Step 5: Extend events.py**
- [ ] **Step 6: Run all CLI tests — PASS (84 + new)**
- [ ] **Step 7: Commit**

---

## Task 2: DB Models (Task, Approval, ConfigRevision)

**Files:**
- Modify: `nomos-api/nomos_api/models.py`

- [ ] **Step 1: Add Task model**

```python
class Task(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True)
    agent_id = Column(String, nullable=False, index=True)
    description = Column(String, nullable=False)
    priority = Column(String, default="normal")  # low, normal, high, urgent
    status = Column(String, default="queued")  # queued, assigned, running, review, done, failed
    created_by = Column(String, nullable=True)
    timeout_minutes = Column(Integer, default=60)
    cost_eur = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 2: Add Approval model**

```python
class Approval(Base):
    __tablename__ = "approvals"
    id = Column(String, primary_key=True)
    agent_id = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False)  # external_api_call, file_deletion, etc.
    description = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, approved, denied, expired
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String, nullable=True)
    timeout_minutes = Column(Integer, default=60)
```

- [ ] **Step 3: Add ConfigRevision model**

```python
class ConfigRevision(Base):
    __tablename__ = "config_revisions"
    id = Column(String, primary_key=True)
    agent_id = Column(String, nullable=False, index=True)
    version = Column(Integer, nullable=False)
    config_json = Column(String, nullable=False)  # JSON snapshot
    change_description = Column(String, nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 4: Extend Agent model: +budget_used_eur, +budget_limit_eur, +heartbeat_at, +status**
- [ ] **Step 5: Commit**

---

## Task 3: Heartbeat Service

**Files:**
- Create: `nomos-api/nomos_api/services/heartbeat.py`
- Test: `nomos-api/tests/test_heartbeat.py`

- [ ] **Step 1: Write failing test**

```python
# nomos-api/tests/test_heartbeat.py
import pytest
from datetime import datetime, timezone, timedelta
from nomos_api.services.heartbeat import HeartbeatService

def test_record_heartbeat():
    svc = HeartbeatService()
    svc.record("agent-1", {"tokens_used": 100, "memory_mb": 256})
    assert svc.get_status("agent-1") == "online"

def test_stale_after_5_minutes():
    svc = HeartbeatService()
    svc.record("agent-1", {})
    svc._last_seen["agent-1"] = datetime.now(timezone.utc) - timedelta(minutes=6)
    assert svc.get_status("agent-1") == "stale"

def test_offline_after_10_minutes():
    svc = HeartbeatService()
    svc.record("agent-1", {})
    svc._last_seen["agent-1"] = datetime.now(timezone.utc) - timedelta(minutes=11)
    assert svc.get_status("agent-1") == "offline"

def test_unknown_agent():
    svc = HeartbeatService()
    assert svc.get_status("unknown") == "offline"
```

- [ ] **Step 2: Run — FAIL**
- [ ] **Step 3: Implement heartbeat.py**
- [ ] **Step 4: Run — PASS**
- [ ] **Step 5: Commit**

---

## Task 4: Budget Service

**Files:**
- Create: `nomos-api/nomos_api/services/budget.py`
- Test: `nomos-api/tests/test_budget.py`

- [ ] **Step 1: Write failing test**

```python
# nomos-api/tests/test_budget.py
from nomos_api.services.budget import BudgetService

def test_check_within_budget():
    svc = BudgetService()
    result = svc.check("agent-1", current=30.0, limit=50.0, warn_at=80)
    assert result["allowed"] is True
    assert result["status"] == "normal"

def test_check_warning_threshold():
    svc = BudgetService()
    result = svc.check("agent-1", current=42.0, limit=50.0, warn_at=80)
    assert result["allowed"] is True
    assert result["status"] == "warning"

def test_check_exceeded():
    svc = BudgetService()
    result = svc.check("agent-1", current=51.0, limit=50.0, warn_at=80)
    assert result["allowed"] is False
    assert result["status"] == "exceeded"

def test_track_cost():
    svc = BudgetService()
    svc.track("agent-1", cost=0.05)
    svc.track("agent-1", cost=0.03)
    assert svc.get_total("agent-1") == pytest.approx(0.08)
```

- [ ] **Step 2: Run — FAIL**
- [ ] **Step 3: Implement budget.py**
- [ ] **Step 4: Run — PASS**
- [ ] **Step 5: Commit**

---

## Task 5: Task Dispatch Service

**Files:**
- Create: `nomos-api/nomos_api/services/task_dispatch.py`
- Test: `nomos-api/tests/test_tasks.py`

- [ ] **Step 1: Write failing test**

```python
# nomos-api/tests/test_tasks.py
from nomos_api.services.task_dispatch import TaskService

def test_create_task():
    svc = TaskService()
    task = svc.create(agent_id="agent-1", description="Write blog post", priority="normal")
    assert task["status"] == "queued"
    assert task["agent_id"] == "agent-1"

def test_task_lifecycle():
    svc = TaskService()
    task = svc.create(agent_id="agent-1", description="Test task")
    task_id = task["id"]
    svc.update_status(task_id, "assigned")
    assert svc.get(task_id)["status"] == "assigned"
    svc.update_status(task_id, "running")
    assert svc.get(task_id)["status"] == "running"
    svc.update_status(task_id, "done")
    assert svc.get(task_id)["status"] == "done"

def test_invalid_status_transition():
    svc = TaskService()
    task = svc.create(agent_id="agent-1", description="Test")
    with pytest.raises(ValueError, match="Invalid"):
        svc.update_status(task["id"], "done")  # Can't go from queued to done

def test_list_tasks_by_agent():
    svc = TaskService()
    svc.create(agent_id="agent-1", description="Task A")
    svc.create(agent_id="agent-2", description="Task B")
    svc.create(agent_id="agent-1", description="Task C")
    tasks = svc.list_by_agent("agent-1")
    assert len(tasks) == 2
```

- [ ] **Step 2: Run — FAIL**
- [ ] **Step 3: Implement task_dispatch.py with status machine**

Valid transitions:
```
queued → assigned → running → review → done
                  → failed
         assigned → queued (requeue)
```

- [ ] **Step 4: Run — PASS**
- [ ] **Step 5: Commit**

---

## Task 6: Approval Service

**Files:**
- Create: `nomos-api/nomos_api/services/approval.py`
- Test: `nomos-api/tests/test_approvals.py`

- [ ] **Step 1: Write failing test**

```python
# nomos-api/tests/test_approvals.py
from nomos_api.services.approval import ApprovalService

def test_request_approval():
    svc = ApprovalService()
    req = svc.request(agent_id="agent-1", action="external_api_call", description="Call CRM API")
    assert req["status"] == "pending"

def test_approve():
    svc = ApprovalService()
    req = svc.request(agent_id="agent-1", action="file_deletion", description="Delete temp.txt")
    svc.resolve(req["id"], "approved", resolved_by="admin@nomos.local")
    assert svc.get(req["id"])["status"] == "approved"

def test_deny():
    svc = ApprovalService()
    req = svc.request(agent_id="agent-1", action="data_export", description="Export CSV")
    svc.resolve(req["id"], "denied", resolved_by="admin@nomos.local")
    assert svc.get(req["id"])["status"] == "denied"

def test_list_pending():
    svc = ApprovalService()
    svc.request(agent_id="agent-1", action="api_call", description="A")
    svc.request(agent_id="agent-2", action="export", description="B")
    pending = svc.list_pending()
    assert len(pending) == 2
```

- [ ] **Step 2-5: Implement + test + commit**

---

## Task 7: Config Revision Service

**Files:**
- Create: `nomos-api/nomos_api/services/config_revision.py`
- Test: `nomos-api/tests/test_config_revision.py`

- [ ] **Step 1: Write failing test**

```python
# nomos-api/tests/test_config_revision.py
from nomos_api.services.config_revision import ConfigRevisionService
import json

def test_save_revision():
    svc = ConfigRevisionService()
    rev = svc.save("agent-1", {"model": "claude-sonnet", "budget": 50}, "created")
    assert rev["version"] == 1

def test_multiple_revisions():
    svc = ConfigRevisionService()
    svc.save("agent-1", {"model": "claude-sonnet"}, "created")
    svc.save("agent-1", {"model": "claude-opus"}, "model changed")
    revs = svc.list("agent-1")
    assert len(revs) == 2
    assert revs[1]["version"] == 2

def test_rollback():
    svc = ConfigRevisionService()
    svc.save("agent-1", {"model": "sonnet", "budget": 50}, "v1")
    svc.save("agent-1", {"model": "opus", "budget": 100}, "v2")
    config = svc.rollback("agent-1", version=1)
    assert config["model"] == "sonnet"
    assert config["budget"] == 50
```

- [ ] **Step 2-5: Implement + test + commit**

---

## Task 8: FCL Enforcement (3 Agent Limit)

**Files:**
- Modify: `nomos-api/nomos_api/services/agent_service.py`
- Test: `nomos-api/tests/test_fcl.py`

- [ ] **Step 1: Write failing test**

```python
# nomos-api/tests/test_fcl.py
from nomos_api.services.agent_service import check_fcl_limit

def test_allows_up_to_3_agents():
    assert check_fcl_limit(active_count=0) is True
    assert check_fcl_limit(active_count=1) is True
    assert check_fcl_limit(active_count=2) is True

def test_blocks_4th_agent():
    assert check_fcl_limit(active_count=3) is False

def test_returns_message():
    allowed, msg = check_fcl_limit_with_message(active_count=3)
    assert allowed is False
    assert "3/3" in msg
    assert "Lizenz" in msg or "license" in msg.lower()
```

- [ ] **Step 2-5: Implement + test + commit**

---

## Task 9: API Routers (Tasks + Approvals + Costs)

**Files:**
- Create: `nomos-api/nomos_api/routers/tasks.py`
- Create: `nomos-api/nomos_api/routers/approvals.py`
- Create: `nomos-api/nomos_api/routers/costs.py`
- Modify: `nomos-api/nomos_api/routers/agents.py` (+PATCH, +heartbeat)
- Modify: `nomos-api/nomos_api/main.py` (+register new routers)
- Modify: `nomos-api/nomos_api/schemas.py` (+new schemas)

Endpoints:
```
POST   /api/agents/{id}/heartbeat     → record heartbeat
PATCH  /api/agents/{id}               → pause/resume/kill + config change
GET    /api/tasks                      → list (filtered)
POST   /api/tasks                      → create task
PATCH  /api/tasks/{id}                 → update status
GET    /api/approvals                  → list pending
POST   /api/approvals/{id}/approve     → approve
POST   /api/approvals/{id}/reject      → reject
GET    /api/costs                      → cost overview all agents
GET    /api/costs/{agent_id}           → cost per agent
```

- [ ] **Step 1: Create Pydantic schemas**
- [ ] **Step 2: Implement routers (one at a time, with tests)**
- [ ] **Step 3: Register in main.py**
- [ ] **Step 4: Run all tests**
- [ ] **Step 5: Commit**

---

## Task 10: Integration Test + Final

- [ ] **Step 1: Run ALL tests**

```bash
cd nomos-api && python -m pytest tests/ -v
cd nomos-cli && python -m pytest tests/ -v
```

Expected: All pass, 0 regressions

- [ ] **Step 2: Commit**

---

## Erfolgs-Kriterien

- [ ] Heartbeat: STALE nach 5min, OFFLINE nach 10min
- [ ] Task Lifecycle: queued → assigned → running → review → done
- [ ] Approval Queue: request → approve/deny
- [ ] Budget: 80% warning, 100% auto-pause
- [ ] Config Revisioning: save + rollback
- [ ] FCL: 4. Agent wird blockiert mit klarer Meldung
- [ ] Alle neuen Services haben Tests
- [ ] Bestehende Tests weiterhin gruen
