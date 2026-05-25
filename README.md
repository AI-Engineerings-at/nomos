<h1 align="center">aie-audit-chain</h1>

<p align="center">
  <strong>Server-side hash-chain audit-trail for EU AI Act compliance.</strong>
</p>

<p align="center">
  Part of the AIE audit-stack: <a href="https://github.com/AI-Engineering-at/aie-audit-primitives">aie-audit-primitives</a>
  · <a href="https://github.com/AI-Engineering-at/aie-hash-chain">aie-hash-chain</a>
  · <strong>aie-audit-chain</strong>.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/EU_AI_Act-Art._12-blue?style=for-the-badge" alt="EU AI Act Art. 12">
  <img src="https://img.shields.io/badge/RFC_6962-Merkle_log-blue?style=for-the-badge" alt="RFC 6962">
  <img src="https://img.shields.io/badge/Ed25519-signed-blue?style=for-the-badge" alt="Ed25519">
  <img src="https://img.shields.io/badge/HMAC--SHA256-fail--closed-green?style=for-the-badge" alt="HMAC-SHA256">
  <img src="https://img.shields.io/badge/License-Fair_Source_v1.0-green?style=for-the-badge" alt="License">
</p>

---

> *"Jeder entwickelt fuer sich, wir fuer alle."*
>
> aie-audit-chain enforces EU AI Act Art. 12 (record-keeping) by design — not by recommendation. Every audit entry is tamper-evident, individually verifiable, and externally anchorable. A regulator can verify a single event with just the public key.

---

## What is aie-audit-chain?

aie-audit-chain is the **server-side audit-trail component** of the AIE
audit-stack. It records every compliance-relevant event (agent action,
gate decision, PII redaction, budget breach, incident) into a
tamper-evident hash chain with per-entry Ed25519 signatures and an
RFC 6962 Merkle transparency log.

It ships as a deployable service (FastAPI on Python 3.12, PostgreSQL,
Valkey, HashiCorp Vault) and exposes verification endpoints any third
party can call without database access.

### Why "audit-chain"?

Three layers, three repos:

| Layer | Repo | Role |
|-------|------|------|
| Crypto primitives | [`aie-audit-primitives`](https://github.com/AI-Engineering-at/aie-audit-primitives) | Shared Ed25519 / HMAC / Merkle building blocks |
| Hash chain (PyPI) | [`aie-hash-chain`](https://github.com/AI-Engineering-at/aie-hash-chain) | Reusable Python library for hash-chain entries |
| **Audit chain (service)** | **`aie-audit-chain`** | **Deployable service + STH + inclusion proofs + retention + anchoring** |

### Rename note (2026-05-24, DEC-020)

This repo was previously named `nomos` / `NomOS`. The wider
"compliance control plane" scope (`nomos-api`, `nomos-cli`,
`nomos-console`, `nomos-plugin`) was narrowed to its load-bearing
audit-trail core. The remaining surface — fleet management, compliance
gate, console UI, OpenClaw plugin — is being unbundled into separate
repos and may be re-introduced as `aie-*` siblings. Until then the
`nomos-api/`, `nomos-cli/`, `nomos-console/`, `nomos-plugin/` source
trees in this repo still carry the historical names; the public name
of the deliverable is **aie-audit-chain**. See [CHANGELOG](CHANGELOG.md)
2026-05-24 for the full rename trail.

---

## Quick Start

```bash
git clone https://github.com/AI-Engineering-at/aie-audit-chain.git
cd aie-audit-chain
cp .env.example .env
# Set the required secrets + an LLM provider key, then:
docker compose up -d
```

Open **http://localhost:3040**. On first run, create the admin account
via the bootstrap form (or `POST /api/users/bootstrap`). See the
[Quickstart](docs/quickstart.md) for required env vars and the full
flow.

---

## Audit-Trail v2 — Key Properties

- **Hash chain** — Each entry includes the previous entry's hash;
  any tamper invalidates the chain from that point forward.
- **HMAC-SHA256 per entry** — `AUDIT_CHAIN_HMAC_KEY`, fail-closed.
  Detects integrity violations without exposing private keys.
- **Ed25519 per entry** — `AUDIT_CHAIN_SIGNING_KEY`, fail-closed.
  Third parties can verify an entry with only the public key.
- **RFC 6962 Merkle transparency log** — Signed Tree Head (STH) +
  inclusion-proof endpoints. O(log n) verification cost; no DB
  access required for the verifier.
- **External anchoring** — Hourly anchor head + daily integrity
  checkpoint via ARQ worker.
- **Retention floor** — 180 days per EU AI Act Art. 12.

See [CHANGELOG](CHANGELOG.md) 0.2.0 for the v2 cut-over and
[Hardening Plan 2026-05-20](docs/hardening-2026-05-20/PLAN.md) for the
A1-A6 + B1 roadmap (all shipped).

---

## Architecture

```
                        +------------------+
                        |    Browser       |
                        |  localhost:3040  |
                        +--------+---------+
                                 |
                    +------------+------------+
                    |       Console           |
                    |    (Next.js 15)         |
                    +------------+------------+
                                 |
              +------------------+------------------+
              |                                     |
   +----------+----------+            +-------------+-------------+
   |       API           |            |   Agent Gateway           |
   |   (FastAPI)         |            |   (headless, plugin)      |
   |   19 Routers        |            |   11 Runtime Hooks        |
   |   47+ Endpoints     |            |   Audit Entry Producer    |
   +----------+----------+            +-------------+-------------+
              |                                     |
   +----------+----------+            +-------------+-------------+
   |   PostgreSQL 16     |            |   LLM Provider            |
   |   + pgvector        |            |   (any: NVIDIA, OpenAI,   |
   +---------------------+            |    Anthropic, local)      |
   |   Valkey (Cache)    |            +---------------------------+
   +---------------------+
   |   HashiCorp Vault   |
   +---------------------+
```

### Audit-entry flow

```
Agent action --> Plugin hook --> API --> aie-hash-chain --> PostgreSQL
                                            |
                                            +--> Ed25519 sign (Vault key)
                                            +--> HMAC-SHA256 (Vault key)
                                            +--> Merkle leaf -> STH
                                            +--> ARQ: hourly anchor + daily checkpoint
```

---

## Security

- **HashiCorp Vault** integration for all secrets (JWT, API keys,
  gateway token, DB password, audit signing key, audit HMAC key) —
  Vault-first settings source, runs as its own compose service.
- **Caddy TLS** — automatic HTTPS reverse proxy on 80/443
  (`AUDIT_CHAIN_DOMAIN`).
- **RBAC + agent ownership** — `/api/monitoring/*` and
  `GET /api/settings` are admin-only; agent state-change and chat
  endpoints enforce agent ownership (`check_agent_access`); heartbeat
  requires the agent-actor principal.
- **Hardened HTTP** — `SecurityHeadersMiddleware` (nosniff, X-Frame
  DENY, HSTS on HTTPS), `SameSite=Strict` session cookies, redacted
  structured logging.
- **Rate Limiting** — Valkey-backed distributed rate limiter.
- **ARQ worker** — 7 cron jobs (retention, stale-agent detection,
  incident deadlines, approval expiry, alert processing, **audit
  anchor head** hourly, **audit integrity checkpoint** daily).
- **Monitoring & Alerting** — admin-only metrics/alerts/alert-rules
  under `/api/monitoring`.
- **11 runtime hooks** — Every agent action passes through compliance,
  audit, PII, and budget checks before execution.

---

## Source layout

```
aie-audit-chain/
 |- nomos-api/        Python 3.12 FastAPI — 19 router modules (incl. monitoring, system)
 |- nomos-cli/        Python CLI — local + API-backed commands, structured logging
 |- nomos-console/    Next.js 15 / React 19 — 20 pages (admin + user)
 |- nomos-plugin/     TypeScript — agent gateway plugin, 11 hooks
 |- schemas/          YAML schema templates for agent manifests
 +- templates/        Agent role templates
```

> The `nomos-*` directory names are historical and will be renamed in
> a follow-up cut. See the rename note above.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | Python 3.12, FastAPI, Pydantic v2 | API, audit-chain logic |
| Frontend | TypeScript strict, Next.js 15, React 19 | Console UI (dark mode default) |
| Database | PostgreSQL 16 + pgvector | Persistent audit storage + embeddings |
| Cache | Valkey (BSD-3 Redis replacement) | Rate limiting, sessions, events |
| Secrets | HashiCorp Vault | JWT, API keys, audit signing key, HMAC key |
| Gateway | OpenClaw 2026.5.18 (pinned in `nomos-plugin/Dockerfile.gateway`) | LLM-provider-agnostic agent runtime |
| Sandbox | NemoClaw (optional) | Container isolation for agents |
| CI/CD | GitHub Actions | 5-stage pipeline (lint, test, quality, build, summary) |

---

## CLI

```bash
aie-audit hire    --name "Mani" --role external-secretary   # Create agent (local)
aie-audit gate    --agent-dir ./data/agents/mani            # Generate compliance docs
aie-audit verify  --agent-dir ./data/agents/mani            # Verify full compliance
aie-audit fleet   --agents-dir ./data/agents                # List local agents
aie-audit audit   --agent-dir ./data/agents/mani --verify   # Verify audit chain
```

> CLI binary is still installed as `nomos` from `nomos-cli/` during
> the rename transition. Set `AUDIT_CHAIN_LOG_LEVEL`
> (DEBUG/INFO/WARNING/ERROR) for structured JSON logs on stderr;
> normal output stays on stdout.

---

## API

Base URL: `http://localhost:8060`

| Domain | Endpoints | Description |
|--------|-----------|-------------|
| Auth | `/api/auth/*` | JWT login, 2FA, recovery keys |
| Agents | `/api/agents/*` | CRUD, hire, pause, resume, terminate |
| Fleet | `/api/fleet/*` | Fleet overview, status aggregation |
| Compliance | `/api/compliance/*` | Gate checks, document generation |
| **Audit** | `/api/audit/*`, `/api/agents/{id}/audit/sth`, `/api/agents/{id}/audit/proof/{n}` | **Hash chain entries, verification, Signed Tree Head, inclusion proofs (RFC 6962)** |
| Users | `/api/users/*` | RBAC user management |
| Tasks | `/api/tasks/*` | Task dispatch and tracking |
| Approvals | `/api/approvals/*` | Human-in-the-loop approval workflow |
| Costs | `/api/costs/*` | Per-agent cost tracking |
| Budget | `/api/budget/*` | Budget limits and alerts |
| PII | `/api/pii/*` | Personal data detection and filtering |
| Incidents | `/api/incidents/*` | Incident management (Art. 14) |
| DSGVO | `/api/dsgvo/*` | Right to erasure (Art. 17) |
| Settings | `/api/settings` | System configuration (GET admin-only) |
| Monitoring | `/api/monitoring/*` | Metrics, alerts, alert-rules (**admin-only**) |
| System | `/api/system/*` | Setup-wizard status + bootstrap-only unseal key |
| Health | `/api/health` | Service health + Vault/PG/Valkey/gateway status |

See [API Reference](docs/api-reference.md) for the authoritative
endpoint and authorization table.

---

## Public verification

A third party (regulator, auditor, customer) can verify a single audit
entry without database access:

1. Fetch the current Signed Tree Head:
   `GET /api/agents/{id}/audit/sth`
2. Fetch the inclusion proof for entry `n`:
   `GET /api/agents/{id}/audit/proof/{n}`
3. Verify the proof against the STH using the published Ed25519
   public key.

A reference verifier and end-user verify page is hosted at
**https://verify.ai-engineering.at**.

---

## Documentation

| Document | Description |
|----------|-------------|
| [Quickstart](docs/quickstart.md) | Get running in 5 minutes |
| [API Reference](docs/api-reference.md) | Complete REST API (49+ endpoints, incl. STH + inclusion-proof) |
| [CLI Reference](docs/cli-reference.md) | All commands with examples |
| [Architecture](docs/architecture.md) | System design, data flow, security |
| [Operations Runbook](docs/operations-runbook.md) | Bring-up, healthchecks, secrets, backup, audit-key rotation, regulator export, troubleshooting |
| [Compliance Guide](docs/compliance-guide.md) | EU AI Act + DSGVO coverage, Audit-Trail v2 Phase-B1 |
| [Hardening Plan 2026-05-20](docs/hardening-2026-05-20/PLAN.md) | Audit-Trail v2 roadmap (A1-A6 + B1 shipped) |
| [CHANGELOG](CHANGELOG.md) | Release history per component |

**Deutsch:** see [README.de.md](README.de.md).

---

## Deployment Tiers

| Tier | Target | How |
|------|--------|-----|
| **Enterprise VPS** | Managed hosting | We deploy and maintain |
| **Docker Self-Hosted** | Your server | `docker compose up -d` |
| **Open Source** | Community | Fork and customize |

---

## License

**Fair Source License v1.0** — Free for up to 3 AI Agents. Commercial
license required for 4+.

See [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with discipline by <a href="https://ai-engineering.at"><strong>AI Engineering</strong></a> — Vienna, Austria.
</p>
