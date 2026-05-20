# Archive

> Historische Dokumente. Lebende Docs liegen in `docs/`.
>
> Strukturiert nach Quartalen, damit ältere Spec/Plan/Report-Sets in
> ihrem Kontext erhalten bleiben aber den lebenden Doc-Baum nicht
> belasten.

## Layout

```
docs/archive/
└── 2026-Q2/
    ├── superpowers/      Spec + Plan files from the v2 design-and-build phase (März-April 2026)
    │   ├── plans/        2026-03-24 .. 2026-04-13 — phased rollout plans
    │   └── specs/        Architecture specs, infra-hardening v1+v2 designs
    ├── reports/          Session reports + the enterprise-audit reports from März-April
    ├── changes/          The 2026-04-13 monitoring + hardening change-set (technical-overview, runbooks, troubleshooting, architecture diagrams, best-practices, README)
    └── hardening-2026-05-18/  Pre-v0.2.0 hardening notes (replaced by hardening-2026-05-20/)
```

## Was bleibt in `docs/` (live)

- `docs/architecture.md` — autoritative System-Architektur (v0.3.0-reconciled)
- `docs/api-reference.md` — REST-Endpoints (49+ inkl. STH + Inclusion-Proof)
- `docs/cli-reference.md` — CLI-Commands
- `docs/operations-runbook.md` — Bring-up, Audit-Key-Rotation, Regulator-Workflow
- `docs/compliance-guide.md` — EU AI Act / DSGVO Mapping inkl. Art. 12
- `docs/quickstart.md` — 5-Minuten-Onboarding
- `docs/de/` — DE-Mirror der Hauptdokumente
- `docs/hardening-2026-05-20/` — aktive Roadmap (PLAN + EVAL)
- `docs/release-2026-05-20-external-index.md` — v0.2.0 External-Index-Punchlist
- `docs/release-2026-05-20-v0.3.0-external-index.md` — v0.3.0 External-Index-Punchlist
- `docs/references/openclaw-nemoclaw-reference.md` — OpenClaw + NemoClaw Reference

## Re-Archivierungs-Regel

Bei jedem Major-Release: Spec + Plan + Report files die zum
abgeschlossenen Release-Cycle gehören in `docs/archive/<YYYY>-Q<N>/`
verschieben. Lebende Docs bleiben in `docs/`.
