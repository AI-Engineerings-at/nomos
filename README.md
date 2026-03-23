# NomOS

> The agentic framework that enforces EU AI Act compliance — not by recommendation, but by design.

## Quick Start

**API (Docker):**
```bash
cd nomos-api
docker compose up -d
# API on http://localhost:8060, PostgreSQL + Redis included
```

**CLI:**
```bash
cd nomos-cli
pip install -e .

nomos hire --name "Mani Ruf" --role external-secretary \
  --company "Acme GmbH" --email mani@acme.at \
  --output-dir ./data/agents/mani-ruf

nomos gate --agent-dir ./data/agents/mani-ruf
nomos verify --agent-dir ./data/agents/mani-ruf
```

## What is NomOS?

NomOS maps every requirement of the EU AI Act to an enforceable software control. It generates the compliance documents regulators expect, blocks deployment until those documents exist, and maintains a cryptographically verifiable audit trail. Built for organizations that deploy AI agents and need to prove compliance.

## Features

| Feature | What it does | Legal basis |
|---------|-------------|-------------|
| `nomos hire` | Creates compliant AI agent from Name + Role + Company | Art. 26 EU AI Act (Deployer obligations) |
| Compliance Gate | Generates 5 required documents (DPIA, Art. 30, Art. 50, Art. 14, Art. 12) | Art. 35 DSGVO, Art. 30 DSGVO, Art. 50/14/12 EU AI Act |
| Blocking Gate | Agent cannot deploy without signed compliance docs | Art. 9 EU AI Act (Risk management) |
| Hash Chain Audit | SHA-256 tamper-evident trail, cryptographically verifiable | Art. 12 EU AI Act (Record-keeping) |
| `nomos verify` | Full compliance check: schema + docs + hash + chain integrity | Art. 11 EU AI Act (Technical documentation) |
| Fleet API | REST endpoints for agent management and compliance status | Art. 13 EU AI Act (Transparency) |
| Dashboard | Visual fleet management with agent detail and audit trail | Art. 14 EU AI Act (Human oversight) |

## Architecture

```
nomos/
├── nomos-cli        Python CLI — 5 commands, 6 core modules, 83 tests
├── nomos-api        FastAPI — 7 REST endpoints, Docker Compose (API + PostgreSQL + Redis), 14 tests
├── nomos-console    Next.js 15 — Fleet overview, agent detail, compliance check, audit trail
├── nomos-plugin     TypeScript — OpenClaw gateway plugin with /nomos commands
├── schemas/         YAML schema templates for agent manifests
└── templates/       Agent role templates (external-secretary, etc.)
```

**Data flow:**
```
nomos hire → Manifest + Hash → nomos gate → 5 Compliance Docs → nomos verify → PASS/FAIL
                                   ↓
                            Audit Trail (SHA-256 hash chain)
                                   ↓
                         Fleet API → Dashboard
```

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

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Service health check |
| `POST` | `/api/agents` | Create new agent |
| `GET` | `/api/fleet` | List all agents |
| `GET` | `/api/fleet/{agent_id}` | Get agent details |
| `GET` | `/api/agents/{agent_id}/compliance` | Check agent compliance |
| `GET` | `/api/agents/{agent_id}/audit` | Get agent audit trail |
| `GET` | `/api/audit/verify/{agent_id}` | Verify audit chain integrity |

## Installation

**CLI (Python 3.11+):**
```bash
cd nomos-cli
pip install -e .
nomos --version
```

**API (Docker):**
```bash
cd nomos-api
docker compose up -d
```

This starts three services:
- **nomos-api** on port 8060 (FastAPI)
- **PostgreSQL 16** with pgvector
- **Redis 8**

## Pricing

| Plan | Price | Agents | Features |
|------|-------|--------|----------|
| Free | EUR 0 | Up to 3 | Core compliance, community support |
| Starter | EUR 49/mo | Up to 10 | Priority support, advanced audit |
| Business | EUR 149/mo | Up to 50 | SSO, custom policies, SLA |
| Enterprise | EUR 29/agent/mo | Unlimited | Dedicated support, on-prem, custom integrations |

## License

Fair Source License v1.0 — free for up to 3 AI Agents.
Commercial license required for 4+. See [LICENSE](LICENSE) for details.

## Built by

[AI Engineering](https://ai-engineering.at) — Vienna, Austria.
