# NomOS Doku-Index — die Landkarte

> **Hier anfangen.** Dieser Index ist das Wiki von NomOS: jede aktive
> Dokumentation hat genau einen Platz in einem von 5 Tiers. Wer etwas
> sucht, startet hier.
>
> **Pflege-Regel:** Jedes neue Dokument bekommt **im selben Commit**
> einen Eintrag hier. Das Datei-Layout bleibt physisch wie es ist —
> dieser Index klassifiziert *logisch* (Operating-Model Prinzip 3).
>
> **Stand:** 2026-05-21.

---

## Tiers auf einen Blick

| Tier | Inhalt | "Ich will…" |
|---|---|---|
| **T0** | Meta / Governance | …wissen wie wir arbeiten, welche Regeln gelten |
| **T1** | Strategie | …Vision, Plan, Entscheidungen verstehen |
| **T2** | Architektur | …wissen wie das System gebaut ist |
| **T3** | Betrieb | …NomOS starten, deployen, releasen |
| **T4** | Wissen | …aus Fehlern, Audits, Reviews lernen |

---

## T0 — Meta / Governance

| Dokument | Zweck |
|---|---|
| [`docs/OPERATING-MODEL.md`](OPERATING-MODEL.md) | **Wie wir arbeiten** — 7 Prinzipien, Arbeits-Kadenz. Kanonisch. |
| [`docs/QUALITY-SYSTEM.md`](QUALITY-SYSTEM.md) | **Wie wir keinen Müll produzieren** — Definition of Done, Test-Architektur, CI-Stages, Eval-Framework, Lücken-Liste |
| [`CLAUDE.md`](../CLAUDE.md) | Projekt-Info, Zeroth-Stack-Rolle |
| [`.claude/CLAUDE.md`](../.claude/CLAUDE.md) | HARD RULES, Tech-Stack, Commit-Convention, aktiver Plan |
| [`.claude/rules/01-06`](../.claude/rules/) | 6 spezifische Rules (Produkt-Standalone, Integration-First, Agent-Führung, PDCA, Refactor-Gate, Integration-Test-Pflicht) |
| [`.claude/agents/`](../.claude/agents/) | 6 Agenten-Briefs (nomos-architect/backend/qa/security/master, console-dev) |
| [`AGENTS.md`](../AGENTS.md) | Agent-Onboarding Quick-Start |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | Beitrags-Regeln |
| [`CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md) | Verhaltenskodex |
| [`SECURITY.md`](../SECURITY.md) | Vulnerability-Disclosure-Policy |

## T1 — Strategie

Alle in `docs/strategy/`. Einstieg: **Decision-Log** (was offen/
entschieden ist) → **MASTER-PLAN** (der Weg) → Rest als Tiefe.

| Dokument | Zweck |
|---|---|
| [`2026-05-21-decision-log.md`](strategy/2026-05-21-decision-log.md) | **Kanonischer Decision-Register** — alle 28 Entscheidungen, Status |
| [`2026-05-20-MASTER-PLAN.md`](strategy/2026-05-20-MASTER-PLAN.md) | Der Plan jetzt→November 2026, Roadmap, Risiko-Register |
| [`2026-05-20-META-VISION.md`](strategy/2026-05-20-META-VISION.md) | Vision auf Meta-Ebene — Constitutional OS, 7 Goals |
| [`2026-05-20-big-picture.md`](strategy/2026-05-20-big-picture.md) | Vision-Tiefendoc |
| [`2026-05-21-competitive-landscape.md`](strategy/2026-05-21-competitive-landscape.md) | Konkurrenz-Map + 6 Differenzierungs-Punkte |
| [`2026-05-20-v0.5.0-roadmap.md`](strategy/2026-05-20-v0.5.0-roadmap.md) | Gap-Liste nach v0.4.0 |
| [`2026-05-20-nomos-atlas-integration.md`](strategy/2026-05-20-nomos-atlas-integration.md) | Atlas↔NomOS Bridge Contract-Spec |
| [`2026-05-21-nomos-wsk-integration.md`](strategy/2026-05-21-nomos-wsk-integration.md) | WSK-Datenquellen-Integration, Modell 2+3 |

## T2 — Architektur

| Dokument | Zweck |
|---|---|
| [`docs/architecture.md`](architecture.md) | System-Design, Datenfluss, Sicherheit |
| [`docs/api-reference.md`](api-reference.md) | Autoritative REST-API (49+ Endpoints, AuthZ-Tabelle) |
| [`docs/cli-reference.md`](cli-reference.md) | Alle CLI-Befehle mit Beispielen |
| [`docs/references/openclaw-nemoclaw-reference.md`](references/openclaw-nemoclaw-reference.md) | OpenClaw/NemoClaw Integrations-Referenz |
| [`MONITORING_DESIGN.md`](../MONITORING_DESIGN.md) | Monitoring-/Alerting-System-Design ⚠ loose top-level |
| [`IMPLEMENTATION_SUMMARY.md`](../IMPLEMENTATION_SUMMARY.md) | Monitoring-Implementierung — Record ⚠ loose top-level |
| `schemas/` · `templates/` | YAML-Manifest-Schemata + Agent-Rollen-Templates |

## T3 — Betrieb

| Dokument | Zweck |
|---|---|
| [`README.md`](../README.md) · [`README.de.md`](../README.de.md) | Produkt-Einstieg, Quick-Start |
| [`docs/quickstart.md`](quickstart.md) | In 5 Minuten lauffähig |
| [`docs/operations-runbook.md`](operations-runbook.md) | Bring-up, Healthchecks, Secrets, Backup, Key-Rotation, Regulator-Export |
| [`docs/compliance-guide.md`](compliance-guide.md) | EU-AI-Act + DSGVO-Abdeckung, Audit-Trail v2 |
| [`RELEASING.md`](../RELEASING.md) | Release-Prozess |
| [`CHANGELOG.md`](../CHANGELOG.md) | Release-Historie je Komponente |
| [`docs/hardening-2026-05-20/PLAN.md`](hardening-2026-05-20/PLAN.md) | Audit-Trail-v2 Hardening-Roadmap |
| [`docs/release-2026-05-20-external-index.md`](release-2026-05-20-external-index.md) | Externer Release-Index |
| [`docs/de/`](de/) | Deutsche Spiegel (Schnellstart, API, Architektur, CLI, Compliance) |

## T4 — Wissen

| Dokument | Zweck |
|---|---|
| [`.claude/knowledge/LEARNINGS.md`](../.claude/knowledge/LEARNINGS.md) | L001-L053 — Erkenntnisse aus Sessions/Audits |
| [`docs/hardening-2026-05-20/EVAL-2026-05-20.md`](hardening-2026-05-20/EVAL-2026-05-20.md) | Hardening-Evaluations-Ergebnis |
| [`docs/reviews/`](reviews/) | Externe Feedback-Reviews |
| [`docs/whitepaper/`](whitepaper/) | Multi-Agent-Development-Methodik, Praxis-Vergleiche |
| [`docs/protocols/`](protocols/) | Deployment-Protokolle |
| [`docs/archive/`](archive/) | Historische Pläne, Specs, Session-Reports, Postmortems (2026-Q2) — siehe [`archive/README.md`](archive/README.md) |

---

## Drift-Watch — bekannte Stale-Stellen

Operating-Model Prinzip 3 fordert Stale-Detection. Stand 2026-05-21
offen:

| Stelle | Problem | Fix wo |
|---|---|---|
| `README.md` Version-Badge | zeigt `0.2.0`, IST `0.4.0` | LICENSE/Release-Phase |
| `README.md` License | "Fair Source/Core License", N1 entschied **AGPL-3.0** | N1-Implementierung (LICENSE-Datei) |
| `.claude/CLAUDE.md` Test-Count | "693+ / 454 API", IST **745** (245 CLI + 440 API + 46 Plugin + …) | nächster Doc-Sync |
| Loose top-level | `MONITORING_DESIGN.md`, `IMPLEMENTATION_PLAN.md`, `IMPLEMENTATION_SUMMARY.md` gehören nach `docs/` bzw. `docs/archive/` | R-Followup |
| `docs/strategy/` | enthält interne Geschäfts-Strategie — vor OSS-Release (N1) klären was public/intern bleibt | vor v0.6 OSS-Release |

---

## Verweise

- Betriebsmodell: [`docs/OPERATING-MODEL.md`](OPERATING-MODEL.md)
- Entscheidungen: [`docs/strategy/2026-05-21-decision-log.md`](strategy/2026-05-21-decision-log.md)
