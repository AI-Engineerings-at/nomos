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
- 2026-05-18: Batch A committed (3da9994) — migration chain, duplicate-index DDL, console healthcheck, datetime, docstrings. Verified: test_alembic 11/11; 191 index setup-errors eliminated.
- 2026-05-18: K1 (".env tracked secret") found to be a FALSE POSITIVE — .env is gitignored, never committed, never in history. No leak; no rotation needed.
- 2026-05-19: Test-infra foundation (commit f039c8f). Decision (Joe): real services in CI. Wired Valkey via NOMOS_VALKEY_URL + autouse rate-limiter isolation fixture. Fixed prod bug in APIMetricsMiddleware (request→500 on metrics failure + session leak via `anext(get_db())`) → now uses `async_session()` and is non-fatal. Removed stale dead code in auth_router test fixture. Added Valkey+Postgres service containers to CI test-api job.
- 2026-05-19: TRUE baseline established — nomos-cli 204/204, nomos-api **332/341** (50s; was 162-failed/13min/CI-red). The 9 residual failures map cleanly to Batch C: context_pipeline (~3), vault graceful-degradation (1), monitoring service (1), + others in same families.
- 2026-05-19: Batch B C1 done (commit a64ba87) — public Vault unseal-key endpoint closed: in-memory one-shot flag → DB-derived setup-complete gate (403) + persistent filesystem one-shot marker (410). 8/8 system tests green incl. new 403 regression test.
- 2026-05-19: Batch E done (NOT committed — left in working tree). (1) OpenClaw pin: `Dockerfile.gateway:1` `:latest`→`2026.5.18` (researched: GitHub releases/latest=v2026.5.18 dated 2026-05-18, ghcr manifest HTTP 200 verified; doc claimed v2026.3.28 but Dockerfile was `:latest`). (2) Base-image digest pins: `nomos-api/Dockerfile` python:3.12-slim@sha256:401f6e1a…, `nomos-console/Dockerfile` node:22-alpine@sha256:968df39a… (×3 stages); no version change. (3) Python upper bounds added to `nomos-cli/pyproject.toml` + `nomos-api/pyproject.toml` (incl. dev). (4) vitest aligned `nomos-plugin/package.json` ^3→^4.1.2 (matches console). (5) Docs reconciled: `docs/references/openclaw-nemoclaw-reference.md` + `.claude/CLAUDE.md`. nomos-cli/Dockerfile & nomos-plugin/Dockerfile do NOT exist (skipped). FOLLOW-UP (orchestrator, isolated): `uv lock` in nomos-cli + nomos-api; `npm install` in nomos-plugin (+ rebuild images for digest pins).

- 2026-05-19: Batch B committed (2c03326) — K3 dev_mode/secret hard-gate, H1 monitoring admin RBAC, H2/H3 proxy+heartbeat authZ/IDOR, H4 settings auth, H5 log redaction, M1 SameSite=strict, M3 hash-chain HMAC, M4 vault/valkey de-exposed, L2 security-headers middleware. Backstop full run (bwf6cfgua) independently confirmed 379/9.
- 2026-05-19: Batch C committed (a4792c4) — context pipeline wired into chat, real prune, vault VaultError re-raise, metrics NULL-PK fix, context tests repaired. Independently verified: full nomos-api **388 passed / 0 failed**; nomos-cli 209.
- 2026-05-19: Batch E committed (7d69290) — OpenClaw `:latest`→`2026.5.18`, base-image digest pins, dep upper bounds (uv.lock regenerated both projects, resolve clean), vitest ^4 (plugin 46/46 green), docs reconciled.
- 2026-05-19: Batch F committed (596af9b + 46fd3d3) — CLI JSON logging + NOMOS_LOG_LEVEL (nomos-cli 229), docs refreshed (architecture/api-reference/quickstart/README + new operations-runbook), X-Request-ID propagated to LLM/gateway egress (proxy 10/10).
- 2026-05-19: Batch D in progress (nomos-qa). **Found a CRITICAL product bug** (agent correctly stopped, did not paper over): all 5 monitoring alert/alert-rule endpoints returned HTTP 500 at runtime — `AlertResponse`/`AlertRuleResponse` lacked `from_attributes=True` for `.from_orm()`. Orchestrator fixed: added `model_config={"from_attributes": True}` + switched 5 sites to `.model_validate()` (Pydantic-v2 idiom). Why the 388/0 missed it: only the service layer + authZ (401/403 before from_orm) were tested — no HTTP functional coverage. Batch D now adding that coverage + deterministically fixing flaky `test_login_rate_limited`.
- 2026-05-19: All committed work pushed (origin up to 46fd3d3).

- 2026-05-19: Batch D committed (ce3dae2) + pushed. Verified chunked (10-min CI cap): nomos-api **417 passed / 0 failed** across all 62 files; nomos-cli 229; ruff check + ruff format --check + S9 grep all clean. 2nd product bug found+fixed: **rate-limiter burst-bypass** (ZADD `str(now)` member collision → undercount → security hole) → unique `f"{now}:{uuid4}"` member. Also: repo-wide `ruff format` (48 files) + S9 comment rewords → CI lint-python + quality-gate now actually pass.
- 2026-05-19: Batch G executed. `docker compose build` (BUILD_EXIT=0; OpenClaw **2026.5.18** image builds+runs healthy; python/node digest pins pull correctly) → stack all-healthy (api/worker/gateway/postgres/valkey/vault; vault-init one-shot exits clean). **3rd real bug found via integration (rule 06: "3 audits < 1 integration run")**: `nomos-console/package.json` `start` ran `next start --port 3040` while Dockerfile(PORT=3000/EXPOSE 3000)+compose(`3040:3000`)+healthcheck all expect 3000 → console unhealthy + host:3040 dead. The original Batch-A K5 fix had trusted an audit agent's unverified "container=3000" claim; the real running stack exposed the truth. Fixed `start` → `next start --port 3000`. Pristine re-verification (`down -v` = customer first deploy) in flight.

- 2026-05-19: Batch G chat-500 ROOT-CAUSED & FIXED (no guess — reproduced in-container with full traceback). Cause: **model↔migration drift** — `AgentMemory.importance_score` exists in the model (so create_all-based unit tests had it) but **no migration created it**, so on real Postgres every context-pipeline write (every chat turn, after Batch C wired it into proxy_chat) failed `UndefinedColumnError` → HTTP 500. Fix: migration `003_agent_memory_importance_score` (NOT NULL, server_default 1.0). Also fixed the enabling observability defect: `nomos-api/Dockerfile` lacked `PYTHONUNBUFFERED=1` + uvicorn's dictConfig wiped the app's JSON root handler → runtime logs invisible in `docker logs`; added `PYTHONUNBUFFERED=1` + `configure_logging()` (re-applied in lifespan, routes uvicorn loggers through JSONFormatter, honors NOMOS_LOG_LEVEL). New regression test `test_all_model_columns_covered_by_migrations` guards the entire drift class. The OpenClaw 2026.5.18 pin-back hypothesis was correctly NOT acted on — evidence showed it was unrelated; gateway answers fine.
- 2026-05-19: **Pristine golden path GREEN end-to-end**: `docker compose up` (all 7 services healthy, OpenClaw 2026.5.18) → system/status → bootstrap 201 → login 200 → hire 201 (compliance_status=passed) → **chat HTTP 200 with a real response in ~16s**. Rule-06 acceptance ("can a customer docker compose up, log in, hire an agent, and chat?") = YES, tested at API/integration level.

### Final state
9/10 batches + all CI-blockers committed & pushed (origin `ce3dae2` + console fix pending with G finalization). Three real production bugs the original audit missed were found by the added test/integration coverage and fixed with no workarounds: (1) monitoring API total 500, (2) rate-limiter burst bypass, (3) console port/healthcheck mismatch. Honest scope note: a literal GUI browser + F12-console pass is not automatable in this environment; Batch G verifies the equivalent **API-level end-to-end golden path against the real Docker stack** (rule 02/06 "real services") on a pristine deploy — the visual/F12 check is the single residual requiring human eyes and is not claimed.
