# Sub-Projekt A: NomOS Plugin Core — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** OpenClaw Plugin das sich beim Gateway-Start registriert, 11 Runtime Hooks ausfuehrt, und jede Agent-Aktion durch die NomOS Control Plane leitet.

**Architecture:** Das Plugin nutzt `api.on(hookName, handler, { priority })` um sich in den OpenClaw Agent Loop einzuklinken. Jeder Hook ruft die NomOS API auf (HTTP). Sequential Hooks (before_*) koennen blockieren (`{ block: true }`), parallel Hooks (after_*, session_*) sind fire-and-forget. `tool_result_persist` ist synchron.

**Tech Stack:** TypeScript strict, vitest, OpenClaw Plugin SDK (`api.on()`), fetch API

**Design Spec:** `docs/superpowers/specs/2026-03-24-nomos-v2-design.md` Sektion 4
**OpenClaw Hook Reference:** `_archive/echo-log-debris/openclaw-reference/src/plugins/types.ts`

---

## OpenClaw Hook System (verifiziert)

```
Hook Registration:
  api.on<K extends PluginHookName>(hookName, handler, { priority? })

Execution Patterns:
  SEQUENTIAL (koennen blockieren/modifizieren):
    before_agent_start  → return { systemPrompt?, prependContext? }
    before_tool_call    → return { block?, blockReason?, params? }
    message_sending     → return { cancel?, content? }

  SYNCHRONOUS (kein async!):
    tool_result_persist → return { message? }

  PARALLEL (fire-and-forget):
    gateway_start, message_received, after_tool_call,
    session_start, session_end, agent_end, message_sent

Handler Signature:
  (event: HookEvent, ctx: HookContext) => Result | void | Promise<Result | void>
```

## NomOS Hook Mapping (11 von 17 OpenClaw Hooks)

| # | NomOS Hook | OpenClaw Hook | Pattern | Was NomOS tut |
|---|-----------|---------------|---------|---------------|
| 1 | gateway_start | `gateway_start` | parallel | Fleet Sync, Health Check, Banner |
| 2 | before_agent_start | `before_agent_start` | sequential | Compliance Gate → BLOCK wenn Docs fehlen |
| 3 | before_tool_call | `before_tool_call` | sequential | Safety Gate + Budget Check + Approval Queue |
| 4 | after_tool_call | `after_tool_call` | parallel | Audit Logger → Hash Chain Entry |
| 5 | tool_result_persist | `tool_result_persist` | **synchron** | PII Filter → maskiert BEVOR es persistiert wird |
| 6 | message_received | `message_received` | parallel | Session Tracking, Kosten-Start, Honcho Message |
| 7 | message_sending | `message_sending` | sequential | Art. 50 Label einfuegen, ai_disclosure |
| 8 | session_start | `session_start` | parallel | Honcho Session erstellen/resumieren |
| 9 | session_end | `session_end` | parallel | Kosten berechnen, Summary, Dreamer triggern |
| 10 | agent_end | `agent_end` | parallel | Final Audit Entry, Compliance Status Update |
| 11 | on_error | (Custom via try/catch in Hooks) | — | Auto-Pause, Incident Detection |

**HINWEIS:** OpenClaw hat keinen expliziten `on_error` Hook. Wir implementieren Error Handling als try/catch Wrapper um JEDEN Hook-Handler. Bei kritischen Fehlern → NomOS API: POST /api/incidents.

---

## File Structure

```
nomos-plugin/
├── src/
│   ├── index.ts              # Plugin Entry: register(), Banner, alle Hooks registrieren
│   ├── api-client.ts         # HTTP Client fuer NomOS API (fetch-basiert)
│   ├── config.ts             # Plugin Config (apiUrl, agentsDir)
│   ├── types.ts              # OpenClaw Plugin SDK Types (aus v1 uebernommen + erweitert)
│   ├── error-handler.ts      # Hook Wrapper mit Error Handling → on_error Logik
│   ├── hooks/
│   │   ├── gateway-start.ts      # Fleet Sync, Health Check
│   │   ├── before-agent-start.ts # Compliance Gate Call
│   │   ├── before-tool-call.ts   # Safety + Budget + Approval
│   │   ├── after-tool-call.ts    # Audit Logger
│   │   ├── tool-result-persist.ts# PII Filter (SYNCHRON!)
│   │   ├── message-received.ts   # Session Tracking, Kosten
│   │   ├── message-sending.ts    # Art. 50 Label
│   │   ├── session-start.ts      # Honcho Session
│   │   ├── session-end.ts        # Kosten, Summary
│   │   └── agent-end.ts          # Final Audit
│   └── commands/
│       └── nomos-command.ts      # /nomos Slash Command (aus v1, erweitert)
├── tests/
│   ├── api-client.test.ts
│   ├── config.test.ts
│   ├── error-handler.test.ts
│   ├── hooks/
│   │   ├── gateway-start.test.ts
│   │   ├── before-agent-start.test.ts
│   │   ├── before-tool-call.test.ts
│   │   ├── after-tool-call.test.ts
│   │   ├── tool-result-persist.test.ts
│   │   ├── message-received.test.ts
│   │   ├── message-sending.test.ts
│   │   ├── session-start.test.ts
│   │   ├── session-end.test.ts
│   │   └── agent-end.test.ts
│   └── helpers/
│       └── mock-api.ts           # Mock NomOS API Server fuer Tests
├── openclaw.plugin.json
├── package.json
├── tsconfig.json
└── vitest.config.ts
```

---

## Task 1: Project Setup + Config + Types

**Files:**
- Create: `nomos-plugin/package.json`
- Create: `nomos-plugin/tsconfig.json`
- Create: `nomos-plugin/vitest.config.ts`
- Create: `nomos-plugin/openclaw.plugin.json`
- Create: `nomos-plugin/src/types.ts`
- Create: `nomos-plugin/src/config.ts`
- Test: `nomos-plugin/tests/config.test.ts`

- [ ] **Step 1: Initialize project**

```bash
cd nomos-plugin
npm init -y
npm install -D typescript vitest @types/node
```

- [ ] **Step 2: Write package.json**

```json
{
  "name": "nomos-plugin",
  "version": "2.0.0",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "test": "vitest run",
    "test:watch": "vitest",
    "typecheck": "tsc --noEmit"
  },
  "devDependencies": {
    "typescript": "^5.7.0",
    "vitest": "^3.0.0",
    "@types/node": "^22.0.0"
  }
}
```

- [ ] **Step 3: Write tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "declaration": true,
    "sourceMap": true,
    "skipLibCheck": true
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

- [ ] **Step 4: Write vitest.config.ts**

```typescript
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true,
    environment: "node",
  },
});
```

- [ ] **Step 5: Write types.ts**

OpenClaw Plugin SDK Types — erweitert aus v1 mit Hook-Typen:

```typescript
// nomos-plugin/src/types.ts

// === OpenClaw Plugin SDK Types ===
// Defined locally because SDK is only available inside OpenClaw host process.

export interface PluginLogger {
  info(message: string): void;
  warn(message: string): void;
  error(message: string): void;
  debug(message: string): void;
}

export interface PluginCommandContext {
  senderId?: string;
  channel: string;
  isAuthorizedSender: boolean;
  args?: string;
  commandBody: string;
  config: Record<string, unknown>;
}

export interface PluginCommandResult {
  text?: string;
}

export interface PluginCommandDefinition {
  name: string;
  description: string;
  acceptsArgs?: boolean;
  requireAuth?: boolean;
  handler: (ctx: PluginCommandContext) => PluginCommandResult | Promise<PluginCommandResult>;
}

// === Hook Event Types ===

export interface HookBeforeAgentStartEvent {
  prompt: string;
  messages?: unknown[];
}

export interface HookBeforeAgentStartResult {
  systemPrompt?: string;
  prependContext?: string;
}

export interface HookBeforeToolCallEvent {
  toolName: string;
  params: Record<string, unknown>;
}

export interface HookBeforeToolCallContext {
  agentId?: string;
  sessionKey?: string;
  toolName: string;
}

export interface HookBeforeToolCallResult {
  params?: Record<string, unknown>;
  block?: boolean;
  blockReason?: string;
}

export interface HookAfterToolCallEvent {
  toolName: string;
  params: Record<string, unknown>;
  result: unknown;
  durationMs: number;
}

export interface HookToolResultPersistEvent {
  toolName: string;
  message: { role: string; content: string };
}

export interface HookToolResultPersistResult {
  message?: { role: string; content: string };
}

export interface HookMessageEvent {
  to?: string;
  from?: string;
  content: string;
  metadata?: Record<string, unknown>;
}

export interface HookMessageSendingResult {
  cancel?: boolean;
  content?: string;
}

export interface HookSessionEvent {
  sessionKey: string;
  agentId?: string;
}

export interface HookAgentEndEvent {
  agentId?: string;
  messages?: unknown[];
  metadata?: Record<string, unknown>;
}

export interface HookGatewayEvent {
  version?: string;
}

// === Plugin API ===

export type HookHandler<E = unknown, R = void> =
  ((event: E, ctx: Record<string, unknown>) => R | void | Promise<R | void>);

export interface OpenClawPluginApi {
  id: string;
  name: string;
  version?: string;
  config: Record<string, unknown>;
  pluginConfig?: Record<string, unknown>;
  logger: PluginLogger;
  registerCommand: (command: PluginCommandDefinition) => void;
  registerCli: (registrar: unknown, opts?: { commands?: string[] }) => void;
  registerService: (service: { id: string; start: (ctx: unknown) => void; stop?: (ctx: unknown) => void }) => void;
  resolvePath: (input: string) => string;
  on: (hookName: string, handler: HookHandler, opts?: { priority?: number }) => void;
}
```

- [ ] **Step 6: Write config.ts**

```typescript
// nomos-plugin/src/config.ts
import type { OpenClawPluginApi } from "./types.js";

export interface NomOSPluginConfig {
  apiUrl: string;
  agentsDir: string;
}

const DEFAULTS: NomOSPluginConfig = {
  apiUrl: "http://nomos-api:8000",
  agentsDir: "./data/agents",
};

export function getPluginConfig(api: OpenClawPluginApi): NomOSPluginConfig {
  const raw = api.pluginConfig ?? {};
  return {
    apiUrl: typeof raw["apiUrl"] === "string" ? raw["apiUrl"] : DEFAULTS.apiUrl,
    agentsDir: typeof raw["agentsDir"] === "string" ? raw["agentsDir"] : DEFAULTS.agentsDir,
  };
}
```

- [ ] **Step 7: Write the failing test for config**

```typescript
// nomos-plugin/tests/config.test.ts
import { describe, it, expect } from "vitest";
import { getPluginConfig } from "../src/config.js";
import type { OpenClawPluginApi } from "../src/types.js";

function mockApi(pluginConfig?: Record<string, unknown>): OpenClawPluginApi {
  return {
    id: "nomos", name: "NomOS", config: {}, pluginConfig,
    logger: { info: () => {}, warn: () => {}, error: () => {}, debug: () => {} },
    registerCommand: () => {}, registerCli: () => {}, registerService: () => {},
    resolvePath: (p: string) => p, on: () => {},
  };
}

describe("getPluginConfig", () => {
  it("returns defaults when no pluginConfig", () => {
    const config = getPluginConfig(mockApi());
    expect(config.apiUrl).toBe("http://nomos-api:8000");
    expect(config.agentsDir).toBe("./data/agents");
  });

  it("uses custom apiUrl from pluginConfig", () => {
    const config = getPluginConfig(mockApi({ apiUrl: "http://custom:9000" }));
    expect(config.apiUrl).toBe("http://custom:9000");
  });

  it("ignores non-string values", () => {
    const config = getPluginConfig(mockApi({ apiUrl: 42 }));
    expect(config.apiUrl).toBe("http://nomos-api:8000");
  });
});
```

- [ ] **Step 8: Run test to verify it passes**

Run: `cd nomos-plugin && npx vitest run tests/config.test.ts`
Expected: 3 tests PASS

- [ ] **Step 9: Write openclaw.plugin.json**

```json
{
  "id": "nomos",
  "name": "NomOS",
  "version": "2.0.0",
  "description": "EU AI Act + DSGVO compliance enforcement for OpenClaw agents",
  "configSchema": {
    "type": "object",
    "properties": {
      "apiUrl": {
        "type": "string",
        "description": "NomOS API URL",
        "default": "http://nomos-api:8000"
      },
      "agentsDir": {
        "type": "string",
        "description": "Local agents directory",
        "default": "./data/agents"
      }
    },
    "additionalProperties": false
  }
}
```

- [ ] **Step 10: Commit**

```bash
git add nomos-plugin/
git commit -m "feat(plugin): project setup, types, config with tests"
```

---

## Task 2: API Client + Mock Server

**Files:**
- Create: `nomos-plugin/src/api-client.ts`
- Create: `nomos-plugin/tests/helpers/mock-api.ts`
- Test: `nomos-plugin/tests/api-client.test.ts`

- [ ] **Step 1: Write the failing test**

```typescript
// nomos-plugin/tests/api-client.test.ts
import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { NomOSApiClient } from "../src/api-client.js";
import { createMockApiServer } from "./helpers/mock-api.js";

let server: ReturnType<typeof createMockApiServer>;
let client: NomOSApiClient;

beforeAll(async () => {
  server = createMockApiServer(19876);
  await server.start();
  client = new NomOSApiClient("http://localhost:19876");
});

afterAll(async () => {
  await server.stop();
});

describe("NomOSApiClient", () => {
  it("checks compliance gate — passed", async () => {
    const result = await client.checkCompliance("agent-1");
    expect(result.passed).toBe(true);
    expect(result.missing).toEqual([]);
  });

  it("adds audit entry and returns hash", async () => {
    const result = await client.addAuditEntry({
      agent_id: "agent-1",
      event_type: "tool.called",
      payload: { tool: "web_search" },
    });
    expect(result.hash).toBeTruthy();
    expect(typeof result.hash).toBe("string");
  });

  it("filters PII from text", async () => {
    const result = await client.filterPII("Email: max@example.com");
    expect(result.filtered).not.toContain("max@example.com");
    expect(result.found.length).toBeGreaterThan(0);
  });

  it("checks budget — allowed", async () => {
    const result = await client.checkBudget("agent-1", 0.05);
    expect(result.allowed).toBe(true);
  });

  it("handles API errors gracefully", async () => {
    const badClient = new NomOSApiClient("http://localhost:1");
    const result = await badClient.checkCompliance("agent-1");
    expect(result.passed).toBe(false);
    expect(result.error).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd nomos-plugin && npx vitest run tests/api-client.test.ts`
Expected: FAIL — NomOSApiClient and createMockApiServer not defined

- [ ] **Step 3: Write mock API server**

```typescript
// nomos-plugin/tests/helpers/mock-api.ts
import { createServer, type Server, type IncomingMessage, type ServerResponse } from "node:http";

export function createMockApiServer(port: number) {
  let server: Server;

  function handler(req: IncomingMessage, res: ServerResponse) {
    let body = "";
    req.on("data", (chunk: Buffer) => { body += chunk.toString(); });
    req.on("end", () => {
      const url = req.url ?? "";
      res.setHeader("Content-Type", "application/json");

      if (url.includes("/api/compliance/gate")) {
        res.end(JSON.stringify({ passed: true, missing: [] }));
      } else if (url.includes("/api/audit/entry")) {
        res.end(JSON.stringify({ hash: "abc123def456", id: "audit-1" }));
      } else if (url.includes("/api/pii/filter")) {
        const parsed = JSON.parse(body);
        const filtered = (parsed.text as string).replace(/[\w.+-]+@[\w.-]+\.\w+/g, "[EMAIL_REDACTED]");
        const found = filtered !== parsed.text ? [{ type: "email", position: [0, 0] }] : [];
        res.end(JSON.stringify({ filtered, found }));
      } else if (url.includes("/api/budget/check")) {
        res.end(JSON.stringify({ allowed: true, remaining: 45.50 }));
      } else if (url.includes("/api/agents") && url.includes("/heartbeat")) {
        res.end(JSON.stringify({ ok: true }));
      } else if (url.includes("/api/incidents")) {
        res.end(JSON.stringify({ id: "incident-1", created: true }));
      } else {
        res.statusCode = 404;
        res.end(JSON.stringify({ error: "not found" }));
      }
    });
  }

  return {
    start: () => new Promise<void>((resolve) => {
      server = createServer(handler);
      server.listen(port, resolve);
    }),
    stop: () => new Promise<void>((resolve) => {
      server.close(() => resolve());
    }),
  };
}
```

- [ ] **Step 4: Write api-client.ts**

```typescript
// nomos-plugin/src/api-client.ts

export interface AuditEntry {
  agent_id: string;
  event_type: string;
  payload: Record<string, unknown>;
}

export interface ComplianceResult {
  passed: boolean;
  missing: string[];
  error?: string;
}

export interface PIIFilterResult {
  filtered: string;
  found: Array<{ type: string; position: number[] }>;
}

export interface BudgetResult {
  allowed: boolean;
  remaining: number;
  error?: string;
}

export interface AuditResult {
  hash: string;
  id?: string;
}

export class NomOSApiClient {
  constructor(private readonly baseUrl: string) {}

  async checkCompliance(agentId: string): Promise<ComplianceResult> {
    try {
      const res = await fetch(`${this.baseUrl}/api/compliance/gate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId }),
      });
      if (!res.ok) return { passed: false, missing: [], error: `HTTP ${res.status}` };
      return await res.json() as ComplianceResult;
    } catch (err) {
      return { passed: false, missing: [], error: String(err) };
    }
  }

  async addAuditEntry(entry: AuditEntry): Promise<AuditResult> {
    try {
      const res = await fetch(`${this.baseUrl}/api/audit/entry`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(entry),
      });
      return await res.json() as AuditResult;
    } catch {
      return { hash: "" };
    }
  }

  async filterPII(text: string): Promise<PIIFilterResult> {
    try {
      const res = await fetch(`${this.baseUrl}/api/pii/filter`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      return await res.json() as PIIFilterResult;
    } catch {
      return { filtered: text, found: [] };
    }
  }

  async checkBudget(agentId: string, estimatedCost: number): Promise<BudgetResult> {
    try {
      const res = await fetch(`${this.baseUrl}/api/budget/check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId, estimated_cost: estimatedCost }),
      });
      return await res.json() as BudgetResult;
    } catch {
      return { allowed: false, remaining: 0, error: "API unreachable" };
    }
  }

  async sendHeartbeat(agentId: string, status: Record<string, unknown>): Promise<boolean> {
    try {
      const res = await fetch(`${this.baseUrl}/api/agents/${agentId}/heartbeat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(status),
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  async reportIncident(agentId: string, description: string, severity: string): Promise<boolean> {
    try {
      const res = await fetch(`${this.baseUrl}/api/incidents`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId, description, severity }),
      });
      return res.ok;
    } catch {
      return false;
    }
  }
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd nomos-plugin && npx vitest run tests/api-client.test.ts`
Expected: 5 tests PASS

- [ ] **Step 6: Commit**

```bash
git add nomos-plugin/src/api-client.ts nomos-plugin/tests/
git commit -m "feat(plugin): API client with mock server and tests"
```

---

## Task 3: Error Handler Wrapper

**Files:**
- Create: `nomos-plugin/src/error-handler.ts`
- Test: `nomos-plugin/tests/error-handler.test.ts`

- [ ] **Step 1: Write the failing test**

```typescript
// nomos-plugin/tests/error-handler.test.ts
import { describe, it, expect, vi } from "vitest";
import { wrapHook, wrapSyncHook } from "../src/error-handler.js";
import type { NomOSApiClient } from "../src/api-client.js";

const mockClient = {
  reportIncident: vi.fn().mockResolvedValue(true),
} as unknown as NomOSApiClient;

const mockLogger = { info: vi.fn(), warn: vi.fn(), error: vi.fn(), debug: vi.fn() };

describe("wrapHook (async)", () => {
  it("passes through successful handler result", async () => {
    const handler = vi.fn().mockResolvedValue({ block: true });
    const wrapped = wrapHook("test_hook", handler, { client: mockClient, logger: mockLogger });

    const result = await wrapped({ toolName: "test" }, {});
    expect(result).toEqual({ block: true });
  });

  it("catches errors and reports incident", async () => {
    const handler = vi.fn().mockRejectedValue(new Error("boom"));
    const wrapped = wrapHook("test_hook", handler, { client: mockClient, logger: mockLogger });

    const result = await wrapped({ toolName: "test" }, {});
    expect(result).toBeUndefined();
    expect(mockLogger.error).toHaveBeenCalled();
    expect(mockClient.reportIncident).toHaveBeenCalled();
  });
});

describe("wrapSyncHook", () => {
  it("passes through successful sync result", () => {
    const handler = vi.fn().mockReturnValue({ message: { role: "tool", content: "ok" } });
    const wrapped = wrapSyncHook("persist_hook", handler, { logger: mockLogger });

    const result = wrapped({ toolName: "test", message: { role: "tool", content: "ok" } }, {});
    expect(result).toEqual({ message: { role: "tool", content: "ok" } });
  });

  it("catches sync errors and returns undefined", () => {
    const handler = vi.fn().mockImplementation(() => { throw new Error("sync boom"); });
    const wrapped = wrapSyncHook("persist_hook", handler, { logger: mockLogger });

    const result = wrapped({ toolName: "test", message: { role: "tool", content: "ok" } }, {});
    expect(result).toBeUndefined();
    expect(mockLogger.error).toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd nomos-plugin && npx vitest run tests/error-handler.test.ts`
Expected: FAIL — wrapHook and wrapSyncHook not defined

- [ ] **Step 3: Write error-handler.ts**

```typescript
// nomos-plugin/src/error-handler.ts
import type { NomOSApiClient } from "./api-client.js";
import type { PluginLogger } from "./types.js";

interface WrapOptions {
  client: NomOSApiClient;
  logger: PluginLogger;
  agentId?: string;
}

interface WrapSyncOptions {
  logger: PluginLogger;
}

export function wrapHook<E, R>(
  hookName: string,
  handler: (event: E, ctx: Record<string, unknown>) => Promise<R | void> | R | void,
  opts: WrapOptions,
): (event: E, ctx: Record<string, unknown>) => Promise<R | void> {
  return async (event, ctx) => {
    try {
      return await handler(event, ctx);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      opts.logger.error(`[NomOS] Hook "${hookName}" error: ${message}`);
      await opts.client.reportIncident(
        opts.agentId ?? (ctx["agentId"] as string) ?? "unknown",
        `Hook "${hookName}" threw: ${message}`,
        "high",
      );
      return undefined;
    }
  };
}

export function wrapSyncHook<E, R>(
  hookName: string,
  handler: (event: E, ctx: Record<string, unknown>) => R | void,
  opts: WrapSyncOptions,
): (event: E, ctx: Record<string, unknown>) => R | void {
  return (event, ctx) => {
    try {
      return handler(event, ctx);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      opts.logger.error(`[NomOS] Sync hook "${hookName}" error: ${message}`);
      return undefined;
    }
  };
}
```

- [ ] **Step 4: Run tests**

Run: `cd nomos-plugin && npx vitest run tests/error-handler.test.ts`
Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add nomos-plugin/src/error-handler.ts nomos-plugin/tests/error-handler.test.ts
git commit -m "feat(plugin): error handler wrapper for hook safety"
```

---

## Task 4–13: Individual Hook Implementations

Jeder Hook folgt dem gleichen TDD-Pattern. Der Plan definiert hier die ERSTEN DREI kritischen Hooks komplett. Die restlichen 7 folgen dem identischen Pattern — der Implementierer liest die Spec (Sektion 4) und implementiert analog.

---

## Task 4: before_agent_start — Compliance Gate

**Files:**
- Create: `nomos-plugin/src/hooks/before-agent-start.ts`
- Test: `nomos-plugin/tests/hooks/before-agent-start.test.ts`

- [ ] **Step 1: Write the failing test**

```typescript
// nomos-plugin/tests/hooks/before-agent-start.test.ts
import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { createBeforeAgentStartHook } from "../../src/hooks/before-agent-start.js";
import { NomOSApiClient } from "../../src/api-client.js";
import { createMockApiServer } from "../helpers/mock-api.js";

let server: ReturnType<typeof createMockApiServer>;
let client: NomOSApiClient;

beforeAll(async () => {
  server = createMockApiServer(19877);
  await server.start();
  client = new NomOSApiClient("http://localhost:19877");
});

afterAll(async () => { await server.stop(); });

describe("before_agent_start hook", () => {
  it("returns prependContext with compliance notice when gate passes", async () => {
    const hook = createBeforeAgentStartHook(client);
    const result = await hook(
      { prompt: "You are a helpful assistant" },
      { agentId: "agent-1" },
    );
    expect(result?.prependContext).toContain("NomOS Compliance");
  });

  it("blocks agent when compliance check fails", async () => {
    // Use a client pointing to a server that returns passed: false
    const failClient = {
      checkCompliance: async () => ({ passed: false, missing: ["DPIA", "Art. 50"] }),
    } as unknown as NomOSApiClient;

    const hook = createBeforeAgentStartHook(failClient);
    const result = await hook(
      { prompt: "You are an assistant" },
      { agentId: "agent-fail" },
    );
    // before_agent_start can't block directly — it prepends a STOP instruction
    expect(result?.prependContext).toContain("BLOCKED");
    expect(result?.prependContext).toContain("DPIA");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Write before-agent-start.ts**

```typescript
// nomos-plugin/src/hooks/before-agent-start.ts
import type { NomOSApiClient } from "../api-client.js";
import type { HookBeforeAgentStartEvent, HookBeforeAgentStartResult } from "../types.js";

export function createBeforeAgentStartHook(
  client: NomOSApiClient,
): (event: HookBeforeAgentStartEvent, ctx: Record<string, unknown>) => Promise<HookBeforeAgentStartResult | void> {
  return async (event, ctx) => {
    const agentId = (ctx["agentId"] as string) ?? "unknown";
    const result = await client.checkCompliance(agentId);

    if (!result.passed) {
      return {
        prependContext: [
          "**[NomOS] BLOCKED — Compliance Gate Failed**",
          `Agent "${agentId}" darf NICHT starten.`,
          `Fehlende Dokumente: ${result.missing.join(", ")}`,
          "Bitte vervollstaendigen Sie die Compliance-Konfiguration.",
          "STOP — fuehre KEINE Aktionen aus.",
        ].join("\n"),
      };
    }

    return {
      prependContext: [
        "**[NomOS Compliance Active]**",
        "EU AI Act + DSGVO Enforcement ist aktiv.",
        "Alle Aktionen werden protokolliert (Hash Chain).",
        "Destruktive Aktionen erfordern Genehmigung.",
      ].join("\n"),
    };
  };
}
```

- [ ] **Step 4: Run tests — expected PASS**

- [ ] **Step 5: Commit**

```bash
git add nomos-plugin/src/hooks/before-agent-start.ts nomos-plugin/tests/hooks/before-agent-start.test.ts
git commit -m "feat(plugin): before_agent_start hook — compliance gate"
```

---

## Task 5: before_tool_call — Safety Gate + Budget + Approval

**Files:**
- Create: `nomos-plugin/src/hooks/before-tool-call.ts`
- Test: `nomos-plugin/tests/hooks/before-tool-call.test.ts`

- [ ] **Step 1: Write the failing test**

```typescript
// nomos-plugin/tests/hooks/before-tool-call.test.ts
import { describe, it, expect } from "vitest";
import { createBeforeToolCallHook } from "../../src/hooks/before-tool-call.js";
import type { NomOSApiClient } from "../../src/api-client.js";

function mockClient(overrides: Partial<NomOSApiClient> = {}): NomOSApiClient {
  return {
    checkBudget: async () => ({ allowed: true, remaining: 45 }),
    addAuditEntry: async () => ({ hash: "abc" }),
    ...overrides,
  } as NomOSApiClient;
}

describe("before_tool_call hook", () => {
  it("allows safe tool calls", async () => {
    const hook = createBeforeToolCallHook(mockClient());
    const result = await hook(
      { toolName: "web_search", params: { query: "test" } },
      { agentId: "agent-1" },
    );
    expect(result?.block).toBeUndefined();
  });

  it("blocks when budget exceeded", async () => {
    const hook = createBeforeToolCallHook(
      mockClient({ checkBudget: async () => ({ allowed: false, remaining: 0 }) }),
    );
    const result = await hook(
      { toolName: "llm_call", params: {} },
      { agentId: "agent-1" },
    );
    expect(result?.block).toBe(true);
    expect(result?.blockReason).toContain("Budget");
  });

  it("blocks destructive tools without approval", async () => {
    const hook = createBeforeToolCallHook(mockClient());
    const result = await hook(
      { toolName: "file_delete", params: { path: "/data/important.txt" } },
      { agentId: "agent-1" },
    );
    expect(result?.block).toBe(true);
    expect(result?.blockReason).toContain("Approval");
  });
});
```

- [ ] **Step 2: Run test — FAIL**

- [ ] **Step 3: Write before-tool-call.ts**

```typescript
// nomos-plugin/src/hooks/before-tool-call.ts
import type { NomOSApiClient } from "../api-client.js";
import type {
  HookBeforeToolCallEvent,
  HookBeforeToolCallContext,
  HookBeforeToolCallResult,
} from "../types.js";

const DESTRUCTIVE_TOOLS = new Set([
  "file_delete", "file_write", "bash_rm", "database_drop",
  "email_send", "api_external", "data_export",
]);

export function createBeforeToolCallHook(
  client: NomOSApiClient,
): (event: HookBeforeToolCallEvent, ctx: Record<string, unknown>) => Promise<HookBeforeToolCallResult | void> {
  return async (event, ctx) => {
    const agentId = (ctx["agentId"] as string) ?? "unknown";

    // 1. Budget check
    const budget = await client.checkBudget(agentId, 0.01);
    if (!budget.allowed) {
      return {
        block: true,
        blockReason: `Budget ueberschritten (${agentId}). Remaining: EUR ${budget.remaining}. Agent wird pausiert.`,
      };
    }

    // 2. Destructive tool check — requires approval
    if (DESTRUCTIVE_TOOLS.has(event.toolName)) {
      return {
        block: true,
        blockReason: `Approval erforderlich: "${event.toolName}" ist eine kritische Aktion. Warten auf Freigabe.`,
      };
    }

    // 3. Audit entry (non-blocking)
    client.addAuditEntry({
      agent_id: agentId,
      event_type: "tool.call_allowed",
      payload: { tool: event.toolName, params_keys: Object.keys(event.params) },
    });

    return undefined;
  };
}
```

- [ ] **Step 4: Run tests — PASS**

- [ ] **Step 5: Commit**

```bash
git add nomos-plugin/src/hooks/before-tool-call.ts nomos-plugin/tests/hooks/before-tool-call.test.ts
git commit -m "feat(plugin): before_tool_call hook — safety gate, budget, approval"
```

---

## Task 6: tool_result_persist — PII Filter (SYNCHRON)

**Files:**
- Create: `nomos-plugin/src/hooks/tool-result-persist.ts`
- Test: `nomos-plugin/tests/hooks/tool-result-persist.test.ts`

- [ ] **Step 1: Write the failing test**

```typescript
// nomos-plugin/tests/hooks/tool-result-persist.test.ts
import { describe, it, expect } from "vitest";
import { createToolResultPersistHook } from "../../src/hooks/tool-result-persist.js";

describe("tool_result_persist hook (SYNC)", () => {
  const hook = createToolResultPersistHook();

  it("masks email addresses", () => {
    const result = hook(
      { toolName: "search", message: { role: "tool", content: "Contact max@example.com for info" } },
      {},
    );
    expect(result?.message.content).not.toContain("max@example.com");
    expect(result?.message.content).toContain("[EMAIL_REDACTED]");
  });

  it("masks phone numbers", () => {
    const result = hook(
      { toolName: "search", message: { role: "tool", content: "Call +43 1 234 5678" } },
      {},
    );
    expect(result?.message.content).not.toContain("+43 1 234 5678");
    expect(result?.message.content).toContain("[PHONE_REDACTED]");
  });

  it("masks IBAN", () => {
    const result = hook(
      { toolName: "search", message: { role: "tool", content: "IBAN: AT611904300234573201" } },
      {},
    );
    expect(result?.message.content).not.toContain("AT611904300234573201");
    expect(result?.message.content).toContain("[IBAN_REDACTED]");
  });

  it("returns unchanged message when no PII found", () => {
    const result = hook(
      { toolName: "search", message: { role: "tool", content: "No personal data here" } },
      {},
    );
    expect(result).toBeUndefined();
  });
});
```

- [ ] **Step 2: Run test — FAIL**

- [ ] **Step 3: Write tool-result-persist.ts**

```typescript
// nomos-plugin/src/hooks/tool-result-persist.ts
// WICHTIG: Dieser Hook ist SYNCHRON — kein async, kein Promise!
import type { HookToolResultPersistEvent, HookToolResultPersistResult } from "../types.js";

const PII_PATTERNS: Array<{ pattern: RegExp; replacement: string }> = [
  { pattern: /[\w.+-]+@[\w.-]+\.\w{2,}/g, replacement: "[EMAIL_REDACTED]" },
  { pattern: /(\+?\d{1,4}[\s.-]?)?\(?\d{1,4}\)?[\s.-]?\d{2,4}[\s.-]?\d{2,9}/g, replacement: "[PHONE_REDACTED]" },
  { pattern: /[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}/g, replacement: "[IBAN_REDACTED]" },
  { pattern: /\d{2,3}\/?\d{3,4}\/?\d{4,5}/g, replacement: "[TAX_ID_REDACTED]" },
];

export function createToolResultPersistHook(): (
  event: HookToolResultPersistEvent,
  ctx: Record<string, unknown>,
) => HookToolResultPersistResult | void {
  return (event, _ctx) => {
    let content = event.message.content;
    let modified = false;

    for (const { pattern, replacement } of PII_PATTERNS) {
      const newContent = content.replace(pattern, replacement);
      if (newContent !== content) {
        modified = true;
        content = newContent;
      }
    }

    if (!modified) return undefined;

    return {
      message: { role: event.message.role, content },
    };
  };
}
```

- [ ] **Step 4: Run tests — PASS**

- [ ] **Step 5: Commit**

```bash
git add nomos-plugin/src/hooks/tool-result-persist.ts nomos-plugin/tests/hooks/tool-result-persist.test.ts
git commit -m "feat(plugin): tool_result_persist hook — sync PII filter"
```

---

## Tasks 7–13: Remaining Hooks (Pattern identisch)

Jeder Hook folgt exakt dem gleichen Pattern wie Tasks 4-6:
1. Test schreiben (was erwartet der Hook?)
2. Test ausfuehren → FAIL
3. Hook implementieren
4. Test → PASS
5. Commit

| Task | Hook | Datei | Test-Fokus |
|------|------|-------|-----------|
| 7 | message_sending | `hooks/message-sending.ts` | Art. 50 Label eingefuegt, ai_disclosure, kann cancel |
| 8 | after_tool_call | `hooks/after-tool-call.ts` | Hash Chain Entry via API, fire-and-forget |
| 9 | message_received | `hooks/message-received.ts` | Session Tracking, Kosten-Start |
| 10 | gateway_start | `hooks/gateway-start.ts` | Fleet Sync, Health Check, Banner |
| 11 | session_start | `hooks/session-start.ts` | Honcho Session erstellen |
| 12 | session_end | `hooks/session-end.ts` | Kosten berechnen, Summary |
| 13 | agent_end | `hooks/agent-end.ts` | Final Audit Entry |

**Fuer jeden Hook gilt:**
- Mindestens 3 Tests (Happy Path, Error Case, Edge Case)
- Handler bekommt `(event, ctx)`, gibt Result oder void zurueck
- Async Hooks: `createXxxHook(client)` Factory Pattern
- Alle Hooks sind in `error-handler.ts` gewrapped

---

## Task 14: Plugin Entry Point — index.ts

**Files:**
- Create: `nomos-plugin/src/index.ts`

- [ ] **Step 1: Write index.ts**

```typescript
// nomos-plugin/src/index.ts
import type { OpenClawPluginApi } from "./types.js";
import { getPluginConfig } from "./config.js";
import { NomOSApiClient } from "./api-client.js";
import { wrapHook, wrapSyncHook } from "./error-handler.js";
import { createBeforeAgentStartHook } from "./hooks/before-agent-start.js";
import { createBeforeToolCallHook } from "./hooks/before-tool-call.js";
import { createToolResultPersistHook } from "./hooks/tool-result-persist.js";
import { createMessageSendingHook } from "./hooks/message-sending.js";
import { createAfterToolCallHook } from "./hooks/after-tool-call.js";
import { createMessageReceivedHook } from "./hooks/message-received.js";
import { createGatewayStartHook } from "./hooks/gateway-start.js";
import { createSessionStartHook } from "./hooks/session-start.js";
import { createSessionEndHook } from "./hooks/session-end.js";
import { createAgentEndHook } from "./hooks/agent-end.js";

export default function register(api: OpenClawPluginApi): void {
  const config = getPluginConfig(api);
  const client = new NomOSApiClient(config.apiUrl);
  const logger = api.logger;
  const wrapOpts = { client, logger };

  // Sequential hooks (can block/modify) — HIGH PRIORITY
  api.on("before_agent_start",
    wrapHook("before_agent_start", createBeforeAgentStartHook(client), wrapOpts),
    { priority: 100 });

  api.on("before_tool_call",
    wrapHook("before_tool_call", createBeforeToolCallHook(client), wrapOpts),
    { priority: 100 });

  api.on("message_sending",
    wrapHook("message_sending", createMessageSendingHook(client), wrapOpts),
    { priority: 100 });

  // Synchronous hook (NO async!)
  api.on("tool_result_persist",
    wrapSyncHook("tool_result_persist", createToolResultPersistHook(), { logger }),
    { priority: 100 });

  // Parallel hooks (fire-and-forget)
  api.on("gateway_start",
    wrapHook("gateway_start", createGatewayStartHook(client, config), wrapOpts));

  api.on("after_tool_call",
    wrapHook("after_tool_call", createAfterToolCallHook(client), wrapOpts));

  api.on("message_received",
    wrapHook("message_received", createMessageReceivedHook(client), wrapOpts));

  api.on("session_start",
    wrapHook("session_start", createSessionStartHook(client), wrapOpts));

  api.on("session_end",
    wrapHook("session_end", createSessionEndHook(client), wrapOpts));

  api.on("agent_end",
    wrapHook("agent_end", createAgentEndHook(client), wrapOpts));

  // Banner
  logger.info("");
  logger.info("  ┌──────────────────────────────────────────────────────────┐");
  logger.info("  │  NomOS v2 — EU AI Act + DSGVO Compliance Active          │");
  logger.info("  │                                                          │");
  logger.info(`  │  API:     ${config.apiUrl.padEnd(47)}│`);
  logger.info("  │  Hooks:   11 registered (compliance, audit, PII, budget) │");
  logger.info("  │  License: FCL — 3 agents free, full functionality        │");
  logger.info("  └──────────────────────────────────────────────────────────┘");
  logger.info("");
}
```

- [ ] **Step 2: TypeScript compile check**

Run: `cd nomos-plugin && npx tsc --noEmit`
Expected: No errors (once all hook files exist)

- [ ] **Step 3: Commit**

```bash
git add nomos-plugin/src/index.ts
git commit -m "feat(plugin): index.ts — registers all 11 hooks with error handling"
```

---

## Task 15: Full Test Suite Run + Final Commit

- [ ] **Step 1: Run all tests**

Run: `cd nomos-plugin && npx vitest run`
Expected: All tests PASS (30+ tests)

- [ ] **Step 2: TypeScript strict check**

Run: `cd nomos-plugin && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Build**

Run: `cd nomos-plugin && npx tsc`
Expected: `dist/` directory created with compiled JS

- [ ] **Step 4: Final commit**

```bash
git add nomos-plugin/
git commit -m "feat(plugin): NomOS v2 plugin complete — 11 hooks, full test suite"
```

---

## Erfolgs-Kriterien (Checklist)

- [ ] 11 Hooks registriert und ausfuehrbar
- [ ] Jeder Hook hat mindestens 3 Tests
- [ ] Compliance Gate blockt Agent ohne Docs
- [ ] Art. 50 Label wird in jede Antwort eingefuegt
- [ ] PII wird SYNCHRON vor Persistierung maskiert (Email, Telefon, IBAN)
- [ ] Budget-Ueberschreitung → Tool-Call blockiert
- [ ] Destruktive Tools → Approval erforderlich
- [ ] Error Handler wrapped jeden Hook (kein unbehandelter Crash)
- [ ] TypeScript strict compile: 0 Errors
- [ ] Alle Tests gruen
- [ ] Plugin laesst sich bauen (`tsc` → `dist/`)
