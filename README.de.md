# NomOS

> Das agentenbasierte Framework, das EU AI Act Compliance durchsetzt — nicht durch Empfehlung, sondern durch Design.

## Schnellstart

**API (Docker):**
```bash
cd nomos-api
docker compose up -d
# API auf http://localhost:8060, PostgreSQL + Redis inklusive
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

## Was ist NomOS?

NomOS bildet jede Anforderung des EU AI Act auf eine durchsetzbare Software-Kontrolle ab. Es generiert die Compliance-Dokumente die Regulierer erwarten, blockiert Deployment bis diese Dokumente existieren, und fuehrt einen kryptographisch verifizierbaren Audit-Trail. Gebaut fuer Organisationen, die AI Agents betreiben und Compliance nachweisen muessen.

## Features

| Feature | Was es tut | Rechtsgrundlage |
|---------|-----------|-----------------|
| `nomos hire` | Erstellt compliant AI Agent aus Name + Rolle + Firma | Art. 26 EU AI Act (Betreiberpflichten) |
| Compliance Gate | Generiert 5 Pflichtdokumente (DPIA, Art. 30, Art. 50, Art. 14, Art. 12) | Art. 35 DSGVO, Art. 30 DSGVO, Art. 50/14/12 EU AI Act |
| Blocking Gate | Agent kann ohne unterschriebene Compliance-Docs nicht deployt werden | Art. 9 EU AI Act (Risikomanagement) |
| Hash Chain Audit | SHA-256 manipulationssicherer Trail, kryptographisch verifizierbar | Art. 12 EU AI Act (Aufzeichnungspflicht) |
| `nomos verify` | Vollstaendige Compliance-Pruefung: Schema + Docs + Hash + Chain | Art. 11 EU AI Act (Technische Dokumentation) |
| Fleet API | REST-Endpoints fuer Agent-Verwaltung und Compliance-Status | Art. 13 EU AI Act (Transparenz) |
| Dashboard | Visuelle Fleet-Verwaltung mit Agent-Detail und Audit-Trail | Art. 14 EU AI Act (Menschliche Aufsicht) |

## Architektur

```
nomos/
├── nomos-cli        Python CLI — 5 Befehle, 6 Kernmodule, 83 Tests
├── nomos-api        FastAPI — 7 REST-Endpoints, Docker Compose (API + PostgreSQL + Redis), 14 Tests
├── nomos-console    Next.js 15 — Fleet-Uebersicht, Agent-Detail, Compliance-Check, Audit-Trail
├── nomos-plugin     TypeScript — OpenClaw Gateway-Plugin mit /nomos Befehlen
├── schemas/         YAML Schema-Templates fuer Agent-Manifeste
└── templates/       Agent-Rollen-Templates (external-secretary, etc.)
```

**Datenfluss:**
```
nomos hire → Manifest + Hash → nomos gate → 5 Compliance-Docs → nomos verify → PASS/FAIL
                                   ↓
                            Audit-Trail (SHA-256 Hash-Chain)
                                   ↓
                         Fleet API → Dashboard
```

## CLI

```bash
# Neuen Agent erstellen
nomos hire --name "Mani Ruf" --role external-secretary \
  --company "Acme GmbH" --email mani@acme.at \
  --output-dir ./data/agents/mani-ruf

# Pflicht-Compliance-Dokumente generieren
nomos gate --agent-dir ./data/agents/mani-ruf

# Vollstaendige Compliance pruefen (Schema + Docs + Hash + Chain)
nomos verify --agent-dir ./data/agents/mani-ruf

# Alle Agents auflisten
nomos fleet --agents-dir ./data/agents

# Audit-Trail anzeigen
nomos audit --agent-dir ./data/agents/mani-ruf

# Audit-Chain-Integritaet verifizieren
nomos audit --agent-dir ./data/agents/mani-ruf --verify
```

## API

Basis-URL: `http://localhost:8060`

| Methode | Endpoint | Beschreibung |
|---------|----------|-------------|
| `GET` | `/health` | Service Health-Check |
| `POST` | `/api/agents` | Neuen Agent erstellen |
| `GET` | `/api/fleet` | Alle Agents auflisten |
| `GET` | `/api/fleet/{agent_id}` | Agent-Details abrufen |
| `GET` | `/api/agents/{agent_id}/compliance` | Agent-Compliance pruefen |
| `GET` | `/api/agents/{agent_id}/audit` | Agent Audit-Trail abrufen |
| `GET` | `/api/audit/verify/{agent_id}` | Audit-Chain-Integritaet verifizieren |

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

Das startet drei Services:
- **nomos-api** auf Port 8060 (FastAPI)
- **PostgreSQL 16** mit pgvector
- **Redis 8**

## Preise

| Plan | Preis | Agents | Funktionen |
|------|-------|--------|------------|
| Free | EUR 0 | Bis zu 3 | Kern-Compliance, Community-Support |
| Starter | EUR 49/Monat | Bis zu 10 | Prioritaets-Support, erweitertes Audit |
| Business | EUR 149/Monat | Bis zu 50 | SSO, benutzerdefinierte Policies, SLA |
| Enterprise | EUR 29/Agent/Monat | Unbegrenzt | Dedizierter Support, On-Prem, individuelle Integrationen |

## Lizenz

Fair Source License v1.0 — kostenlos fuer bis zu 3 AI Agents.
Kommerzielle Lizenz erforderlich ab 4+. Siehe [LICENSE](LICENSE) fuer Details.

## Entwickelt von

[AI Engineering](https://ai-engineering.at) — Wien, Oesterreich.
