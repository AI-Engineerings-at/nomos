// nomos-plugin/tests/hooks/session-end.test.ts
import { describe, it, expect, vi } from "vitest";
import { createSessionEndHook } from "../../src/hooks/session-end.js";
import type { NomOSApiClient } from "../../src/api-client.js";

describe("session_end hook", () => {
  it("logs session end with duration calculated from context", async () => {
    const addAuditEntry = vi.fn().mockResolvedValue({ hash: "abc" });
    const client = { addAuditEntry } as unknown as NomOSApiClient;

    const startTime = Date.now() - 5000; // 5 seconds ago
    const hook = createSessionEndHook(client);
    await hook(
      { sessionKey: "sess-123" },
      { agentId: "agent-1", sessionStartTime: startTime },
    );

    expect(addAuditEntry).toHaveBeenCalledOnce();
    const call = addAuditEntry.mock.calls[0][0];
    expect(call.agent_id).toBe("agent-1");
    expect(call.event_type).toBe("session.ended");
    expect(call.payload.session_key).toBe("sess-123");
    expect(call.payload.duration_ms).toBeGreaterThanOrEqual(4000);
  });

  it("uses zero duration when startTime is not available", async () => {
    const addAuditEntry = vi.fn().mockResolvedValue({ hash: "abc" });
    const client = { addAuditEntry } as unknown as NomOSApiClient;

    const hook = createSessionEndHook(client);
    await hook(
      { sessionKey: "sess-456" },
      { agentId: "agent-1" },
    );

    const call = addAuditEntry.mock.calls[0][0];
    expect(call.payload.duration_ms).toBe(0);
  });

  it("does not throw when API fails", async () => {
    const addAuditEntry = vi.fn().mockRejectedValue(new Error("fail"));
    const client = { addAuditEntry } as unknown as NomOSApiClient;

    const hook = createSessionEndHook(client);
    await expect(hook(
      { sessionKey: "sess-789" },
      { agentId: "agent-1" },
    )).resolves.toBeUndefined();
  });
});
