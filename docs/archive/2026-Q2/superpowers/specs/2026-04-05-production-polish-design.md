# NomOS Production Polish — Design Spec

> **Status:** ENTWURF v1
> **Datum:** 05.04.2026
> **Ziel:** Von 8/10 auf 10/10. Kunde macht `docker compose up`, loggt ein, stellt Agent ein, chattet — ohne einen einzigen Haker.
> **Scope:** 8 Gaps (G1-G8), priorisiert nach Kunden-Impact.

---

## 1. Problemstellung

NomOS funktioniert technisch: 8/8 Docker Services healthy, Hire Wizard erstellt compliant Agents, Audit Hash Chain laeuft. Aber der Kunde erlebt Friction:

- Chat haengt ohne Fehlermeldung bei LLM-Problemen (G1)
- Deutsche Texte haben keine Umlaute — "Bestaetigen" statt "Bestätigen" (G2)
- Kein Hinweis ob LLM-Provider konfiguriert ist bevor Chat gestartet wird (G3)
- Console kann vor Ready-State Traffic empfangen (G4)
- Mischung aus DE/EN Strings, fehlende Uebersetzungen (G5)
- .env.example erklaert nicht alle Optionen (G6)
- Alte Test-Agents bleiben "blocked" in DB (G7)
- Kein Deployment Guide fuer Kunden (G8)

---

## 2. Design — Gap fuer Gap

### G1: Chat Error Handling

**Problem:** `POST /api/proxy/chat` gibt bei Gateway-Fehlern HTTP 502/503 zurueck, aber das Frontend zeigt dem User nichts — der Chat haengt.

**Loesung:**

Backend (proxy.py):
- Bereits implementiert: 502 bei Timeout, 503 bei Auth-Fehler, Error-Detail wird zurueckgegeben
- Kein Backend-Change noetig

Frontend (chat/[id]/page.tsx):
- `handleSend()` muss den Error-Response abfangen und als Chat-Message anzeigen
- Drei Fehler-Typen im Chat anzeigen:
  - **429 Rate Limit:** "Anfrage-Limit erreicht. Bitte warten Sie einen Moment."
  - **502 Gateway Offline:** "Der Chat-Dienst ist nicht erreichbar. Bitte pruefen Sie die Einstellungen."
  - **503 Kein Provider:** "Kein LLM-Provider konfiguriert. [Einstellungen oeffnen]" mit Link zu /admin/settings
- Error-Messages erscheinen als Agent-Nachricht mit Error-Styling (roter Rand)
- Retry-Button bei 429 und 502

**Dateien:**
- Aendern: `nomos-console/src/app/app/chat/[id]/page.tsx`
- Aendern: `nomos-console/src/lib/i18n/de.ts` + `en.ts` (Error-Texte)

### G2: Umlaut-Encoding

**Problem:** Systematisch ue/ae/oe statt ueoeae in:
- `nomos-console/src/lib/i18n/de.ts` (~50+ Stellen)
- `nomos-cli/nomos/core/gate.py` (Compliance-Templates)
- Error-Messages in API Routern

**Loesung:**
- Suchen und Ersetzen in allen drei Bereichen
- Systematisch: ae→ä, oe→ö, ue→ü, Ae→Ä, Oe→Ö, Ue→Ü
- ACHTUNG: Nicht blind ersetzen — "true", "blue", "queue", "value" etc. duerfen nicht geaendert werden
- Strategie: Nur in deutschen Text-Strings ersetzen, nicht in Code/Keys
- de.ts: Alle Value-Strings pruefen
- gate.py: Alle Template-Strings pruefen
- API Router: Alle deutschen Error/Detail Strings pruefen

**Dateien:**
- Aendern: `nomos-console/src/lib/i18n/de.ts`
- Aendern: `nomos-cli/nomos/core/gate.py`
- Aendern: `nomos-api/nomos_api/routers/proxy.py` (Error-Texte)

### G3: LLM-Provider-Status im UI

**Problem:** Agent ist compliant, User klickt "Chat starten", Chat geht nicht weil kein API Key konfiguriert. Keine Warnung vorher.

**Loesung:**

Ansatz A (empfohlen): Provider-Check in der Chat-Page
- Beim Laden der Chat-Page: `GET /api/proxy/status` aufrufen (existiert bereits)
- Wenn `status !== "online"`: Banner zeigen "Chat-Dienst nicht verfuegbar"
- Wenn `status === "online"` aber kein Provider: Pruefen ob Settings keys gesetzt sind
- Settings-Page hat bereits `openai_api_key_set`, `anthropic_api_key_set`, `nvidia_api_key_set`

Ansatz B (zusaetzlich): Provider-Status im Hire-Wizard
- Nach Deploy-Completion: Wenn kein LLM-Key gesetzt → Hinweis zeigen
- "Tipp: Konfigurieren Sie einen LLM-Provider in den Einstellungen, damit Ihr Agent antworten kann."

**Dateien:**
- Aendern: `nomos-console/src/app/app/chat/[id]/page.tsx`
- Aendern: `nomos-console/src/app/admin/hire/page.tsx` (optional, Ansatz B)

### G4: Console Docker Healthcheck

**Problem:** nomos-console hat keinen Healthcheck. Caddy haengt von `service_started` ab, nicht `service_healthy`.

**Loesung:**
```yaml
nomos-console:
  healthcheck:
    test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000"]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 15s
```

Caddy-Dependency aendern:
```yaml
caddy:
  depends_on:
    nomos-console:
      condition: service_healthy  # war: service_started
```

**Dateien:**
- Aendern: `docker-compose.yml`

### G5: i18n Vollstaendigkeit

**Problem:** Fehlende Keys fuer incidents, diagnostics. Hardcoded Strings in hire/page.tsx.

**Loesung:**
- Fehlende Keys in de.ts und en.ts identifizieren und ergaenzen
- Hardcoded Validierungs-Strings in hire/page.tsx durch i18n-Keys ersetzen
- Grep nach pattern `language === 'de' ?` → alle Stellen in i18n-Keys umwandeln

**Dateien:**
- Aendern: `nomos-console/src/lib/i18n/de.ts`
- Aendern: `nomos-console/src/lib/i18n/en.ts`
- Aendern: `nomos-console/src/app/admin/hire/page.tsx`
- Aendern: Alle Pages die `language === 'de' ?` nutzen

### G6: .env.example vervollstaendigen

**Problem:** CORS_ORIGINS, VALKEY_PORT nicht dokumentiert.

**Loesung:**
- Alle ENV-Variablen aus docker-compose.yml extrahieren
- Jede in .env.example dokumentieren mit Beschreibung
- Gruppiert: Required, TLS, Ports, Optional, LLM Provider

**Dateien:**
- Aendern: `.env.example`

### G7: Selina DB-Status updaten

**Problem:** Selina wurde vor dem Auto-Onboarding erstellt. DB-Status ist "blocked" obwohl Compliance-Docs jetzt existieren.

**Loesung:**
- API-Endpoint `POST /api/agents/{id}/gate` existiert bereits
- Aufruf: `curl -X POST /api/agents/selina/gate` → aktualisiert DB-Status
- Oder: Startup-Task der alle Agents re-evaluiert

**Dateien:** Kein Code-Change noetig, nur ein API-Call.

### G8: Deployment Guide

**Problem:** Kein Kunden-sichtbares Dokument das erklaert wie man NomOS installiert.

**Loesung:**
- `docs/quickstart.md` erstellen (existiert als Platzhalter im README verlinkt)
- Inhalt:
  1. Voraussetzungen (Docker, 4GB RAM, Port 80/443 frei)
  2. `.env` konfigurieren (mit Erklaerung jedes Felds)
  3. `docker compose up -d`
  4. Im Browser oeffnen
  5. Admin-User erstellen (bootstrap)
  6. Ersten Agent einstellen
  7. LLM-Provider konfigurieren
  8. Chatten
- Bilingual DE/EN

**Dateien:**
- Erstellen: `docs/quickstart.md`
- Erstellen: `docs/de/schnellstart.md`

---

## 3. Reihenfolge

```
G4 (Console Healthcheck)     ─── 10 min ──┐
G7 (Selina DB fix)           ─── 5 min  ──┤── Parallel, unabhaengig
G6 (.env.example)            ─── 15 min ──┘

G2 (Umlaute)                 ─── 45 min ──── Grosser Search/Replace, muss sorgfaeltig sein

G1 (Chat Error Handling)     ─── 60 min ──┐
G3 (LLM Provider Check)      ─── 30 min ──┘── Zusammen (beide in Chat-Page)

G5 (i18n)                    ─── 45 min ──── Nach Umlaut-Fix (sonst doppelte Arbeit)

G8 (Deployment Guide)        ─── 60 min ──── Am Ende (braucht fertigen Flow fuer Screenshots)

Integration Test              ─── 30 min ──── docker compose up + Browser + kompletter Flow
```

**Geschaetzter Gesamtaufwand: ~5 Stunden**

---

## 4. Abnahme-Kriterien

Ein Kunde (ohne technisches Wissen) macht Folgendes — ALLES muss funktionieren:

1. `cp .env.example .env` → Pflichtfelder ausfuellen → `docker compose up -d`
2. Browser oeffnen → Login-Seite erscheint (korrekte Umlaute!)
3. Admin-User erstellen (bootstrap) → einloggen
4. LLM-Provider konfigurieren (Settings → NVIDIA/OpenAI/Anthropic Key eingeben → Speichern)
5. "Einstellen" klicken → Hire Wizard → Agent erstellen
6. Agent ist sofort "Compliant" → gruener Badge
7. "Chat starten" → Nachricht schicken → Agent antwortet
8. Wenn kein LLM Key: Klare Meldung "Kein Provider konfiguriert" mit Link zu Settings
9. Compliance-Tab → alle Dokumente gruen → Audit Trail sichtbar
10. Alles auf Deutsch mit korrekten Umlauten

---

## 5. Was NICHT in diesem Scope ist

- Pixel Office UI (PixiJS) — spaeter
- WebSocket Live Updates — spaeter
- Multi-User Rollentest — spaeter
- NemoClaw Container Integration — spaeter
- Honcho Memory — spaeter
- CSRF Token — spaeter
- JWT Secret Minimum Length — spaeter
