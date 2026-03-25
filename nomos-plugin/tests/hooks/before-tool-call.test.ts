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
