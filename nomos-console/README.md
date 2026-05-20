# nomos-console

> Next.js 15 (App Router) / React 19 dashboard for NomOS. Dark mode
> default, bilingual DE/EN, 20 pages (12 admin + 8 user), Vitest unit
> tests.

Top-level overview: [`../README.md`](../README.md).

## 1. Purpose & Boundary

The operator/user UI. Read- and operate-only — no business logic in
the console itself. Every page that mutates state delegates to
`nomos-api` via Next.js rewrites over the internal Docker network.
The console does NOT talk to PostgreSQL, OpenClaw, or LLM providers
directly.

Admin pages: dashboard, team, hire wizard, approvals, costs, audit,
compliance, diagnostics, incidents, users, tasks, settings.
User pages: dashboard, chat, tasks, help.

## 2. Prerequisites

- Node 22 (CI runs 22 only).
- npm (the repo uses `npm ci`; lockfile is `package-lock.json`).
- A running `nomos-api` on port 8060 (or wherever
  `NEXT_PUBLIC_API_URL` points).

## 3. Dev Setup

```bash
cd nomos-console
npm ci
npm run dev          # next dev --port 3040 --turbopack
# typecheck without emit (also what CI runs):
npm run typecheck    # tsc --noEmit
npm run lint         # next lint
```

Open `http://localhost:3040`. On first run, the bootstrap form
triggers `POST /api/users/bootstrap`. After that, login → /admin or
/dashboard depending on role.

## 4. Environment Variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | yes (dev) | `http://localhost:8060` | API base; rewritten in `next.config.*` for in-cluster traffic |
| `NEXT_PUBLIC_DEFAULT_LOCALE` | no | `de` | Initial language (`de`/`en`) |

In Docker the console talks to `http://nomos-api:8000` over the
compose network; the `NEXT_PUBLIC_*` vars are only used in dev or
when serving outside compose.

## 5. Tests

```bash
cd nomos-console
npx vitest run                      # full suite
npx vitest run path/to/spec.ts      # one file
npx vitest                          # watch mode
```

Component tests use Vitest + React Testing Library. Hardcoded
fixture data in the UI is forbidden (LEARNING L025) — every list
must come from the API.

## 6. Build & Ship

```bash
npm run build      # next build (production)
npm run start      # next start --port 3000 (production server)
docker compose build nomos-console
```

Version bump: `package.json` `version`. Bump together with
`nomos-api` and `nomos-cli`. The console's own version is NOT the
plugin's version (the plugin tracks `2.x` separately).

The production image runs `next start` on port 3000 internally;
compose maps to `${NOMOS_CONSOLE_PORT:-3040}` on the host. Caddy
fronts it on 80/443 in prod.

## 7. Common Gotchas

- **L025 / hardcoded lists are poison** — every fleet/agents/audit
  list must read from `/api/*`. Mock data that lives in
  `src/data/*.ts` is a code smell and will fail review.
- **Dark-mode hydration mismatch** — `<html>` must carry the
  theme class server-side; otherwise React's first client render
  flashes. Read the existing theme provider; don't add another.
- **CSRF + same-origin cookies** — login sets `SameSite=Strict`,
  `HttpOnly`, `Secure`-when-HTTPS. Local dev over plain HTTP must
  use the Next.js rewrite (`/api/...`), not direct
  `http://localhost:8060/api/...` from the browser — the latter is
  cross-origin and drops the cookie.
- **Hire-wizard 502 on Compliance step** — the wizard awaits
  `POST /api/agents/{id}/gate` which can take a few seconds; if
  the gateway is slow, increase the wizard timeout rather than
  polling. The console shows a "Compliance noch in Arbeit" banner
  until the gate returns.
- **OpenClaw plugin version drift** — if chat 502s after upgrading
  the gateway, verify `nomos-plugin/Dockerfile.gateway` still pins
  to a known-good OpenClaw version (currently `2026.5.18`).
