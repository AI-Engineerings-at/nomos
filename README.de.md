# aie-audit-chain

> Server-seitiger Hash-Chain-Audit-Trail fuer EU-AI-Act-Konformitaet.
> Teil des AIE-Audit-Stacks: `aie-audit-primitives` + `aie-hash-chain` + **`aie-audit-chain`**.

## Was ist aie-audit-chain?

aie-audit-chain ist die **server-seitige Audit-Trail-Komponente** des
AIE-Audit-Stacks. Sie zeichnet jedes compliance-relevante Ereignis
(Agent-Aktion, Gate-Entscheidung, PII-Redaktion, Budget-Verletzung,
Vorfall) in eine manipulationssichere Hash-Chain mit
Ed25519-Signatur pro Eintrag und einem RFC-6962-Merkle-Transparency-
Log.

Sie wird als deploybarer Dienst ausgeliefert (FastAPI auf Python 3.12,
PostgreSQL, Valkey, HashiCorp Vault) und stellt Verifikations-Endpoints
bereit, die jede dritte Partei ohne Datenbank-Zugriff aufrufen kann.

### Umbenennungs-Hinweis (2026-05-24, DEC-020)

Das Repo hiess vorher `nomos` / `NomOS`. Der ehemals breitere
"Compliance-Control-Plane"-Scope (`nomos-api`, `nomos-cli`,
`nomos-console`, `nomos-plugin`) wurde auf den tragenden Audit-Trail-
Kern zugeschnitten. Die uebrigen Flaechen — Fleet-Verwaltung,
Compliance-Gate, Console-UI, OpenClaw-Plugin — werden in eigene Repos
entbuendelt und ggf. als `aie-*`-Geschwister wieder aufgenommen. Bis
dahin tragen die Quellbaeume `nomos-api/`, `nomos-cli/`,
`nomos-console/`, `nomos-plugin/` weiter die historischen Namen; der
oeffentliche Name des Liefer-Artefakts ist **aie-audit-chain**.
Siehe [CHANGELOG](CHANGELOG.md) 2026-05-24 fuer den vollen Trail.

## Schnellstart

**API (Docker):**
```bash
cd nomos-api
docker compose up -d
# API auf http://localhost:8060, PostgreSQL + Valkey inklusive
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

> Das CLI-Binary heisst waehrend der Umbenennungsphase weiterhin
> `nomos`. Spaeter wird es `aie-audit` heissen.

## Audit-Trail v2 — Schluesseleigenschaften

| Eigenschaft | Was sie tut | Rechtsgrundlage |
|-------------|-------------|-----------------|
| Hash-Chain | SHA-256 + jedem Eintrag haengt der Hash des Vorgaengers an; jede Manipulation invalidiert die Kette ab dort | Art. 12 EU AI Act |
| HMAC-SHA256 | Pro-Eintrag-HMAC, fail-closed, erkennt Integritaetsbruch ohne Schluessel-Offenlegung | Art. 12 EU AI Act |
| Ed25519 | Pro-Eintrag-Signatur, fail-closed; Dritte koennen mit Public Key allein verifizieren | Art. 12 EU AI Act |
| RFC-6962 Merkle Log | Signed Tree Head (STH) + Inclusion-Proof-Endpoints, O(log n) Verifikation, kein DB-Zugriff noetig | Art. 12 EU AI Act |
| Externes Anchoring | Stuendlicher Anchor-Head + taeglicher Integritaets-Checkpoint via ARQ-Worker | Art. 12 EU AI Act |
| Retention-Floor | 180 Tage Mindestaufbewahrung | Art. 12 EU AI Act |

Siehe [CHANGELOG](CHANGELOG.md) 0.2.0 fuer den v2-Schwenk und den
[Hardening-Plan 2026-05-20](docs/hardening-2026-05-20/PLAN.md) fuer die
A1-A6 + B1 Roadmap (alle ausgeliefert).

## Quell-Layout

```
aie-audit-chain/
├── nomos-cli        Python CLI — Befehle, Kernmodule, Tests
├── nomos-api        FastAPI — REST-Endpoints, Docker-Compose
├── nomos-console    Next.js 15 — Fleet-Uebersicht, Audit-Trail
├── nomos-plugin     TypeScript — Agent-Gateway-Plugin
├── schemas/         YAML-Schema-Templates fuer Agent-Manifeste
└── templates/       Agent-Rollen-Templates
```

> Die `nomos-*`-Verzeichnisnamen sind historisch und werden in einem
> Folge-Schnitt umbenannt. Siehe Umbenennungs-Hinweis oben.

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
| `GET` | `/api/agents/{agent_id}/audit/sth` | Signed Tree Head |
| `GET` | `/api/agents/{agent_id}/audit/proof/{n}` | Inclusion-Proof fuer Eintrag n |
| `GET` | `/api/audit/verify/{agent_id}` | Audit-Chain-Integritaet verifizieren |

## Oeffentliche Verifikation

Eine dritte Partei (Regulator, Auditor, Kunde) kann einen einzelnen
Audit-Eintrag ohne Datenbank-Zugriff verifizieren:

1. Aktuellen Signed Tree Head holen: `GET /api/agents/{id}/audit/sth`
2. Inclusion-Proof fuer Eintrag `n` holen: `GET /api/agents/{id}/audit/proof/{n}`
3. Proof gegen STH mit dem veroeffentlichten Ed25519-Public-Key
   verifizieren.

Ein Referenz-Verifier und eine Endnutzer-Verify-Seite laufen auf
**https://verify.ai-engineering.at**.

## Installation

**CLI (Python 3.12+):**
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

Das startet die Services:
- **API** auf Port 8060 (FastAPI)
- **PostgreSQL 16** mit pgvector
- **Valkey** (Cache)
- **HashiCorp Vault** (Secrets)

## Preise

| Plan | Agents | Preis |
|------|--------|-------|
| Free | Bis zu 3 | Alle Features enthalten |
| Commercial | 4+ | [Kontakt](https://ai-engineering.at) |

Fair-Core-Lizenz (FCL) — voller Funktionsumfang auf jeder Stufe. Kein
Feature-Gating.

## Dokumentation

| Dokument | Beschreibung |
|----------|-------------|
| [Schnellstart](docs/de/schnellstart.md) | In 5 Minuten starten |
| [API-Referenz](docs/de/api-referenz.md) | Vollstaendige REST API |
| [CLI-Referenz](docs/de/cli-referenz.md) | Alle CLI-Befehle |
| [Architektur](docs/de/architektur.md) | System-Design, Datenfluss, Sicherheit |
| [Compliance-Leitfaden](docs/de/compliance-leitfaden.md) | EU AI Act + DSGVO |

**English:** see [README.md](README.md).

## Lizenz

Fair Source License v1.0 — kostenlos fuer bis zu 3 AI Agents.
Kommerzielle Lizenz erforderlich ab 4+. Siehe [LICENSE](LICENSE) fuer
Details.

## Entwickelt von

[AI Engineering](https://ai-engineering.at) — Wien, Oesterreich.
