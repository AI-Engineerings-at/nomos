# NomOS

> The agentic framework that enforces EU AI Act compliance — not by recommendation, but by design.

## Quick Start

```bash
cp .env.example .env
# Set NVIDIA_API_KEY or your LLM provider key
docker compose up -d
# Open http://localhost:3040 — Login: admin@nomos.local
```

## What is NomOS?

NomOS maps every requirement of the EU AI Act to an enforceable software control. It generates the compliance documents regulators expect, blocks deployment until those documents exist, and maintains a cryptographically verifiable audit trail. Built for organizations that deploy AI agents and need to prove compliance.

## Features

- **17 API routers** covering agents, fleet, compliance, audit, auth, users, tasks, approvals, costs, budget, PII, incidents, workspace, DSGVO, proxy, settings, health
- **20 Console pages** — Admin dashboard, team, hire, approvals, costs, audit, compliance, diagnostics, incidents, users, tasks, settings + User dashboard, chat, tasks, help
- **11 OpenClaw Plugin hooks** — before-agent-start, before-tool-call, after-tool-call, message-sending, message-received, tool-result-persist, gateway-start, session-start, session-end, agent-end, on-error
- **770+ tests** across all packages
- **Dark mode default**, bilingual DE/EN UI
- **Compliance Gate** — generates 5 required documents (DPIA, Art. 30, Art. 50, Art. 14, Art. 12), blocks deployment until signed
- **Hash Chain Audit** — SHA-256 tamper-evident trail, cryptographically verifiable
- **Fair Core License** — 3 agents free, full functionality; commercial license from 4+ agents

## Architecture

```
nomos/
├── nomos-api        Python 3.12 FastAPI — 17 routers, 47+ endpoints
├── nomos-cli        Python CLI — 5 commands, 6 core modules
├── nomos-console    Next.js 15 / React 19 — 20 pages (admin + user dashboard)
├── nomos-plugin     TypeScript — OpenClaw gateway plugin, 11 hooks
├── schemas/         YAML schema templates for agent manifests
└── templates/       Agent role templates (external-secretary, etc.)
```

**Data flow:**
```
Console → Next.js rewrite → FastAPI → PostgreSQL
Console → API Proxy → OpenClaw Gateway → LLM Provider
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12 (FastAPI, Pydantic v2, SQLAlchemy async) |
| Frontend | TypeScript strict (Next.js 15, React 19) |
| Database | PostgreSQL 16 + pgvector |
| Cache | Valkey (BSD-3 Redis replacement) |
| Gateway | OpenClaw (LLM provider agnostic) |
| Voice (optional) | Piper TTS (MIT) + Whisper.cpp (MIT) |
| Deployment | Docker Compose |
| CI/CD | GitHub Actions |

## CLI

```bash
# Create a new agent
nomos hire --name "Mani Ruf" --role external-secretary \
  --company "Acme GmbH" --email mani@acme.at \
  --output-dir ./data/agents/mani-ruf

# Generate required compliance documents
nomos gate --agent-dir ./data/agents/mani-ruf

# Verify full compliance (schema + docs + hash + chain)
nomos verify --agent-dir ./data/agents/mani-ruf

# List all agents
nomos fleet --agents-dir ./data/agents

# Show audit trail
nomos audit --agent-dir ./data/agents/mani-ruf

# Verify audit chain integrity
nomos audit --agent-dir ./data/agents/mani-ruf --verify
```

## API

Base URL: `http://localhost:8060`

See [API Reference](docs/api-reference.md) for all 47+ endpoints grouped by domain (health, auth, agents, fleet, compliance, audit, users, tasks, approvals, costs, budget, PII, incidents, workspace, DSGVO, proxy, settings).

## Pricing (FCL — Fair Core License)

| Plan | Agents | Details |
|------|--------|---------|
| Free | Up to 3 | Full functionality, all features |
| Commercial | 4+ | Commercial license required |

## Documentation

| Document | Description |
|----------|-------------|
| [Quickstart](docs/quickstart.md) | Get running in 5 minutes |
| [API Reference](docs/api-reference.md) | Complete REST API documentation (47+ endpoints) |
| [CLI Reference](docs/cli-reference.md) | All 5 CLI commands with flags and examples |
| [Architecture](docs/architecture.md) | System design, data flow, database schema, security model |
| [Compliance Guide](docs/compliance-guide.md) | EU AI Act + DSGVO coverage — what's implemented, what's not |

**Deutsch:**

| Dokument | Beschreibung |
|----------|-------------|
| [Schnellstart](docs/de/schnellstart.md) | In 5 Minuten starten |
| [API-Referenz](docs/de/api-referenz.md) | Vollstaendige REST API Dokumentation |
| [CLI-Referenz](docs/de/cli-referenz.md) | Alle 5 CLI-Befehle mit Flags und Beispielen |
| [Architektur](docs/de/architektur.md) | System-Design, Datenfluss, Datenbank-Schema, Sicherheitsmodell |
| [Compliance-Leitfaden](docs/de/compliance-leitfaden.md) | EU AI Act + DSGVO Abdeckung |

## License

Fair Source License v1.0 — free for up to 3 AI Agents.
Commercial license required for 4+. See [LICENSE](LICENSE) for details.

## Built by

[AI Engineering](https://ai-engineering.at) — Vienna, Austria.
