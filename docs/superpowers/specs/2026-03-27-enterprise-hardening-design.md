# NomOS Enterprise Hardening — Design Spec

> **Status:** Approved by @hq on 2026-03-27
> **Scope:** Security Hardening + Feature Completion + Enterprise Test Suite
> **Trigger:** GSD Audit identified 19 findings (4 CRITICAL, 5 HIGH) — plain ENV secrets, in-memory rate limiter, hardcoded CORS, MVP framing throughout docs

---

## Context

Two independent audits (2026-03-27) plus a GSD security audit confirmed:
- NomOS is an **Enterprise product** with 3 deployment tiers (Enterprise VPS, Docker Self-Hosted, Open-Source)
- The codebase was built with "standalone MVP" assumptions that contaminated security, config, and documentation
- All 25+ contract mismatches were fixed in the stabilization sprint — but the security foundation was never addressed

**This spec addresses the security foundation and completes the remaining feature gaps.**

---

## Architecture Decisions

### AD-1: HashiCorp Vault is the Secret Management layer
- Vault runs as a Docker service in the Compose stack
- `pydantic-settings` `settings_customise_sources()` is the integration hook
- Priority: Vault → ENV → .env (Vault wins when available)
- AppRole auth for service-to-service (nomos-api → Vault)
- KV v2 engine at `nomos/` path — built-in versioning for rollback
- **Unsealing strategy:** Vault runs in `-dev` mode for local development (auto-unseal). For production, `vault/config/vault.hcl` configures file-based auto-unseal with keys stored in a Docker named volume (`nomos-vault-keys`). `vault/init.sh` handles first-run init + unseal, subsequent starts auto-unseal from stored keys.
- **Vault unavailable at runtime:** nomos-api caches last-known config in memory on startup. If Vault goes down mid-operation, reads use cache (with WARNING log), writes (PATCH /settings) fail with 503. Health endpoint reports `vault: degraded`.
- **Vault policy (least privilege):** nomos-api AppRole gets: `path "nomos/data/*" { capabilities = ["create", "read", "update", "delete", "list"] }` and `path "nomos/metadata/*" { capabilities = ["read", "list"] }` — nothing else.

### AD-1b: Managed Secrets Inventory

| Secret | Vault Path | Read By | Written By |
|--------|-----------|---------|------------|
| JWT Secret | `nomos/secrets/jwt_secret` | nomos-api | Vault init only |
| Plugin API Key | `nomos/secrets/plugin_api_key` | nomos-api | Vault init only |
| Gateway Token | `nomos/secrets/gateway_token` | nomos-api, openclaw-gateway | Vault init only |
| DB Password | `nomos/secrets/db_password` | nomos-api | Vault init only |
| OpenAI API Key | `nomos/secrets/openai_api_key` | openclaw-gateway (via API) | Admin via Settings UI |
| Anthropic API Key | `nomos/secrets/anthropic_api_key` | openclaw-gateway (via API) | Admin via Settings UI |
| NVIDIA API Key | `nomos/secrets/nvidia_api_key` | openclaw-gateway (via API) | Admin via Settings UI |
| Gateway URL | `nomos/config/gateway_url` | nomos-api | Admin via Settings UI |
| Retention Days | `nomos/config/retention_days` | nomos-api | Admin via Settings UI |
| PII Filter Mode | `nomos/config/pii_filter_mode` | nomos-api | Admin via Settings UI |

### AD-2: No insecure defaults ship
- `config.py` validates at startup: if jwt_secret/plugin_api_key/gateway_token/db_password match known dev defaults → `SystemExit` with clear error message
- `docker-compose.yml` uses `${VAR:?Error}` syntax for ALL secrets including `NOMOS_DB_PASSWORD` — container refuses to start without required secrets
- `config/openclaw.json` is templated via `envsubst` or Vault agent
- `.env.example` contains placeholder values like `CHANGE_ME_REQUIRED` — never functional defaults

### AD-3: Rate Limiter uses Valkey (distributed, persistent)
- Valkey is already in the stack, currently unused for rate limiting
- Rate limiter state persists across restarts
- Works correctly with multiple API replicas

### AD-4: CORS is configurable via ENV
- `NOMOS_CORS_ORIGINS` as comma-separated list of allowed origins
- The hardcoded `allow_origin_regex=r"^http://localhost(:\d+)?$"` in `main.py` is **removed entirely**
- `NOMOS_DEV_MODE=true` is the ONLY way localhost gets into allowed origins — it appends `http://localhost:*` to the configured origins list
- Production default: Only explicitly configured origins are allowed

### AD-5: Settings are stored in Vault, editable via UI
- `PATCH /api/settings` writes to Vault KV v2
- Admin-only, every change audit-logged
- Config values shown in cleartext, secret values masked (`sk-...***`)
- CEO workflow: Login → Settings → Paste API Key → Save → Done

### AD-6: Contract enforcement is automated in CI
- Python script exports Pydantic JSON Schema
- TypeScript script parses types.ts via ts-morph
- CI step compares field-by-field, fails build on mismatch
- Naming map handles intentional renames (AgentResponse → Agent)

---

## Phases

### Phase 0: Security Hardening (BLOCKER)

**P0.1 — Vault Integration + Secret Hardening**
- Add `hashicorp/vault:1.15` to `docker-compose.yml` with health check
- Add `hvac` + `valkey[asyncio]` to nomos-api dependencies
- Create `nomos_api/vault_source.py` — custom pydantic-settings source
- Create `nomos_api/vault_client.py` — SecretClient singleton (get/put/list/delete) with in-memory cache fallback
- Create `vault/config/vault.hcl` — production config with file-based auto-unseal
- Create `vault/policies/nomos-api.hcl` — least-privilege policy (read/write `nomos/data/*` only)
- Modify `config.py` — add `settings_customise_sources()` with VaultSettingsSource
- Add startup validation — abort on known insecure defaults (jwt_secret, plugin_api_key, gateway_token, **db_password**)
- Create `vault/init.sh` — idempotent bootstrap (KV engine, AppRole, policies, initial secrets)
- Replace ALL `${VAR:-fallback}` with `${VAR:?Required}` in **both** `docker-compose.yml` and `nomos-api/docker-compose.yml`
- Template `config/openclaw.json` — no hardcoded tokens, use `${NOMOS_GATEWAY_TOKEN}`
- Create `.env.example` with `CHANGE_ME_REQUIRED` placeholders — never functional defaults
- Create `.env.vault` example for Vault bootstrap credentials

**P0.2 — Rate Limiter → Valkey Migration**
- Rewrite `auth/rate_limiter.py` to use Valkey (async Redis client)
- Use sorted sets for sliding window rate limiting
- Rate limit state persists across restarts, shared across instances
- Fix `nomos-api/docker-compose.yml` — replace `redis:8-alpine` with `valkey/valkey:8-alpine`

**P0.3 — Startup Validation + CORS + Docker Hardening**
- CORS: **Remove** the hardcoded `allow_origin_regex` line from `main.py` entirely
- CORS: Use only `NOMOS_CORS_ORIGINS` (comma-separated list)
- Add `NOMOS_DEV_MODE` flag — only in dev mode is localhost auto-appended to origins
- Startup check: Validate all required secrets are set and non-default
- Health endpoint: Include Vault connectivity status (`healthy`, `degraded`, `unavailable`)
- Fix `nomos-api/docker-compose.yml`: Replace `redis:8-alpine` (SSPL) with `valkey/valkey:8-alpine` (BSD-3)

**Ralph-Loop #1:** nomos-security Red Team scan after Phase 0. Loop until 0 findings.

---

### Phase 1: Backend Completion

**P1.1 — Budget-Hook Fix**
- `nomos-plugin/src/api-client.ts`: Add `res.ok` guard to `checkBudget()` (same pattern as `checkCompliance()`)
- `nomos-plugin/src/hooks/before-tool-call.ts`: Handle `budget.error` field, don't block on API errors
- `nomos-api/nomos_api/routers/budget.py`: Return **restrictive** default for unknown agents (`{ allowed: false, remaining: 0, reason: "unknown_agent" }`) — fail-closed, not fail-open. A compliance product does not permit unregistered agents to bypass budget controls.
- `before-tool-call.ts`: When budget returns `reason: "unknown_agent"`, log warning and skip (agent registration is the fix, not silent permission)

**P1.2 — Settings PATCH with Vault**
- Move `SystemSettingsResponse` from `routers/settings.py` to `schemas.py`
- Create `SettingsUpdateRequest` schema with all editable fields
- Add `PATCH /api/settings` endpoint — writes to Vault, admin-only, audit-logged
- Add LLM key fields: `openai_api_key`, `anthropic_api_key`, `nvidia_api_key`
- Sensitive keys stored/retrieved masked
- Console Settings page: Remove "read-only" notice, add edit forms with masked key inputs
- Console Settings page: Save button with admin password confirmation for key changes

**P1.3 — Contract Tests CI Guard**
- Create `scripts/export-schemas.py` — exports ALL Pydantic schemas (Request AND Response) as JSON Schema
- Create `scripts/check-contracts.ts` — parses types.ts with ts-morph, compares against JSON Schema
- Create `scripts/contract-naming-map.json` — maps intentional name differences (e.g. AgentResponse → Agent)
- Add CI step in `.github/workflows/ci.yml` — runs both scripts, fails on mismatch
- Add `test-console` to quality-gate `needs` array (currently missing — console failures silently pass)

**P1.4 — Docs/Framing Cleanup**
- `.claude/CLAUDE.md`: Remove "Standalone Docker-Produkt", add Enterprise tier description
- `docs/architecture.md`: Replace ENV-as-security-control with Vault architecture
- `docs/architecture.md`: Remove `nomos` as documented DB password default
- `docs/references/openclaw-nemoclaw-reference.md`: Remove "NomOS v2 MVP" framing
- `docs/superpowers/plans/2026-03-24-nomos-v2-master-plan.md`: "Console MVP" → "Console v1"
- All docs: "spaeter Valkey" → done (rate limiter migrated)
- `nomos-console/src/lib/i18n/en.ts` + `de.ts`: Remove "Read-only view" string
- `.claude/agents/nomos-security.md`: Add Vault guidance, remove ENV-as-final-solution

**Ralph-Loop #2:** CI green, contract tests pass, all endpoints correct, docs aligned.

---

### Phase 2: Frontend Quality + Enterprise Test Suite

**P2.1 — Vitest Setup + Full Page Coverage**
- Install: `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom`
- Create `vitest.config.ts` with jsdom environment
- Create `src/test-utils.tsx` — render wrapper with AuthProvider mock, Zustand store reset
- Add `test` script to `package.json`
- **Mandatory pages (compliance-critical, must be tested first):**
  - Login page (auth flow entry point)
  - Admin Dashboard (primary operator view)
  - Compliance page (EU AI Act compliance gate)
  - Audit page (audit trail — regulatory requirement)
  - Settings page (secret management UI)
  - Chat page (core product functionality)
- **All other pages:** Test every page (20 total) with 4 states each: loading, error, empty, data
- Every page component has at least 4 test cases covering loading, error, empty, and populated states
- Test all hooks: `useFetch`, `useAuth`
- Test all utils: `formatDate`, `formatEur`, `getGreetingKey`, `agentStatusToBadge`
- Test form validation: Login, Hire, Tasks, Users, Settings
- Test UI interactions: Theme toggle, sidebar collapse, toast notifications
- Test auth guards: Redirect to /login when not authenticated

**P2.2 — E2E Enterprise Suite (Playwright)**
- Update `playwright.config.ts`: Add CI config, retries, reporters, screenshot on failure
- Auth setup: `auth.setup.ts` — login once, store session, reuse across tests
- **Happy Path Suite:**
  - Login (email + password) → Admin Dashboard loads
  - Navigate to Team → Agents visible
  - Hire Agent → Wizard completes
  - Open Chat → Send message → LLM responds (or mock gateway response)
  - Check Audit → New entries appear
  - Settings → Change a config value → Saved
  - Logout → Redirected to login
- **Error Case Suite:**
  - Wrong password → Error message shown
  - 2FA required → TOTP form appears
  - Budget exceeded → Agent blocked message
  - Agent paused → Cannot chat
  - Session expired → Redirect to login
  - API down → Error state shown on all pages
- **Multi-User Suite:**
  - Admin: Full access to all admin pages
  - User: Access to /app/* only, no /admin/*
  - Officer: Compliance-specific access
- **Full Page Sweep:**
  - Visit every one of 20 pages
  - Assert: No console errors, page loads, correct heading/title
  - Assert: Responsive (mobile viewport)
  - Assert: a11y basics (lang attribute, alt texts, keyboard nav)

**Ralph-Loop #3:** All vitest green, all Playwright green, 0 console errors in browser.

---

### Phase 3: Final Validation

**Ralph-Loop #4 (Final):**
- CI Pipeline: ALL jobs green (lint, test-cli, test-api, test-plugin, test-console, contract-check, quality-gate, docker-build)
- nomos-security: Full Red Team re-scan — 0 CRITICAL, 0 HIGH
- nomos-qa: Test coverage report — all pages covered
- Playwright: Full Enterprise Suite passes
- Browser walkthrough: Screenshots of every page saved as artifacts
- GSD: Final report generated

---

## Success Criteria

1. `docker compose up -d` starts ALL services including Vault — healthy within 60s
2. NO insecure defaults active — app refuses to start with dev secrets
3. CEO can login, go to Settings, paste an OpenAI API key, save it — key stored in Vault
4. Rate limiter persists across API restarts
5. CORS allows configured customer domains
6. CI breaks on schema drift between schemas.py and types.ts
7. Every page component (20 total) has at least 4 test cases covering loading, error, empty, and populated states
8. E2E suite covers login → hire → chat → audit → settings → logout
9. E2E suite covers wrong password, 2FA, budget exceeded, session expired
10. 0 CRITICAL, 0 HIGH findings in final security scan. MEDIUM findings documented with accepted-risk rationale.
11. All documentation says "Enterprise", zero "MVP" references
12. **Explicit dependency:** P1.2 (Settings PATCH) requires P0.1 (Vault) to be complete and stable

---

## Non-Goals (explicitly excluded)

- Multi-tier secret backend abstraction (Vault only — YAGNI for now)
- Vault HA/clustering (single instance sufficient for first enterprise release)
- Automated key rotation (manual rotation via Settings UI is sufficient — operational playbook: Admin changes key in Settings → Vault stores new version → openclaw-gateway picks up via next API call → no restart needed for LLM keys; JWT/gateway_token rotation requires rolling restart documented in ops guide)
- Kubernetes deployment (Docker Compose is the deployment target)
- Performance testing / load testing
- Mobile-native UI testing

## Ralph-Loop Methodology

Each Ralph-Loop uses `/ralph-loop` with:
- **Loop #1 (Security):** nomos-security agent scans for hardcoded secrets, default credentials, auth bypass, injection, CORS misconfiguration. Completion promise: "SECURITY_CLEAN"
- **Loop #2 (Backend):** nomos-qa agent runs CI pipeline, contract tests, endpoint validation. Completion promise: "BACKEND_CLEAN"
- **Loop #3 (Frontend):** console-dev agent runs vitest + Playwright, checks console errors. Completion promise: "FRONTEND_CLEAN"
- **Loop #4 (Final):** All agents. Full CI + security scan + browser walkthrough. Completion promise: "ENTERPRISE_READY"

---

*Approved by @hq — 2026-03-27*
