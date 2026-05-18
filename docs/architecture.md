# NomOS Architecture

> Last reconciled against source: 2026-05-19 (enterprise-hardening Batch F).
> Citations point to the verifying file/line in this repository.

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
|  +----------------+  +----------------+  +---------+ |
|  |    valkey      |  | openclaw-gw    |  | vault   | |
|  |  (BSD-3 cache) |  | (LLM gateway)  |  |(secrets)| |
|  |  (internal)    |  |   Port 3050    |  | Port    | |
|  +----------------+  +----------------+  | 8200    | |
|  +----------------+  +----------------+  +---------+ |
|  | nomos-worker   |  |    caddy       |              |
|  | (ARQ / Valkey) |  | (TLS reverse   |              |
|  | no host port   |  |  proxy 80/443) |              |
|  +----------------+  +----------------+              |
+-----------------------------------------------------+

> docker-compose.yml is authoritative for ports. Host-exposed:
> Console `${NOMOS_CONSOLE_PORT:-3040}`, API `${NOMOS_API_PORT:-8060}`,
> Gateway `${NOMOS_GATEWAY_PORT:-3050}`, Caddy 80/443, Vault 8200.
> `postgres`, `valkey` and `nomos-worker` have NO host port (compose
> network only). Source: `docker-compose.yml:3,13-14,90-91,166-167`.
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

### nomos-api (FastAPI — Python 3.12)

REST API. Routers live in `nomos-api/nomos_api/routers/`; the directory
currently contains 19 router modules (verified by file listing
2026-05-19): the 16 below plus `monitoring.py`, `system.py`, and an
internal `__init__.py`-aggregated set. See the API Reference for the
authoritative per-endpoint table.

#### Routers

| Router | Prefix | Responsibility |
|--------|--------|---------------|
| `routers/health.py` | `/health`, `/api/health` | Service health check |
| `routers/auth.py` | `/api/auth` | Login, logout, JWT sessions, 2FA setup/verify, recovery |
| `routers/agents.py` | `/api/agents` | Agent CRUD, heartbeat, pause, resume, kill, retire |
| `routers/fleet.py` | `/api/fleet` | Fleet listing, agent detail |
| `routers/compliance.py` | `/api/compliance`, `/api/agents/{id}/compliance` | Compliance checks, gate, matrix |
| `routers/audit.py` | `/api/audit` | Audit trail, export, verification, entry creation |
| `routers/users.py` | `/api/users` | User CRUD, bootstrap |
| `routers/tasks.py` | `/api/tasks` | Task CRUD |
| `routers/approvals.py` | `/api/approvals` | Approval workflow (create, approve, reject) |
| `routers/costs.py` | `/api/costs` | Cost tracking per agent |
| `routers/budget.py` | `/api/budget` | Budget check and tracking |
| `routers/pii.py` | `/api/pii` | PII filtering |
| `routers/incidents.py` | `/api/incidents` | Incident CRUD |
| `routers/workspace.py` | `/api/workspace` | Workspace mount/unmount |
| `routers/dsgvo.py` | `/api/dsgvo` | DSGVO forget and export |
| `routers/proxy.py` | `/api/proxy` | LLM proxy status, chat relay (auth + agent-ownership) |
| `routers/settings.py` | `/api/settings` | System settings (GET admin-gated) |
| `routers/monitoring.py` | `/api/monitoring` | Metrics, alerts, alert-rules (**admin-only**) |
| `routers/system.py` | `/api/system` | Setup-wizard status + bootstrap-only unseal-key |

> Auth verified in source: `routers/monitoring.py:34,40` (every endpoint
> `Depends(require_admin)`), `routers/proxy.py:34,126,147`
> (`get_current_user` + `check_agent_access(user, agent, "chat")`),
> `routers/settings.py:56,59,154` (GET behind `_require_admin`),
> `routers/system.py:129-156` (unseal-key: 403 once an admin exists,
> 410 after one-shot serve), `routers/agents.py:78-226`
> (`check_agent_access` on patch/pause/resume/kill/retire).

#### ORM Models

| Model | Table | Description |
|-------|-------|-------------|
| `Agent` | `agents` | Agent registry with manifest, status, compliance state |
| `AuditLog` | `audit_log` | Queryable index of audit chain entries |
| `IncidentRecord` | `incidents` | Security and compliance incidents |
| `User` | `users` | User accounts with roles and 2FA |
| `Task` | `tasks` | Task assignments for agents |
| `Approval` | `approvals` | Approval workflow records |
| `ConfigRevision` | `config_revisions` | Configuration change history |
| `AgentMemory` | `agent_memory` | Agent conversation/context memory |
| `WorkspaceMount` | `workspace_mounts` | Mounted workspace directories |

#### Auth Flow

Two authentication mechanisms run in parallel:

1. **JWT Cookie (browser)** — `POST /api/auth/login` returns a signed JWT in an HttpOnly cookie. The console uses this for all subsequent requests. Supports optional 2FA via TOTP.
2. **X-NomOS-API-Key (plugin/service)** — The OpenClaw plugin and external services authenticate via an API key header. Configured per-environment.

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
| `logging_config.py` | Structured JSON diagnostics logger; `NOMOS_LOG_LEVEL`-driven, writes to stderr (stdout reserved for `rich` UX) |
| `cli.py` | Click CLI: `hire`, `verify`, `fleet`, `gate`, `audit`, plus API-backed `pause`, `resume`, `retire`, `forget`, `assign`, `costs`, `incidents`, `workspace mount/unmount` |

> The CLI emits two streams: user-facing output via `rich`/`click.echo`
> on **stdout** (unchanged UX), and structured JSON diagnostics on
> **stderr** via `nomos.logging_config`. Verbosity: env `NOMOS_LOG_LEVEL`
> (DEBUG/INFO/WARNING/ERROR, case-insensitive; invalid → INFO + warning).
> The JSON record shape (`timestamp`/`level`/`logger`/`message`,
> `exception` when present) mirrors the API's
> `nomos-api/nomos_api/middleware/logging.py` JSONFormatter.

### nomos-console (Next.js 15 / React 19)

Web dashboard with 20 pages, dark mode default, bilingual DE/EN.

**Admin pages:** Dashboard, team, hire, approvals, costs, audit, compliance, diagnostics, incidents, users, tasks, settings.

**User pages:** Dashboard, chat, tasks, help.

Communicates with nomos-api via Next.js rewrites over the internal Docker network.

### nomos-plugin (TypeScript)

OpenClaw gateway plugin providing 11 hooks:

| Hook | Purpose |
|------|---------|
| `before-agent-start` | Compliance gate check before agent activation |
| `before-tool-call` | Policy enforcement before tool execution |
| `after-tool-call` | Audit logging after tool execution |
| `message-sending` | PII filtering on outbound messages |
| `message-received` | Input validation on inbound messages |
| `tool-result-persist` | Audit trail for tool results |
| `gateway-start` | Plugin initialization |
| `session-start` | Session tracking |
| `session-end` | Session cleanup |
| `agent-end` | Agent lifecycle completion |
| `on-error` | Error reporting and incident creation |

### PostgreSQL 16 + pgvector

Stores the agent registry, users, tasks, approvals, incidents, and indexed audit entries. The JSONL files on disk remain the source of truth for audit chain integrity.

### Valkey

BSD-3 licensed Redis replacement. Used for session caching, rate limiting, and ephemeral state.

### nomos-worker (ARQ on Valkey)

Background job processor. Runs `python -m arq
nomos_api.worker.main.WorkerSettings` (`docker-compose.yml:127-131`),
sharing the API codebase but with no HTTP port. Five cron jobs are
registered in `nomos-api/nomos_api/worker/main.py:62-83`:

| Job | Schedule | Purpose |
|-----|----------|---------|
| `retention_cleanup` | daily 03:00 | Data-retention enforcement |
| `detect_stale_agents` | every 5 min | Mark agents missing heartbeats |
| `check_incident_deadlines` | hourly | Art. 33/34 reporting deadlines |
| `expire_approvals` | every 10 min | Time out stale approval requests |
| `process_alerts` | every minute | Evaluate alert rules, raise alerts |

### Monitoring & Alerting

`routers/monitoring.py` exposes metrics, alerts and alert-rules under
`/api/monitoring`. **Every endpoint requires an admin user**
(`Depends(require_admin)`, `routers/monitoring.py:40,96,120,146,172,185,210`).
Alert evaluation is driven by the `process_alerts` worker cron. An
`APIMetricsMiddleware` records request metrics; metric-recording
failures are non-fatal (do not 500 the request).

### Context-Management Pipeline (wired into chat)

`nomos-api/nomos_api/services/context_pipeline.py` provides
`ContextPipeline` (chunker + summarizer + agent memory). It is wired
into the chat path: `routers/proxy.py:24-25,158-160` instantiates
`ContextPipeline` and uses managed context, and persists turns via
`memory.store_message(...)` (`routers/proxy.py:185,218`) so chat
retains history across requests.

### HashiCorp Vault

Secret management layer (KV v2). All credentials (DB passwords, JWT
secrets, API keys, gateway token) are stored in Vault and fetched at
startup via a Vault-first settings source. ENV vars serve as a
documented fallback path (e.g. `NOMOS_DB_PASSWORD` is also injected via
compose for the postgres init). Vault runs as its own compose service
(`docker-compose.yml:41,69`).

### Caddy (TLS reverse proxy)

`caddy:2-alpine` terminates TLS and fronts the console/API on ports
80/443 (`docker-compose.yml:219-228`), with the public domain set via
`NOMOS_DOMAIN` (default `localhost`). Automatic HTTPS in production.

---

## Data Flow

### Console to API

```
Browser → Next.js (port 3040) → rewrite /api/* → FastAPI (port 8060) → PostgreSQL
```

### Console to LLM (Chat)

```
Browser → Next.js → API Proxy (/api/proxy/chat) → OpenClaw Gateway (port 8080) → LLM Provider
```

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

### Authentication

- **JWT Cookie** — HttpOnly, Secure, SameSite=Strict. Issued on login,
  checked by global middleware.
- **API Key** — `X-NomOS-API-Key` header for plugin and
  service-to-service calls.
- **2FA** — Optional TOTP-based two-factor authentication with recovery
  codes.

### Authorization (RBAC + agent ownership)

Authorization is enforced per-router, not just authentication:

- **Admin-only:** the entire `/api/monitoring/*` surface requires an
  admin user (`require_admin`, `routers/monitoring.py:40+`). `GET
  /api/settings` is admin-gated (`routers/settings.py:59,154`).
- **Agent ownership / IDOR protection:** state-changing agent endpoints
  and chat resolve the target agent then call
  `check_agent_access(user, agent, <action>)`, which permits admins and
  the owning user only — `routers/proxy.py:147` (chat),
  `routers/agents.py:86,105,144,188,226` (patch/pause/resume/kill/retire).
- **Bootstrap-only unseal key:** `GET /api/system/unseal-key` returns
  403 once any admin user exists and 410 after a durable one-shot serve
  (`routers/system.py:129-156`) — it is never a standing public endpoint.

### Security headers & cookies

`SecurityHeadersMiddleware` (`middleware/security_headers.py`, added in
`main.py:48,208`) sets `X-Content-Type-Options: nosniff`,
`X-Frame-Options: DENY`, and `Strict-Transport-Security` (only when
cookie-secure / HTTPS is active). Session cookies are
`SameSite=Strict`.

### Redacted structured logging

The API JSON log formatter (`middleware/logging.py`) runs every message
and serialized exception through a redaction step that scrubs
token-like blobs, Bearer tokens and the values of known secret keys, so
Vault/LLM-provider exception bodies cannot leak credentials into the
log stream.

### Audit hash-chain HMAC

The on-disk hash chain supports an HMAC key, env-injectable via
`NOMOS_HASHCHAIN_HMAC_KEY` (`nomos-cli/nomos/core/hash_chain.py:30-43`),
inject from Vault in production. This makes the chain tamper-evident
against an attacker who can also recompute plain SHA-256 hashes.

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

The `POST /api/pii/filter` endpoint applies these rules at runtime. The DPIA document states filtering limitations per backend.

### Manifest Integrity

Each agent has a `manifest.sha256` file containing the SHA-256 hash of the manifest's canonical JSON representation. `nomos verify` checks this hash to detect tampering.

### Audit Chain Integrity

The hash chain is append-only. Each entry's hash depends on all previous entries. Verification recomputes every hash from scratch and checks the chain links. Any modification is detectable.

---

## Configuration

All secrets are managed via HashiCorp Vault KV v2. ENV vars serve as fallback in dev mode only.
No secret may appear as a default value in `config.py` or `docker-compose.yml`.

### Vault Secret Paths

| Secret Path | Description |
|-------------|-------------|
| `secret/nomos/db` | PostgreSQL credentials (`url`, `password`) |
| `secret/nomos/api` | API key for plugin/service-to-service auth |
| `secret/nomos/jwt` | JWT signing secret |

### Runtime ENV Variables (non-secret)

| Variable | Default | Description |
|----------|---------|-------------|
| `NOMOS_API_HOST` | `0.0.0.0` | API bind address |
| `NOMOS_API_PORT` | `8000` | API internal port (mapped to 8060 via Docker) |
| `NOMOS_API_TITLE` | `NomOS Fleet API` | API title |
| `NOMOS_API_VERSION` | `0.1.0` | API version |
| `NOMOS_CORS_ORIGINS` | `["http://localhost:3040"]` | Allowed CORS origins |
| `NOMOS_AGENTS_DIR` | `/data/agents` | Agent file storage directory (compose) |
| `NOMOS_VALKEY_URL` | `valkey://valkey:6379` | Valkey URL for rate limiting + ARQ (`docker-compose.yml:97,136`) |
| `NOMOS_GATEWAY_URL` | `http://openclaw-gateway:18789` | OpenClaw gateway base URL (compose-internal) |
| `NOMOS_LOG_LEVEL` | `INFO` | CLI diagnostics log level (DEBUG/INFO/WARNING/ERROR) |
| `NOMOS_DEV_MODE` | `false` | Dev fallbacks; production must be `false` |
| `NOMOS_COOKIE_SECURE` | `true` | Secure-cookie + HSTS toggle |
| `NOMOS_DOMAIN` | `localhost` | Public domain for Caddy TLS |
| `NOMOS_API_PORT` (docker-compose) | `8060` | External API port |
| `NOMOS_CONSOLE_PORT` (docker-compose) | `3040` | External console port |
| `NOMOS_GATEWAY_PORT` (docker-compose) | `3050` | External gateway port |

Secret env vars (injected from Vault in production; never defaulted in
code/compose): `NOMOS_JWT_SECRET`, `NOMOS_PLUGIN_API_KEY`,
`NOMOS_GATEWAY_TOKEN`, `NOMOS_DB_PASSWORD`,
`NOMOS_HASHCHAIN_HMAC_KEY`, and one LLM provider key
(`NVIDIA_API_KEY` / `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`).

> All secrets managed via HashiCorp Vault KV v2. ENV vars as fallback in dev mode only.
