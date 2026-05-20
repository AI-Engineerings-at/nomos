# nomos-plugin

> TypeScript OpenClaw plugin. 11 hooks that intercept every step of
> the agent loop and call `nomos-api` for compliance, audit, PII,
> budget, and incident decisions.

Top-level overview: [`../README.md`](../README.md).

## 1. Purpose & Boundary

The plugin is the **only** path through which agent traffic reaches
an LLM. It enforces NomOS policy decisions at runtime by intercepting
the OpenClaw plugin lifecycle. Every hook is a thin wrapper around an
API call — the plugin contains no business logic. Verdict =
nomos-api's response.

11 hooks:

| Hook | Purpose |
|---|---|
| `gateway-start` | Plugin initialization, API connectivity probe |
| `before-agent-start` | Compliance-gate check before activation |
| `before-tool-call` | Policy enforcement before tool execution |
| `after-tool-call` | Audit entry after tool execution |
| `tool-result-persist` | Audit trail for tool results |
| `message-sending` | PII filter on outbound messages |
| `message-received` | Input validation on inbound messages |
| `session-start` | Session tracking |
| `session-end` | Session cleanup |
| `agent-end` | Agent lifecycle completion |
| `on-error` | Error reporting → incident creation |

## 2. Prerequisites

- Node 22.
- npm.
- OpenClaw 2026.5.18 (pinned in
  [`Dockerfile.gateway`](Dockerfile.gateway), never `:latest`).
- A reachable `nomos-api` on the same Docker network.
- A valid `NOMOS_PLUGIN_API_KEY` matching the server's value.

## 3. Dev Setup

```bash
cd nomos-plugin
npm ci
npm run typecheck                # tsc --noEmit
npx tsc                          # build to dist/
docker compose build openclaw-gateway   # full image with plugin baked in
```

Local dev against a running gateway:

```bash
docker compose up -d openclaw-gateway
docker compose logs -f openclaw-gateway | grep -i nomos
```

## 4. Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `NOMOS_API_URL` | yes | Where the plugin sends decisions (compose-internal `http://nomos-api:8000`) |
| `NOMOS_PLUGIN_API_KEY` | yes (≥32 chars) | `X-NomOS-API-Key` header value |
| `NOMOS_GATEWAY_TOKEN` | yes | Mutual auth: gateway → API and back |
| `OPENCLAW_API_KEY` | yes | Provider key forwarded into OpenClaw's `apiKey` field. Missing this = silent total failure (LEARNING L033) |
| `OPENCLAW_DEFAULT_MODEL` | no | Default LLM model name |

## 5. Tests

```bash
cd nomos-plugin
npx vitest run                   # full suite
npx vitest run src/hooks/        # one folder
```

Each hook ships its own fixture set. Contract tests assert the
shapes the plugin sends to nomos-api match `nomos_api/schemas.py`
(also enforced by the `contract-check` CI job).

## 6. Build & Ship

```bash
npx tsc                          # dist/
docker compose build openclaw-gateway
```

Version bump: `package.json` `version`. The plugin tracks its own
major (currently `2.x`) — independent of the API/CLI/console line
(currently `0.2.0`). Update `manifest.json` so OpenClaw recognises
the bump on hot-reload.

The published artifact is the gateway image (plugin baked in via
`Dockerfile.gateway`); there is no standalone npm publish.

## 7. Common Gotchas

- **L033: missing `OPENCLAW_API_KEY` = silent total failure** —
  OpenClaw will start, register hooks, accept chat traffic, and
  return 200s with empty bodies. Always inject the env var; the
  gateway logs the missing-key warning once at startup but does
  not refuse to start.
- **L032: `/v1/chat/completions` is an agent loop, not an LLM
  proxy** — never call it for "just send this to the model". Use
  the direct-LLM path for ad-hoc chat (nomos-api `routers/proxy.py`
  picks the right one).
- **OpenClaw version pin** — `Dockerfile.gateway` lives in THIS
  package and pins to `2026.5.18`. Never use `:latest`; the gateway
  has had breaking plugin-contract changes between minor versions
  in the past.
- **Hook ordering** — `before-agent-start` MUST run before
  `before-tool-call`; the plugin relies on `before-agent-start`
  caching the compliance verdict for subsequent tool calls in the
  same session.
- **Contract drift** — if the plugin sends a field the API doesn't
  recognise (or vice versa) the `contract-check` CI job fails. Fix
  the schema or the plugin; never silence the check.
