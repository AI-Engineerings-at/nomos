# NomOS Enterprise-Hardening — Agent Briefs & Playbook

> Created 2026-05-18. Goal: bring everything open/untested to enterprise-grade, no compromises.
> Mandate: full-autonomous (Joe decision 2026-05-18). Stop only on a real blocker requiring a product decision.

## Shared rules for every agent (override defaults)

1. **No guessing.** Unknown → read the source/docs. Cite file:line for every claim.
2. **Exploration before implementation.** ≥3 Read calls before the first Write.
3. **Lint before commit, always.** Python: `ruff check`. TS: `npm run lint`. Per `.claude/CLAUDE.md`.
4. **Test after every change, not batched.** One fix → run its test → verify → next.
5. **Refactor quality gate** (`.claude/rules/05`): rename → grep all refs; type change → update all fixtures/mocks.
6. **Integration is truth** (`.claude/rules/06`): unit green ≠ done. Final gate = `docker compose up` + browser golden path + F12 zero errors.
7. **Product standalone** (`.claude/rules/01`): no internal IPs `10.40.10.x`, all external URLs via ENV.
8. **Commit convention:** `feat|fix|refactor|test|docs(component): description`. Code/commits EN.
9. Report findings with evidence. Do not claim "done" without fresh verification output.

## Component map

| Component | Path | Stack | Test cmd |
|---|---|---|---|
| CLI | `nomos-cli/` | Python 3.12, Click, pytest | `uv run pytest` |
| API | `nomos-api/` | FastAPI, Pydantic v2, pytest | `uv run pytest` |
| Plugin | `nomos-plugin/` | TS strict, vitest | `npx vitest run` |
| Console | `nomos-console/` | Next.js 15, React 19, vitest | `npx vitest run` |

## Agent assignments

- **nomos-backend** — Batch A (critical bugs), Batch C (context pipeline + vault), Batch B impl (authZ wiring).
- **nomos-security** — Batch B re-audit after fixes; verify each CRITICAL/HIGH closed with a regression test.
- **nomos-qa** — Batch D (test completeness); verify every new fix has a specific-assertion test.
- **nomos-architect** — Batch C design (context pipeline wiring contract proxy↔pipeline↔memory), Batch E upgrade-risk review.

## Batch order & done-criteria

| Batch | Scope | Done when |
|---|---|---|
| A | K1 .env untrack, K4 migration chain, K5 console healthcheck, datetime.utcnow, prune honesty | all suites collect w/o 191 errors; `test_alembic` green; `.env` untracked |
| B | K2/K3 + all HIGH authZ + log redaction + CSRF/headers/HMAC/host-ports | per-fix regression test; golden path intact after docker up; security re-audit clean |
| C | wire context pipeline into proxy, persist history, real prune, fix 7 tests, vault exception | 7 context tests green; chat retains history; doc reconciled |
| D | monitoring HTTP, CORS ASGITransport, costs/approvals/fleet, weak assertions | all 4 suites green in CI; no skipped/xfail without reason |
| E | OpenClaw pin (current stable), image digests, dep upper bounds, vitest align | reproducible builds; docs match Dockerfiles |
| F | CLI logging + NOMOS_LOG_LEVEL, correlation-id egress, README/arch/api refresh, runbook | logging ENV-configurable; docs match code |
| G | docker compose up → healthy → browser golden path → F12 clean → CI green | rule-06 question answered "yes, tested" |

## Open product decision (Joe)

- Secret K1: Joe rotates the leaked `NVIDIA_API_KEY`; agents only untrack + .gitignore + history note.

## Progress log

- 2026-05-18: Assessment complete (4 agents). Scope contract accepted, full-autonomous. Batches A–G tracked in task list.
