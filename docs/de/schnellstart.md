# NomOS Schnellstart

NomOS in 5 Minuten zum Laufen bringen.

## Voraussetzungen

- Docker Desktop (Windows/Mac) oder Docker Engine + Docker Compose v2 (Linux)
- Mindestens 4 GB RAM für Docker
- Ports 80 und 443 verfügbar (oder eigene Ports in `.env` konfigurieren)

## 1. Klonen und konfigurieren

```bash
git clone https://github.com/ai-engineering-at/nomos.git
cd nomos
cp .env.example .env
```

`.env` im Editor öffnen und die sechs **Pflicht-Secrets** setzen — Docker verweigert den Start mit den Platzhalter-Werten:

| Variable | Beschreibung | Beispiel |
|---|---|---|
| `NOMOS_JWT_SECRET` | 32+ Zeichen Secret für Session-Tokens | `openssl rand -hex 32` |
| `NOMOS_PLUGIN_API_KEY` | Auth-Key für OpenClaw-Gateway-Kommunikation | `openssl rand -hex 24` |
| `NOMOS_GATEWAY_TOKEN` | Bidirektionaler Gateway ↔ API Auth-Token | `openssl rand -hex 24` |
| `NOMOS_DB_PASSWORD` | PostgreSQL-Passwort | beliebiges starkes Passwort |
| `NOMOS_HASHCHAIN_HMAC_KEY` | HMAC-Anker des Audit-Trails (≥32 Bytes, fail-closed) | `openssl rand -hex 32` |
| `NOMOS_AUDIT_SIGNING_KEY` | Ed25519-Signatur-Seed des Audit-Trails (32 Byte hex, fail-closed) | `openssl rand -hex 32` |

Alle sechs auf einmal generieren:

```bash
echo "NOMOS_JWT_SECRET=$(openssl rand -hex 32)"
echo "NOMOS_PLUGIN_API_KEY=$(openssl rand -hex 24)"
echo "NOMOS_GATEWAY_TOKEN=$(openssl rand -hex 24)"
echo "NOMOS_DB_PASSWORD=$(openssl rand -hex 16)"
echo "NOMOS_HASHCHAIN_HMAC_KEY=$(openssl rand -hex 32)"
echo "NOMOS_AUDIT_SIGNING_KEY=$(openssl rand -hex 32)"
```

Die Ausgabe in die `.env`-Datei eintragen.

Mindestens einen LLM-Provider-Key setzen (NVIDIA bietet ein kostenloses Kontingent auf https://build.nvidia.com):

```
NVIDIA_API_KEY=nvapi-dein-key-hier
# oder: ANTHROPIC_API_KEY=sk-ant-...
# oder: OPENAI_API_KEY=sk-...
```

## 2. NomOS starten

```bash
docker compose up -d
```

NomOS startet 8 Services. Warten bis alle healthy sind (beim ersten Start ca. 60 Sekunden):

```bash
docker compose ps
```

Alle Services sollten `healthy` oder `running` anzeigen:

| Service | Port | Zweck |
|---|---|---|
| `caddy` | 80 / 443 | Reverse Proxy mit automatischem TLS |
| `nomos-console` | 3040 | Next.js Dashboard |
| `nomos-api` | 8060 | FastAPI Control Plane |
| `nomos-worker` | — | Hintergrund-Job-Prozessor |
| `openclaw-gateway` | 3050 | Headless Plugin Framework |
| `postgres` | — | PostgreSQL 16 + pgvector (intern) |
| `valkey` | — | Cache und Rate-Limiting (compose-intern, kein Host-Port) |
| `vault` | 8200 | HashiCorp Vault Secret Management |

API-Health prüfen:

```bash
curl http://localhost:8060/health
```

Erwartete Antwort (Status `healthy` nur wenn PostgreSQL erreichbar; `degraded` wenn Gateway offline):

```json
{
  "status": "healthy",
  "service": "NomOS Fleet API",
  "version": "0.2.0",
  "vault": "ready",
  "components": {
    "vault": "ok",
    "postgres": "ok",
    "valkey": "ok",
    "gateway": "ok"
  }
}
```

## 3. Erster Login

**http://localhost:3040** im Browser öffnen.

Beim ersten Start zeigt die Konsole einen **Bootstrap**-Dialog. Admin-Account anlegen:

```bash
curl -X POST http://localhost:8060/api/users/bootstrap \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "jetzt-aendern",
    "role": "admin"
  }'
```

Die Antwort enthält eine einmalige **Recovery-Phrase** — sicher offline aufbewahren (`routers/users.py:66`).

Oder das Bootstrap-Formular im Browser ausfüllen. Danach mit den Zugangsdaten einloggen.

> **Hinweis:** Der Bootstrap-Endpoint (`/api/users/bootstrap`) ist nur verfügbar, solange noch kein Benutzer existiert. Er liefert 403 sobald ein Admin existiert.

## 4. LLM-Provider konfigurieren

1. **Einstellungen** in der linken Sidebar klicken
2. Bereich **LLM-Provider** öffnen
3. API-Key eintragen (NVIDIA / Anthropic / OpenAI)
4. Standardmodell auswählen
5. **Speichern** klicken

NomOS ist provider-agnostisch. Provider können jederzeit gewechselt oder mehrere Keys hinterlegt werden.

## 5. Ersten Agent einstellen

**Hire** in der Sidebar klicken oder **http://localhost:3040/hire** aufrufen.

Der Hire-Wizard führt durch vier Schritte:

1. **Identität** — Name, Rolle und Unternehmen (z.B. `Support-Assistent`, `customer-support`, `Acme GmbH`)
2. **Fähigkeiten** — Auswählen was der Agent darf (Websuche, Dateizugriff, Code-Ausführung)
3. **Risikoklasse** — EU AI Act Risikoklasse festlegen (`minimal`, `limited`, `high`)
4. **Überprüfung** — Generierte Compliance-Dokumente vor dem Deployment prüfen

**Agent deployen** klicken. NomOS generiert automatisch die erforderlichen EU AI Act Compliance-Dokumente:

- DPIA (Art. 35 DSGVO)
- Verarbeitungsverzeichnis (Art. 30 DSGVO)
- Transparenzerklärung (Art. 50 EU AI Act)
- Human Oversight / Kill-Switch-Richtlinie (Art. 14 EU AI Act)
- Aufzeichnungs- und Logging-Richtlinie (Art. 12 EU AI Act)

## 6. Chatten

1. **Fleet**-Ansicht öffnen — der neue Agent erscheint mit Compliance-Status `COMPLIANT`
2. Agent-Namen klicken um die Detailansicht zu öffnen
3. **Chat** oben rechts klicken
4. Nachricht senden — der Agent antwortet über den konfigurierten LLM-Provider

Das Audit-Trail zeichnet jede Interaktion automatisch auf.

## Fehlerbehebung

**"Not compliant"-Status** — Kann auftreten wenn die Compliance-Dokumenten-Generierung noch läuft. Einige Sekunden warten und neu laden. Wenn es anhält, Detailansicht des Agents öffnen und **Compliance Gate ausführen** klicken.

**Chat antwortet nicht** — Prüfen ob ein LLM-Provider-Key in den Einstellungen konfiguriert ist. Key-Gültigkeit direkt beim Provider testen.

**502 Bad Gateway Fehler** — Das OpenClaw-Gateway startet möglicherweise noch. Logs prüfen:
```bash
docker logs nomos-openclaw-gateway-1 --tail 50
```

**Services starten nicht** — Logs aller Services anzeigen:
```bash
docker compose logs -f
```
Für einen einzelnen Service: `docker compose logs -f nomos-api`

**Port-Konflikte** — Falls Ports 80, 443, 3040 oder 8060 belegt sind, Alternativen in `.env` festlegen:
```
NOMOS_HTTP_PORT=8080
NOMOS_HTTPS_PORT=8443
NOMOS_CONSOLE_PORT=3041
NOMOS_API_PORT=8061
```

**Vault initialisiert sich nicht** — Beim ersten Start muss Vault initialisiert werden. Prüfen:
```bash
docker compose logs vault --tail 30
```

**docker compose schlägt sofort fehl** — Platzhalter-Werte in `.env` vorhanden. Alle `CHANGE_ME_REQUIRED_*`-Werte durch echte Secrets ersetzen (siehe Schritt 1).

---

## Audit-Trail v2 (ab 0.2.0)

Nach dem ersten Start läuft im Worker stündlich `anchor_audit_heads`
(Phase-A2): die per-Agent Chain-Spitzen werden samt HMAC, Ed25519-
Signatur und Merkle-Wurzel nach `/data/audit-anchors/anchors.jsonl`
geschrieben. Täglich um 04:00 läuft `audit_integrity_checkpoint`
(Phase-A3) und schreibt eine `audit.retention.checkpoint`-Zeile in
die Chain.

Ein Prüfer kann jedes einzelne Audit-Event mit **ausschliesslich dem
Ed25519 Public Key** verifizieren — ohne DB-Zugriff:

```bash
# Signed Tree Head + Inclusion-Proof für Sequenz N abrufen
curl -H "X-NomOS-API-Key: $KEY" \
  http://localhost:8060/api/agents/AGENT_ID/audit/sth
curl -H "X-NomOS-API-Key: $KEY" \
  http://localhost:8060/api/agents/AGENT_ID/audit/proof/N
```

Verifikations-Snippet siehe `docs/operations-runbook.md` Abschnitt
"Phase-B1: Signed Tree Head + inclusion-proof for a single event".

## Nächste Schritte

- [API-Referenz](api-referenz.md) — REST-Endpoints (Kurzform; vollständig: [api-reference.md](../api-reference.md))
- [Compliance-Leitfaden](compliance-leitfaden.md) — EU AI Act Abdeckung im Detail
- [Architektur](architektur.md) — System-Design und Datenfluss
- [CLI-Referenz](cli-referenz.md) — Kommandozeilen-Interface für Automatisierung
- [Operations-Runbook](../operations-runbook.md) (EN) — Bring-up, Audit-Key-Rotation, Regulator-Export
- [CHANGELOG](../../CHANGELOG.md) — Release-Historie 0.2.0
