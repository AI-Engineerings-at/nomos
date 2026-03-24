# NomOS GAP-Analyse — 24.03.2026

## Was gebaut wurde (Library Layer — funktioniert)

| Komponente | Tests | Status |
|------------|-------|--------|
| manifest.py | 21 | Pydantic v2 Schema, strict validation |
| manifest_validator.py | 21 | load, validate, SHA-256 hash |
| hash_chain.py | 12 | Tamper-evident JSONL audit trail |
| events.py | 9 | 14 Event Types |
| compliance_engine.py | 10 | Blocking Gate (PASSED/WARNING/BLOCKED) |
| gate.py | 12 | 5 EU AI Act + DSGVO Dokumente generieren |
| forge.py | 9 | Agent-Verzeichnis aus Name+Role |
| cli.py | 10 | hire, gate, verify, fleet, audit |
| API (8 Endpoints) | 19 | FastAPI + PostgreSQL |
| Console | 9 (Playwright) | Next.js Dashboard |
| Plugin | kompiliert | TypeScript OpenClaw |

## Was FEHLT (Produkt Layer — existiert nicht)

| Feature | Status | Warum kritisch |
|---------|--------|----------------|
| NemoClaw Container | 0% | Spec: "IMMER dabei" — Sandbox, Network Policy |
| Agent Deploy | 0% | `nomos deploy` existiert nicht |
| Laufender Agent | 0% | Kein Agent antwortet auf Nachrichten |
| Kill Switch Runtime | 0% | Kein Mechanismus der echten Agent stoppt |
| PII-Filter Runtime | 0% | Kein Code der echte Daten filtert |
| Governance Hooks Runtime | 0% | Hooks nur als Markdown-Dokumente |
| Art. 50 Labeling Runtime | 0% | Label nur im Dokument, nicht in Ausgabe |
| Branding | 0% | Playbook01 ignoriert |
| OpenClaw Plugin geladen | 0% | Nie in Gateway getestet |
| Mattermost Integration | 0% | Nie getestet |

## Richtige Reihenfolge (korrigiert)

```
Schritt 1: NemoClaw Container starten
           → docker run nemoclaw → Sandbox existiert
           → BEWEIS: Container laeuft, Health Check OK

Schritt 2: OpenClaw Agent in NemoClaw deployen
           → openclaw gateway im Container
           → BEWEIS: Gateway antwortet

Schritt 3: Agent antwortet auf Mattermost
           → Nachricht an Bot → Bot antwortet
           → BEWEIS: Screenshot von MM-Antwort

Schritt 4: Governance Hooks erzwingen Regeln
           → Agent versucht destruktiven Befehl → BLOCKED
           → BEWEIS: Audit Log zeigt Block

Schritt 5: Compliance Docs + Hash Chain
           → nomos hire + gate → 5 Docs + Chain
           → BEWEIS: chain.jsonl + verify = VALID
           (DAS haben wir — funktioniert)

Schritt 6: Dashboard zeigt echte Daten
           → Console zeigt laufenden Agent mit Compliance
           → BEWEIS: Browser Screenshot
```

## Verletzte Regeln

| Regel | Verstoss |
|-------|----------|
| S9 Geist | Fassade statt Produkt |
| R8 Scope Gate | "Loest das ein Kunden-Problem?" — Nein |
| R9 Architecture Gate | Keine echten User Stories |
| R10 Anti-Skeleton | Console = UI ohne Backend |
| Playbook01 | Null Branding |
| NomOS Spec | "NemoClaw IMMER dabei" — nicht dabei |
| NomOS Spec | "Enforcement not recommendation" — nur Markdown |

## Lessons Learned

1. Bottom-up ist nur richtig wenn die RICHTIGEN Schichten gebaut werden
2. 84 gruene Tests koennen 0% Produkt-Funktion bedeuten
3. UI vor funktionierendem Backend = Fassade
4. "Production-ready" sagen ohne NemoClaw = Luege
5. Selbes Pattern wie vorherige Session — trotz 6 Analyse-Reports nicht verhindert
6. Tests pruefen Code-Korrektheit, nicht Produkt-Funktion
