# NomOS Architecture

## Component Overview

```
+-----------------------------------------------------+
|                    Docker Compose                    |
|                                                      |
|  +----------------+  +----------------+  +---------+ |
|  |   nomos-api    |  | nomos-console  |  |postgres | |
|  |   (FastAPI)    |  |  (Next.js 15)  |  |(pg16 +  | |
|  |   Port 8060    |  |   Port 3040    |  |pgvector)| |
|  +-------+--------+  +-------+--------+  +----+----+ |
|          |                    |                |      |
|          +--------------------+                |      |
|          | HTTP (internal)    |                |      |
|          +------------------------------------+      |
|          | asyncpg (PostgreSQL)                       |
+-----------------------------------------------------+
           |
           v
   +---------------+
   |  /data/agents  |  (Docker volume: nomos-agents)
   |  Agent files   |
   +---------------+

+-----------------------------------------------------+
|                    nomos-cli                          |
|              (standalone Python CLI)                 |
|           Works directly on local files              |
+-----------------------------------------------------+

+-----------------------------------------------------+
|                   nomos-plugin                        |
|           (TypeScript OpenClaw plugin)               |
|           Gateway integration layer                  |
+-----------------------------------------------------+
```

## Components

### nomos-cli (Python CLI)

The core library and command-line tool. Contains all business logic.

| Module | Responsibility |
|--------|---------------|
| `core/manifest.py` | Pydantic v2 models for agent manifest schema (AgentManifest, 12 sub-models) |
| `core/manifest_validator.py` | Load YAML, validate schema + business rules, compute SHA-256 manifest hash |
| `core/forge.py` | Create complete agent directories (manifest + hash + audit chain) |
| `core/gate.py` | Generate 5 compliance documents from manifest data |
| `core/compliance_engine.py` | Blocking compliance check (PASSED / WARNING / BLOCKED) |
| `core/hash_chain.py` | SHA-256 append-only hash chain (JSONL storage), verification |
| `core/events.py` | Canonical event type definitions (14 event types) |
| `cli.py` | Click CLI with 5 commands: hire, gate, verify, fleet, audit |

Test coverage: 84 tests.

### nomos-api (FastAPI)

REST API wrapping the core library for remote access and fleet management.

| Module | Responsibility |
|--------|---------------|
| `config.py` | Settings from NOMOS_ environment variables (Pydantic BaseSettings) |
| `database.py` | AsyncSession factory (SQLAlchemy + asyncpg) |
| `models.py` | ORM models: Agent, AuditLog |
| `schemas.py` | Pydantic request/response schemas (8 models) |
| `services/agent_service.py` | Agent creation: forge + persist to DB |
| `services/fleet_service.py` | Fleet CRUD operations |
| `routers/health.py` | GET /health |
| `routers/agents.py` | POST /api/agents |
| `routers/fleet.py` | GET /api/fleet, GET /api/fleet/{id} |
| `routers/compliance.py` | GET /api/agents/{id}/compliance, POST /api/agents/{id}/gate |
| `routers/audit.py` | GET /api/agents/{id}/audit, GET /api/audit/verify/{id} |

Test coverage: 14 tests.

### nomos-console (Next.js 15)

Web dashboard for visual fleet management:
- Fleet overview with agent list
- Agent detail view with manifest data
- Compliance status and document check
- Audit trail viewer

Communicates with nomos-api via internal Docker network HTTP.

### nomos-plugin (TypeScript)

OpenClaw gateway plugin providing `/nomos` commands for chat-based agent interaction.

### PostgreSQL 16 + pgvector

Stores the agent registry and indexed audit entries. The database is the fleet registry; the JSONL files on disk are the source of truth for audit chains.

---

## Data Flow

### Agent Creation (nomos hire / POST /api/agents)

```
1. Input: name, role, company, email, risk_class
         |
2. forge_agent()
   +-- Slugify name to agent ID (e.g. "Mani Ruf" -> "mani-ruf")
   +-- Build manifest data (Pydantic AgentManifest)
   +-- Create directory structure:
   |     agents/<id>/
   |       manifest.yaml
   |       manifest.sha256
   |       compliance/     (empty)
   |       audit/chain.jsonl
   +-- Initialize hash chain with "agent.created" event
   +-- Return ForgeResult(manifest_hash)
         |
3. check_compliance()
   +-- Verify required docs exist -> BLOCKED (docs not yet generated)
         |
4. [API only] Persist Agent + AuditLog to PostgreSQL
         |
5. Output: AgentResponse with compliance_status="blocked"
```

### Compliance Gate (nomos gate / POST /api/agents/{id}/gate)

```
1. Load manifest from agent directory
         |
2. generate_compliance_docs()
   +-- Generate 5 markdown documents:
   |     compliance/dpia.md
   |     compliance/verarbeitungsverzeichnis.md
   |     compliance/art50_transparency.md
   |     compliance/art14_killswitch.md
   |     compliance/art12_logging.md
         |
3. check_compliance() -> PASSED
         |
4. [API only] Update compliance_status in DB
         |
5. Output: ComplianceResponse with status="passed"
```

### Verification (nomos verify / GET /api/audit/verify/{id})

```
1. Load manifest from YAML
2. Validate manifest schema (Pydantic)
3. Validate manifest business rules
4. Check compliance documents exist
5. Verify manifest hash (SHA-256)
6. Verify audit chain integrity:
   +-- Read chain.jsonl line by line
   +-- Recompute each entry's hash
   +-- Verify previous_hash links
   +-- Verify first entry links to genesis hash (64 zeros)
7. Output: PASS/FAIL per check
```

---

## Database Schema

### agents table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(128) | PRIMARY KEY | Agent ID (slugified name) |
| `name` | VARCHAR(256) | NOT NULL | Human-readable name |
| `role` | VARCHAR(256) | NOT NULL | Agent role |
| `company` | VARCHAR(256) | NOT NULL | Company name |
| `email` | VARCHAR(256) | NOT NULL | Contact email |
| `risk_class` | VARCHAR(32) | NOT NULL, DEFAULT 'limited' | EU AI Act risk class |
| `status` | VARCHAR(32) | NOT NULL, DEFAULT 'created' | Agent lifecycle status |
| `manifest_hash` | VARCHAR(64) | NOT NULL | SHA-256 of manifest |
| `manifest_data` | JSON | NOT NULL | Full manifest as JSON |
| `compliance_status` | VARCHAR(32) | NOT NULL, DEFAULT 'pending' | Compliance gate result |
| `agents_dir` | TEXT | NOT NULL | Filesystem path to agent directory |
| `created_at` | TIMESTAMP WITH TZ | NOT NULL, DEFAULT now() | Creation timestamp |
| `updated_at` | TIMESTAMP WITH TZ | NOT NULL, DEFAULT now() | Last update timestamp |

### audit_log table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-increment ID |
| `agent_id` | VARCHAR(128) | NOT NULL, INDEX | Agent reference |
| `sequence` | INTEGER | NOT NULL | Sequence number within chain |
| `event_type` | VARCHAR(64) | NOT NULL, INDEX | Event type string |
| `data` | JSON | NULLABLE | Event-specific payload |
| `chain_hash` | VARCHAR(64) | NOT NULL | SHA-256 hash of this entry |
| `timestamp` | VARCHAR(64) | NOT NULL | ISO 8601 timestamp |

**Index:** Composite index on `(agent_id, sequence)`.

Note: The audit_log table is a queryable index. The source of truth for audit integrity is the JSONL chain file on disk.

---

## Hash Chain Format

The audit trail is stored as a JSONL file (`audit/chain.jsonl`). Each line is a self-contained JSON object:

```jsonl
{"agent_id":"mani-ruf","data":{"company":"Acme GmbH","manifest_hash":"a1b2...","name":"Mani Ruf","risk_class":"limited","role":"external-secretary"},"event_type":"agent.created","hash":"e4f5a6b7...","previous_hash":"0000000000000000000000000000000000000000000000000000000000000000","sequence":0,"timestamp":"2026-03-24T10:00:00.123456+00:00"}
```

**Fields per entry:**

| Field | Description |
|-------|-------------|
| `sequence` | 0-based sequential number |
| `timestamp` | ISO 8601 UTC timestamp |
| `event_type` | Canonical event type (see Events) |
| `agent_id` | Agent this event belongs to |
| `data` | Event-specific payload (arbitrary JSON object) |
| `previous_hash` | SHA-256 hash of the previous entry (genesis = 64 zeros) |
| `hash` | SHA-256 of canonical JSON of all fields except `hash` itself |

**Hash computation:**

```
canonical = JSON.stringify({sequence, timestamp, event_type, agent_id, data, previous_hash},
                           sort_keys=true, separators=(",",":"))
hash = SHA-256(canonical)
```

Modifying any field in any entry invalidates that entry's hash and breaks the chain for all subsequent entries.

---

## Security Model

### Non-root Docker Container

The API container creates a dedicated `nomos` user and runs as that user:
```dockerfile
RUN adduser --disabled-password --no-create-home --gecos "" nomos
USER nomos
```

### Path Validation

Before accessing agent directories via the API, every request validates that the resolved path is within the configured `agents_dir`:

```python
agent_dir = Path(agent.agents_dir).resolve()
safe_base = settings.agents_dir.resolve()
if not agent_dir.is_relative_to(safe_base):
    raise HTTPException(status_code=400, detail="Invalid agent directory")
```

This prevents path traversal attacks.

### PII Handling

The manifest defines PII filter configuration:
- `pii_filter.enabled` — master switch
- `pii_filter.mask_emails` — mask email addresses
- `pii_filter.mask_phones` — mask phone numbers
- `pii_filter.mask_addresses` — mask physical addresses
- `pii_filter.keep_names` — whether to preserve names

PII filtering requires the Honcho memory backend. With the local backend, the PII filter configuration is stored in the manifest but filtering is not active. The DPIA document clearly states this limitation.

### Manifest Integrity

Each agent has a `manifest.sha256` file containing the SHA-256 hash of the manifest's canonical JSON representation. `nomos verify` checks this hash to detect tampering.

### Audit Chain Integrity

The hash chain is append-only. Each entry's hash depends on all previous entries. Verification recomputes every hash from scratch and checks the chain links. Any modification is detectable.

---

## Configuration

All API settings are configured via environment variables with the `NOMOS_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `NOMOS_DATABASE_URL` | `postgresql+asyncpg://nomos:nomos@localhost:5432/nomos` | Database connection string |
| `NOMOS_API_HOST` | `0.0.0.0` | API bind address |
| `NOMOS_API_PORT` | `8000` | API internal port (mapped to 8060 via Docker) |
| `NOMOS_API_TITLE` | `NomOS Fleet API` | API title |
| `NOMOS_API_VERSION` | `0.1.0` | API version |
| `NOMOS_CORS_ORIGINS` | `["http://localhost:3040"]` | Allowed CORS origins |
| `NOMOS_AGENTS_DIR` | `./data/agents` | Agent file storage directory |
| `NOMOS_DB_PASSWORD` | `nomos` | PostgreSQL password |
| `NOMOS_API_PORT` (docker-compose) | `8060` | External API port |
| `NOMOS_CONSOLE_PORT` (docker-compose) | `3040` | External console port |
