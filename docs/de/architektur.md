# NomOS Architektur

## Komponentenuebersicht

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
|          | HTTP (intern)      |                |      |
|          +------------------------------------+      |
|          | asyncpg (PostgreSQL)                       |
+-----------------------------------------------------+
           |
           v
   +---------------+
   |  /data/agents  |  (Docker Volume: nomos-agents)
   |  Agent-Dateien |
   +---------------+

+-----------------------------------------------------+
|                    nomos-cli                          |
|              (eigenstaendige Python CLI)              |
|           Arbeitet direkt auf lokalen Dateien         |
+-----------------------------------------------------+

+-----------------------------------------------------+
|                   nomos-plugin                        |
|           (TypeScript OpenClaw Plugin)               |
|           Gateway-Integrationsschicht                |
+-----------------------------------------------------+
```

## Komponenten

### nomos-cli (Python CLI)

Die Kernbibliothek und das Kommandozeilen-Tool. Enthaelt die gesamte Geschaeftslogik.

| Modul | Verantwortlichkeit |
|-------|-------------------|
| `core/manifest.py` | Pydantic v2 Modelle fuer Agent-Manifest-Schema (AgentManifest, 12 Sub-Modelle) |
| `core/manifest_validator.py` | YAML laden, Schema + Geschaeftsregeln validieren, SHA-256 Manifest-Hash berechnen |
| `core/forge.py` | Komplette Agent-Verzeichnisse erstellen (Manifest + Hash + Audit-Chain) |
| `core/gate.py` | 5 Compliance-Dokumente aus Manifest-Daten generieren |
| `core/compliance_engine.py` | Blockierende Compliance-Pruefung (PASSED / WARNING / BLOCKED) |
| `core/hash_chain.py` | SHA-256 Append-Only Hash-Chain (JSONL Speicher), Verifikation |
| `core/events.py` | Kanonische Event-Typ-Definitionen (14 Event-Typen) |
| `cli.py` | Click CLI mit 5 Befehlen: hire, gate, verify, fleet, audit |

Testabdeckung: 84 Tests.

### nomos-api (FastAPI)

REST API die die Kernbibliothek fuer Remote-Zugriff und Fleet-Management umschliesst.

| Modul | Verantwortlichkeit |
|-------|-------------------|
| `config.py` | Einstellungen aus NOMOS_ Umgebungsvariablen (Pydantic BaseSettings) |
| `database.py` | AsyncSession Factory (SQLAlchemy + asyncpg) |
| `models.py` | ORM Modelle: Agent, AuditLog |
| `schemas.py` | Pydantic Request/Response Schemas (8 Modelle) |
| `services/agent_service.py` | Agent-Erstellung: Forge + DB-Persistierung |
| `services/fleet_service.py` | Fleet CRUD-Operationen |
| `routers/health.py` | GET /health |
| `routers/agents.py` | POST /api/agents |
| `routers/fleet.py` | GET /api/fleet, GET /api/fleet/{id} |
| `routers/compliance.py` | GET /api/agents/{id}/compliance, POST /api/agents/{id}/gate |
| `routers/audit.py` | GET /api/agents/{id}/audit, GET /api/audit/verify/{id} |

Testabdeckung: 14 Tests.

### nomos-console (Next.js 15)

Web-Dashboard fuer visuelle Fleet-Verwaltung:
- Fleet-Uebersicht mit Agent-Liste
- Agent-Detailansicht mit Manifest-Daten
- Compliance-Status und Dokumenten-Check
- Audit Trail Viewer

Kommuniziert mit nomos-api ueber internes Docker-Netzwerk HTTP.

### nomos-plugin (TypeScript)

OpenClaw Gateway Plugin mit `/nomos` Befehlen fuer chat-basierte Agent-Interaktion.

### PostgreSQL 16 + pgvector

Speichert die Agent-Registry und indizierte Audit-Eintraege. Die Datenbank ist die Fleet-Registry; die JSONL-Dateien auf der Festplatte sind die Source of Truth fuer Audit-Chains.

---

## Datenfluss

### Agent-Erstellung (nomos hire / POST /api/agents)

```
1. Eingabe: name, role, company, email, risk_class
         |
2. forge_agent()
   +-- Name zu Agent-ID slugifizieren (z.B. "Mani Ruf" -> "mani-ruf")
   +-- Manifest-Daten erstellen (Pydantic AgentManifest)
   +-- Verzeichnisstruktur anlegen:
   |     agents/<id>/
   |       manifest.yaml
   |       manifest.sha256
   |       compliance/     (leer)
   |       audit/chain.jsonl
   +-- Hash-Chain mit "agent.created" Event initialisieren
   +-- ForgeResult(manifest_hash) zurueckgeben
         |
3. check_compliance()
   +-- Pflichtdokumente pruefen -> BLOCKED (Docs noch nicht generiert)
         |
4. [Nur API] Agent + AuditLog in PostgreSQL persistieren
         |
5. Ausgabe: AgentResponse mit compliance_status="blocked"
```

### Compliance Gate (nomos gate / POST /api/agents/{id}/gate)

```
1. Manifest aus Agent-Verzeichnis laden
         |
2. generate_compliance_docs()
   +-- 5 Markdown-Dokumente generieren:
   |     compliance/dpia.md
   |     compliance/verarbeitungsverzeichnis.md
   |     compliance/art50_transparency.md
   |     compliance/art14_killswitch.md
   |     compliance/art12_logging.md
         |
3. check_compliance() -> PASSED
         |
4. [Nur API] compliance_status in DB aktualisieren
         |
5. Ausgabe: ComplianceResponse mit status="passed"
```

### Verifikation (nomos verify / GET /api/audit/verify/{id})

```
1. Manifest aus YAML laden
2. Manifest-Schema validieren (Pydantic)
3. Manifest-Geschaeftsregeln validieren
4. Compliance-Dokumente auf Existenz pruefen
5. Manifest-Hash verifizieren (SHA-256)
6. Audit-Chain-Integritaet verifizieren:
   +-- chain.jsonl Zeile fuer Zeile lesen
   +-- Hash jedes Eintrags neu berechnen
   +-- previous_hash Verkettung pruefen
   +-- Ersten Eintrag gegen Genesis-Hash pruefen (64 Nullen)
7. Ausgabe: PASS/FAIL pro Pruefung
```

---

## Datenbank-Schema

### agents Tabelle

| Spalte | Typ | Constraints | Beschreibung |
|--------|-----|-------------|-------------|
| `id` | VARCHAR(128) | PRIMARY KEY | Agent-ID (slugifizierter Name) |
| `name` | VARCHAR(256) | NOT NULL | Menschenlesbarer Name |
| `role` | VARCHAR(256) | NOT NULL | Agent-Rolle |
| `company` | VARCHAR(256) | NOT NULL | Firmenname |
| `email` | VARCHAR(256) | NOT NULL | Kontakt-Email |
| `risk_class` | VARCHAR(32) | NOT NULL, DEFAULT 'limited' | EU AI Act Risikoklasse |
| `status` | VARCHAR(32) | NOT NULL, DEFAULT 'created' | Agent-Lifecycle-Status |
| `manifest_hash` | VARCHAR(64) | NOT NULL | SHA-256 des Manifests |
| `manifest_data` | JSON | NOT NULL | Vollstaendiges Manifest als JSON |
| `compliance_status` | VARCHAR(32) | NOT NULL, DEFAULT 'pending' | Compliance-Gate-Ergebnis |
| `agents_dir` | TEXT | NOT NULL | Dateisystem-Pfad zum Agent-Verzeichnis |
| `created_at` | TIMESTAMP WITH TZ | NOT NULL, DEFAULT now() | Erstellungszeitpunkt |
| `updated_at` | TIMESTAMP WITH TZ | NOT NULL, DEFAULT now() | Letzter Aenderungszeitpunkt |

### audit_log Tabelle

| Spalte | Typ | Constraints | Beschreibung |
|--------|-----|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-Increment ID |
| `agent_id` | VARCHAR(128) | NOT NULL, INDEX | Agent-Referenz |
| `sequence` | INTEGER | NOT NULL | Sequenznummer in der Chain |
| `event_type` | VARCHAR(64) | NOT NULL, INDEX | Event-Typ String |
| `data` | JSON | NULLABLE | Event-spezifische Nutzdaten |
| `chain_hash` | VARCHAR(64) | NOT NULL | SHA-256 Hash dieses Eintrags |
| `timestamp` | VARCHAR(64) | NOT NULL | ISO 8601 Zeitstempel |

**Index:** Zusammengesetzter Index auf `(agent_id, sequence)`.

Hinweis: Die audit_log Tabelle ist ein abfragbarer Index. Die Source of Truth fuer die Audit-Integritaet ist die JSONL-Chain-Datei auf der Festplatte.

---

## Hash-Chain-Format

Der Audit Trail wird als JSONL-Datei gespeichert (`audit/chain.jsonl`). Jede Zeile ist ein eigenstaendiges JSON-Objekt:

```jsonl
{"agent_id":"mani-ruf","data":{"company":"Acme GmbH","manifest_hash":"a1b2...","name":"Mani Ruf","risk_class":"limited","role":"external-secretary"},"event_type":"agent.created","hash":"e4f5a6b7...","previous_hash":"0000000000000000000000000000000000000000000000000000000000000000","sequence":0,"timestamp":"2026-03-24T10:00:00.123456+00:00"}
```

**Felder pro Eintrag:**

| Feld | Beschreibung |
|------|-------------|
| `sequence` | 0-basierte fortlaufende Nummer |
| `timestamp` | ISO 8601 UTC Zeitstempel |
| `event_type` | Kanonischer Event-Typ (siehe Events) |
| `agent_id` | Agent dem dieses Event gehoert |
| `data` | Event-spezifische Nutzdaten (beliebiges JSON-Objekt) |
| `previous_hash` | SHA-256 Hash des vorherigen Eintrags (Genesis = 64 Nullen) |
| `hash` | SHA-256 des kanonischen JSON aller Felder ausser `hash` selbst |

**Hash-Berechnung:**

```
canonical = JSON.stringify({sequence, timestamp, event_type, agent_id, data, previous_hash},
                           sort_keys=true, separators=(",",":"))
hash = SHA-256(canonical)
```

Die Aenderung eines Feldes in einem Eintrag invalidiert den Hash dieses Eintrags und bricht die Chain fuer alle nachfolgenden Eintraege.

---

## Sicherheitsmodell

### Non-root Docker-Container

Der API-Container erstellt einen dedizierten `nomos`-Benutzer und laeuft als dieser:
```dockerfile
RUN adduser --disabled-password --no-create-home --gecos "" nomos
USER nomos
```

### Pfad-Validierung

Vor jedem Zugriff auf Agent-Verzeichnisse ueber die API wird der aufgeloeste Pfad gegen das konfigurierte `agents_dir` validiert:

```python
agent_dir = Path(agent.agents_dir).resolve()
safe_base = settings.agents_dir.resolve()
if not agent_dir.is_relative_to(safe_base):
    raise HTTPException(status_code=400, detail="Invalid agent directory")
```

Das verhindert Path-Traversal-Angriffe.

### PII-Behandlung

Das Manifest definiert PII-Filter-Konfiguration:
- `pii_filter.enabled` — Hauptschalter
- `pii_filter.mask_emails` — Email-Adressen maskieren
- `pii_filter.mask_phones` — Telefonnummern maskieren
- `pii_filter.mask_addresses` — physische Adressen maskieren
- `pii_filter.keep_names` — ob Namen beibehalten werden

PII-Filterung erfordert das Honcho Memory Backend. Mit dem lokalen Backend ist die PII-Filter-Konfiguration im Manifest gespeichert, aber die Filterung ist nicht aktiv. Das DPIA-Dokument dokumentiert diese Einschraenkung klar.

### Manifest-Integritaet

Jeder Agent hat eine `manifest.sha256`-Datei die den SHA-256 Hash der kanonischen JSON-Darstellung des Manifests enthaelt. `nomos verify` prueft diesen Hash um Manipulationen zu erkennen.

### Audit-Chain-Integritaet

Die Hash-Chain ist append-only. Der Hash jedes Eintrags haengt von allen vorherigen Eintraegen ab. Die Verifikation berechnet jeden Hash von Grund auf neu und prueft die Chain-Verkettung. Jede Manipulation ist erkennbar.

---

## Konfiguration

Alle API-Einstellungen werden ueber Umgebungsvariablen mit dem `NOMOS_`-Praefix konfiguriert:

| Variable | Standard | Beschreibung |
|----------|----------|-------------|
| `NOMOS_DATABASE_URL` | `postgresql+asyncpg://nomos:nomos@localhost:5432/nomos` | Datenbank-Verbindungsstring |
| `NOMOS_API_HOST` | `0.0.0.0` | API Bind-Adresse |
| `NOMOS_API_PORT` | `8000` | API interner Port (gemappt auf 8060 via Docker) |
| `NOMOS_API_TITLE` | `NomOS Fleet API` | API Titel |
| `NOMOS_API_VERSION` | `0.1.0` | API Version |
| `NOMOS_CORS_ORIGINS` | `["http://localhost:3040"]` | Erlaubte CORS Origins |
| `NOMOS_AGENTS_DIR` | `./data/agents` | Agent-Dateispeicher-Verzeichnis |
| `NOMOS_DB_PASSWORD` | `nomos` | PostgreSQL Passwort |
| `NOMOS_API_PORT` (docker-compose) | `8060` | Externer API-Port |
| `NOMOS_CONSOLE_PORT` (docker-compose) | `3040` | Externer Console-Port |
