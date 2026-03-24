# NomOS API-Referenz

Basis-URL: `http://localhost:8060`

Alle Endpoints liefern JSON. Die API ist mit FastAPI gebaut und bietet automatische OpenAPI-Dokumentation unter `/docs` (Swagger UI) und `/redoc` (ReDoc).

---

## Health

### GET /health

Service-Status und Version pruefen.

**Antwort:** `200 OK`

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `status` | string | Service-Status (`"ok"`) |
| `service` | string | Service-Name (`"NomOS Fleet API"`) |
| `version` | string | API-Version (`"0.1.0"`) |

**Beispiel:**

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

Neuen AI Agent erstellen. Generiert das Agent-Verzeichnis mit Manifest, Compliance-Ordner und Audit-Chain. Persistiert den Agent in der Datenbank.

**Request Body:**

| Feld | Typ | Pflicht | Standard | Beschreibung |
|------|-----|---------|----------|-------------|
| `name` | string | ja | — | Agent-Name (1-256 Zeichen), z.B. `"Mani Ruf"` |
| `role` | string | ja | — | Agent-Rolle (1-256 Zeichen), z.B. `"external-secretary"` |
| `company` | string | ja | — | Firmenname (1-256 Zeichen), z.B. `"Acme GmbH"` |
| `email` | string | ja | — | Kontakt-Email, z.B. `"mani@acme.at"` |
| `risk_class` | string | nein | `"limited"` | EU AI Act Risikoklasse: `"minimal"`, `"limited"` oder `"high"` |

**Antwort:** `201 Created`

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `id` | string | Generierte Agent-ID (slugifiziert aus Name) |
| `name` | string | Agent-Name |
| `role` | string | Agent-Rolle |
| `company` | string | Firmenname |
| `email` | string | Kontakt-Email |
| `risk_class` | string | EU AI Act Risikoklasse |
| `status` | string | Agent-Status (`"created"`) |
| `manifest_hash` | string | SHA-256 Hash des Agent-Manifests |
| `compliance_status` | string | Aktueller Compliance-Status (`"pending"`, `"passed"`, `"blocked"`) |
| `created_at` | string | ISO 8601 Erstellungszeitpunkt |
| `updated_at` | string | ISO 8601 letzter Aenderungszeitpunkt |

**Fehler:** `400 Bad Request` wenn Agent-Verzeichnis bereits existiert oder Validierung fehlschlaegt.

**Beispiel:**

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

Hinweis: `compliance_status` ist `"blocked"` nach der Erstellung, da noch keine Compliance-Dokumente generiert wurden. Das Compliance Gate ausfuehren um sie zu generieren.

---

## Fleet

### GET /api/fleet

Alle Agents in der Fleet-Registry auflisten.

**Antwort:** `200 OK`

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `agents` | array | Liste von `AgentResponse`-Objekten |
| `total` | integer | Gesamtanzahl der Agents |

**Beispiel:**

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

Details fuer einen einzelnen Agent abrufen.

**Pfad-Parameter:**

| Parameter | Typ | Beschreibung |
|-----------|-----|-------------|
| `agent_id` | string | Agent-ID (z.B. `"mani-ruf"`) |

**Antwort:** `200 OK` — `AgentResponse`-Objekt (gleiches Schema wie in der Fleet-Liste).

**Fehler:** `404 Not Found` wenn Agent nicht existiert.

**Beispiel:**

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

Compliance-Status fuer einen Agent pruefen. Liest das Manifest und verifiziert, dass alle Pflichtdokumente existieren.

**Pfad-Parameter:**

| Parameter | Typ | Beschreibung |
|-----------|-----|-------------|
| `agent_id` | string | Agent-ID |

**Antwort:** `200 OK`

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `agent_id` | string | Agent-ID |
| `status` | string | `"passed"`, `"warning"` oder `"blocked"` |
| `missing_documents` | array | Liste fehlender Dokument-Namen |
| `errors` | array | Blockierende Fehlermeldungen |
| `warnings` | array | Nicht-blockierende Warnungen |

**Fehler:** `404 Not Found` wenn Agent nicht existiert. `400 Bad Request` wenn Agent-Verzeichnis ungueltig.

**Beispiel:**

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

Alle Pflicht-Compliance-Dokumente fuer einen Agent generieren und Compliance erneut pruefen. API-Aequivalent zu `nomos gate`.

**Pfad-Parameter:**

| Parameter | Typ | Beschreibung |
|-----------|-----|-------------|
| `agent_id` | string | Agent-ID |

**Request Body:** Keiner.

**Antwort:** `200 OK` — Gleiches Schema wie `GET /api/agents/{agent_id}/compliance`.

Nach erfolgreicher Generierung ist der `status` `"passed"` und `missing_documents` leer.

**Fehler:** `404 Not Found` wenn Agent nicht existiert. `400 Bad Request` wenn Agent-Verzeichnis ungueltig.

**Beispiel:**

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

Vollstaendigen Audit Trail fuer einen Agent abrufen. Gibt alle Eintraege aus der Datenbank zurueck, sortiert nach Sequenznummer.

**Pfad-Parameter:**

| Parameter | Typ | Beschreibung |
|-----------|-----|-------------|
| `agent_id` | string | Agent-ID |

**Antwort:** `200 OK`

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `agent_id` | string | Agent-ID |
| `entries` | array | Liste von Audit-Eintraegen |
| `total` | integer | Gesamtanzahl der Eintraege |

Jeder Eintrag enthaelt:

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `sequence` | integer | Sequenznummer (0-basiert) |
| `event_type` | string | Event-Typ (z.B. `"agent.created"`) |
| `agent_id` | string | Agent-ID |
| `data` | object | Event-spezifische Daten |
| `chain_hash` | string | SHA-256 Hash dieses Eintrags |
| `timestamp` | string | ISO 8601 UTC Zeitstempel |

**Fehler:** `404 Not Found` wenn Agent nicht existiert.

**Beispiel:**

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

Audit-Chain fuer einen Agent kryptographisch verifizieren. Liest die JSONL-Chain-Datei von der Festplatte, berechnet jeden Hash neu und verifiziert die Chain-Integritaet.

**Pfad-Parameter:**

| Parameter | Typ | Beschreibung |
|-----------|-----|-------------|
| `agent_id` | string | Agent-ID |

**Antwort:** `200 OK`

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `agent_id` | string | Agent-ID |
| `valid` | boolean | `true` wenn Chain intakt, `false` wenn manipuliert |
| `entries_checked` | integer | Anzahl verifizierter Eintraege |
| `errors` | array | Liste von Verifikationsfehlern (leer wenn gueltig) |

**Fehler:** `404 Not Found` wenn Agent nicht existiert. `400 Bad Request` wenn Agent-Verzeichnis ungueltig.

**Beispiel:**

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

## Event-Typen

Der Audit Trail verwendet diese kanonischen Event-Typen:

| Event-Typ | Beschreibung |
|-----------|-------------|
| `agent.created` | Agent wurde via `nomos hire` oder POST /api/agents erstellt |
| `agent.deployed` | Agent wurde deployt |
| `agent.stopped` | Agent wurde gestoppt |
| `agent.retired` | Agent wurde ausser Dienst gestellt |
| `compliance.check.passed` | Compliance-Check bestanden |
| `compliance.check.failed` | Compliance-Check fehlgeschlagen |
| `compliance.doc.signed` | Compliance-Dokument unterschrieben |
| `governance.hook.triggered` | Governance-Hook ausgeloest |
| `governance.hook.blocked` | Governance-Hook hat Aktion blockiert |
| `governance.kill_switch` | Kill Switch aktiviert |
| `governance.escalation` | Eskalation ausgeloest |
| `audit.chain.created` | Audit-Chain initialisiert |
| `audit.chain.verified` | Audit-Chain verifiziert |
| `audit.exported` | Audit Trail exportiert |

---

## Fehler-Antworten

Alle Fehler-Antworten haben dieses Format:

```json
{
  "detail": "Fehlermeldung die beschreibt was schiefgelaufen ist"
}
```

| Status-Code | Bedeutung |
|-------------|-----------|
| `400` | Ungueltige Anfrage (Validierungsfehler, ungueltiges Verzeichnis) |
| `404` | Ressource nicht gefunden (Agent existiert nicht) |
| `422` | Validierungsfehler (ungueltiger Request Body) |
| `500` | Interner Serverfehler |
