// nomos-plugin/tests/hooks/agent-end.test.ts
import { describe, it, expect, vi } from "vitest";
import { createAgentEndHook } from "../../src/hooks/agent-end.js";
import type { NomOSApiClient } from "../../src/api-client.js";

describe("agent_end hook", () => {
  it("sends final audit entry with completed status", async () => {
    const addAuditEntry = vi.fn().mockResolvedValue({ hash: "final-hash" });
    const client = { addAuditEntry } as unknown as NomOSApiClient;

    const hook = createAgentEndHook(client);
    await hook(
      { agentId: "agent-1", metadata: { exitCode: 0 } },
      { agentId: "agent-1" },
    );

    expect(addAuditEntry).toHaveBeenCalledOnce();
    expect(addAuditEntry).toHaveBeenCalledWith({
      agent_id: "agent-1",
      event_type: "agent.ended",
      payload: { status: "completed" },
    });
  });

  it("uses agentId from event when ctx is missing", async () => {
    const addAuditEntry = vi.fn().mockResolvedValue({ hash: "hash" });
    const client = { addAuditEntry } as unknown as NomOSApiClient;

    const hook = createAgentEndHook(client);
    await hook(
      { agentId: "agent-from-event" },
      {},
    );

    expect(addAuditEntry.mock.calls[0][0].agent_id).toBe("agent-from-event");
  });

  it("does not throw when API fails", async () => {
    const addAuditEntry = vi.fn().mockRejectedValue(new Error("fail"));
    const client = { addAuditEntry } as unknown as NomOSApiClient;

    const hook = createAgentEndHook(client);
    await expect(hook(
      { agentId: "agent-1" },
      { agentId: "agent-1" },
    )).resolves.toBeUndefined();
  });
});
