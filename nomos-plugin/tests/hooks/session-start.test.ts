// nomos-plugin/tests/hooks/session-start.test.ts
import { describe, it, expect, vi } from "vitest";
import { createSessionStartHook } from "../../src/hooks/session-start.js";
import type { NomOSApiClient } from "../../src/api-client.js";

describe("session_start hook", () => {
  it("logs session start event via audit entry", async () => {
    const addAuditEntry = vi.fn().mockResolvedValue({ hash: "abc" });
    const client = { addAuditEntry } as unknown as NomOSApiClient;

    const hook = createSessionStartHook(client);
    await hook(
      { sessionKey: "sess-123", agentId: "agent-1" },
      { agentId: "agent-1" },
    );

    expect(addAuditEntry).toHaveBeenCalledOnce();
    expect(addAuditEntry).toHaveBeenCalledWith({
      agent_id: "agent-1",
      event_type: "session.started",
      payload: { session_key: "sess-123" },
    });
  });

  it("uses agentId from event when ctx is missing", async () => {
    const addAuditEntry = vi.fn().mockResolvedValue({ hash: "abc" });
    const client = { addAuditEntry } as unknown as NomOSApiClient;

    const hook = createSessionStartHook(client);
    await hook(
      { sessionKey: "sess-456", agentId: "agent-2" },
      {},
    );

    expect(addAuditEntry.mock.calls[0][0].agent_id).toBe("agent-2");
  });

  it("does not throw when API fails", async () => {
    const addAuditEntry = vi.fn().mockRejectedValue(new Error("fail"));
    const client = { addAuditEntry } as unknown as NomOSApiClient;

    const hook = createSessionStartHook(client);
    await expect(hook(
      { sessionKey: "sess-789" },
      { agentId: "agent-1" },
    )).resolves.toBeUndefined();
  });
});
