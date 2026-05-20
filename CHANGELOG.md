# Changelog

All notable changes to NomOS are documented here.
Versioning follows [SemVer](https://semver.org/) per component.
Date format: ISO-8601.

---

## [0.3.0] — 2026-05-20

> **Maintenance release.** Follows the v0.2.0 5-agent post-release
> audit + the v0.2.1 security hotfix. Closes the highest-impact
> Maintenance items: audit-trail forensic anti-patterns, container
> hardening, performance quick wins, error-handling pass, and the
> test gaps the QA audit found.

Components bumped: `nomos-api 0.3.0`, `nomos-cli 0.3.0`,
`nomos-console 0.3.0`.

### M1 — Audit-Trail Anti-Pattern Fix (HIGH, audit C-F3 + C-F16)

The hourly anchor cron and the daily integrity-checkpoint cron used to
write `AUDIT_CHAIN_ANCHORED` / `AUDIT_RETENTION_CHECKPOINT` events back
INTO the chain they had just verified. That made every anchor describe a
`head_hash` that became stale one entry later, and produced reassurance
("checkpoint reported valid") that was structurally non-falsifiable.

0.3.0 separates the concerns:

- `worker/jobs/audit_anchor.py`: anchor records still go to
  `anchors.jsonl`; the chain itself is no longer written back to.
- `worker/jobs/audit_retention.py`: checkpoint outcomes go to a sibling
  `checkpoints.jsonl` (next to `anchors.jsonl` on the same WORM-ready
  volume). Configurable via new setting `audit_checkpoints_path`.
- The chain now stays a quiescent target for external verifiers; anchor
  and current head are equal at any moment with no chain activity in
  between (the v0.2.0 contract a regulator would expect).

LEARNINGS.md **L040** documents this anti-pattern.

### M2 — Performance (partial)

- **M2b: hash_chain key caching.** `_hmac_key_for` and `_signing_key_for`
  are now `functools.lru_cache(maxsize=1)`-decorated. Previously a
  100k-entry chain replay rebuilt the Ed25519 PrivateKey 100k times —
  every replay-step parsed the 32-byte seed to internal libsodium state.
  Audit C-F4. Tests still get isolation by calling `.cache_clear()` in
  a fixture.
- **M2d: `expire_approvals` SQL update.** Replaced the per-row Python
  loop with a single dialect-aware `UPDATE ... WHERE ... <= NOW()`.
  Audit C-F8.
- **M2a (cache for /compliance/matrix) and M2c (metrics-middleware
  batch)** are deferred to 0.4.0 — both require schema-level redesigns
  that don't fit a maintenance release.

### M3 — Hardening

- **M3a: `vault/init-entrypoint.sh`** writes all secret files with
  `chmod 600` instead of the previous `chmod 644`. The init-output.json
  carrying the root token was already 600 in 0.2.1; this finishes the
  pass over gateway-token, plugin-api-key, and the AppRole file. Audit
  A-#9/#10.
- **M3b: `/docs` + `/openapi.json` + `/redoc`** are no longer
  unconditionally public. New `DEV_MODE_PUBLIC_PATHS` set; in production
  (`NOMOS_DEV_MODE=false`, the default) these paths now require the
  usual cookie / api-key auth. Audit A-#15.
- **M3c: `docker-compose.yml`** every service gets
  `security_opt: ["no-new-privileges:true"]`; the stateless services
  (api, worker, console, gateway) additionally `cap_drop: [ALL]`. Caddy
  keeps only `NET_BIND_SERVICE` (needed for port 80/443). Audit
  A-#22/#23.
- **M3d: `bcrypt` upper bound tightened** `>=4.0,<6` → `>=4.2,<5`. The
  previous bound permitted a known-bad 5.x. Plus production startup
  now refuses `cors_origins` that contains `localhost` / `127.0.0.1`
  (defense-in-depth for credentialed cross-origin). Audit A-#17/#19.

### M4 — Error-Handling Pass

Closes the highest-impact items from audit D:

- `services/context_summarizer.py`: never log `exc.response.text` (could
  contain provider API keys / tenant PII echoed back). Status code +
  reason only. Plus explicit `TimeoutException` branch with retry.
  Audit D-#10.
- `database.py`: explicit `pool_size=20, max_overflow=10,
  pool_timeout=30, pool_recycle=1800`. The previous SQLAlchemy defaults
  let one slow query exhaust the pool and block indefinitely. Audit D-#15.
- `routers/health.py`: every `_check_*` failure now logs the exception
  before returning the opaque status string — Vault outage vs. config
  drift is now diagnosable from logs. Audit D-#3.
- `nomos-plugin/src/hooks/before-tool-call.ts` +
  `after-tool-call.ts`: audit-entry POSTs wrapped in `try/catch` that
  logs to the gateway console instead of silently swallowing. A
  cluster of audit-write failures is now visible. Audit D-#1/#11.
- Worker jobs (`audit_anchor`, `audit_retention`): exception logging
  now includes `agent_id` + `agents_dir` so failures are reproducible
  without re-running the cron. Audit D-#4/#5.

### M5 — Test Coverage

New `nomos-cli/tests/test_merkle_edge_cases.py` with 6 tests closing
the QA audit gaps:

- **B-F04**: STH signed with key A must NOT verify with key B.
- **B-F08**: STH on an empty tree (`tree_size == 0`) is well-defined
  and signable.
- **B-F11**: Chain written under key A must NOT verify under key B
  (key-rotation negative scenario; HMAC AND Ed25519 errors both
  surface).
- Plus 2 fail-closed regression tests for `verify_chain` when the
  signing or HMAC env vars are stripped mid-flight (regression
  guard for LEARNINGS L038).

### Verified

- nomos-cli **245 / 0 failed** (239 baseline + 6 new M5 tests).
- nomos-api full audit-related suite **79 / 0** (full chunked suite
  in CI; ad-hoc sweep clean).
- nomos-plugin **46 / 0** (vitest).
- ruff check + format + tsc clean.

### Deferred to 0.4.0

- **M2a**: `/compliance/matrix` N+1 fix — requires denormalized
  `missing_docs` column on `agents` + a write-time invalidation
  contract from hire/gate. Schema migration.
- **M2c**: `APIMetricsMiddleware` batch — requires in-memory queue +
  background-drain job. Architectural touchpoint with the existing
  ARQ worker.
- Remaining audit-D findings (15 of 20) — minor logging cleanup.
- Sigstore Rekor public anchoring (Phase-B2, opt-in).

---

## [0.2.1] — 2026-05-20

> **Security hotfix.** 5-agent post-release audit (security / QA /
> architecture / error-handling / ops) found 17 BLOCKER/CRITICAL items
> still on `v0.2.0` main. This release closes the seven worst — the
> seven router AuthZ holes plus the four audit-trail forensics gaps
> they amplified.

Bumped: `nomos-api 0.2.1`, `nomos-cli 0.2.1`, `nomos-console 0.2.1`.

### Security (CRITICAL — Router AuthZ Lockdown)

Seven state-changing routers shipped on `0.2.0` without an AuthZ
guard. Any authenticated user could touch any tenant's data. Closed:

- `routers/dsgvo.py` — `/forget` + `/export` now `require_admin`,
  audit event records the requester's email
- `routers/incidents.py` — `POST` + `PATCH` + `GET` list all
  `require_admin` (Art. 33/34 reporting integrity)
- `routers/approvals.py` — `/approve` + `/reject` `require_admin`;
  `resolved_by` no longer trustable from request body, set from
  authenticated admin's email instead
- `routers/tasks.py` — `POST` + `PATCH` enforce
  `authorize_agent_action` (owner-or-admin per target agent)
- `routers/workspace.py` — `GET` + `/mount` + `/unmount` enforce
  agent-ownership
- `routers/compliance.py` — `/agents/{id}/gate` + `/compliance/gate`
  alias both enforce agent-ownership; shared `_run_gate_for_loaded_agent`
  removes the alias's auth-bypass surface
- `routers/budget.py` + `routers/costs.py` — `/check` + `/track` +
  per-agent costs enforce ownership; cross-tenant `/costs` list is
  admin-only

New helper `nomos_api.auth.rbac.authorize_agent_action(...)` for
body-driven `agent_id` AuthZ (path-driven endpoints keep using
`require_agent_actor`).

### Security (HIGH — Audit-Trail Forensics)

- `hash_chain.verify_chain` now asserts `sequence == i` for every
  entry AND `entries[0].previous_hash == GENESIS_HASH` — closes the
  prefix-truncation attack that was undetectable even with key-
  recompute capability.
- `merkle._mth` + `merkle._path` rewritten to use `(start, end)`
  indices instead of `leaves[start:end]` slicing — same RFC 6962
  algorithm, but memory drops from O(n log n) to O(log n) per call.
  Closes the unbounded-tree DoS vector on `/audit/sth` +
  `/audit/proof/{n}`.
- `merkle.verify_inclusion_proof` no longer raises on non-hex
  `audit_path` / `root_hash` — returns `False`. The regulator-facing
  verifier API must never crash the caller on corrupt-by-design input.

### Fixed (stale code & doc references)

- `nomos-api/nomos_api/config.py:47` — `api_version = "0.1.0"` →
  `"0.2.1"`. `/health` was lying about the running version.
- `nomos-cli/nomos/cli.py:64` — `nomos --version` was printing
  `0.1.0`.
- `nomos-console/src/app/login/page.tsx:140` +
  `src/components/layout/sidebar.tsx:229` — UI was showing
  `NomOS Console v0.1.0` to every user.
- `worker/main.py:64` docstring — said "5 cron jobs", registered 7.
- `docs/architecture.md` — same, said "Five cron jobs".
- `AGENTS.md:15` + `README.md:73` — said "17 routers / 47+
  endpoints", actually 19 / 49+.
- `CLAUDE.md:3,8` — said "324+ Tests", actually 693+ (454 API + 239
  CLI).
- `docs/quickstart.md:109` + `docs/cli-reference.md:18` +
  `docs/de/cli-referenz.md:18` — version strings in user-facing
  examples.

### Fixed (Vault path consistency)

- `vault/init-entrypoint.sh` writes audit keys to
  `nomos/secrets/audit` (one KV-v2 record, two fields:
  `hashchain_hmac_key` + `audit_signing_key`).
- `docs/operations-runbook.md` previously listed THREE different,
  none-of-which-existed paths. Rotation drill would have failed
  silently. Reconciled to the single path the init script actually
  uses.

### Added (docs)

- `docs/operations-runbook.md` backup-volumes table now lists
  `nomos-anchors` as Critical (WORM in prod) — previously omitted
  even though `docker-compose.yml` shipped a separate volume for it.

### Self-reflection (`.claude/knowledge/LEARNINGS.md`)

L035–L041 added — documents the mistakes that produced this hotfix:
- L035: "AuthZ on state-change endpoints" must sweep ALL routers, not
  selectively the 3 "important" ones.
- L036: Version-bump = code + docs + UI strings, not only
  `pyproject.toml`.
- L037: Vault paths in docs must reflect what the init script writes.
- L038: `verify_chain` must check `sequence == i` AND genesis
  `previous_hash`, not only per-entry HMAC + signature.
- L039: Public-API endpoints with user-controlled `n` must be
  iterative OR rate-limited OR capped.
- L040: Anchors / integrity-checkpoints must NOT write into the
  chain they're verifying — that produces a moving-target anchor.
- L041: 5-agent post-release audit pass catches what pre-release
  tests miss; run before every tag-push.

### Verified

- nomos-cli 239 passed / 0 failed
- nomos-api Phase-B1 suite 10 passed / 0 failed
- ruff check + format clean

---

## [0.2.0] — 2026-05-20

> "Audit-Trail v2" — bring the audit trail to documented state-of-the-art
> before EU AI Act Article 12 takes effect on **2026-08-02**.

Components bumped: `nomos-api 0.2.0`, `nomos-cli 0.2.0`,
`nomos-console 0.2.0`. Plugin stays on its own track (`nomos-plugin 2.0.0`).

### Added — Audit-Trail Phase A (PR #5, #6)

- **Ed25519 per-entry signatures** alongside the existing HMAC-SHA256
  hash chain. Public-key non-repudiation; verifier no longer needs a
  shared secret. Fail-closed key handling — missing key = chain
  invalid.
- **External anchoring cron** `anchor_audit_heads` (hourly, ARQ).
  Appends `{agent_id, chain_length, head_hash, head_hmac,
  head_signature, anchored_at}` to `/data/audit-anchors/anchors.jsonl`
  on a separate volume (WORM-capable in production).
- **Periodic integrity checkpoint** `audit_integrity_checkpoint`
  (daily, ARQ). Verifies every agent's chain and writes a
  `audit.retention.checkpoint` row that itself joins the chain.
- **Retention floor** `manifest.governance.audit_retention_days`
  with code-level floor `>= 180` (Article 12 ≥6 months). Manifest
  loader rejects sub-floor values.
- **Annex IV event-category coverage**: added `AUDIT_CHAIN_ANCHORED`
  and `AUDIT_RETENTION_CHECKPOINT` event types and mapped Article 12
  / Annex IV categories to existing entry types. Mapping documented
  in `docs/compliance-guide.md`.
- **`/audit/verify` enrichment**: response now carries
  `last_anchored_at`, `last_anchored_head_hash`, and a boolean
  indicating whether the current head matches the latest anchor.
- **Operations runbook**: how to verify the chain with the public key,
  how to roll the signing key, how to export for a regulator, where
  the anchors live, WORM-storage recommendation. See
  `docs/operations-runbook.md`.

### Added — Audit-Trail Phase B1 (PR #7)

- **Embedded RFC 6962 Merkle transparency log** in
  `nomos.core.merkle`: leaf prefix `0x00`, node prefix `0x01`, Merkle
  Tree Hash (MTH), inclusion-proof PATH, signed tree heads (STH)
  signed by the same Ed25519 key.
- **API endpoint** `GET /api/agents/{id}/audit/sth` — returns
  `{origin, tree_size, root_hash, timestamp, signature}`
  (Sigstore-Rekor-style checkpoint).
- **API endpoint** `GET /api/agents/{id}/audit/proof/{sequence}` —
  returns a per-entry inclusion proof
  `{leaf_index, tree_size, root_hash, audit_path[]}`. Out-of-range
  returns 404.
- **Pure-function verifier** `verify_inclusion_proof` — recomputes
  the root from leaf + audit path; needs only the data the regulator
  was handed.
- **Anchor record** extended: `merkle_tree_size` and
  `merkle_root_hash` are now also persisted so historical proofs can
  be verified against time-stamped roots from the WORM-ready volume.

### Changed

- `nomos-api/pyproject.toml`, `nomos-cli/pyproject.toml`,
  `nomos-console/package.json`: version `0.1.0 → 0.2.0`.
- `nomos-api/pyproject.toml`, `nomos-cli/pyproject.toml`: explicit
  `cryptography>=42,<46` dep so Ed25519 is no longer transitive.
- `nomos-cli`: `[project.optional-dependencies] dev` adds
  `pytest>=8,<9` + `pytest-asyncio>=0.23,<1` so `uv run python -m
  pytest` works inside the cli venv.

### Tests

- **nomos-api**: 454 passed / 0 failed (chunked 170 + 119 + 165;
  +10 new tests in `test_audit_merkle_phase_b1.py`).
- **nomos-cli**: 239 passed / 0 failed.
- ruff + format clean.

### Deferred (explicitly)

- **Phase B2** — public Sigstore-Rekor anchoring. Opt-in only;
  off by default; would expose chain roots externally
  (data-protection trade-off).
- **NemoClaw backend** — manifest field stays as marker.
- **Hermes** — not a NomOS concern (separate product).

### References

- Roadmap: `docs/hardening-2026-05-20/PLAN.md`.
- Compliance: `docs/compliance-guide.md`.
- Ops: `docs/operations-runbook.md`.
- EU AI Act Art. 12: enforcement 2026-08-02, fines up to €15 M or 3 %.

---

## [0.1.0] — 2026-04 (pre-changelog era)

Initial production-ready release. 10/10 production-readiness verified
on a pristine `docker compose up`. Login → Hire → Compliant → Chat →
LLM responds. Auth (RBAC + state-change endpoints), 14
risk-class-dependent compliance documents, ARQ worker, TLS via Caddy,
Hire-to-Chat auto-generation, dual-mode chat proxy. 324+ compliance
tests. Pre-history captured in `Documents/nomos/.claude/CLAUDE.md`
"Aktiver Plan".
