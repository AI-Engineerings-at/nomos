// nomos-plugin/tests/hooks/after-tool-call.test.ts
import { describe, it, expect, vi } from "vitest";
import { createAfterToolCallHook } from "../../src/hooks/after-tool-call.js";
import type { NomOSApiClient } from "../../src/api-client.js";

describe("after_tool_call hook", () => {
  it("sends audit entry with tool name, params, and duration", async () => {
    const addAuditEntry = vi.fn().mockResolvedValue({ hash: "abc123" });
    const client = { addAuditEntry } as unknown as NomOSApiClient;

    const hook = createAfterToolCallHook(client);
    await hook(
      { toolName: "web_search", params: { query: "test" }, result: { data: "ok" }, durationMs: 150 },
      { agentId: "agent-1" },
    );

    expect(addAuditEntry).toHaveBeenCalledOnce();
    expect(addAuditEntry).toHaveBeenCalledWith({
      agent_id: "agent-1",
      event_type: "tool.completed",
      payload: {
        tool: "web_search",
        params_keys: ["query"],
        duration_ms: 150,
      },
    });
  });

  it("handles missing agentId gracefully", async () => {
    const addAuditEntry = vi.fn().mockResolvedValue({ hash: "abc123" });
    const client = { addAuditEntry } as unknown as NomOSApiClient;

    const hook = createAfterToolCallHook(client);
    await hook(
      { toolName: "read_file", params: {}, result: null, durationMs: 50 },
      {},
    );

    expect(addAuditEntry).toHaveBeenCalledOnce();
    expect(addAuditEntry.mock.calls[0][0].agent_id).toBe("unknown");
  });

  it("does not throw when API client fails", async () => {
    const addAuditEntry = vi.fn().mockRejectedValue(new Error("network error"));
    const client = { addAuditEntry } as unknown as NomOSApiClient;

    const hook = createAfterToolCallHook(client);
    // fire-and-forget — should not throw
    await expect(hook(
      { toolName: "bash", params: {}, result: null, durationMs: 10 },
      { agentId: "agent-1" },
    )).resolves.toBeUndefined();
  });
});
