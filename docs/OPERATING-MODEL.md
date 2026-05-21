# NomOS Operating Model — Wie wir arbeiten

> **Zweck:** Dieses Dokument ist die Antwort auf "wie arbeiten wir?".
> Es definiert das feste Betriebsmodell für jede Arbeit an NomOS —
> damit Arbeit systematisch statt ad-hoc läuft, das System nicht "zu
> groß für den Kopf" wird (Joe-Constraint #1), und Qualität
> mechanisch erzwungen ist statt verhandelt.
>
> **Stand:** 2026-05-21. Kanonisch. Gilt für Joe, Claude und jeden
> Sub-Agenten. Bei Konflikt mit einem Einzel-Rule (`/.claude/rules/`)
> gewinnt das spezifischere Rule — dieses Dokument ist der Rahmen.

---

## Die 7 Prinzipien

### 1. Arbeitseinheit ist die Phase, nicht der PR

**Regel:** Eine Phase = ein Branch, mehrere Commits, eine PR.
Zusammengehörige Arbeit wird gebündelt, nicht in Mini-PRs zersplittert.

**Warum:** Jede PR ist ein Context-Load. 5 Mini-PRs = 5× Aufwand für
Joe und für den Kontext (Constraint #1 Übersicht, #3 Token).

**Konkret:**
- Phase benennen (`R1`, `v0.5.0`, `Agent-Refresh`) → Branch
  `<typ>/<phase-slug>`.
- Innerhalb der Phase: kleine, einzeln verifizierte Commits.
- Phase endet mit *einer* PR, *einem* Merge.
- Nie auf `main` committen ohne Branch (sonst: fehlgeschlagener Push).

### 2. Informations-Hierarchie — nie eine Stufe überspringen

**Regel:** Information wird in fester Reihenfolge gesucht. Eine höhere
Stufe wird erst genutzt wenn die niedrigeren nichts liefern.

| Stufe | Quelle | Wofür |
|---|---|---|
| 1 | Repo: `Read` / `Grep` / `Glob` | Was steht schon im Code/Doc |
| 2 | `docs/INDEX.md` → Decision-Log, LEARNINGS, Strategy | Was wurde entschieden/gelernt |
| 3 | open-notebook KB (`notebook:v7s87re90iyxxlv7dd5x`) | Akkumuliertes Projekt-Wissen |
| 4 | legal-scraper FTS5-Index | EU/AT/DE/CH-Recht (Compliance-Produkt!) |
| 5 | Context7 MCP | Library-/Framework-Doku |
| 6 | WebSearch | Aktuelle externe Fakten (Konkurrenz, Regulierung) |

**Warum:** WebSearch für etwas das in Stufe 1-2 steht ist
Token-Verschwendung. Raten statt Stufe 3-5 zu fragen verletzt
HARD-RULE 1 ("Weißt du es sicher? Nein → lies die Doku").

**Konkret:** Vor jeder Faktenaussage die Stufe nennen können.
Zahlen/Versionen/Modellnamen brauchen eine Quelle aus Stufe 1-5,
nie aus dem Gedächtnis.

### 3. Doku-Architektur — 4 Tiers mit INDEX als Einstieg

**Regel:** `docs/INDEX.md` ist die Landkarte. Jedes Dokument hat genau
einen Tier-Platz. Jeder neue Doc bekommt **im selben Commit** einen
INDEX-Eintrag.

| Tier | Inhalt |
|---|---|
| T0 | Meta/Governance — dieses Doc, CLAUDE.md, rules/, agents/ |
| T1 | Strategie — Vision, Master-Plan, Decision-Log, Competitive |
| T2 | Architektur — Specs, Contracts, API/CLI-Referenz |
| T3 | Betrieb — Quickstart, Runbooks, Deployment, Release |
| T4 | Wissen — LEARNINGS, Audits, Postmortems, Reviews |

**Warum:** 8 Strategy-Docs ohne Index = niemand findet ohne Vorwissen
rein. Das ist Constraint #1 in Reinform.

**Konkret:** Datei-Layout bleibt physisch wie es ist — der INDEX
klassifiziert *logisch*. Kein Massen-`git mv` (bricht
Cross-Referenzen). Stale-Detection: INDEX führt eine "Drift-Watch"-
Sektion; Doc älter als die referenzierte Version → dort gelistet.

### 4. Learnings als geschlossener Kreis

**Regel:** Jede Phase endet mit der Frage "was haben wir gelernt?".
Neue Erkenntnis → nummerierter `Lxxx`-Eintrag in
`.claude/knowledge/LEARNINGS.md`. Kritische Learnings werden nach
`phantom-ai/.claude/knowledge/` gespiegelt (kanonisch).

**Warum:** Ein Fehler der nicht zum Learning wird, wiederholt sich.
Die 4.7-Friction-Vektoren (Wrong-Approach, Buggy-Code) sinken nur
wenn Learnings gepflegt + gelesen werden.

**Konkret:** LEARNINGS-Eintrag = Muster + Auslöser + Gegenmaßnahme.
Kein "war doof", sondern eine prüfbare Regel fürs nächste Mal.

### 5. Agenten + Skills sind die Automation dieses Modells

**Regel:** Wo sich ein Workflow ≥3× wiederholt, wird er ein Skill.
Die `nomos-*`-Agenten tragen aktuellen Kontext (Decision-Log,
dieses Modell, v-Stand).

**Warum:** Ein Modell das nur im Doc steht wird vergessen. In einem
Hook/Skill ist es selbst-erzwingend.

**Konkret:** `meta-skills:session-analyst` läuft periodisch und
findet Wiederhol-Muster → Skill-Kandidaten. Agenten-Briefs werden
bei jedem Major-Release gegen den IST-Stand geprüft.

### 6. Quality-Gates — mechanisch, "keine Kompromisse"

**Regel:** Nicht verhandelbar, jede Phase:

- **3+ Reads vor dem ersten Write** (Exploration-First).
- **Lint vor JEDEM Commit** — `ruff check` / `npm run lint`.
- **Test-Run nach JEDEM Fix** — nicht batchen (Rule 05).
- **Integration-Test vor "fertig"** — `docker compose up` + Browser,
  nicht nur `pytest`/`tsc` (Rule 06).
- **PDCA nach jeder Phase** — die echte Audit-Frage stellen, nicht
  Zeilen zählen (Rule 04).

**Warum:** 3 Audits fanden weniger Bugs als 1 Browser-Test
(Rule 06). Verhandelbare Gates werden weggelassen sobald es eilt.

### 7. Rollen sind fix

| Rolle | Verantwortung |
|---|---|
| **Joe** | Entscheidungen (Decision-Log), Customer, Geld, externe Cred-Tasks |
| **Claude** | Ausführung, Tests, Doku, Releases, Orchestrierung |
| **Sub-Agenten** | Parallelisierung — Audits, Multi-File-Scans, Recherche |

**Warum:** Joe macht in dieser Phase keinen Code (Burnout-Risiko R6).
Klare Rollen verhindern Doppelarbeit und Approach-Drift.

---

## Die Arbeits-Kadenz (pro Arbeitseinheit)

Joe's Schritt 1-5 aus der globalen CLAUDE.md, gehärtet:

```
1. VERSTEHEN     Aufgabe in einem Satz. Bei Unklarheit: Joe fragen.
2. SCOPE         Erlaubte Dateien + "fertig" in 1-3 Kriterien + was NICHT.
3. EXPLORE       3+ Reads. Informations-Hierarchie (Prinzip 2).
4. IMPLEMENT     Eine Aktion pro Schritt, danach verifizieren.
5. VERIFY        Quality-Gates (Prinzip 6). Bei Fehler: STOP, Joe melden.
6. DOCUMENT      INDEX-Eintrag, LEARNINGS, Commit-Message.
7. CLOSE         PDCA. "Fertig: [was]. Was als nächstes?"
```

**Wenn blockiert:** STOP. Blocker in 1-2 Sätzen. Joe melden. Kein
eigenständiger Approach-Wechsel (74 Wrong-Approach-Incidents/65
Sessions — höchster Friction-Vektor).

**Wenn Joe korrigiert:** sofort stoppen, Korrektur in einem Satz
zurückspiegeln, neuen Plan ableiten, Joe vorlegen, erst dann weiter.

---

## Verweise (nicht duplizieren)

- `.claude/CLAUDE.md` — HARD RULES + Tech-Stack + Commit-Convention
- `.claude/rules/01-06` — die 6 spezifischen Rules
- `docs/INDEX.md` — die Doku-Landkarte (Prinzip 3)
- `docs/strategy/2026-05-21-decision-log.md` — was entschieden ist
- `.claude/knowledge/LEARNINGS.md` — was gelernt wurde
