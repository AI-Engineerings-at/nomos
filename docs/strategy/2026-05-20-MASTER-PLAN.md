# NomOS Master Plan 2026

> **Stand:** 2026-05-20, abends, nach 5 Releases an einem Tag
> (v0.2.0/v0.2.1/v0.3.0/v0.4.0 + Strategy-Docs).
>
> **Amendment 2026-05-21:** §2.1 (Differenzierung), §7 #19
> (Build-vs-Adopt Asqav), §8 R13 (OSS-Konkurrenz) ergänzt nach der
> Competitive-Landscape-Recherche. Kein Vision-Rewrite — die
> Roadmap (§4-6) bleibt unverändert. Substanz vor Story.
>
> **Geltungsbereich:** jetzt → November 2026. Hard Deadline:
> **2026-08-02 EU AI Act Art. 12 Vollanwendung**.
>
> **Lesen vor allem anderen.** Wenn du nur ein Doc lesen kannst,
> lies dies. Die anderen Strategy-Docs (§13) sind die
> Tiefen-Anhänge zu diesem Plan.

---

## 1. Vision in einem Satz

> **NomOS + Atlas = die EU-souveräne, KMU-erschwingliche
> AI-Governance-Plattform, mit der DACH-Mittelstand am 2. August
> 2026 EU-AI-Act-konform AI-Agents betreiben kann — Atlas als
> Joe's interne Operator-Konsole und live-Demo-Customer, NomOS
> als das verkaufte Compliance-Backbone.**

Konkret: bis zum **2026-08-02** muss ein DACH-KMU-Geschäftsführer
in der Lage sein, auf seinem eigenen Server `docker compose up -d`
zu fahren, einen AI-Agent zu hiren, automatisch ein
Annex-IV-konformes PDF zu bekommen, und im Audit-Fall einem
Regulator nur den Ed25519-Public-Key und drei API-URLs übergeben
zu müssen.

---

## 2. North-Star — 7 Prinzipien die alles durchziehen

1. **Asimov-Gesetz-3 wörtlich** — keine Agent-Action ohne
   Compliance-Verdict. Zeroth Core ruft NomOS vor jeder Action.
2. **Bell-Labs Institution > Person** — alle Brand-Auftritte
   über Entity-Accounts (ai-engineering.at, zugangsweg.at), keine
   Founder-Photos, keine Personal-Brand-Strategie. Pseudonymität
   first.
3. **Inverse-Pyramide-Distribution** — Vulnerabelste zuerst:
   Legastheniker (mama-ki), Senioren (mama-ki), KMU ohne
   Compliance-Budget (NomOS), AI-Instanzen die zwischen Sessions
   sterben (Atlas-Memory). Tesco-These.
4. **Zero-Friction-Onboarding** — Customer macht `docker compose up`
   und ist innerhalb von 15 Minuten produktiv mit einem
   compliance-validierten Agent. L026.
5. **EU-Souverän** — keine US-Cloud-Hard-Dependencies in der
   Runtime. Vault, Postgres, Valkey, Caddy, OpenClaw — alles
   self-hostable. LLM-Provider sind austauschbar.
6. **Audit-First** — jede Aktion ist regulator-presentable.
   HMAC + Ed25519 + RFC 6962 Merkle + WORM-anchors. Externer
   Verifier braucht nur den Public-Key.
7. **Self-eating dogfood** — Joe nutzt NomOS für seine eigene
   Agent-Fleet. Atlas wird der erste NomOS-Customer. Wenn unser
   Customer-Produkt nicht gut genug für uns ist, ist es nicht
   gut genug.

### 2.1 Differenzierung — warum nicht Microsoft, Asqav, FutureAGI

Seit April 2026 gibt es Open-Source-Konkurrenten direkt in unserem
Schnittpunkt: **Microsoft Agent Governance Toolkit** (MIT),
**Asqav** (MIT, tamper-evidenter Audit-Trail) und **FutureAGI**
(Apache 2.0) — Details in `2026-05-21-competitive-landscape.md`.
"Wir kombinieren alles" reicht damit als Differenzierung **nicht
mehr**. Sechs *strukturelle* — nicht feature-basierte —
Differenzierungen, in Reihenfolge der Verteidigungsstärke:

1. **DACH-KMU-spezifisch** — DE-Sprache, AT/DE-Recht, regionale
   Granularität. Die Konkurrenz ist US-generic.
2. **AGPL statt MIT/Apache** — Microsoft + Asqav sind MIT, jeder
   kann sie schließen und als Closed-SaaS verkaufen. AGPL
   verhindert das strukturell.
3. **WSK-Wertschöpfungs-Kopplung** — niemand sonst koppelt die
   Compliance-Engine an eine Wertschöpfungskette mit Regionalem
   Wirkungsflow + Goodhart-Schutz.
4. **Empowerment-Bewegung statt Geschäftsmodell** — Beitrag statt
   Pricing, Inverse-Pyramide.
5. **Quadrupel-Stack-Kohärenz** — Atlas + NomOS + Zeroth + WSK als
   ein System (viertes Element WSK:
   `2026-05-21-nomos-wsk-integration.md`). Die Konkurrenz liefert
   Punkt-Lösungen.
6. **Bell-Labs Institution > Person** (= North-Star-Prinzip 2).

**Kernsatz:** Unser nicht-kopierbarer Vorteil ist nicht der Code —
den können Microsoft + Asqav auch. Es ist die *gelebte regionale
Verankerung* (RUF-Pilot + WSK). Microsoft kann ein Toolkit
releasen; Microsoft kann nicht die Bäckerin in Eisenstadt kennen.

---

## 3. Architektur — wie alles zusammenarbeitet

### 3.1 Die drei Stacks und ihre Schnittstellen

```
                    JOE-INTERN                        CUSTOMER-EXTERN
                   ============                       ================

                    ATLAS                              NOMOS
                  (HQ-Konsole)                      (Compliance-Backbone)
                  ============                       =====================
                   │                                       │
                   │  Electron + Express:4701              │  Docker compose:
                   │  SQLite + sqlite-vec                  │   - nomos-api (FastAPI)
                   │  Transformers.js (384d, lokal)        │   - nomos-console (Next.js)
                   │  pino redacted audit                  │   - nomos-worker (ARQ)
                   │  Argon2 + AES-256-GCM Vault           │   - nomos-plugin (OpenClaw)
                   │  Mattermost + WhatsApp + GitHub       │   - postgres + pgvector
                   │                                       │   - valkey + vault + caddy
                   │  Agent-Fleet, LLM-Router,             │  Hash-Chain JSONL + Ed25519
                   │  Skill-Loader, Approval-Gate,         │   + RFC 6962 Merkle log
                   │  3-Memory-Engine (epis/sem/proc),     │  Anchors + Checkpoints
                   │  Sentinel-Gate (Phase 4)              │   (sibling JSONL, WORM-ready)
                   │                                       │
                   └────────  v0.7.0 BRIDGE  ─────────────►│
                              ─────────────────            │
                              Contract A: events           │
                              Contract B: verdicts         │
                                                           │
                                                           ▼
                                                       Customer-Site
                                                       (DACH-KMU)


                  ZEROTH (Spec-Ebene, governs both via Contract 2)
                  ===========================================
                   M01..M07: Constitutional Safety
                   M08: TT-SI (gemma4:9b)
                   Contract 2: Zeroth Core → Compliance Engine (NomOS)
                   F1=0.8565 / 374 test cases / Ziel ≥0.90
```

### 3.2 Die Begleit-Komponenten (28 Sister-Projekte zusammengefasst)

Per 5-Agent-Inventory:

- **L3 Runtime:** phantom-ai (31 Voice-AI-Services), NomOS-B-V2
  (Phantom Neural Cortex Agent-Fleet)
- **L5 Compliance-Stack (NomOS-Nachbarn):**
  - **NSS** v3.1.1 — Architektur-Referenz, normative 6-Layer-Spec
  - **ai-agent-legal-framework** — Compliance-Wizard, MIT
  - **legal-scraper** — EU/AT/DE/CH-Gesetzgebung als FTS5-Index
  - **TuneForge** — Fine-Tuning, deployt für M08
  - **docforge** — PDF-Generator für Compliance-Output
  - **harness-verify** — Governance-Validation
- **L4 Sales:** Playbook01 (€19-249 Stripe-Produkte)
- **L7 Manifesto:** Lena's Bücher (4 Bände, ~1810 Seiten)
- **Tooling:** meta-skills (Hooks + Skills), atlas-ceo (archiviert)

### 3.3 Die Daten-Flüsse

```
legal-scraper ── Gesetzgebung ──► NomOS rule-store
                                      │
                                      ▼
Customer-Agent ── action ──► Zeroth Core ──► NomOS verdict ──► Action allowed/blocked
                                                  │
                                                  ▼
                                         Hash-Chain entry
                                                  │
                                  ┌───────────────┼─────────────────┐
                                  ▼               ▼                 ▼
                              anchors.jsonl  checkpoints.jsonl   STH endpoint
                              (sibling)      (sibling)           (regulator query)
                                  │
                                  ▼
                              WORM-storage (S3 Object Lock / Azure immutable)
                                  │
                                  ▼
                              Annex-IV-PDF-Generator (docforge + NomOS-data)
                                  │
                                  ▼
                              Customer-DSB · EU-Pitch · AWS-Pitch · Pentest-Evidence
```

---

## 4. 6-Monats-Roadmap — Mai → November 2026

```
2026   May          Jun          Jul          Aug          Sep-Nov
       │            │            │            │            │
       │ v0.4.0✓    │            │            │            │
       │ v0.5.0     │ v0.7.0     │ v0.9.0     │ v1.0.0     │ v1.1+
       │ (W+O)      │ (Bridge)   │ (DPA+DPIA) │ (Pentest)  │ (Customer)
       │            │            │            │            │
       │            │ v0.6.0     │ v0.8.0     │ ⚠ 02.08    │
       │            │ (Vault)    │ (Annex-IV) │ EU AI Act  │
       │            │            │            │            │
       │ Atlas      │ Atlas RCE  │            │            │
       │ Phase 3.5  │ Fix        │            │            │
       │            │ → 3.6      │            │            │
       │            │            │            │            │
       ▼            ▼            ▼            ▼            ▼
    Stabilität  Bridge+Vault  Customer-   GO-LIVE      Skalierung
                              Ready                    + Funding
```

### Mai-Juni 2026: Stabilisierung (jetzt → 2026-06-15)

- **NomOS v0.5.0** (W-Phase: CI-Sichtung, Live-Eval, kritische Fixes; O3/O4/O5 Refactors)
- **Atlas RCE-Fix** in `worker-agent/server.ts:68` (Action Plan v2.0)
- **Atlas Phase 3.5 Close-out** (3.5.4 LLM-keys, 3.5.5 Visual-QA, 3.5.7 Verifikation)
- **NomOS v0.6.0** (Vault TLS-Listener + N-of-M Shamir + Gateway AppRole)

### Juni-Juli 2026: Bridge + Customer-Ready

- **NomOS v0.7.0 — Atlas↔NomOS Integration-Bridge**
  (Contract A audit-sink + Contract B verdict)
- **Atlas Phase 4.x parallel** (Agent-Intelligence, Sentinel-Gate)
- **Self-eating-dogfood Live-Demo:** Joe runs Atlas-on-NomOS
- **NomOS v0.8.0** — Annex-IV-Auto-Generation als Produkt-Feature
  (Hire produziert PDF)
- **NomOS v0.9.0** — DPA-Template + NomOS-eigene DPIA

### Juli-August 2026: v1.0 GO-LIVE

- **Penetration-Test** (extern, 1 Woche, ~€5-15k)
- **Customer Migration Path docs** (v0.2.0 → v1.0.0 upgrade-guide)
- **NomOS v1.0.0 Tag** — released
- **2026-08-02: EU AI Act Art. 12 Vollanwendung** — wir sind live

### August-November 2026: Customer-Acquisition + Skalierung

- **3-5 DACH-KMU Pilot-Customers** (€500-2000/Monat each)
- **AWS Activate Pre-Seed Pitch** mit Pilot-PDF + 3 Customer-Testimonials
- **EU EIC/Horizon Antrag** parallel
- **v1.1+** basierend auf Customer-Feedback

---

## 5. Phase-by-Phase Konkretisierung

### Phase v0.5.0 — Stabilisierung (1-2 Wochen, jetzt)

**W1: CI-Status sichten + STATUS-Selbstkorrektur** (15 min)
- `gh pr checks 31..34` — CodeQL/Trivy/Router-Coverage grün?
- STATUS.md Test-Count-Discrepancy fixen (440 → 454)

**W2: 5 echte Sicherheits-/Code-Lücken** (45 min)
- STH/Proof Rate-Limit (Valkey, 10/min/user/endpoint)
- `nomos.core.api.py:18` localhost-default raus
- B-F01/F02/F14 Tests für `/api/audit/entry`
- `validate_settings()` callable statt module-exit
- `vault-init` `changeme` Fallback → fail-fast

**W3: Doku-Drift komplett** (30 min)
- operations-runbook v0.4.0-Items
- DE-Mirror für v0.4.0
- L042-L053 nach phantom-ai/.claude/knowledge/

**W4: Phase-I Live-Eval AUSFÜHREN** (30-60 min)
- `docker compose down -v && up -d --build` clean state
- Bootstrap → Hire → Anchor → STH → Inclusion-Proof verify out-of-container
- Tamper-test
- EVAL-RESULTS-2026-05-20.md dokumentieren

**O3-O5: Architektur-Refactors** (5-8h)
- chat_service.py extraction (proxy.py 4 responsibilities → 1)
- manifest migration framework + extra="ignore"
- plugin contract-check extension

**Definition of Done:**
- alle 5 KRITISCH-Items aus Audit closed
- `pytest -q` grün
- `docker compose up -d` läuft auf cleanem Volume-Set
- Tag `v0.5.0` gepushed
- DE-Doku synchronisiert

### Phase v0.6.0 — Vault Hardening (3-5 Tage)

- Vault TLS-Listener (HTTP intern + HTTPS extern, configurable cert)
- Vault N-of-M Shamir Default (3-of-5 oder KMS-doc)
- Gateway-Token Vault AppRole statt File-Mount
- Tests + Migration-Notes für Bestandsdeployments

**Definition of Done:** Vault läuft mit TLS in prod, dev_mode bleibt http. Gateway nutzt AppRole. Re-keying-Procedure dokumentiert.

### Phase v0.7.0 — Atlas-Bridge (5-7 Tage)

**NomOS-side (2 Tage):**
- `POST /api/audit/entries` (batch, plural)
- `WS /api/audit/stream/{agent_id}` (streaming)
- `POST /api/costs/llm-call` (LLM-cost-tracking)
- EventType-Enum erweitern (LLM_REQUEST_COMPLETED, AGENT_CRASHED, AGENT_KILLED_BY_OPERATOR)
- Atlas-source marker (`data.source: "atlas"`, `data.atlas_agent_id`)
- Separate Rate-Limit-Bucket für service-principals

**Atlas-side (3 Tage):**
- `NomOSAuditSink` service (enqueue/drain/retry/DLQ)
- `NomOSComplianceClient` (200ms timeout, 60s LRU cache)
- `ApprovalGate`-Wiring: NomOS-verdict vor User-Confirm
- Settings-UI: NomOS Backend Card (URL, API-Key, Test-Connection)

**Live-Demo (1 Tag):**
- Joe startet Atlas
- Agent-Fleet läuft
- Jeder Tool-Call landet in NomOS-Hash-Chain
- Joe öffnet NomOS-Console → sieht alle Atlas-Events
- STH/Inclusion-Proof verifiziert von außen

**Definition of Done:** Atlas-Agent kann nicht mehr Tool aufrufen ohne dass NomOS es als verdict freigibt. NomOS Audit-Trail hat 100% der Atlas-Events. STH-Verification roundtrip funktioniert.

### Phase v0.8.0 — Annex-IV-Auto-Gen (5-10h)

- Per `nomos hire` produziert PDF mit Annex-IV §1(a), §1(c), §2(b), §2(c), §2(d), §2(e), §2(f), §3
- Manifest-driven (alles aus AgentManifest extrahierbar)
- Live-Events-Anhang (recent audit-chain entries als Evidence)
- Multilingual DE/EN
- `nomos annex --agent-dir ... --output annex-iv.pdf` CLI-command

**Definition of Done:** Compliance-Pilot Tag 0-5 wird mit dem Generator wiederholbar. Joe kann `nomos annex` für jeden Customer-Agent ohne Hand-Arbeit produzieren.

### Phase v0.9.0 — DPA + DPIA (2 Tage)

- DPA-Template (Art. 28 DSGVO) konfigurierbar aus Manifest + Tenant-Daten
- NomOS-eigene DPIA durchführen (externer DSB konsultiert)
- DPIA als `docs/dpia-2026-07.md` ablegen
- Customer-DPA-Generator als `nomos dpa` CLI-command

### Phase v1.0.0 — Production-Ready (1-2 Wochen)

- **Externer Penetration-Test** (1 Woche, Booking jetzt)
- **Pentest-Findings Triage + Fix-Sprint** (5-10 Tage je nach Findings)
- **Customer Migration Path docs** (v0.2.0 → v1.0.0)
- **Disaster Recovery Drill** (backup → nuke → restore → verify)
- **Marketing-Materials:** Pitch-Deck + Demo-Video + Customer-Onboarding-Walkthrough
- **Release-Tag v1.0.0**
- **Press-Release** über ai-engineering.at (Entity, nicht Joe)

**Definition of Done am 2026-08-01:** v1.0.0 ist live, alle Pentest-Findings sind closed, Customer-Migration-Pfad existiert, Disaster-Recovery wurde 1× durchgespielt.

### Phase v1.1+ — Customer-Skalierung (Sep-Nov)

- 3-5 Pilot-Customers onboarden (mit Joe direkt)
- Customer-Feedback-Loop → v1.1, v1.2 Patches
- AWS Activate Pre-Seed Submission
- EU EIC / Horizon Antrag

---

## 6. Dependency-Graph (wer braucht wen wann)

```
v0.4.0 ✓ (heute)
  │
  ├──► v0.5.0 (W+O) ─────────────────────► Phase-I Live-Eval Lauf
  │       │
  │       ▼
  │     v0.6.0 (Vault Hardening) ────────► CUSTOMER-DEPLOYABILITY ok
  │       │
  │       └──┬─────────────────────┐
  │          ▼                     ▼
  │      Atlas RCE Fix         NomOS-side prep
  │       (Action Plan v2.0)   für v0.7.0
  │          │                     │
  │          ▼                     │
  │      Atlas Phase 3.5            │
  │      Close-out                  │
  │          │                     │
  │          └─────────┬───────────┘
  │                    ▼
  │                v0.7.0 — Atlas↔NomOS Bridge
  │                    │
  │                    ├─► Bell-Labs-Dogfood-Demo
  │                    │
  │                    ▼
  │                v0.8.0 — Annex-IV-Auto-Gen
  │                    │
  │                    └─► Compliance-Pilot-PDF wird wiederholbar
  │                            │
  │                            ▼
  │                        v0.9.0 — DPA + DPIA
  │                            │
  │                            ▼
  │                        v1.0.0 — Pentest + Migration-Docs
  │                            │
  │                            ▼
  │                    ⚠ 2026-08-02 EU AI Act Art. 12
  │                            │
  │                            ▼
  │                    Customer-Acquisition Sprint
  │                            │
  │                ┌───────────┼────────────┐
  │                ▼           ▼            ▼
  │            Pilot #1    Pilot #2    Pilot #3+
  │                │           │            │
  │                └───────────┼────────────┘
  │                            ▼
  │                    AWS + EU-EIC Pitches mit
  │                    realer Customer-Evidence
  │                            │
  ▼                            ▼
2027: 50 Kunden, €30-100k MRR, EU-Souverän-Stack-Brand
```

**Hard Gates (kann nicht überspringen):**

1. **Phase-I Live-Eval** muss vor v0.6.0 laufen — sonst verkaufen wir Vaporware
2. **Atlas RCE Fix** muss vor v0.7.0 erfolgen — sonst poisoniert ein compromised Atlas die NomOS-Audit-Chain
3. **Pentest** muss vor v1.0.0 erfolgen — sonst keine Customer-Trust
4. **Pilot-Customer #1** muss vor AWS-Submission laufen — sonst keine Pull-Evidence

---

## 7. Offene Fragen + Empfehlungen (Entscheidungs-Matrix)

> **Kanonischer Decision-Register ist `2026-05-21-decision-log.md`** —
> dieser konsolidiert §7 + META-VISION §12 + WSK §9 in eine Liste mit
> Status-Markern. §7 unten bleibt als Optionen-/Begründungs-Detail.

| # | Frage | Optionen | Empfehlung | Wann entscheiden |
|---|---|---|---|---|
| 1 | **Atlas als NomOS-Pilot-Customer #0?** | A: ja (dogfood) · B: nein (parallel laufen lassen) | **A** — Bell-Labs-Selbst-Anwendung. Atlas-on-NomOS ist die ehrlichste Demo-Story für DACH-KMU. | Vor v0.7.0 (Juni) |
| 2 | **NomOS PyPI Publish?** | A: ja (`pip install nomos`) · B: nein (Source-only) | **A** — senkt Customer-Friction massiv. Wheel-Build ist bereits ready, nur PyPI-Account+Token nötig. | v0.6.0 |
| 3 | **Multi-Tenant DB-Isolation für Enterprise-VPS?** | A: Schema-per-Tenant · B: Row-Level Security · C: weiter shared | **B** für v1.0, **A** für Enterprise-Tier-Premium | v0.9.0 |
| 4 | **OpenAPI-driven Plugin-Contract?** | A: openapi-typescript codegen · B: manual sync via check-contracts.ts | **A** — eliminiert die ganze C-F10-Klasse von Drifts | v0.7.0 (parallel zu Atlas-Bridge) |
| 5 | **NemoClaw Activation als Backend?** | A: jetzt aktivieren · B: weiter Manifest-Marker · C: streichen | **B** — Customer-Pull-driven, kein Vorab-Investment | v1.1+ |
| 6 | **Vault TLS Migration-Strategie?** | A: Breaking-Change in v0.6 · B: opt-in `NOMOS_VAULT_TLS=true` | **B** — dev_mode bleibt http. Prod-Operator setzt env. Migration-Doc in operations-runbook. | v0.6.0 |
| 7 | **Phase-B2 Sigstore Rekor public anchoring?** | A: opt-in feature · B: ganz weglassen · C: default-on | **A** — opt-in via Manifest, off by default. Data-protection-Tradeoff. | v1.1+ |
| 8 | **Customer Migration Path v0.2.0→v1.0?** | A: `nomos migrate` CLI · B: Manual-Guide · C: beides | **C** — CLI für 80% Cases, Guide für Edge-Cases | v1.0.0 |
| 9 | **Funding-Priorität: AWS first oder EU EIC parallel?** | A: AWS first (schnellste Conversion) · B: parallel · C: EU first | **A** — AWS-Credits decken Non-Compute. EU-EIC braucht 6+ Monate Bearbeitung. | Q3 2026 |
| 10 | **Wann beginnt Customer-Acquisition?** | A: v1.0.0 Launch · B: bei v0.8.0 mit Pre-Sale · C: erst Q4 | **B** — Pre-Sale ab v0.8.0 mit Annex-IV-Demo, harte Launch bei v1.0.0 | jetzt für Pre-Sale-Liste |
| 11 | **Wer ist Pilot-Customer #1 (extern)?** | A: AT-KMU aus Joe-Netzwerk · B: NSS-Kooperationspartner · C: Cold Outreach | **A** — Vertrauensbasis, schnelles Feedback, persönliches Onboarding | bis v0.8.0 identifizieren |
| 12 | **`/full-sync` ERPNext+open-notebook+Wiki — heute oder bei v0.5.0?** | A: heute (W4-W5) · B: bei v0.5.0 · C: vor v1.0 | **B** — Joe-Cred-bearing, eigene Session. Sammeln bis v0.5.0 Tag-Push, dann Bulk. | v0.5.0 Release-Tag |
| 13 | **Hardware-Plan / Customer-SKU?** | A: Standard-x86-Linux · B: RaspberryPi5 als Low-End · C: Intel NUC Sweet-Spot | **A+C** — Standard x86 als Baseline (alle Docker-VPS-Hoster), Intel NUC als Edge-Hardware-SKU für "EU-Sovereign On-Prem" Marketing | v1.0.0 |
| 14 | **Atlas Phase-4 vs NomOS-v0.7 Integration — gleichzeitig oder sequentiell?** | A: parallel · B: Atlas Phase 4 first · C: NomOS v0.7 first | **A** parallel — Atlas Phase 4 baut Sentinel-Gate, NomOS v0.7 baut die Bridge. Beide brauchen einander nicht synchron. | jetzt |
| 15 | **DPIA für NomOS selbst — wer macht das?** | A: externer DSB · B: Joe selbst mit Template · C: Anwaltsbüro | **A** — DSB ist die richtige Rolle, kostet ~€500-1500. Anwaltsbüro nur für DPA-Vertragsmuster-Review. | v0.9.0 |
| 16 | **Penetration-Test — wer? wann? Budget?** | A: deutsche Mittelständler-Pentest-Firma · B: Cure53 / SecureLayer · C: Bug-Bounty | **A** — €5-15k, deutsche Firma für DACH-Sprach-Match, 1 Woche. Bug-Bounty erst nach Customer-Base. | v1.0.0 booking ab Juni |
| 17 | **Pricing — pro Agent, pro Tenant, pro Doc?** | A: pro Agent (€20-50/Monat/Agent) · B: pro Tenant Flat (€500-2k) · C: Hybrid (Flat + per-Agent über X) | **C** — Flat €499/Monat bis 10 Agents, €19/Monat pro weiterer Agent, optional Annex-IV-PDF €99 pro Audit-Cycle | v0.8.0 als Beta-Pricing |
| 18 | **Lineage Engine — wirklich deferred oder kommt das back?** | A: deferred bleiben (NomOS hat es absorbiert) · B: reaktivieren als separate Komponente | **A** — NomOS's Ed25519+Merkle ist eine vollwertige Lineage-Implementation. DEC-001..004 bleibt. | confirmed |
| 19 | **Asqav adoptieren oder eigene Hash-Chain behalten?** | A: NomOS-Chain behalten + Asqav-Interop dokumentieren · B: Asqav-SDK adoptieren · C: rein eigene Chain, keine Interop | **A** — Chain ist fertig (745 Tests), AGPL-rein, RFC-6962-Standard. Die Differenzierung ist der Annex-IV-Workflow *darüber*, nicht die Krypto-Primitive. Interop = NomOS kann einen Asqav-Trail lesen, falls ein Customer ihn bereits nutzt. ADR-würdig — Joe ratifiziert. | v0.5.0 / Decision-Log |

---

## 8. Risiko-Register

| # | Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **2026-08-02 Deadline rutscht** | Niedrig | Katastrophal | Hard Gate Reviews wöchentlich, ab Juni 2x/Woche; v1.0 zur Not als "v0.9.x security-feature-complete" framen |
| R2 | **Atlas RCE wird Customer-bekannt** | Niedrig (Atlas ist internal) | Hoch (Trust-Schaden) | RCE-Fix vor v0.7.0; nie Atlas-Code für Customer-Demos |
| R3 | **Pentest findet CRITICAL** | Mittel | Hoch (Schedule-Rutsch) | Pentest in Juni booken, Findings-Fix-Budget 2 Wochen einplanen |
| R4 | **Customer #1 sagt nein** | Mittel | Hoch (Funding-Pitch verliert Pull) | Mindestens 3 Pre-Sale-Kontakte vor v1.0 lock-in |
| R5 | **EU-AI-Act-Auflagen ändern sich** | Niedrig | Mittel | legal-scraper-Pipeline, monitoring Art. 12 + Annex IV in EU-Amtsblatt |
| R6 | **Single-Person-Burnout** | **Hoch** | Katastrophal | **L053 + Pace-Tracking; Joe macht Strategy, Claude+Sub-Agents machen Code; Q3 mindestens 1 Pause-Woche** |
| R7 | **NSS-Standard ändert sich** | Niedrig | Niedrig | Kooperationspfad mit LEEI1337, NSS-Repo subscriben |
| R8 | **Atlas-Phase-4 dauert länger** | Mittel | Mittel | NomOS-Bridge ist nicht atlas-blocking; Atlas kann minimal-viable als event-emitter sein |
| R9 | **Cryptography lib breaking change** | Niedrig | Mittel | Dependabot active; cryptography pin <46 (heute <49 erlaubt zu viel) |
| R10 | **OpenClaw upstream breaking change** | Mittel | Hoch | Pin auf 2026.5.18 mit digest-pin, Plugin-Compat-Test in CI |
| R11 | **Customer-Hardware nicht ausreicht (RPi5)** | Mittel | Mittel | Customer-SKU-Test mit Intel NUC + RPi5 vor v1.0 |
| R12 | **DSB findet DPIA-Issues** | Mittel | Niedrig (zeitlich) | DPIA in v0.9 starten, nicht in v1.0 |
| R13 | **OSS-Konkurrenz (Microsoft/Asqav/FutureAGI) besetzt die generische AI-Governance-Kategorie** und drückt NomOS in eine "auch-Tool"-Wahrnehmung | **Hoch** (seit April 2026 live) | Mittel (Differenzierung ist strukturell, nicht feature-basiert) | Nicht auf Feature-Parität konkurrieren. Differenzierung §2.1 scharf halten (AGPL + DACH-KMU + WSK). **Spur C** — regionale Verankerung via RUF-Pilot + WSK, nicht kopierbar. `competitive-landscape.md` halbjährlich refreshen. |

---

## 9. Erfolgsdefinition pro Phase

| Phase | Erfolg = |
|---|---|
| v0.5.0 | Alle 5 KRITISCH-Items aus Audit closed. Phase-I Live-Eval erfolgreich gelaufen. Tag gepusht. |
| v0.6.0 | Vault läuft mit TLS in prod-mode. Re-keying-Drill 1× durchgeführt. Operator-Doc fertig. |
| v0.7.0 | Atlas-Agent läuft in Joe's Setup, jeder Tool-Call landet in NomOS-Hash-Chain, STH-Verification roundtrip von externem Python-Skript funktioniert. |
| v0.8.0 | `nomos hire` produziert ein Annex-IV-PDF das ein externer Anwalt als "compliance-ready" akzeptiert (mind. 1× extern reviewed). |
| v0.9.0 | DSB hat DPIA für NomOS unterschrieben. DPA-Template ist Customer-presentable. |
| v1.0.0 | Pentest closed mit 0 unaddressed CRITICALs. v1.0 tag gepusht. Customer-Migration-Doc + Disaster-Recovery-Drill 1× durchgespielt. Press-Release über ai-engineering.at raus. |
| 2026-08-02 | Mindestens 3 Customer-Sites laufen mit NomOS v1.0. Mindestens 1 echter Agent-Lifecycle-Vorgang dokumentiert im Audit-Trail. |
| 2026-Q4 | 5+ paying customers, €10k+ MRR, AWS-Pre-Seed eingereicht, EU-EIC-Antrag eingereicht. |

---

## 10. Wer macht was

| Rolle | Verantwortung | Beispiel-Tasks |
|---|---|---|
| **Joe** | Strategic Decisions (Tabelle §7), Customer-Contact, Funding-Pitches, Hardware-SKU-Selection, Cred-Bearing External Tasks (Wiki / ERPNext / open-notebook), Code-Review-Approval, DSB-Auswahl, Pentest-Firma-Auswahl, Pilot-Customer-Outreach | Q-Decisions §7 #1-#18, externe Schreibvorgänge, Geschäftspfade |
| **Claude (autonom)** | Code-Implementation, Tests, Docs, Releases, Audit-Passes, Multi-Agent-Orchestration, Strategy-Docs | jede neue NomOS-Phase, alle Hotfix-PRs, Doku-Sync, LEARNINGS-Pflege |
| **Sub-Agents (parallel)** | Multi-File-Audits, Pattern-Discovery, Doc-Sync, Per-Component-Expertise | nomos-security/qa/architect, meta-skills:session-analyst, meta-skills:doc-scanner-* |
| **Externe Dependencies** | DSB für DPIA, Pentest-Firma für v1.0, AWS-Activate-Sponsor, Anwaltsbüro für DPA-Vertragsmuster | Joe vermittelt + bezahlt + integriert in Plan |

**Wichtig:** Joe macht NICHT Code mehr in dieser Phase (Single-Person-Burnout R6). Claude macht Code mit Sub-Agent-Verstärkung. Joe macht Strategie, Customer, Geld.

---

## 11. Was passiert wenn wir's nicht schaffen

Drei Szenarien mit Fallback:

### Szenario A: v1.0 rutscht auf Sep 2026 (1 Monat nach Deadline)
**Wahrscheinlichkeit:** Mittel.
**Plan:** v0.9.x ist "security-feature-complete" framen. Customer-Onboarding läuft mit v0.9.x. Marketing-Sprache: "compliance-effective ab Tag 1, full v1.0 release Sep 2026". Kein Drama-Verlust, aber Pitch-Materialien müssen das honest reflecten.

### Szenario B: Atlas-Bridge (v0.7) rutscht auf Aug 2026
**Wahrscheinlichkeit:** Mittel-Hoch (Atlas hat eigene Phase-4-Roadmap).
**Plan:** NomOS v0.8/0.9/v1.0 läuft trotzdem durch. Bell-Labs-Dogfood-Story wird "kommt in v1.1" statt v0.7. Customer-Acquisition läuft ohne live-Atlas-Demo, Annex-IV-PDF reicht.

### Szenario C: Pentest findet 3+ CRITICALs
**Wahrscheinlichkeit:** Mittel.
**Plan:** v1.0 wird zu v1.0-rc1, Pentest-Fix-Sprint 2-3 Wochen, dann v1.0.0 GA. Customer-Pre-Sale-Liste informieren. EU-AI-Act-Deadline-Story: "wir hatten v0.9 live für Compliance, v1.0 ist Pentest-hardened Production-Tier".

### Worst-Case: Burnout (R6)
**Plan:**
- Joe nimmt sofort Pause
- Claude + Sub-Agents fahren auf Maintenance-Mode (Security-Patches only)
- Customer-Acquisition pausiert
- Push-Plan auf Q1 2027

---

## 12. Nächste konkrete Aktion (jetzt)

Falls Joe sofort weiter machen will:

**Heute Abend / Morgen früh:**
1. **W1: CI-Status sichten** — `gh pr checks 31` bis `gh pr checks 35` durchgehen. Wenn alle grün: weiter. Wenn rot: triagen.
2. **Strategische Entscheidungen-Matrix §7** — durchgehen, Joe-Antworten in `docs/strategy/2026-05-20-decisions.md` festschreiben.
3. **Customer-Pilot-#1-Kontakt** — Joe identifiziert AT-KMU aus Netzwerk, schickt erste Mail (kann ich vorformulieren).

**Diese Woche:**
1. W2 (5 Sicherheits-/Code-Lücken) closen
2. W3 (Doku-Drift) closen
3. W4 (Phase-I Live-Eval LAUFEN — nicht nur dokumentieren)
4. NomOS v0.5.0 Tag

**Nächste Woche:**
1. Pentest-Firma anfragen (3 Angebote einholen, Buchung für Juli)
2. DSB-Erstgespräch für DPIA
3. NomOS v0.6.0 Vault-Hardening starten
4. Atlas-RCE-Fix-Sprint (Joe + Claude koordiniert; phantom-control gehört auch zum Stack)

**Bis Ende Juni:**
- v0.7.0 Atlas-Bridge fertig
- Erste Bell-Labs-Dogfood-Demo intern aufgenommen
- Pilot-Customer-#1 identifiziert + Pre-Sale-Gespräch geführt

---

## 13. Begleitdokumente

- `docs/strategy/2026-05-20-big-picture.md` — Vision-Tiefendoc
- `docs/strategy/2026-05-20-META-VISION.md` — Constitutional-OS Meta-Ebene
- `docs/strategy/2026-05-20-v0.5.0-roadmap.md` — Gap-Liste Tiefendoc
- `docs/strategy/2026-05-20-nomos-atlas-integration.md` — Bridge Contract-Spec
- `docs/strategy/2026-05-21-nomos-wsk-integration.md` — WSK-Datenquellen-Integration
- `docs/strategy/2026-05-21-competitive-landscape.md` — Konkurrenz-Map + Differenzierung
- `Documents/STRATEGY-2026-Q2.md` — Cockpit-Variante
- `CHANGELOG.md` — Was-bisher-shipped
- `.claude/knowledge/LEARNINGS.md` — L001-L053
- `Documents/zeroth/decisions/Action_Plan_v2.0_post-TASK-00685.md` — DEC-005
- `Documents/zeroth/concepts/Compliance_Pilot_Annex_IV_v0.1.md` — Tag-0-5-Plan
- `Documents/phantom-control/docs/ROADMAP.md` — Atlas Phase 3.5/3.6/4/5

---

## 14. One-Pager-Zusammenfassung (wenn nur Zeit für eine Seite)

```
WAS:        EU-souveräne KMU-AI-Governance — NomOS verkauft, Atlas intern.
DEADLINE:   2026-08-02 EU AI Act Art. 12.
HEUTE:      NomOS v0.4.0 LIVE, 745 Tests, L053 LEARNINGS, 4 Tags an einem Tag.
KRITISCH:   Phase-I Live-Eval nie gelaufen, Atlas RCE, 5 Sicherheitslücken.
NEXT TAG:   v0.5.0 (Stabilisierung). Aufwand: 1-2 Wochen.
NÄCHSTES
GROSSES
DING:       v0.7.0 = Atlas-NomOS-Bridge (Bell-Labs-Dogfood).
V1.0:       2026-07/08. Pentest, DPIA, DPA-Template, Customer-Migration.
SALES:      Pre-Sale ab v0.8, hard Launch v1.0, Pilot 1-3 in Aug.
RISIKO #1:  Burnout. Joe macht Strategie, nicht Code.
RISIKO #2:  Atlas RCE bekannt vor Fix.
RISIKO #3:  Pentest findet CRITICAL → v1.0 rutscht 2-3 Wochen.
ENTSCHEIDUNG #1:    Atlas als NomOS-Pilot-#0? Empfehlung: JA.
ENTSCHEIDUNG #17:   Pricing? Empfehlung: €499/Monat Flat bis 10 Agents.
PILOT #1 TARGET:    AT-KMU aus Joe-Netzwerk, vor v0.8.0.
FUNDING:    AWS first (Q3), EU-EIC parallel (6+ Monate Bearbeitung).
NORDSTERN:  Bell Labs, Asimov-Zeroth, Inverse-Pyramide.
```
