# Das große Ganze — wo NomOS hingehört

> **Stand:** 2026-05-20 nach v0.4.0 Release.
> **Adressaten:** Joe (Owner), zukünftiges Selbst, jeder Senior-Developer
> der nach dieser Session in den Stack einsteigt.
> **Quellen:** Action_Plan_v2.0_post-TASK-00685.md, zeroth/concepts/*,
> phantom-control/docs/ROADMAP.md + ARCHITECTURE.md, STATUS.md,
> 5-Agent-Audit-Reports vom heutigen Tag.

---

## 1. Worum es wirklich geht

Joe baut nicht "ein Compliance-Tool" und nicht "noch eine AI-Plattform".
Er baut **Legal-Aligned AI Infrastructure für DACH-KMU**, mit drei
Säulen und einer Operating-Klammer:

| Säule | Funktion | Komponente |
|---|---|---|
| **Rule-Compliance** | Asimov-Cascade, Safety, Veto-Layer | **Zeroth Core** (M01-M07) |
| **Legal Reasoning** | Juristische Compliance-Checks, EU AI Act | **NomOS** (das Produkt dieser Sessions) |
| **Law-as-Blueprint** | Audit-Chain, ADR, Hash-Anker | `ai-agent-legal-framework` + Lineage Engine (deferred) |
| **Operating-Klammer** | Operator-Cockpit, Agent-Fleet, Skills | `phantom-control` (Atlas) + `meta-skills` |

Drei strategische Anker bilden die Vision:

- **Bell Labs als North Star** — Institution > Person.
  Founder-Pseudonymität ist Strategie, nicht Defizit. Marketing
  läuft über Entitäten (`ai-engineering.at`, `zugangsweg.at`),
  nicht über Joe-Person. Keine Selfies, keine Personal-Brand,
  keine Linktrees auf den CTO.
- **Asimov-Zeroth wörtlich** — Asimov-Gesetz 3 ("Schutz der eigenen
  Existenz und der Constitutional Safety") wird operationalisiert.
  NomOS = Asimov-Gesetz 3, validiert vor jeder Agent-Aktion.
- **Inverse-Pyramide-Distribution** — Vulnerabelste zuerst:
  Legastheniker, Senioren, KMU ohne Compliance-Budget, AI-Instanzen
  die zwischen Sessions sterben. Tesco-These: was am unteren Ende
  funktioniert, skaliert nach oben.

Konkurrenz baut Agenten (RAPTOR, Devin, Cognition). **Joe baut die
Harness, Governance, Audit-Infra plus Operating-Console drumherum.**

---

## 2. Die 60/20/5/15-Allokation (DEC-005)

Seit 2026-05-12 gilt das 4-Lane-Modell:

| % | Lane | Inhalt | Wo NomOS sitzt |
|---|---|---|---|
| **60** | Zeroth-Engineering | TT-SI gemma4:9b, Production-Hooks M01/M06, Spec v1.1, M08-TT-SI grün | Nicht hier |
| **20** | **Compliance-Brücke** | Compliance-Pilot Tag 0-5, Annex-IV + RAPTOR-Scan + PDF, RAPTOR-Scan Kern-Services | **NomOS sitzt HIER** |
| **5** | Geschäftlich | AWS Pre-Seed, EU EIC/Horizon | Outputs aus NomOS sind Pitch-Material |
| **15** | Tooling/Operating-Layer (NEU) | phantom-control Phase 3.5.x → 4 (~10%), meta-skills v4.x (~3%), atlas-ceo Sunset (~2%) | Atlas sitzt hier |

**Schlüsselaussage:** NomOS ist NICHT im Tooling-Slot. NomOS ist die
**Legal-Reasoning-Säule** und liefert die Plattform für den
Compliance-Pilot-Annex-IV-Output. Es ist eines der zwei produktbaren
Assets der Firma (das andere ist Atlas, intern).

7 explizite Ausschlüsse (DEC-001..004 + v2.0-Ergänzungen):

1. RAPTOR-Architektur-Redesign (Domain-Mismatch)
2. Memetik/Memplex in Spec/Pitch/Produkt (DEC-004)
3. Lineage Engine Phase 1 jetzt bauen — **NomOS hat die Hash-Chain übernommen** (Ed25519 + RFC 6962 Merkle seit v0.2.0)
4. Longhorn V2 SPDK Migration
5. Transformer-Squared / SEAL / TTT-E2E / MeG
6. Modellwechsel weg von gemma4
7. Neue Brainstorming-Sessions

Plus: atlas-ceo nicht weiterentwickeln (Read-Only-Archiv);
phantom-control nicht über 15%-Soft-Target ohne v2.1-Plan.

---

## 3. Wie NomOS im Zeroth-Stack hängt

Per `nomos/CLAUDE.md`: **Compliance Engine = Asimov Gesetz 3.**

```
Zeroth Core (Veto-Layer)
       │
       ├──> Contract 2 ──> NomOS  (synchron, vor jeder Aktion)
       │                     │
       │                     └─> EU AI Act Validation
       │                     └─> Risk Classification (Art. 6)
       │                     └─> Audit-Trail (Art. 12, Ed25519+Merkle)
       │
       └──> phantom-ai Runtime (31 Services)
                     │
                     └─> NomOS-B-V2 Agent Fleet
                                │
                                └─> jeder Agent meldet sich bei
                                    NomOS via heartbeat + audit
```

**Contract 2 (Zeroth Core → Compliance)** in `zeroth/.claude/rules/contracts.md`:
- Synchroner Call vor Action-Execution
- NomOS antwortet mit Verdict + Rule-IDs + Confidence
- F1=0.8565 auf 374 Test-Cases (Ziel: ≥0.90 nach Tuning)
- Production Readiness 10/10 seit 2026-04-06
- OpenClaw v2026.5.18 gepinnt

NomOS deckt **Annex IV Punkte §2(d), §2(e), §2(f), §3** bereits ab
(Eval-Suite, Asimov-Cascade+Killswitch, Audit-Chain, Override).
Compliance-Pilot Tag 0-5 ergänzt §1(c), §2(b), §2(c) über alle 30
Komponenten.

---

## 4. NomOS heute (Stand v0.4.0)

Vier Releases an einem Tag (2026-05-20):

| Tag | Inhalt | PRs |
|---|---|---|
| `v0.2.0` | Audit-Trail v2 (Ed25519 + HMAC + RFC 6962 Merkle + STH + Inclusion-Proofs, Phase A1-A6 + B1) | #5-#8 |
| `v0.2.1` | Security-Hotfix: 7 Router-AuthZ-Lücken (dsgvo/tasks/approvals/workspace/incidents/compliance/budget+costs) + verify_chain sequence-check + Merkle iterativ + DoS-Schutz + non-hex Safety | #31 |
| `v0.3.0` | Maintenance: M1 Anker/Checkpoint sibling-files + M2b/d Perf (lru_cache + SQL UPDATE) + M3a-d Hardening (chmod 600, /docs auth, security_opt+cap_drop, bcrypt floor, CORS prod-block) + M4 Error-Handling + M5 Test-Coverage | #32 |
| _no-tag_ | Meta-Sweep: LEARNINGS L042-L048, Archiv-Reorg, nomos-master.md refresh | #33 |
| `v0.4.0` | Finish-the-deferred: O1 worker dispose + O2 router-coverage CI gate + P1 matrix N+1 + P2 metrics batch + 5 audit-A hardening + 5/15 audit-D + 3 audit-B test gaps | #34 |

**Tests:** 245 cli + 454 api (440 in audit-sweep) + 46 plugin = **745**.
**LEARNINGS:** L001-L053 (53 dokumentierte Erkenntnisse).
**Audit-Trail:** EU AI Act Art. 12 ready, regulator-facing STH +
inclusion-proof endpoints, Ed25519 non-repudiation.

---

## 5. Was Atlas IS und wie es reinpasst

**A.T.L.A.S. CEO** (Adaptive Task Leadership & Agent Synchronization)
ist Joe's internes **Operator-Cockpit** — Electron-Desktop-App, **nicht**
ein Customer-facing Produkt.

**Tech-Stack:**
- Electron + React/Vite + Zustand + React Query
- Express + Socket.IO Control-Plane (port 4701)
- SQLite + sqlite-vec für lokale Vektor-Suche
- Transformers.js für 384d-Embeddings (lokal, 2ms)
- pino + pino-http mit Redaction
- Argon2id Auth + AES-256-GCM Vault
- Mattermost + WhatsApp + GitHub Connectors

**Was Atlas tut:**
- Agent-Lifecycle (start/stop/log)
- LLM-Router (OpenAI-kompatibler `/v1/chat/completions` Proxy)
- Infra-Monitor (pollt 7 phantom-ai Services)
- 3-Memory-Engine (episodic/semantic/procedural mit Vector-Search)
- Skill/Hook/Approval-Gate System
- Multi-Operator RBAC
- Audit-Trail (pino-redacted)
- CEO/Worker-Channel-Modell (Joe-as-CEO ↔ Agent-Fleet)

**Aktueller Stand:**
- Phase 3.5.x in Arbeit (App.tsx 4485 → 92 LOC am 2026-05-12 erledigt, **-81% Bundle**)
- Phase 3.6 = OpenFang UI-Pivot (blockiert auf Joe's Screenshot-Upload)
- Phase 4 = Agent Intelligence (State-Machine, Sentinel-Gate, MVP-Gate)
- **Bekanntes CRITICAL: RCE in `worker-agent/server.ts:68`** — Action Plan v2.0 listet das als must-fix
- Hard-coded `10.40.10.x` IPs → **internal-only-by-design**, verstößt
  gegen NomOS-Rule 01-produkt-standalone.md → Atlas wird nicht
  shippable. Bewusst.

**Wie Atlas mit NomOS verbunden ist:**
- **Heute: GAR NICHT.** Kein Code-Pfad, kein API-Contract, kein
  gemeinsames docker-compose. Verschiedene Use-Cases (Atlas = Joe's
  internes HQ, NomOS = Kunden-Produkt).
- **Konzeptionell:** Atlas's MemoryEngine, audit_log, automation_jobs,
  cost-tracking sind **exakt die Artefakte**, die NomOS für
  Annex-IV-Evidence brauchen würde.
- **Zukunft (v0.5.0+):** Atlas-managed Agents könnten vor jeder
  Action NomOS via Contract 2 anfragen. Atlas wird zum Tier-A
  Compliance-Konsumenten, NomOS zur Compliance-Source.

**Atlas-ceo (Sunset) vs phantom-control (active):**
- `Playbook01/atlas-ceo/` ist seit 2026-05-02 **ARCHIVED**. 2
  Showstopper (vault master-key dead code, worker heartbeat infinite
  restart) + 5 Codex-verified Bugs incl. die RCE. Codex-Schätzung
  16-24h to harden — bewusst nicht verfolgt.
- `phantom-control/` ist der v2.0.1-Fork von 2026-04-01, jetzt
  canonical. Trägt die gleiche legacy RCE.
- TASK-2026-00685 mit Option C ("voller Rework via phantom-control")
  hat am 2026-05-11 den v1.0 → v2.0 Trigger gezogen.

---

## 6. Was NomOS NICHT abdeckt (ehrlich)

Aus dem heutigen 5-Agent-Audit + Strategy-Synthese, ehrliche Bestandsaufnahme:

### Kritisch — vor Customer-Launch
1. **Phase-I Live-Eval nie auf cleanem Docker-Stack ausgeführt.**
   `docs/hardening-2026-05-20/EVAL-2026-05-20.md` ist Procedure, kein Lauf.
2. **CI-Status der heute gemergten PRs ungeprüft** (CodeQL, Trivy,
   Security-Audit, Router-Coverage Workflows zum ersten Mal aktiv auf main).
3. **STH/Proof Endpoints ohne Rate-Limit** — Audit A-#12 hatte zwei
   Forderungen, iterativ ist erledigt, Rate-Limit fehlt.
4. **B-F01/F02/F14 BLOCKER-Tests** für audit/entry endpoint nie geschrieben —
   v0.2.1 hat die AuthZ gefixt, aber kein Test garantiert dass es so bleibt.
5. **`nomos.core.api.py:18` defaultet auf `http://localhost:8060`** —
   Rule-01-Verstoss seit März.

### High — vor v1.0
6. `validate_settings()` `sys.exit(1)` at module load (bricht Alembic standalone)
7. `extra="forbid"` auf disk-persisted Manifests (Forward-Compat-Falle)
8. `vault-init` `changeme` Fallback
9. `openclaw-gateway` ohne digest-pin + ohne USER instruction
10. operations-runbook nicht für v0.4.0-Items ergänzt
11. DE-Doku nicht für v0.4.0 synchronisiert
12. LEARNINGS L042-L053 nicht in `phantom-ai/.claude/knowledge/` (kanonischer Ort)
13. STATUS.md Test-Count-Discrepancy

### Architektur-Schulden (zu v0.5.0+ deferred mit Plan)
- **O3** `chat_service.py` extraction
- **O4** Manifest Migration Framework
- **O5** Plugin Contract-Check (api-client.ts → schemas.json)
- C-F6 19 Router Prefix-Cohesion
- C-F14 Settings nested groups
- C-F17 `validate_settings` callable-statt-module-load

### Compliance-Frontier
- **Art. 28 DPA-Template** (compliance-guide sagt explizit "Not covered")
- **DPIA für NomOS selbst** (eine DSGVO-Maschine ohne eigene DPIA)
- **Art. 43 Konformitätsbewertung** für Hochrisiko-Systeme

### Performance-Behauptungen ungetestet
- "scales to 200+ agents" (matrix) — nie load-tested
- "1000 req/s → 1 batch/30s" (metrics) — nie verifiziert
- "100k chain entries faster with lru_cache" — nie benchmarkt

### Never Attempted
- `/full-sync` → ERPNext + open-notebook + Wiki-Eintrag
- Customer Migration Path v0.2.0 → v0.4.0
- Disaster Recovery Drill
- Vault TLS-Listener + N-of-M Shamir Default (audit A-#16)
- Phase-B2 Sigstore Rekor public anchoring
- Playwright e2e ohne Mocks (L023-Verstoß)

---

## 7. Wo geht der Weg hin (Roadmap-Skizze)

| Horizon | Inhalt | Wann |
|---|---|---|
| **v0.5.0** | Kritische W1-W4 Items, O3/O4/O5 Architektur-Refactors, Vault-TLS + N-of-M Shamir, OpenAPI-driven Plugin-Contract, Live-Eval Lauf | **vor 2026-06-15** |
| **v0.6.0** | Atlas↔NomOS Integration-Bridge: Atlas-Agents melden via Contract 2 an NomOS; NomOS-Audit-Trail nimmt Atlas-Events auf | **2026-06** |
| **v0.7.0** | Annex-IV-Auto-Generation als NomOS-Produkt-Feature (Compliance-Pilot-Pattern wird zum Hire-Wizard-Output) | **2026-07** |
| **v1.0** | Production-Customer-Launch-Tauglich. Penetration-tested, DPIA durchgeführt, DPA-Template, Customer-Migration-Docs, EU EIC/Horizon Pitch-Material | **2026-07 / Aug 2** |
| **2026-08-02** | **EU AI Act Art. 12 Vollanwendung Hochrisiko-Systeme.** NomOS muss live, geprüft, regulator-presentable sein. | Deadline |
| **2026 Q4** | Erste DACH-KMU-Pilotkunden (zahlende). 5-10 Kunden, €500-2.000/Monat ARR | Pull aus Deadline |
| **2027** | 50 Kunden, €30-100k MRR. Atlas zur Produkt-Sellable-Variante (CEO-Cockpit für andere Operator) | — |
| **2027+** | EU-EIC/Horizon Mittel landen. Atlas-NomOS-Bundle als EU-Sovereign-Stack-Option | — |

---

## 8. Geschäftlicher Pfad

- **AWS Activate Pre-Seed (TASK-00704)** — Anker-Pitch mit
  Compliance-Pilot-PDF als Beweis "real, nicht Vaporware". Liefert
  AWS-Credits für Non-Compute-Workloads.
- **EU EIC / Horizon Europe (TASK-00705)** — FFG ist vom Tisch. EIC
  + Horizon, €100k-2M je Pfad. Pitch baut auf Kolt 2026 (Legal
  Alignment) als Forschungs-Anker, Annex-IV-Pilot als
  Umsetzungs-Beweis.
- **AMS** in Arbeit als Cash-Bridge (Constraint-Hierarchie Stufe 4).
- **DACH-KMU-Pilotkunden ab Aug 2026** als organischer Pfad —
  direkter Markt-Pull durch EU-AI-Act-Deadline.

Priorität: AWS zuerst (schnellste Conversion), EU parallel (länger),
Direkt-Kunden nach Pilot-PDF fertig.

---

## 9. Was wir versuchen zu erreichen — in einem Satz

**Eine EU-souveräne, DACH-fokussierte, KMU-erschwingliche AI-Governance-Infrastructure**,
die vor dem 2. August 2026 produktionsreif für regulator-vorzeigbare
Hochrisiko-Systeme ist, mit NomOS als operational-backbone für die
EU-AI-Act-Compliance und Atlas als interne Operator-Konsole, die das
Bauen, Betreiben und Auditieren dieser Stacks für eine einzige
Person handhabbar macht.

Bell-Labs-förmig, Asimov-Zeroth-prinzipientreu, Inverse-Pyramide
ausgerichtet. Vulnerabelste zuerst empowern, dann skaliert alles
aufwärts.

---

## Verlinkte Dokumente

- `Documents/zeroth/decisions/Action_Plan_v2.0_post-TASK-00685.md` — die DEC-005-Quelle
- `Documents/zeroth/concepts/Compliance_Pilot_Annex_IV_v0.1.md` — der Tag-0-5-Plan
- `Documents/zeroth/concepts/legal-alignment.md` — Kolt-2026-Mapping
- `Documents/phantom-control/docs/ROADMAP.md` — Atlas Phase-3.5/3.6/4/5
- `Documents/phantom-control/docs/PHANTOM_CONTROL_ARCHITECTURE.md`
- `Documents/STATUS.md` — Joe's Cockpit
- `nomos/CHANGELOG.md` — die 4 Releases vom 2026-05-20
- `nomos/.claude/knowledge/LEARNINGS.md` — L001-L053
- `nomos/docs/strategy/2026-05-20-v0.5.0-roadmap.md` — was als nächstes (sibling-Datei)
- `nomos/docs/strategy/2026-05-20-nomos-atlas-integration.md` — wie Atlas+NomOS gekoppelt werden (sibling-Datei)
