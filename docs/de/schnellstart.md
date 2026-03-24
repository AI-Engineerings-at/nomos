# NomOS Schnellstart

NomOS in 5 Minuten starten und den ersten compliant AI Agent erstellen.

## Voraussetzungen

- Docker und Docker Compose
- Python 3.11+ (nur fuer CLI)
- curl (zum Testen)

## 1. Repository klonen

```bash
git clone https://github.com/ai-engineering-at/nomos.git
cd nomos
```

## 2. Umgebung konfigurieren

```bash
cp .env.example .env
```

`.env` bearbeiten und ein sicheres Datenbank-Passwort setzen:

```
NOMOS_DB_PASSWORD=dein-sicheres-passwort
NOMOS_API_PORT=8060
NOMOS_CONSOLE_PORT=3040
```

## 3. Stack starten

```bash
docker compose up -d
```

Das startet drei Services:
- **nomos-api** auf `http://localhost:8060` (FastAPI REST API)
- **nomos-console** auf `http://localhost:3040` (Next.js Dashboard)
- **PostgreSQL 16** mit pgvector (intern, nicht exponiert)

Warten bis alle Services gesund sind:

```bash
docker compose ps
```

API pruefen:

```bash
curl http://localhost:8060/health
```

Erwartete Antwort:

```json
{
  "status": "ok",
  "service": "NomOS Fleet API",
  "version": "0.1.0"
}
```

## 4. Ersten Agent erstellen

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

Die Antwort zeigt den neuen Agent mit `compliance_status: "blocked"` — das ist erwartet. Der Agent hat noch keine Compliance-Dokumente.

## 5. Compliance Gate ausfuehren

Alle 5 Pflicht-Compliance-Dokumente generieren:

```bash
curl -X POST http://localhost:8060/api/agents/mani-ruf/gate
```

Erwartete Antwort:

```json
{
  "agent_id": "mani-ruf",
  "status": "passed",
  "missing_documents": [],
  "errors": [],
  "warnings": []
}
```

Das Gate generiert:
- DPIA (Art. 35 DSGVO)
- Verarbeitungsverzeichnis (Art. 30 DSGVO)
- Transparenzerklaerung (Art. 50 EU AI Act)
- Human Oversight / Kill Switch Policy (Art. 14 EU AI Act)
- Record-Keeping / Logging Policy (Art. 12 EU AI Act)

## 6. Im Dashboard pruefen

`http://localhost:3040` im Browser oeffnen. Dort sieht man:

- Fleet-Uebersicht mit dem Agent
- Agent-Detailansicht mit Manifest-Daten
- Compliance-Status: PASSED
- Audit Trail mit dem Erstellungs-Event

## 7. Audit Trail anzeigen

```bash
curl http://localhost:8060/api/agents/mani-ruf/audit
```

Gibt alle Audit-Eintraege fuer den Agent zurueck, einschliesslich des Erstellungs-Events mit Hash-Chain-Eintrag.

## 8. Chain-Integritaet verifizieren

```bash
curl http://localhost:8060/api/audit/verify/mani-ruf
```

Erwartete Antwort:

```json
{
  "agent_id": "mani-ruf",
  "valid": true,
  "entries_checked": 1,
  "errors": []
}
```

Verifiziert kryptographisch, dass keine Audit-Eintraege manipuliert wurden.

---

## CLI statt API verwenden

Wenn man lieber lokal ohne Docker arbeitet:

```bash
cd nomos-cli
pip install -e .
```

### Agent erstellen

```bash
nomos hire --name "Mani Ruf" --role external-secretary \
  --company "Acme GmbH" --email mani@acme.at \
  --output-dir ./data/agents/mani-ruf
```

### Compliance-Dokumente generieren

```bash
nomos gate --agent-dir ./data/agents/mani-ruf
```

### Compliance verifizieren

```bash
nomos verify --agent-dir ./data/agents/mani-ruf
```

### Alle Agents auflisten

```bash
nomos fleet --agents-dir ./data/agents
```

### Audit Trail anzeigen

```bash
nomos audit --agent-dir ./data/agents/mani-ruf
```

### Audit-Chain-Integritaet verifizieren

```bash
nomos audit --agent-dir ./data/agents/mani-ruf --verify
```

---

## Naechste Schritte

- [API-Referenz](api-referenz.md) fuer alle Endpoints
- [Compliance-Leitfaden](compliance-leitfaden.md) fuer EU AI Act Abdeckung
- [CLI-Referenz](cli-referenz.md) fuer alle Befehle und Flags
- [Architektur](architektur.md) fuer System-Design Details
