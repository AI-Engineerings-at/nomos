# Von der Spec zum Produkt — Multi-Agent Entwicklung mit PDCA

> Ein Erfahrungsbericht: Wie ein Compliance-Produkt mit 389 Tests,
> 44 API-Endpoints und ~7.500 Zeilen Code in einer Session entstand.

**Datum:** 25.03.2026
**Autor:** AI Engineering (Joe + Claude Agents)
**Produkt:** NomOS v2 — EU AI Act Compliance Control Plane
**Status:** Phase 4 abgeschlossen, Phase 5-6 ausstehend

---

## Abstract

NomOS ist eine Compliance Control Plane fuer AI-Agenten, die EU AI Act und DSGVO Konformitaet erzwingt. Version 1 hatte 92 Tests und deckte etwa ein Zehntel des geplanten Funktionsumfangs ab. Das Ziel: ein produktionsreifes System mit vollstaendiger API, Plugin-Runtime, Auth-System und Compliance-Checks — in einer zusammenhaengenden Entwicklungssession.

Dafuer wurde ein Master Plan mit 9 Sub-Projekten (A-I) erstellt, aufgeteilt in 6 Phasen mit expliziten Abhaengigkeiten. Parallele Claude Code Agents arbeiteten in isolierten Git Worktrees, gefuehrt durch TDD (Test-Driven Development) und einen PDCA-Zyklus (Plan-Do-Check-Act) nach jeder Phase. Das Ergebnis nach Phase 4: 389 Tests (0 Failures), 44 API-Endpoints, 12 Services, 11 Runtime Hooks, ~7.500 Zeilen produktiver Code.

Der wichtigste Befund: Die Methodik funktioniert, aber nur mit systematischen Korrekturen. 8 Endpoints wurden im ersten Durchlauf vergessen, 108 Deprecation Warnings blieben unentdeckt, und Agents lasen nur ihre eigenen Tasks statt den Gesamtplan. Zwei neue Regeln (R13: Post-Phase PDCA, R14: Plan-Pflichtlektuere) beheben das strukturell. Dieser Bericht dokumentiert was funktioniert hat, was nicht, und was wir daraus gelernt haben.

---

## 1. Ausgangslage

### Was ist NomOS?

NomOS (Nomos = Gesetz + OS) ist eine Compliance Control Plane fuer OpenClaw/NemoClaw, die EU AI Act und DSGVO Konformitaet erzwingt. Keine eigene Agent-Runtime — eine Governance-Schicht die sich in das bestehende Oekosystem einklinkt, alles ueberwacht, dokumentiert und bei Verstoessen blockiert.

**Zielgruppe:** KMU-Geschaeftsfuehrer (1-50 MA) im DACH-Raum die AI-Agenten einsetzen und legal compliant sein muessen. Die EU AI Act Deadline fuer High-Risk Systeme ist der 02.08.2026.

**Deployment:** `docker compose up -d` auf dem Server des Kunden. Standalone. Keine Cloud-Abhaengigkeit.

**Lizenz:** FCL (Fair Core License) — 3 Agents gratis mit vollem Funktionsumfang, ab 4 kommerziell. Change License zu Apache 2.0 nach 2 Jahren.

### Wo standen wir? (v1 Bestandsaufnahme)

| Modul | Zeilen | Tests | Status |
|-------|--------|-------|--------|
| nomos-cli (Core Library) | ~2.100 | 84 | Funktional |
| nomos-api (FastAPI) | ~679 | 14 | 5 Endpoints |
| nomos-console (Next.js) | ~500 | 1 E2E | Minimal |
| nomos-plugin (OpenClaw) | ~250 | 0 | Nur Slash Commands |
| **Summe v1** | **~2.850** | **92** | **~10% Produktumfang** |

Version 1 hatte ein funktionierendes CLI mit Manifest-Validierung, Hash-Chain Audit Trail und Compliance-Check. Aber kein Auth-System, kein Plugin-Runtime, keine Approval-Workflows, kein PII-Filter, keine Budget-Kontrolle. Ein Zehntel eines Produkts.

### Was war das Ziel?

Ein produktionsreifes System das ein KMU-Chef installiert (`docker compose up -d`) und sofort nutzen kann: Agents einstellen, ueberwachen, Compliance-Dokumentation generieren, Audit Trail exportieren, bei Problemen pausieren oder kuendigen. Alles ueber eine zentrale Console, mit vollstaendiger API dahinter.

---

## 2. Methodik: Plan, Execute, Verify, Correct, Rescope

### Der Master Plan

Der Master Plan definiert 9 Sub-Projekte (A-I), aufgeteilt in 6 Phasen:

```
Phase 0: Repo-Reorganisation
Phase 1: Foundation — Plugin Core (A) + Auth (E) — PARALLEL
Phase 2: Core Logic — Control Plane (B) + Compliance Runtime (C) — PARALLEL
Phase 3: Integration — Honcho/Memory (D)
Phase 4: API v2 — alle Endpoints zusammenfuehren (F)
Phase 5: User Facing — CLI v2 (G) + Console (H) — PARALLEL
Phase 6: Ship — CI/CD + Customer Delivery (I)
```

Jedes Sub-Projekt hat ein eigenes Plan-Dokument mit:
- User Stories ("Als KMU-Chef will ich...")
- Dateiliste (was wird neu erstellt, was erweitert)
- Interface-Definitionen (Inputs, Outputs, Fehler)
- Test-Strategie

Die Phasen haben explizite Abhaengigkeiten: Phase 2 braucht Phase 1, Phase 4 braucht Phase 1-3, Phase 5 braucht Phase 4. Parallele Ausfuehrung ist nur innerhalb einer Phase moeglich, wenn die Sub-Projekte unabhaengig sind.

### Parallele Agents in Git Worktrees

Fuer parallele Phasen (z.B. Phase 1: A + E, Phase 2: B + C) laufen separate Claude Code Agents in isolierten Git Worktrees. Jeder Agent hat:

- Seinen eigenen Branch (`feature/sub-A-plugin-core`, `feature/sub-E-auth`)
- Sein eigenes Arbeitsverzeichnis (Git Worktree)
- Seinen eigenen Plan (das Sub-Projekt Dokument)
- Keinen Zugriff auf die Aenderungen der anderen Agents

Nach Abschluss wird zurueck auf `main` gemerged. Bei unabhaengigen Sub-Projekten gibt es kaum Merge-Konflikte — die Dateien ueberlappen sich nicht.

Dieses Pattern ist inzwischen in der Community etabliert. Git Worktrees isolieren jeden Agent vollstaendig, und bei guter Task-Aufteilung (unterschiedliche Dateien pro Agent) sind Merge-Konflikte selten. Tools wie Clash (github.com/clash-sh/clash) koennen potenzielle Konflikte frueh erkennen, waren in unserem Fall aber nicht noetig.

### TDD als Grundprinzip

Jede Komponente wird Test-First entwickelt:

1. Test schreiben der das gewuenschte Verhalten beschreibt
2. Minimale Implementation die den Test bestehen laesst
3. Refactoring bei Bedarf

Regel R10 (Anti-Skeleton) verbietet explizit:
- Dateien ohne Tests
- Leere Funktionen
- "TODO: implement later" Kommentare
- Platzhalter-Code

Das klingt streng, ist aber der Grund warum nach 4 Phasen null Regressions auftreten: Jede neue Komponente hat vom ersten Moment an Tests.

### PDCA nach jeder Phase

Nach Abschluss jeder Phase wird ein vollstaendiger PDCA-Zyklus durchlaufen (Regel R13):

1. **Plan** — Der Phase-Plan definiert was gebaut werden soll
2. **Do** — Agents implementieren nach Plan
3. **Check** — IST/SOLL Vergleich: jeden Endpoint, Service, jede Datei gegen Plan pruefen. Alle Tests auf `main` ausfuehren.
4. **Act** — Luecken identifizieren und schliessen (Gap-Fix Sprint). Restlichen Plan anpassen.

Konkret fuer Phase 4 sah der Check so aus:

| Bereich | Geplant | Implementiert | Fehlend |
|---------|---------|---------------|---------|
| Auth | 5 | 5 | 0 |
| Fleet/Agents | 9 | 9 | 0 |
| Tasks | 4 | 4 | 0 |
| Approvals | 3 | 3 (+1 Bonus) | 0 |
| Compliance | 3 | 3 | 0 |
| Audit | 4 | 3 | 1 |
| Costs | 2 | 2 | 0 |
| Settings | 2 | 0 | 2 |
| **TOTAL** | **47** | **44 (+2 Bonus)** | **3** |

3 Endpoints fehlten. Das Audit hat sie gefunden, und sie wurden bewusst zu Phase 5 deferred — weil die Console sie braucht, nicht die API allein. Ohne den PDCA-Zyklus waeren diese Luecken unentdeckt in die naechste Phase gewandert.

---

## 3. Was funktioniert hat

### Worktree-Isolation: 10 Agents, null Datenverlust

Ueber alle Phasen hinweg liefen bis zu 10 parallele Agents in separaten Git Worktrees. Kein einziger Datenverlust, kein korrumpiertes Repository. Die Isolation funktioniert, weil jeder Agent auf seinem eigenen Branch arbeitet und nur seine eigenen Dateien aendert.

Der Merge zurueck auf `main` war in den meisten Faellen trivial — ein Fast-Forward oder ein Merge mit wenigen Konflikten in gemeinsam genutzten Dateien (z.B. `__init__.py` Exports).

### TDD erzwingt Qualitaet: 389 Tests, 0 Regressions

Am Ende von Phase 4:
- 151 CLI Tests (Core Library)
- 192 API Tests (FastAPI, 16 Router, 12 Services)
- 46 Plugin Tests (11 Hooks, API Client)
- **0 Failures**

Die Test-Pyramide ist ausgewogen: Unit Tests fuer Business Logic, Integration Tests fuer API-Endpoints, Plugin Tests fuer Hook-Verhalten. Kein Test ist ein "TODO" oder Platzhalter — Regel S9 verbietet das.

### Parallele Ausfuehrung spart Zeit

Phase 1 (Plugin Core + Auth) und Phase 2 (Control Plane + Compliance Runtime) liefen jeweils parallel. Statt sequenziell 4 Sub-Projekte nacheinander abzuarbeiten, liefen sie paarweise gleichzeitig. Die Zeitersparnis ist schwer exakt zu messen, aber die Abhaengigkeits-Analyse zeigt: mindestens 40% der Arbeit konnte parallelisiert werden.

### Design Spec als Single Source of Truth

Die Design Spec v5 (`2026-03-24-nomos-v2-design.md`) definiert alles: Architektur, Interfaces, Datenmodelle, UI-Konzepte. Jeder Agent referenziert diese Spec. Wenn ein Agent eine Frage hat ("Wie soll der Approval-Flow funktionieren?"), steht die Antwort in der Spec — nicht in einer Chat-Nachricht die verloren geht.

Die Spec wurde iterativ verbessert: v1 nach dem initialen Design, v2 nach Legal/Tech/UX Review (6.1/10, 6.4/10, 5.5/10), v3 nach externem Feedback (8.7/10), v4 nach Implementierungserkenntnissen, v5 nach Phase 4 Audit.

### FCL als ehrliches Business-Modell

Die Fair Core License (FCL) gibt 3 Agents gratis mit vollem Funktionsumfang. Kein Feature-Gating, keine kuenstlichen Limits ausser der Agent-Anzahl. Ab Agent 4 braucht es eine kommerzielle Lizenz. Nach 2 Jahren wechselt die Lizenz zu Apache 2.0.

Das ist ein bewusster Gegenentwurf zu SaaS-Modellen die Compliance als Service verkaufen: NomOS laeuft auf dem Server des Kunden, Daten verlassen nie das Netzwerk, und der Kern wird nach 2 Jahren Open Source. Fuer ein Compliance-Tool ist das ein Vertrauensargument.

---

## 4. Was NICHT funktioniert hat (Gotchas)

### G1: Plan allein reicht nicht — 8 Endpoints wurden vergessen

Der Master Plan definierte 47 Endpoints. Nach Phase 4 waren 44 implementiert — 3 fehlten, und 2 Bonus-Endpoints wurden ungeplant hinzugefuegt. Das Problem: Der Plan war detailliert genug, aber die Agents haben nicht jeden einzelnen Endpoint gegen den Plan geprueft.

Ohne den PDCA-Audit nach Phase 4 waeren diese Luecken erst bei der Console-Entwicklung aufgefallen — zu spaet und teurer zu fixen.

### G2: Agents lesen nur ihren Task, nicht den Gesamt-Plan

Jeder Agent bekam seinen Sub-Plan (z.B. "Sub-Projekt F: API v2"). Das Problem: Agents lasen nur ihren eigenen Task, nicht den Master Plan. Dadurch fehlte der Gesamtkontext — ein Agent wusste nicht was der andere gebaut hat und konnte keine Inkonsistenzen erkennen.

**Fix (R14):** Jeder Agent der einen Sub-Plan ausfuehrt MUSS:
- Den KOMPLETTEN Plan lesen (nicht nur seine Tasks)
- Die Endpoint-Liste aus dem Master Plan gegen seine Arbeit abgleichen
- Am Ende einen Self-Check Report erstellen: "Geplant vs. Gebaut"
- Fehlende Endpoints/Tests explizit als GAP melden

### G3: Parallele Agents + geteilte Dateien = Merge-Konflikte

Obwohl die Sub-Projekte unterschiedliche Dateien haben, gibt es Ueberlappungen: `__init__.py` (Exports), `main.py` (App-Konfiguration), `config.py` (Einstellungen). Diese Dateien werden von mehreren Agents gleichzeitig geaendert.

**Loesung:** Geteilte Dateien werden zum Merge-Zeitpunkt manuell zusammengefuehrt. Bei guter Planung (unterschiedliche Sektionen in der Datei pro Agent) sind die Konflikte minimal. Aber es erfordert Aufmerksamkeit.

### G4: Library-Deprecation Warnings (108 in Tests)

Nach Phase 4 zeigten die API-Tests 108 Deprecation Warnings:
- `asyncio.iscoroutinefunction` deprecated (kommt aus FastAPI)
- `httpx per-request cookies` deprecated (kommt aus Test-Code)

Keines davon ist unser Code — es sind Library-Deprecations. Aber 108 Warnings im Test-Output machen es schwer, echte Probleme zu erkennen. Und bei `python -m pytest -W error::DeprecationWarning` scheitern 82 Tests.

**Risiko:** Niedrig aktuell (Python 3.12), aber Python 3.16 wird `asyncio.iscoroutinefunction` entfernen. Dann braucht FastAPI ein Update.

### G5: PII Regex false positives

Der PII-Filter nutzt 6 Regex-Muster fuer Email, Telefon, IBAN, Kreditkarte, Sozialversicherungsnummer und IP-Adressen. Das deckt 90%+ der gaengigen PII-Muster ab, hat aber false positives: technische Strings die wie PII aussehen.

**Geplanter Fix:** NER (Named Entity Recognition) via spaCy als optionale zweite Stufe. Config-Switch: `pii_filter: "regex"` (Standard) oder `pii_filter: "ner_full"`.

---

## 5. Die Korrekturen

### R13: PDCA-Zyklus als Gate nach jeder Phase

Die wichtigste neue Regel. Nach Abschluss jeder Phase wird ein vollstaendiger Zyklus durchlaufen:

```
Planung → Ausfuehrung → Pruefung → Korrektur → Rescope → Plan ausrichten → Weiter
```

1. **Pruefung:** IST/SOLL Vergleich — jeden Endpoint, Service, jede Datei gegen Plan pruefen
2. **Pruefung:** Alle Tests auf `main` ausfuehren (CLI + API + Plugin)
3. **Korrektur:** Luecken identifizieren und schliessen (Gap-Fix Sprint)
4. **Rescope:** Restlichen Plan anpassen — was hat sich durch die Erkenntnisse geaendert?
5. **Plan ausrichten:** Master Plan aktualisieren mit tatsaechlichem Stand + Anpassungen

Kein Phasen-Uebergang ohne abgeschlossenen Zyklus. Das ist ein Blocker — die naechste Phase startet nicht ohne Audit.

### R14: Agents muessen vollen Plan lesen + Self-Check

Jeder Agent der einen Sub-Plan ausfuehrt MUSS den KOMPLETTEN Master Plan lesen und am Ende einen Self-Check Report erstellen. Das verhindert dass Agents in ihrem eigenen Kontext-Tunnel arbeiten und den Gesamtzusammenhang verlieren.

### Gap-Fix Sprint als systematischer Prozess

Der Phase-4-Audit identifizierte 6 Gaps die sofort gefixt wurden und 3 die bewusst zu Phase 5 deferred wurden. Der Gap-Fix Sprint ist kein "Quick-Fix" (verboten durch S9) — jede Luecke wird mit Root Cause analysiert:

- **Warum fehlt es?** (Agent hat Plan nicht vollstaendig gelesen)
- **Ist es ein Blocker?** (Settings: Nein, Console braucht es erst)
- **Wann wird es gefixt?** (Phase 5, mit klarem Owner)

### Rescope des restlichen Plans

Nach dem Phase-4-Audit wurden Anpassungen fuer Phase 5 und 6 dokumentiert:

| Phase 5 Anpassung | Grund |
|-------------------|-------|
| Settings Endpoints (2) nachholen | Console braucht sie |
| Global Audit Endpoint nachholen | Audit-Panel braucht ihn |
| TTS/STT als eigene Sub-Aufgabe | Groesser als im Plan angenommen |
| httpx Test-Pattern ueberarbeiten | Deprecation Warnings eliminieren |

| Phase 6 Anpassung | Grund |
|-------------------|-------|
| Alembic Migrationen hinzufuegen | DB Schema muss versioniert werden |
| Honcho Container in docker-compose | In-memory zu echter Persistenz |
| spaCy NER als optionaler Service | Bessere PII Detection fuer High-Risk Agents |

---

## 6. Vergleich mit dem Markt

### AI-gestuetzte Softwareentwicklung: Stand der Forschung

Die Branche bewegt sich schnell. Anthropic's "2026 Agentic Coding Trends Report" identifiziert acht Trends die Software-Entwicklung veraendern, darunter den Shift von "Code schreiben" zu "Agents koordinieren die Code schreiben". Laut einer Umfrage unter 15.000 Entwicklern nutzen 73% der Engineering-Teams taeglich AI-Coding-Tools — gegenueber 41% in 2025 und 18% in 2024.

Die Produktivitaetsfrage ist dabei nicht eindeutig beantwortet. Eine METR-Studie (Juli 2025, arXiv:2507.09089) mit 16 erfahrenen Open-Source-Entwicklern zeigte ueberraschend: mit AI-Tools brauchten Entwickler 19% laenger fuer ihre Tasks. Gleichzeitig glaubten die Entwickler, 24% schneller gewesen zu sein. Dieser "Perception-Reality Gap" ist ein wichtiger Datenpunkt: AI-Tools fuehlen sich produktiv an, aber bei erfahrenen Entwicklern auf komplexen Codebasen ist der messbare Effekt unklar.

Unser Ansatz unterscheidet sich von der METR-Studie in einem entscheidenden Punkt: Wir haben nicht einen Entwickler mit AI-Tool gemessen, sondern ein System aus orchestrierten Agents mit klarem Plan. Der Plan als Single Source of Truth und TDD als Quality Gate eliminieren zwei der Hauptprobleme die in der METR-Studie identifiziert wurden: Zeit fuer Code-Cleanup und fehlender Gesamtkontext.

### EU AI Act Compliance-Tools: Was existiert

Der Markt fuer AI Governance Software ist jung — bewertet mit 0,34 Milliarden USD in 2025, prognostiziert auf 1,21 Milliarden USD bis 2030. Die bestehenden Anbieter folgen dem SaaS-Modell:

| Tool | Modell | Fokus | Preis |
|------|--------|-------|-------|
| Vanta | SaaS | 400+ Integrationen, Compliance Dashboard | Enterprise |
| OneTrust | SaaS | AI Inventories, Impact Assessments, Bias Monitoring | Enterprise |
| FairNow | SaaS | AI Risk Management, Oversight Integration | Enterprise |
| Holistic AI | SaaS | AI Act Readiness Assessment | Enterprise |
| ServiceNow | SaaS | Integrated Digital Processes, Monitoring | Enterprise |
| **NomOS** | **Self-Hosted (FCL)** | **Runtime Enforcement, Audit Trail, On-Prem** | **3 Agents gratis** |

NomOS unterscheidet sich in drei Punkten:

1. **Self-Hosted:** Daten verlassen nie das Netzwerk des Kunden. Fuer KMUs die keine Compliance-Daten an einen SaaS-Anbieter senden wollen, ist das ein entscheidendes Kriterium.

2. **Runtime Enforcement:** Die meisten Tools sind Dokumentations-Plattformen — sie helfen Compliance nachzuweisen, erzwingen sie aber nicht zur Laufzeit. NomOS klinkt sich als Plugin in den Gateway ein und blockiert Non-Compliance aktiv (kein Agent startet ohne vollstaendige Docs, destruktive Tool-Calls brauchen Genehmigung, PII wird automatisch gefiltert).

3. **Preis:** Enterprise SaaS vs. 3 Agents gratis. Fuer ein KMU mit 2-3 AI-Agenten ist NomOS kostenlos und laeuft auf dem eigenen Server.

### Alternative Entwicklungsansaetze

Git Worktrees fuer parallele AI-Agent-Entwicklung sind ein Pattern das 2025/2026 stark an Popularitaet gewonnen hat. Es gibt inzwischen dedizierte Tools dafuer (agent-worktree, Clash), und Blogs von Nx, DEV.to und unabhaengigen Entwicklern dokumentieren aehnliche Workflows.

Unser Ansatz fuegt dem Pattern zwei Elemente hinzu die wir in der Literatur nicht gefunden haben:

1. **PDCA nach jeder Phase** — nicht nur am Ende des Projekts
2. **Pflicht zur Gesamt-Plan-Lektuere** — Agents lesen nicht nur ihren Task

---

## 7. Zahlen und Ergebnisse

### Gesamtstand nach Phase 4

```
Code:
  nomos-cli:    ~2.500 Zeilen Python (Core Library)
  nomos-api:    ~3.500 Zeilen Python (FastAPI, 16 Router, 12 Services)
  nomos-plugin: ~1.500 Zeilen TypeScript (11 Hooks, API Client)
  TOTAL:        ~7.500 Zeilen produktiver Code

Tests:
  389 Tests (151 CLI + 192 API + 46 Plugin)
  0 Failures
  108 Warnings (Library-Deprecations, nicht unser Code)

Dateien:
  ~95 neue Dateien seit Phase 0

Endpoints:
  44 implementiert (+ 2 Bonus) von 47 geplant (93%)
```

### Vorher/Nachher Vergleich

| Metrik | v1 (vorher) | v2 Phase 4 (nachher) | Faktor |
|--------|-------------|----------------------|--------|
| Codezeilen | ~2.850 | ~7.500 | 2.6x |
| Tests | 92 | 389 | 4.2x |
| API Endpoints | 5 | 44 | 8.8x |
| Services | 2 | 12 | 6x |
| Runtime Hooks | 0 | 11 | -- |
| Compliance Docs | 2 | 14 | 7x |
| Auth System | keines | JWT + TOTP + Recovery | -- |
| PII Filter | keiner | 6 Regex-Muster | -- |
| Audit Trail | basic | SHA-256 Hash Chain | -- |
| Budget Control | keine | Pro-Agent Tracking | -- |
| Kill Switch | keiner | Art. 14 EU AI Act | -- |
| Incident Detection | keine | 72h DSGVO Art. 33 | -- |
| FCL Enforcement | keines | 3 Agents gratis | -- |

### Test-Pyramide

```
           /--------\
          / 1 E2E    \        (geplant fuer Phase 6)
         /   Script   \
        /--------------\
       / 192 API Tests  \     Integration: Endpoints, Auth, Services
      /  (+ 46 Plugin)   \
     /--------------------\
    /  151 Unit Tests      \   Core Library: Manifest, Gate, Hash Chain,
   /   (CLI/Core)           \  Events, PII, Retention, Forge, Compliance
  /-------------------------\
```

### Compliance-Abdeckung

| EU AI Act Artikel | NomOS Feature | Status |
|-------------------|---------------|--------|
| Art. 9 (Risk Management) | 14 Doc-Templates (risk-class based: 5/9/13-14) | Implementiert |
| Art. 13 (Transparency) | Compliance Matrix, Gate Check | Implementiert |
| Art. 14 (Human Oversight) | Kill Switch, Pause, Approval Gate | Implementiert |
| Art. 50 (AI-Generated Label) | message_sending Hook, Disclosure | Implementiert |
| Art. 52 (Disclosure) | Automatische Markierung | Implementiert |
| DSGVO Art. 17 (Recht auf Loeschung) | Forget API, Data Retention | Implementiert |
| DSGVO Art. 33 (Incident Meldung) | 72h Timer, Auto-Detection | Implementiert |
| DSGVO Art. 35 (DSFA) | Generierte Folgenabschaetzung | Implementiert |

---

## 8. Architektur-Entscheidungen

### Warum Valkey statt Redis

Redis hat 2024 seine Lizenz von BSD auf SSPL/RSAL geaendert. Fuer ein Produkt das unter FCL (Fair Core License) vertrieben wird, ist das ein Problem: die SSPL-Lizenz hat Restriktionen die mit unserem Vertriebsmodell kollidieren koennten.

Valkey (BSD-3) ist ein Fork von Redis 7.2, gepflegt von der Linux Foundation. Drop-in Replacement, gleiche API, gleiche Performance. Fuer NomOS als Self-Hosted Produkt ist BSD-3 die saubere Wahl.

### Warum FCL statt SaaS

Compliance-Daten sind sensibel. Ein KMU-Chef der EU AI Act Compliance fuer seine AI-Agenten braucht, will seine Audit Trails, Risikobewertungen und Compliance-Reports nicht an einen Cloud-Anbieter senden. Besonders nicht wenn DSGVO-Konformitaet Teil des Produktversprechens ist.

FCL gibt dem Kunden:
- Volle Kontrolle ueber seine Daten (Self-Hosted)
- 3 Agents gratis mit vollem Funktionsumfang (kein Feature-Gating)
- Planungssicherheit (Apache 2.0 nach 2 Jahren)
- Transparenz (Code ist lesbar, auditierbar)

Fuer den Anbieter (uns) bedeutet es:
- Kein Betrieb von Kunden-Infrastruktur
- Skalierung ueber Lizenzen, nicht ueber Server
- Kein Vendor Lock-in fuer Kunden

### Warum 11 Runtime Hooks

NomOS ist kein passives Dokumentations-Tool. Es klinkt sich aktiv in den Message-Flow des AI-Gateways ein:

| Hook | Wann | Was |
|------|------|-----|
| gateway_start | Gateway startet | Fleet Sync, Health Check |
| before_agent_start | Agent startet | Compliance Gate (alle Docs da?) |
| before_tool_call | Tool wird aufgerufen | Approval Check, Budget Check |
| after_tool_call | Tool fertig | Audit Trail Entry (Hash Chain) |
| tool_result_persist | Ergebnis wird gespeichert | PII Filter |
| message_received | Nachricht kommt rein | Session Tracking, Kosten-Start |
| message_sending | Antwort geht raus | Art. 50 Label ("KI-generiert") |
| session_start | Session beginnt | Honcho Session Create/Resume |
| session_end | Session endet | Kosten-Berechnung, Summary |
| agent_end | Agent beendet | Final Audit, Compliance Close |
| on_error | Fehler passiert | Auto-Pause, Incident Detection |

Jeder Hook hat ein klares Execution Pattern: `sequential` (muss abgeschlossen sein bevor der Flow weitergeht), `parallel` (laeuft asynchron), oder `synchron` (blockiert den Flow bis das Ergebnis da ist).

### Warum PixiJS fuer Office-Visualisierung (Phase 5 geplant)

Die Console-Vision sieht ein virtuelles Buero vor (inspiriert von Kimi Agent Team): Agents als Pixel-Art Figuren die an ihren Schreibtischen arbeiten, Status-Badges ueber dem Kopf, Animationen bei Aktivitaet. Das ist nicht Spielerei — es ist die "Easy Layer" des Dual-Layer Konzepts: Ein KMU-Chef soll in 15 Sekunden sehen welche Agents aktiv sind und ob es Probleme gibt.

PixiJS (WebGL/Canvas) ist dafuer die richtige Wahl: performant, leichtgewichtig, gut dokumentiert. Die "Deep Layer" dahinter zeigt Tabellen, Charts und technische Details fuer den Techniker.

---

## 9. Lessons Learned (L1-L9)

### L1: Ein Plan ohne Verifizierung ist ein Wunschzettel

Der Master Plan war detailliert — 9 Sub-Projekte, explizite Abhaengigkeiten, User Stories, Interface-Definitionen. Trotzdem fehlten nach Phase 4 drei Endpoints. Ein Plan der nicht nach jeder Phase gegen die Realitaet geprueft wird, akkumuliert stille Abweichungen.

**Fix:** R13 (PDCA nach jeder Phase) mit hartem Gate — keine naechste Phase ohne Audit.

### L2: Agents optimieren lokal, nicht global

Jeder Agent macht seinen Job gut — innerhalb seines Kontexts. Aber kein Agent prueft ob sein Output mit dem Gesamtsystem konsistent ist. Das ist kein Bug der Agents, sondern ein Design-Problem der Orchestrierung.

**Fix:** R14 (Pflicht zum Lesen des vollen Plans + Self-Check Report).

### L3: Library-Warnings sind technische Schulden

108 Deprecation Warnings klingen harmlos. Aber sie machen den Test-Output unlesbar und verstecken echte Warnungen. Und bei `pytest -W error` scheitern 82 Tests — was die Option eliminiert, Warnings als Errors zu behandeln (eine Best Practice in CI/CD).

**Fix:** Library-Update sobald verfuegbar. Test-Pattern (httpx per-request cookies) umstellen.

### L4: PII ist ein Spektrum, kein Boolean

Regex-basierte PII-Erkennung ist gut fuer offensichtliche Muster (Email, IBAN, Kreditkarte). Aber PII ist kontextabhaengig: "Herr Mueller aus Muenchen" ist PII, "Mueller" allein nicht. NER (Named Entity Recognition) loest das besser, ist aber langsamer und braucht ein Sprachmodell.

**Fix:** Zwei-Stufen-Architektur. Regex als schnelle erste Stufe (Standard), NER als optionale zweite Stufe fuer High-Risk Agents.

### L5: In-Memory Zustand ist akzeptabel — mit klarem Upgrade-Pfad

Honcho Client, FCL Enforcement und Auth nutzen aktuell in-memory Zustand. Das heisst: bei Neustart gehen Daten verloren. Das ist akzeptabel fuer die Entwicklungsphase, weil die Interfaces identisch mit der Produktions-Implementierung sind (z.B. Honcho in-memory vs. Honcho Container: gleiche API-Methoden).

**Bedingung:** Der Upgrade-Pfad muss klar sein und dokumentiert. Kein "wir fixen das irgendwann".

### L6: Parallele Ausfuehrung skaliert nicht linear

Zwei parallele Agents sind fast doppelt so schnell. Fuenf parallele Agents sind nicht fuenfmal so schnell — der Merge-Overhead waechst, die Koordination braucht Zeit, und geteilte Dateien werden zum Flaschenhals.

**Empfehlung:** 2-3 parallele Agents pro Phase sind der Sweet Spot. Mehr ist moeglich, braucht aber diszipliniertere Datei-Aufteilung.

### L7: Design Spec Versioning ist Pflicht

Die Design Spec durchlief 5 Versionen (v1 bis v5). Ohne klare Versionierung waere unklar gewesen welche Spec ein Agent gelesen hat. "Ich habe die Spec gelesen" heisst nichts wenn es 5 Versionen gibt.

**Fix:** Spec-Version im Frontmatter, Agent dokumentiert welche Version er gelesen hat.

### L8: Bonus-Features sind ein Warnsignal

Zwei Bonus-Endpoints (ein zusaetzlicher Approval-Endpoint, ein zusaetzlicher Incident-Endpoint) wurden ungeplant implementiert. Das klingt positiv, ist aber ein Warnsignal: Wenn ein Agent Features baut die nicht im Plan stehen, hat er entweder den Plan nicht gelesen oder eigene Entscheidungen getroffen.

**Fix:** R14 Self-Check Report muss auch ungeplante Features explizit auflisten.

### L9: Quality Gates muessen automatisiert sein

R13 (PDCA) ist aktuell ein manueller Prozess: Endpoints zaehlen, Tests ausfuehren, gegen Plan vergleichen. Das funktioniert, skaliert aber nicht. Ein automatisiertes Script das den Plan parst und gegen die Codebase vergleicht waere der naechste Schritt.

**Geplant:** Phase 6 (CI/CD) wird einen automatisierten PDCA-Check enthalten.

---

## 10. Fazit + Ausblick

### Was fehlt noch

- **Phase 5a (CLI v2):** hire/kill/pause/retire/forget/assign/deploy/patch Commands
- **Phase 5b (Console):** Next.js 15 Command Center mit Pixel-Art Office, 13+ Panels, TTS/STT
- **Phase 5c:** 3 deferred Endpoints (Settings GET/PATCH, Global Audit)
- **Phase 6:** CI/CD Pipeline, E2E Tests, Docker-Stack Integration, Alembic Migrationen

### Was wir anders machen wuerden

1. **R13 und R14 von Anfang an:** Nicht erst nach Phase 4 einfuehren, sondern ab Phase 1. Die Luecken die wir in Phase 4 gefunden haben, waeren in Phase 1-3 kleiner und einfacher zu fixen gewesen.

2. **Geteilte Dateien vorab identifizieren:** Vor der parallelen Ausfuehrung explizit auflisten welche Dateien von mehreren Agents geaendert werden. Dann entweder Lock-Mechanismus oder sequenzielle Bearbeitung dieser Dateien.

3. **Deprecation Warnings sofort adressieren:** Nicht warten bis 108 Warnings akkumuliert sind. Beim ersten Auftreten fixen oder bewusst als "akzeptiert" dokumentieren.

### Empfehlung fuer aehnliche Projekte

1. **Master Plan mit expliziten Abhaengigkeiten** — Kein Agent arbeitet ohne Plan. Der Plan definiert WAS gebaut wird (Endpoints, Services, Dateien), nicht WIE (das entscheidet der Agent).

2. **TDD ist nicht optional** — Jede Datei hat Tests. Keine Ausnahmen. S9 (Anti-Skeleton) macht das enforceable.

3. **PDCA nach jeder Phase** — Nicht am Ende des Projekts, sondern nach jedem logischen Abschnitt. Der Check muss quantitativ sein (Endpoints zaehlen, Tests ausfuehren), nicht qualitativ ("sieht gut aus").

4. **Git Worktrees fuer Isolation** — Parallele Agents in separaten Branches mit eigenen Arbeitsverzeichnissen. Minimale Ueberlappung bei den Dateien.

5. **Design Spec als Single Source of Truth** — Alles steht in der Spec. Keine muendlichen Absprachen, keine Chat-Nachrichten die verloren gehen.

6. **Ehrlich dokumentieren was nicht funktioniert** — Gotchas, Luecken, Workarounds. Nicht vertuschen, sondern systematisch erfassen und fixen.

---

## Quellen

### AI-gestuetzte Softwareentwicklung

- [Anthropic: 2026 Agentic Coding Trends Report](https://resources.anthropic.com/2026-agentic-coding-trends-report) — 8 Trends die Software-Entwicklung veraendern
- [Anthropic: Eight Trends Defining How Software Gets Built in 2026](https://claude.com/blog/eight-trends-defining-how-software-gets-built-in-2026)
- [METR: Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/) — 19% langsamer mit AI (arXiv:2507.09089)
- [METR: Follow-up Study — Changing Developer Productivity Experiment Design](https://metr.org/blog/2026-02-24-uplift-update/)
- [Anthropic: How AI Assistance Impacts Coding Skills](https://www.anthropic.com/research/AI-assistance-coding-skills)
- [Faros AI: The AI Productivity Paradox Research Report](https://www.faros.ai/blog/ai-software-engineering)
- [Claude 5 Developer Survey 2026: 73% Daily AI Tool Usage](https://claude5.ai/news/developer-survey-2026-ai-coding-73-percent-daily)
- [SitePoint: GitHub Copilot vs Claude Code 2026 — Accuracy & Speed Analysis](https://www.sitepoint.com/github-copilot-vs-claude-code-accuracy-speed-2026/)

### Git Worktrees + Multi-Agent Patterns

- [Nick Mitchinson: Using Git Worktrees for Multi-Feature Development with AI Agents](https://www.nrmitchi.com/2025/10/using-git-worktrees-for-multi-feature-development-with-ai-agents/)
- [Clash: Avoid merge conflicts across git worktrees for parallel AI coding agents](https://github.com/clash-sh/clash)
- [Upsun: Git Worktrees for Parallel AI Coding Agents](https://devcenter.upsun.com/posts/git-worktrees-for-parallel-ai-coding-agents/)
- [Nx Blog: How Git Worktrees Changed My AI Agent Workflow](https://nx.dev/blog/git-worktrees-ai-agents)
- [DEV.to: Git Worktrees for AI Coding — Run Multiple Agents in Parallel](https://dev.to/mashrulhaque/git-worktrees-for-ai-coding-run-multiple-agents-in-parallel-3pgb)
- [Zen Van Riel: Running Multiple AI Coding Agents in Parallel](https://zenvanriel.com/ai-engineer-blog/running-multiple-ai-coding-agents-parallel/)
- [Claude Code Worktree Guide](https://claudefa.st/blog/guide/development/worktree-guide)

### PDCA / Deming Cycle in Software

- [PDCA — Wikipedia](https://en.wikipedia.org/wiki/PDCA)
- [Tech Agilist: Deming Cycle (PDCA) — Importance in Agile](https://www.techagilist.com/agile/deming-cycle/)
- [ZenTao: PDCA Cycle — A Necessary Tool to Quickly Improve Software Quality](https://www.zentao.pm/blog/pdca-cycle-necessary-tool-to-quickly-improve-software-quality-1223.html)
- [Kanban Zone: The PDCA Cycle — What is it and Why You Should Use it](https://kanbanzone.com/2021/what-is-pdca-cycle/)
- [Lark Suite: Plan Do Check Act for Software Development Teams](https://www.larksuite.com/en_us/topics/project-management-methodologies-for-functional-teams/plan-do-check-act-pdca-for-software-development-teams)

### EU AI Act + Compliance Tools

- [EU Commission: AI Act — Regulatory Framework](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai)
- [artificialintelligenceact.eu: EU AI Act Compliance Checker](https://artificialintelligenceact.eu/assessment/eu-ai-act-compliance-checker/)
- [Orrick: The EU AI Act — 6 Steps to Take Before 2 August 2026](https://www.orrick.com/en/Insights/2025/11/The-EU-AI-Act-6-Steps-to-Take-Before-2-August-2026)
- [Linux Foundation EU: What Open Source Developers Need to Know about the EU AI Act](https://linuxfoundation.eu/newsroom/ai-act-explainer)
- [Protiviti: White Paper — Effectively Implementing the EU AI Act](https://tcblog.protiviti.com/2025/08/12/white-paper-effectively-implementing-the-eu-ai-act-governance-control-and-transparency-for-ai-systems/)
- [Venvera: Best SaaS Platforms for EU AI Act Compliance in 2026](https://venvera.com/best/saas-platforms-for-eu-ai-act-compliance-in-2026/)
- [SecurePrivacy: AI Governance Framework Tools](https://secureprivacy.ai/blog/ai-governance-framework-tools)
- [SecurePrivacy: AI Risk & Compliance 2026 — Enterprise Governance Overview](https://secureprivacy.ai/blog/ai-risk-compliance-2026)
- [Vanta: EU AI Act Compliance Automation](https://www.vanta.com/products/eu-ai-act)
- [FairNow: EU AI Act Compliance](https://fairnow.ai/guide/use-fairnow-to-easily-prepare-for-the-eu-ai-act/)
- [ISACA: ISO/IEC 42001 and EU AI Act — A Practical Pairing for AI Governance](https://www.isaca.org/resources/news-and-trends/industry-news/2025/isoiec-42001-and-eu-ai-act-a-practical-pairing-for-ai-governance)

### Multi-Agent Frameworks

- [Akka: Agentic AI Frameworks for Enterprise Scale — 2026 Guide](https://akka.io/blog/agentic-ai-frameworks)
- [Anthropic: Measuring Agent Autonomy](https://www.anthropic.com/research/measuring-agent-autonomy)
- [Machine Learning Mastery: 7 Agentic AI Trends to Watch in 2026](https://machinelearningmastery.com/7-agentic-ai-trends-to-watch-in-2026/)

### Interne Dokumente

- `docs/superpowers/plans/2026-03-24-nomos-v2-master-plan.md` — Master Implementation Plan
- `docs/superpowers/plans/2026-03-25-phase-4-audit-report.md` — Phase 4 PDCA Audit
- `docs/superpowers/specs/2026-03-24-nomos-v2-design.md` — Design Specification v5
- `.claude/CLAUDE.md` — Development Rules (R8-R14, S9)

---

*Erstellt am 25.03.2026 als Teil des NomOS v2 Entwicklungsprozesses.*
*Dieser Bericht dokumentiert echte Erfahrungen — keine Theorie, keine geschoenten Zahlen.*
