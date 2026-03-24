# NomOS API Reference

Base URL: `http://localhost:8060`

All endpoints return JSON. The API is built with FastAPI and provides automatic OpenAPI documentation at `/docs` (Swagger UI) and `/redoc` (ReDoc) when running.

---

## Health

### GET /health

Check service health and version.

**Response:** `200 OK`

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Service status (`"ok"`) |
| `service` | string | Service name (`"NomOS Fleet API"`) |
| `version` | string | API version (`"0.1.0"`) |

**Example:**

```bash
curl http://localhost:8060/health
```

```json
{
  "status": "ok",
  "service": "NomOS Fleet API",
  "version": "0.1.0"
}
```

---

## Agents

### POST /api/agents

Create a new AI agent. Generates the agent directory with manifest, compliance folder, and audit chain. Persists the agent to the database.

**Request body:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | yes | — | Agent name (1-256 chars), e.g. `"Mani Ruf"` |
| `role` | string | yes | — | Agent role (1-256 chars), e.g. `"external-secretary"` |
| `company` | string | yes | — | Company name (1-256 chars), e.g. `"Acme GmbH"` |
| `email` | string | yes | — | Contact email, e.g. `"mani@acme.at"` |
| `risk_class` | string | no | `"limited"` | EU AI Act risk class: `"minimal"`, `"limited"`, or `"high"` |

**Response:** `201 Created`

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Generated agent ID (slugified from name) |
| `name` | string | Agent name |
| `role` | string | Agent role |
| `company` | string | Company name |
| `email` | string | Contact email |
| `risk_class` | string | EU AI Act risk class |
| `status` | string | Agent status (`"created"`) |
| `manifest_hash` | string | SHA-256 hash of the agent manifest |
| `compliance_status` | string | Current compliance status (`"pending"`, `"passed"`, `"blocked"`) |
| `created_at` | string | ISO 8601 creation timestamp |
| `updated_at` | string | ISO 8601 last update timestamp |

**Error:** `400 Bad Request` if agent directory already exists or validation fails.

**Example:**

```bash
curl -X POST http://localhost:8060/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mani Ruf",
    "role": "external-secretary",
    "company": "Acme GmbH",
    "email": "mani@acme.at",
    "risk_class": "limited"
  }'
```

```json
{
  "id": "mani-ruf",
  "name": "Mani Ruf",
  "role": "external-secretary",
  "company": "Acme GmbH",
  "email": "mani@acme.at",
  "risk_class": "limited",
  "status": "created",
  "manifest_hash": "a1b2c3d4e5f6...",
  "compliance_status": "blocked",
  "created_at": "2026-03-24T10:00:00+00:00",
  "updated_at": "2026-03-24T10:00:00+00:00"
}
```

Note: `compliance_status` is `"blocked"` after creation because compliance documents have not been generated yet. Run the compliance gate to generate them.

---

## Fleet

### GET /api/fleet

List all agents in the fleet registry.

**Response:** `200 OK`

| Field | Type | Description |
|-------|------|-------------|
| `agents` | array | List of `AgentResponse` objects |
| `total` | integer | Total number of agents |

**Example:**

```bash
curl http://localhost:8060/api/fleet
```

```json
{
  "agents": [
    {
      "id": "mani-ruf",
      "name": "Mani Ruf",
      "role": "external-secretary",
      "company": "Acme GmbH",
      "email": "mani@acme.at",
      "risk_class": "limited",
      "status": "created",
      "manifest_hash": "a1b2c3d4e5f6...",
      "compliance_status": "passed",
      "created_at": "2026-03-24T10:00:00+00:00",
      "updated_at": "2026-03-24T10:15:00+00:00"
    }
  ],
  "total": 1
}
```

### GET /api/fleet/{agent_id}

Get details for a single agent.

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | string | Agent ID (e.g. `"mani-ruf"`) |

**Response:** `200 OK` — `AgentResponse` object (same schema as in fleet list).

**Error:** `404 Not Found` if agent does not exist.

**Example:**

```bash
curl http://localhost:8060/api/fleet/mani-ruf
```

```json
{
  "id": "mani-ruf",
  "name": "Mani Ruf",
  "role": "external-secretary",
  "company": "Acme GmbH",
  "email": "mani@acme.at",
  "risk_class": "limited",
  "status": "created",
  "manifest_hash": "a1b2c3d4e5f6...",
  "compliance_status": "passed",
  "created_at": "2026-03-24T10:00:00+00:00",
  "updated_at": "2026-03-24T10:15:00+00:00"
}
```

---

## Compliance

### GET /api/agents/{agent_id}/compliance

Check compliance status for an agent. Reads the manifest and verifies all required documents exist.

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | string | Agent ID |

**Response:** `200 OK`

| Field | Type | Description |
|-------|------|-------------|
| `agent_id` | string | Agent ID |
| `status` | string | `"passed"`, `"warning"`, or `"blocked"` |
| `missing_documents` | array | List of missing document names |
| `errors` | array | Blocking error messages |
| `warnings` | array | Non-blocking warning messages |

**Error:** `404 Not Found` if agent does not exist. `400 Bad Request` if agent directory is invalid.

**Example:**

```bash
curl http://localhost:8060/api/agents/mani-ruf/compliance
```

```json
{
  "agent_id": "mani-ruf",
  "status": "blocked",
  "missing_documents": [
    "dpia",
    "verarbeitungsverzeichnis",
    "art50_transparency",
    "art14_killswitch",
    "art12_logging"
  ],
  "errors": [
    "Missing 5 required document(s): dpia, verarbeitungsverzeichnis, art50_transparency, art14_killswitch, art12_logging"
  ],
  "warnings": []
}
```

### POST /api/agents/{agent_id}/gate

Generate all required compliance documents for an agent and re-check compliance. This is the API equivalent of `nomos gate`.

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | string | Agent ID |

**Request body:** None.

**Response:** `200 OK` — Same schema as `GET /api/agents/{agent_id}/compliance`.

After successful generation, the response `status` will be `"passed"` and `missing_documents` will be empty.

**Error:** `404 Not Found` if agent does not exist. `400 Bad Request` if agent directory is invalid.

**Example:**

```bash
curl -X POST http://localhost:8060/api/agents/mani-ruf/gate
```

```json
{
  "agent_id": "mani-ruf",
  "status": "passed",
  "missing_documents": [],
  "errors": [],
  "warnings": []
}
```

---

## Audit

### GET /api/agents/{agent_id}/audit

Get the full audit trail for an agent. Returns all entries from the database, ordered by sequence number.

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | string | Agent ID |

**Response:** `200 OK`

| Field | Type | Description |
|-------|------|-------------|
| `agent_id` | string | Agent ID |
| `entries` | array | List of audit entries |
| `total` | integer | Total number of entries |

Each entry contains:

| Field | Type | Description |
|-------|------|-------------|
| `sequence` | integer | Entry sequence number (0-based) |
| `event_type` | string | Event type (e.g. `"agent.created"`) |
| `agent_id` | string | Agent ID |
| `data` | object | Event-specific data |
| `chain_hash` | string | SHA-256 hash of this entry |
| `timestamp` | string | ISO 8601 UTC timestamp |

**Error:** `404 Not Found` if agent does not exist.

**Example:**

```bash
curl http://localhost:8060/api/agents/mani-ruf/audit
```

```json
{
  "agent_id": "mani-ruf",
  "entries": [
    {
      "sequence": 0,
      "event_type": "agent.created",
      "agent_id": "mani-ruf",
      "data": {
        "name": "Mani Ruf",
        "role": "external-secretary",
        "company": "Acme GmbH",
        "risk_class": "limited",
        "manifest_hash": "a1b2c3d4e5f6..."
      },
      "chain_hash": "e4f5a6b7c8d9...",
      "timestamp": "2026-03-24T10:00:00.123456+00:00"
    }
  ],
  "total": 1
}
```

### GET /api/audit/verify/{agent_id}

Cryptographically verify the audit chain for an agent. Reads the JSONL chain file from disk, recomputes every hash, and verifies chain integrity.

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | string | Agent ID |

**Response:** `200 OK`

| Field | Type | Description |
|-------|------|-------------|
| `agent_id` | string | Agent ID |
| `valid` | boolean | `true` if chain is intact, `false` if tampered |
| `entries_checked` | integer | Number of entries verified |
| `errors` | array | List of verification errors (empty if valid) |

**Error:** `404 Not Found` if agent does not exist. `400 Bad Request` if agent directory is invalid.

**Example:**

```bash
curl http://localhost:8060/api/audit/verify/mani-ruf
```

```json
{
  "agent_id": "mani-ruf",
  "valid": true,
  "entries_checked": 1,
  "errors": []
}
```

---

## Event Types

The audit trail uses these canonical event types:

| Event Type | Description |
|------------|-------------|
| `agent.created` | Agent was created via `nomos hire` or POST /api/agents |
| `agent.deployed` | Agent was deployed |
| `agent.stopped` | Agent was stopped |
| `agent.retired` | Agent was retired |
| `compliance.check.passed` | Compliance check passed |
| `compliance.check.failed` | Compliance check failed |
| `compliance.doc.signed` | Compliance document was signed |
| `governance.hook.triggered` | Governance hook was triggered |
| `governance.hook.blocked` | Governance hook blocked an action |
| `governance.kill_switch` | Kill switch was activated |
| `governance.escalation` | Escalation was triggered |
| `audit.chain.created` | Audit chain was initialized |
| `audit.chain.verified` | Audit chain was verified |
| `audit.exported` | Audit trail was exported |

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

| Status Code | Meaning |
|-------------|---------|
| `400` | Bad request (validation error, invalid directory) |
| `404` | Resource not found (agent does not exist) |
| `422` | Validation error (invalid request body) |
| `500` | Internal server error |
