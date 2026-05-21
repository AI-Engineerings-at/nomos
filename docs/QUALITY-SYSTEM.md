# NomOS Quality System — wie wir keinen Müll produzieren

> **Zweck:** Operating-Model Prinzip 6 *nennt* die Quality-Gates.
> Dieses Dokument *operationalisiert* sie: was genau geprüft wird,
> wo, womit, und ab wann etwas "fertig" heißen darf. Eine Liste von
> Gate-Namen verhindert keinen Müll — ein mechanisch erzwungenes
> System schon.
>
> **Stand:** 2026-05-21. Geerdet im echten CI-Stand
> (`.github/workflows/ci.yml`), nicht aus dem Gedächtnis.
> Tier T0 (Governance). Verweist auf `.claude/rules/04-06`.

---

## 1. Was "kein Müll" mechanisch heißt — Definition of Done

Eine Änderung ist **fertig**, wenn *alle* folgenden Punkte grün sind.
Nicht "die meisten". Nicht "sieht gut aus". Alle.

| # | Gate | Prüfung |
|---|---|---|
| 1 | Lint Python | `ruff check` + `ruff format --check` sauber |
| 2 | Lint TypeScript | `tsc --noEmit` sauber (plugin + console) |
| 3 | Tests grün | alle 4 Suiten — CLI, API, Plugin, Console |
| 4 | Coverage-Gate | Coverage ≥ Schwelle (siehe §6 Q-G1 — Gate noch zu setzen) |
| 5 | Contract-Check | `schemas.py` ↔ `types.ts` driftfrei |
| 6 | Router-AuthZ | jede state-ändernde Route hat einen AuthZ-Guard (L043) |
| 7 | S9 | kein TODO/FIXME/HACK/placeholder/`pass #` im Produkt-Code |
| 8 | R12 | keine internen IPs (`10.40.10.*`) im Produkt-Code |
| 9 | Secret-Scan | keine Credentials im Code |
| 10 | Trivy | 0 CRITICAL im Image |
| 11 | Integration | bei Features: `docker compose up` + Browser-Test (Rule 06) |
| 12 | PDCA | die echte Audit-Frage beantwortet (Rule 04), nicht Zeilen gezählt |

**Gate 1-10** sind in CI mechanisch erzwungen. **Gate 11-12** sind
*menschlich* — sie können nicht automatisiert werden und sind genau
deshalb die, die unter Zeitdruck fallen. Sie sind trotzdem Pflicht.

---

## 2. Test-Architektur — die 4 Suiten

| Suite | Ort | Runner | Umfang (v0.4.0) | Besonderheit |
|---|---|---|---|---|
| **CLI** | `nomos-cli/tests/` | pytest | 245 | Core-Library (hash_chain, merkle, forge) |
| **API** | `nomos-api/tests/` | pytest-asyncio | 440 | gegen **echtes** Postgres+pgvector + Valkey, Alembic-Migration *vor* den Tests |
| **Plugin** | `nomos-plugin/` | vitest | 46 | OpenClaw-Gateway-Plugin, 11 Hooks |
| **Console** | `nomos-console/` | vitest | — | Next.js, conditional Job |

**Warum API gegen echte Services:** SQLite-`create_all` fängt
Model↔Migration-Drift NICHT. CI fährt `alembic upgrade head` gegen
echtes Postgres *bevor* ein Test läuft → Drift schlägt sofort fehl.

**Test-Daten-Isolation:** `tmp_path` + `copy.deepcopy` für Shared
Fixtures — nie Module-Level-Konstanten mutieren (Cross-Test-Leak).

---

## 3. Die CI-Pipeline — 6 Stages

`.github/workflows/ci.yml` — läuft auf jedem Push + PR gegen `main`:

```
Stage 1  Lint        ruff check/format · tsc --noEmit (plugin+console)
Stage 2  Tests       test-cli · test-api · test-plugin · test-console
                     + contract-check · router-coverage (L043)
Stage 3  Security    pip-audit · npm audit · SBOM (CycloneDX)
Stage 4  Quality-Gate  S9 · R12 · Secret-Scan         ← BLOCKT Merge
Stage 5  Docker      docker compose build · Trivy fs + image
                     (CRITICAL blockt)
Stage 6  Summary     Status-Tabelle in den Step-Summary
```

Separat: `codeql.yml` (statische Analyse), `release.yml`,
`dependabot.yml` (Dependency-Bumps).

**Was blockt einen Merge:** Lint-Fehler, ein roter Test, Contract-
Drift, ungeschützte Route, S9/R12/Secret-Verstoß, ein CRITICAL-CVE
im Image.

---

## 4. Eval-Framework — was über Tests hinaus evaluiert wird

"Test" = tut der Code was er soll. "Eval" = verhält sich das *System*
korrekt und erreicht es eine *messbare Schwelle*.

| Eval | Was | Status |
|---|---|---|
| **Coverage** | % abgedeckter Code je Suite | gemessen, **nicht gegated** (Q-G1) |
| **Contract-Eval** | `schemas.py` ↔ `types.ts` Drift | ✅ CI, blockend |
| **Router-AuthZ-Eval** | jede state-ändernde Route geschützt | ✅ CI, blockend (L043) |
| **Audit-Tamper-Eval** | Hash-Chain erkennt Manipulation | ✅ pytest-Suite |
| **Phase-I Live-Eval** | `docker compose up` → bootstrap → hire → anchor → STH → inclusion-proof → tamper-test | ⚠ **manuell, nicht automatisiert** (Q-G2) |
| **Security-Eval** | pip-audit · npm audit · Trivy · CodeQL | teilw. (audits non-blocking, Q-G4) |
| **Zeroth M08-Eval** | TT-SI F1 ≥ 0.90 (aktuell 0.8565) | extern (Zeroth-Repo), nicht NomOS-CI |

Die **Phase-I Live-Eval** ist die wichtigste — sie beantwortet die
einzige Frage die zählt (Rule 06: *kann ein Kunde docker compose up
machen, einloggen, Agent einstellen, chatten?*). Dass sie nicht
automatisiert ist, ist die größte Lücke.

---

## 5. Test-Qualitäts-Standard

Ein grüner Test der nichts prüft ist Müll mit grünem Häkchen. Verbindlich
(durchgesetzt vom `nomos-qa`-Agenten beim Review):

1. **Spezifische Assertion** — `assert result.status == BLOCKED`,
   niemals `assert result` oder `assert True`.
2. **Edge-Cases zuerst** — leerer Input, Unicode/Umlaute (AT-Firmen!),
   Boundaries, Timeout, Race-Conditions — nicht nur Happy-Path.
3. **Spezifischer Name** — `test_forge_rejects_unparseable_name`,
   nicht `test_forge`.
4. **Exceptions spezifisch** — `pytest.raises(ValueError, match="...")`.
5. **Jeder Error-Pfad hat einen Test** (R10) — kein
   `if not agent_id: raise` ohne `test_empty_id_fails`.
6. **Keine Mocks in Integration-Tests** (S9) — gegen echte Komponenten.
7. **Regression-Test bei jedem Bug** — ein Bug ohne Regression-Test
   gilt als nicht gefixt.

---

## 6. Die Lücken — was fehlt, als konkrete Tasks

Ehrlicher Stand: das CI-Gerüst ist gut, aber 4 Müll-Vektoren sind offen.

| ID | Lücke | Risiko | Fix | Phase |
|---|---|---|---|---|
| **Q-G1** | **Kein Coverage-Gate.** Coverage wird gemessen, aber kein `--cov-fail-under` / vitest `coverage.thresholds`. Coverage kann lautlos verrotten. | Hoch | Baseline messen → `fail-under = Baseline − 2%` setzen → quartalsweise +5% Ratchet. Alle 4 Suiten. | v0.5.0 |
| **Q-G2** | **Live-Eval nicht automatisiert.** `scripts/e2e-test.sh` existiert, ist aber nicht in CI. Die Kern-Frage (Rule 06) wird nie mechanisch verifiziert. | Hoch | `e2e-test.sh` als separater (scheduled/nightly) CI-Job — docker compose ist zu schwer für jeden PR. | v0.5.0 |
| **Q-G3** | **Test-Qualität nicht erzwungen.** Der §5-Standard lebt nur im Agent-Brief. Nichts flaggt `assert True` / bare `assert <var>`. | Mittel | Lint-Check gegen schwache Assertions. Optional: Mutation-Testing (mutmut/Stryker) als periodischer Job. | v0.5.1 |
| **Q-G4** | **Security-Audits non-blocking.** `pip-audit`/`npm audit` enden mit `\|\| echo ::warning` — ein bekanntes CVE bricht CI nicht. | Mittel | aktuelle Findings triagen → dann `exit-code 1`. | v0.5.0 |
| **Q-G5** | `pyproject.toml` `license = "Fair Source"` in beiden Paketen — N1 entschied **AGPL-3.0**. | Niedrig | beim N1-Rollout (LICENSE-Datei) mitziehen. | N1-Impl |
| **Q-G6** | `nomos-qa`-Agent-Brief Test-Counts stale (sagt 84/14, IST 245/440) + verweist auf archivierte Pläne. | Niedrig | Agent-Refresh. | R3 |

**Q-G1, Q-G2, Q-G4 gehen in die v0.5.0 W-Phase** — sie werden damit
von "vage Absicht" zu spezifizierten Tasks.

---

## 7. Definition of Done pro Phase

Keine Phase gilt als abgeschlossen ohne:

1. **Alle 12 Gates aus §1 grün** (1-10 mechanisch, 11-12 menschlich).
2. **PDCA-Durchlauf** (Rule 04) — IST/SOLL gegen den Plan, die echte
   Audit-Frage gestellt.
3. **Learnings gezogen** — neue `Lxxx`-Einträge wo etwas schiefging
   (Operating-Model Prinzip 4).
4. **INDEX + Doku aktuell** — jeder neue/geänderte Doc indexiert.

Ein "fertig" das einen dieser vier Punkte überspringt, ist kein
"fertig" — es ist aufgeschobener Müll.

---

## Verweise

- `docs/OPERATING-MODEL.md` Prinzip 6 — der Rahmen
- `.claude/rules/04-pdca-zyklus.md` · `05-refactor-quality-gate.md` · `06-integration-test-pflicht.md`
- `.claude/agents/nomos-qa.md` — der QA-Agent der §5 durchsetzt
- `.github/workflows/ci.yml` — die ausführbare Form von §3
