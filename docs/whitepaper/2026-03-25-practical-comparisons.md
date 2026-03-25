# Praxis-Vergleiche: So macht man es FALSCH vs. RICHTIG

> Basierend auf echten Erfahrungen aus der NomOS v2 Entwicklung.
> Jeder Vergleich zeigt was die meisten machen, und was besser funktioniert.

---

## 1. Agent-Prompts: Vage vs. Praezise

### ❌ SCHLECHT (was die meisten machen)

```
"Implementiere die Authentifizierung fuer die API."
```

Was passiert:
- Agent baut irgendeine Auth (vielleicht Basic Auth, vielleicht OAuth)
- Keine Tests, oder nur Happy-Path Tests
- Kein Recovery Key, kein Rate Limiting
- Hardcoded Secrets in Code
- Am Ende: "funktioniert irgendwie", aber nicht produktionsreif

### ✅ BESSER (was wir gelernt haben)

```
"Du implementierst Sub-Projekt E: Auth + Security fuer NomOS.

LIES den Plan: docs/superpowers/plans/2026-03-25-sub-E-auth.md

Regeln aus .claude/CLAUDE.md:
- R10: Keine Datei ohne Tests. Kein TODO. Kein Placeholder.
- R12: Keine internen IPs in Produkt-Code.
- TDD: Test ZUERST schreiben, ausfuehren (FAIL), implementieren,
       ausfuehren (PASS), committen.

Der Plan hat KOMPLETTEN Code fuer Tasks 1-7.
Implementiere EXAKT wie geschrieben.

Am Ende: R14 Self-Check — liste alle Komponenten und bestaetigne
dass jede Tests hat."
```

Was passiert:
- Agent liest den Plan mit konkretem Code
- TDD erzwingt Qualitaet (Test vor Implementation)
- Self-Check am Ende faengt Luecken auf
- Regeln verhindern Shortcuts (kein TODO, kein Placeholder)
- Ergebnis: 43 Tests, JWT + 2FA + Recovery Key + Rate Limiter + 3 Rollen

**Warum es besser ist:** Der Agent hat KONTEXT. Er weiss nicht nur WAS er bauen soll, sondern WIE (Code im Plan), WARUM (User Stories), und WONACH er pruefen soll (Self-Check). Vage Prompts erzeugen vage Ergebnisse.

---

## 2. Projekt-Struktur: Chaos vs. System

### ❌ SCHLECHT

```
Session 1: "Bau mir eine API"
Session 2: "Jetzt das Frontend"
Session 3: "Warum funktioniert nichts zusammen?"
Session 4: "Fix die 47 Bugs"
```

Kein Plan. Kein Spec. Kein Review zwischen den Sessions. Ergebnis: Code der "irgendwie" funktioniert aber nicht zusammenpasst.

### ✅ BESSER

```
1. Design Spec schreiben (was + warum + wie)
   → Review (3 Perspektiven: Legal, Tech, UX)
   → Externes Feedback einholen
   → Korrekturen einarbeiten

2. Master Plan (Phasen, Abhaengigkeiten, Dateien)
   → Review durch Plan-Document-Reviewer
   → Offene Entscheidungen ALLE klaeren

3. Phase-fuer-Phase ausfuehren
   → PDCA nach jeder Phase
   → Gap-Fix wenn noetig
   → Rescope des restlichen Plans

4. Ergebnis: 416 Tests, 45 Endpoints, 0 Regressions
```

**Warum es besser ist:** Struktur kostet Zeit am Anfang, spart ein Vielfaches spaeter. Unsere Spec hat 921 Zeilen, der Master Plan 1.200. Das klingt nach viel — aber es hat verhindert dass wir 47 Bugs fixen muessen.

---

## 3. Agent-Fuehrung: Blind vs. Informiert

### ❌ SCHLECHT

```
Agent bekommt: "Implementiere Task 5 aus dem Plan"

Agent liest nur Task 5. Kennt nicht:
- Den Gesamt-Plan (was kommt vor und nach Task 5?)
- Die Endpoint-Liste (welche Endpoints sollen am Ende existieren?)
- Die Abhaengigkeiten (wer nutzt was ich baue?)

Ergebnis: Task 5 ist perfekt, aber 3 Endpoints die der Gesamt-Plan
erwartet wurden vergessen weil sie nicht explizit in Task 5 stehen.
```

Das ist uns passiert: 8 Endpoints fehlten nach Phase 1-3.

### ✅ BESSER

```
R14: Agent MUSS den VOLLEN Plan lesen.
R14: Agent macht am Ende einen Self-Check: "Geplant vs. Gebaut"
R14: Fehlende Endpoints werden explizit als GAP gemeldet.

Agent bekommt:
"Lies den KOMPLETTEN Plan. Nicht nur deine Tasks.
Am Ende: Liste JEDEN geplanten Endpoint und markiere
ob er implementiert ist oder fehlt."

Ergebnis: Agent meldet selbst "41/44 Endpoints implementiert,
3 fehlen: settings (2x), global audit (1x)"
```

**Warum es besser ist:** Der Agent prueft sich selbst. Luecken werden SOFORT sichtbar, nicht erst im Audit.

---

## 4. Parallele Agents: Chaos vs. Isolation

### ❌ SCHLECHT

```
Agent A: Aendert main.py (fuegt Router hinzu)
Agent B: Aendert main.py (fuegt andere Router hinzu)
Agent C: Aendert main.py (fuegt noch mehr Router hinzu)

→ Merge: 15 Konflikte, keiner weiss was der andere gemacht hat
→ Haelfte des Codes geht verloren
```

### ✅ BESSER

```
Agent A: Eigener Git Worktree (Branch sub-a/plugin-core)
Agent B: Eigener Git Worktree (Branch sub-b/control-plane)

→ Beide arbeiten isoliert
→ Merge danach: 5 Konflikte (beide Seiten behalten)
→ Nichts geht verloren
→ Konflikte sind "additive" (beide fuegen Code hinzu)
```

Unser Ergebnis: 10 Worktree-Agents, 5 Merge-Konflikte, alle geloest in 5 Minuten.

**Tipp:** Wenn zwei Agents die GLEICHE Datei erweitern (z.B. main.py fuer Router-Registration), entweder:
- Sequenziell statt parallel arbeiten lassen
- ODER: Klare Datei-Ownership definieren (Agent A besitzt main.py, Agent B schreibt nur seinen Router)

---

## 5. Qualitaets-Gate: Minimal vs. Vollstaendig

### ❌ SCHLECHT

```yaml
# CI Pipeline
on: push
jobs:
  test:
    run: pytest
```

"Tests laufen" ist KEIN Quality Gate. Was wenn:
- Ein TODO im Code steht? → Geht durch
- Eine interne IP hardcoded ist? → Geht durch
- Ein API Key im Code steht? → Geht durch
- Eine Datei keine Tests hat? → Geht durch

### ✅ BESSER

```yaml
# 5-Stufen Quality Gate
Stage 1: Lint (ruff + tsc)           → Code-Qualitaet
Stage 2: Tests (pytest + vitest)     → Funktionalitaet
Stage 3: Quality Gate                → Compliance
  - S9 Check: grep TODO/FIXME/placeholder
  - R12 Check: grep 10.40.10 (interne IPs)
  - Secret Check: grep sk-proj/ghp_/AKIA
Stage 4: Docker Build                → Integration
Stage 5: Summary                     → Ueberblick
```

**Warum es besser ist:** Jede Stufe faengt eine andere Kategorie von Fehlern. Tests allein reichen nicht — Code kann funktionieren und trotzdem unsicher oder unvollstaendig sein.

---

## 6. UI Fehler-Handling: Crash vs. Graceful

### ❌ SCHLECHT

```tsx
// API Call ohne Error Handling
const data = await fetch('/api/fleet').then(r => r.json());
return <Table data={data.agents} />;

// Was der User sieht wenn die API nicht laeuft:
// → Weisser Bildschirm
// → "Cannot read properties of undefined (reading 'agents')"
// → User denkt: "Kaputt"
```

### ✅ BESSER

```tsx
// Jedes Panel hat 4 Zustaende
<ErrorBoundary fallback={<PanelError onRetry={reload} />}>
  {isLoading && <Skeleton variant="table-row" count={3} />}
  {error && <ErrorMessage message={t('error.api_unreachable')} onRetry={retry} />}
  {data?.agents.length === 0 && (
    <EmptyState
      title={t('team.empty.title')}
      description={t('team.empty.description')}
      action={{ label: t('team.hire_cta'), href: '/admin/hire' }}
    />
  )}
  {data && <AgentTable agents={data.agents} />}
</ErrorBoundary>

// Was der User sieht:
// Loading: Animierte Skeleton-Balken (nicht leere Seite)
// Error: "Verbindung zum Server unterbrochen. [Erneut versuchen]"
// Empty: "Noch keine Mitarbeiter. [Jetzt einstellen]"
// Data: Normale Tabelle
```

**Warum es besser ist:** Der User sieht NIE einen Crash, NIE eine leere Seite, NIE eine technische Fehlermeldung. Jeder Zustand ist gestaltet.

---

## 7. Skills + Sub-Agents: Monolith vs. Spezialisierung

### ❌ SCHLECHT

```
Ein riesiger Agent-Prompt (3.000 Woerter) der:
- Backend bauen soll
- Frontend bauen soll
- Tests schreiben soll
- Deployen soll
- Dokumentieren soll

→ Agent ist ueberfordert
→ Macht alles "ein bisschen"
→ Nichts ist wirklich gut
```

### ✅ BESSER

```
Spezialisierte Agents mit eigenen Rules:

console-dev:    UI, Next.js, WCAG, Brand Bible, frontend-design Skill
plugin-dev:     TypeScript, OpenClaw Hooks, API Client
auth-dev:       Python, JWT, 2FA, bcrypt, Rate Limiting
control-dev:    Heartbeat, Tasks, Approvals, Budget
compliance-dev: PII Filter, Gate v2, Incidents, Kill Switch

Jeder Agent:
- Kennt NUR seinen Bereich
- Hat eigene Tool-Einschraenkungen
- Hat eigene Referenz-Dokumente
- Macht eine Sache RICHTIG
```

**Warum es besser ist:** Ein Experte pro Bereich statt ein Generalist fuer alles. Gleich wie in echten Teams.

---

## 8. Dokumentation: Am Ende vs. Laufend

### ❌ SCHLECHT

```
Tag 1-29: Code schreiben
Tag 30: "Jetzt muessen wir noch dokumentieren..."
→ Keiner erinnert sich warum Entscheidung X getroffen wurde
→ Dokumentation ist unvollstaendig oder falsch
→ Naechste Session: "Wo waren wir?"
```

### ✅ BESSER

```
NACH JEDER Aenderung (nicht am Ende):
1. Git: commit + push (was wurde gemacht)
2. ERPNext: Task updaten (Status, Ergebnis)
3. open-notebook: Note erstellen (Kontext, Entscheidungen, Learnings)

Ergebnis in EINER Session:
- ~50 Git Commits
- 12 open-notebook Notes
- 3 ERPNext Tasks
- 1 Audit Report
- 9 dokumentierte Learnings
```

**Warum es besser ist:** Dokumentation ist Teil des Prozesses, nicht Nacharbeit. Jede Entscheidung ist nachvollziehbar. Die naechste Session startet mit vollem Kontext.

---

## 9. Design: Standard vs. Einzigartig

### ❌ SCHLECHT

```bash
npx create-next-app --typescript --tailwind
npx shadcn-ui@latest init
# → Fertig, sieht aus wie jedes andere Dashboard
# → Inter Font, graue Sidebar, blaue Buttons
# → Der Kunde denkt: "Hab ich schon 100x gesehen"
```

### ✅ BESSER

```
1. Design-Philosophie definieren: "Trusted Control"
   → Serioes wie Online-Banking, warm wie ein Buero

2. Brand-Elemente einsetzen:
   → Montserrat Headlines (nicht Inter)
   → #4262FF NomOS-Blau + #31F1A8 Neon-Green Akzent
   → Eagle Logo mit Akzent-Linie
   → Pixel-Art Agent-Avatare (Differenzierung!)

3. Dual-Layer Dashboard:
   → Buero-Ansicht (visuell, KMU-Chef)
   → Analytics-Ansicht (Daten, IT-Leiter)

4. Mitarbeiter-Metapher UEBERALL:
   → "Mein Team" statt "Fleet"
   → "Einarbeitung" statt "Deploy"
   → "Kostenlimit" statt "Budget"

→ Ergebnis: Kein anderes Compliance-Tool sieht so aus
→ Der Kunde zeigt es seinem Partner: "Schau, mein AI Team"
```

**Warum es besser ist:** Ein Produkt das aussieht wie alle anderen wird auch so behandelt — austauschbar. Ein Produkt mit eigener Identitaet bleibt im Kopf.

---

## 10. PDCA vs. Wasserfall

### ❌ SCHLECHT (Wasserfall)

```
Plan schreiben (1.200 Zeilen) → Komplett ausfuehren → Am Ende pruefen

Ergebnis: 80% perfekt, 20% fehlt
→ 8 Endpoints vergessen
→ 108 Warnings uebersehen
→ TypeScript Errors nach Merge
→ Am Ende alles fixen = teuer
```

Das ist uns in Phase 1-3 passiert.

### ✅ BESSER (PDCA Zyklus)

```
Planung → Ausfuehrung → Pruefung → Korrektur → Rescope → Weiter
    ↑                                                        |
    └────────────────────────────────────────────────────────┘

Nach JEDER Phase:
1. IST/SOLL Vergleich (was fehlt?)
2. Tests ausfuehren (was bricht?)
3. Luecken schliessen (Gap-Fix Sprint)
4. Plan anpassen (was aendert sich fuer die naechsten Phasen?)

Ergebnis: Phase 4 Audit fand 8 Gaps → alle in 1h gefixt
→ Phase 5 startete mit sauberer Basis
→ Kein "am Ende alles fixen" noetig
```

**Warum es besser ist:** Fehler werden SOFORT gefunden, nicht am Ende. Der Plan passt sich der Realitaet an, nicht umgekehrt. Das ist Deming — aus der industriellen Automatisierung in die Software-Entwicklung uebertragen.

---

## Zusammenfassung: Die 10 Regeln

```
1. Praezise Prompts > vage Anweisungen
2. Spec + Plan > "einfach anfangen"
3. Agent kennt Gesamt-Plan > Agent kennt nur seinen Task
4. Git Worktrees > gleiche Branch
5. 5-Stufen Quality Gate > "Tests laufen"
6. 4 UI States > "Error 500"
7. Spezialisierte Agents > ein Generalist
8. Laufende Doku > Doku am Ende
9. Eigene Design-Identitaet > Standard-Template
10. PDCA Zyklus > Wasserfall
```
