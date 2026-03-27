# NomOS API Reference

Base URL: `http://localhost:8060`

All endpoints return JSON. The API is built with FastAPI and provides automatic OpenAPI documentation at `/docs` (Swagger UI) and `/redoc` (ReDoc) when running.

**Authentication:** Most endpoints require either a JWT cookie (browser sessions) or an `X-NomOS-API-Key` header (plugin/service calls). Exceptions are noted below.

---

## Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | No | Service health check (status, service name, version) |
| `GET` | `/api/health` | No | Alias — same response as `/health` |

---

## Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/auth/login` | No | Authenticate with email + password, returns JWT cookie; includes `requires_2fa` flag |
| `GET` | `/api/auth/me` | JWT | Return the currently authenticated user |
| `POST` | `/api/auth/logout` | JWT | Clear the JWT cookie and end the session |
| `POST` | `/api/auth/2fa/setup` | JWT | Generate TOTP secret and QR code for 2FA enrollment |
| `POST` | `/api/auth/2fa/verify` | JWT | Verify a TOTP code to complete 2FA setup or login |
| `POST` | `/api/auth/recovery` | No | Authenticate using a recovery code when 2FA device is unavailable |

---

## Agents

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/agents` | JWT/Key | Create a new agent (manifest, hash chain, DB record) |
| `PATCH` | `/api/agents/{id}` | JWT/Key | Update agent fields (role, risk class, status, etc.) |
| `POST` | `/api/agents/{id}/heartbeat` | JWT/Key | Record an agent heartbeat (marks agent as alive) |
| `POST` | `/api/agents/{id}/pause` | JWT/Key | Pause a running agent |
| `POST` | `/api/agents/{id}/resume` | JWT/Key | Resume a paused agent |
| `POST` | `/api/agents/{id}/kill` | JWT/Key | Immediately terminate an agent (kill switch) |
| `POST` | `/api/agents/{id}/retire` | JWT/Key | Retire an agent permanently |

---

## Fleet

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/fleet` | JWT/Key | List all agents in the fleet registry |
| `GET` | `/api/fleet/{id}` | JWT/Key | Get details for a single agent |

---

## Compliance

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/agents/{id}/compliance` | JWT/Key | Check compliance status for an agent |
| `POST` | `/api/agents/{id}/gate` | JWT/Key | Generate compliance documents and re-check |
| `GET` | `/api/compliance/matrix` | JWT/Key | Compliance matrix across all agents |
| `POST` | `/api/compliance/gate` | JWT/Key | Alias — run compliance gate (plugin compatibility) |

---

## Audit

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/audit` | JWT/Key | List audit entries (filterable by agent, event type, date range) |
| `GET` | `/api/agents/{id}/audit` | JWT/Key | Get the full audit trail for a specific agent |
| `GET` | `/api/agents/{id}/audit/export` | JWT/Key | Export agent audit trail (downloadable format) |
| `GET` | `/api/audit/verify/{id}` | JWT/Key | Cryptographically verify audit chain integrity for an agent |
| `POST` | `/api/audit/entry` | JWT/Key | Manually append an entry to the audit trail |

---

## Users

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/users` | JWT | List all users |
| `POST` | `/api/users` | JWT | Create a new user account |
| `PATCH` | `/api/users/{id}` | JWT | Update user fields (role, email, status) |
| `DELETE` | `/api/users/{id}` | JWT | Delete a user account |
| `POST` | `/api/users/bootstrap` | No | Create the initial admin user (only works when no users exist) |

---

## Tasks

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/tasks` | JWT/Key | List tasks (filterable by agent, status) |
| `GET` | `/api/tasks/{id}` | JWT/Key | Get a single task by ID |
| `POST` | `/api/tasks` | JWT/Key | Create a new task assignment |
| `PATCH` | `/api/tasks/{id}` | JWT/Key | Update task status or fields |

---

## Approvals

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/approvals` | JWT | List pending and resolved approvals |
| `POST` | `/api/approvals` | JWT/Key | Create a new approval request |
| `POST` | `/api/approvals/{id}/approve` | JWT | Approve a pending request |
| `POST` | `/api/approvals/{id}/reject` | JWT | Reject a pending request |

---

## Costs

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/costs` | JWT/Key | List cost records (filterable by agent, date range) |
| `GET` | `/api/costs/{id}` | JWT/Key | Get cost details for a specific agent |

---

## Budget

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/budget/check` | JWT/Key | Check whether an action fits within the configured budget |
| `POST` | `/api/budget/track` | JWT/Key | Record a cost event against the budget |

---

## PII

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/pii/filter` | JWT/Key | Apply PII masking rules to a text payload |

---

## Incidents

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/incidents` | JWT/Key | List incidents (filterable by severity, status) |
| `POST` | `/api/incidents` | JWT/Key | Create a new incident record |
| `PATCH` | `/api/incidents/{id}` | JWT/Key | Update incident status or resolution |

---

## Workspace

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/workspace/{id}` | JWT/Key | Get workspace mount details for an agent |
| `POST` | `/api/workspace/mount` | JWT/Key | Mount a workspace directory for an agent |
| `POST` | `/api/workspace/unmount` | JWT/Key | Unmount a workspace directory |

---

## DSGVO

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/dsgvo/forget` | JWT | DSGVO Art. 17 — erase all personal data for a subject |
| `POST` | `/api/dsgvo/export` | JWT | DSGVO Art. 20 — export all personal data for a subject |

---

## Proxy

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/proxy/status` | JWT/Key | Check OpenClaw gateway connectivity |
| `POST` | `/api/proxy/chat` | JWT/Key | Relay a chat message through the OpenClaw gateway to the LLM |

---

## Settings

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/settings` | JWT | Retrieve current system settings |

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
| `401` | Unauthorized (missing or invalid JWT/API key) |
| `403` | Forbidden (insufficient permissions) |
| `404` | Resource not found |
| `422` | Validation error (invalid request body) |
| `500` | Internal server error |
