// nomos-plugin/tests/hooks/message-received.test.ts
import { describe, it, expect, vi } from "vitest";
import { createMessageReceivedHook } from "../../src/hooks/message-received.js";
import type { NomOSApiClient } from "../../src/api-client.js";

describe("message_received hook", () => {
  it("sends heartbeat with active status", async () => {
    const sendHeartbeat = vi.fn().mockResolvedValue(true);
    const client = { sendHeartbeat } as unknown as NomOSApiClient;

    const hook = createMessageReceivedHook(client);
    await hook(
      { content: "Hello", from: "user" },
      { agentId: "agent-1" },
    );

    expect(sendHeartbeat).toHaveBeenCalledOnce();
    expect(sendHeartbeat).toHaveBeenCalledWith("agent-1", { status: "active", event: "message_received" });
  });

  it("handles missing agentId gracefully", async () => {
    const sendHeartbeat = vi.fn().mockResolvedValue(true);
    const client = { sendHeartbeat } as unknown as NomOSApiClient;

    const hook = createMessageReceivedHook(client);
    await hook(
      { content: "Hello", from: "user" },
      {},
    );

    expect(sendHeartbeat).toHaveBeenCalledWith("unknown", { status: "active", event: "message_received" });
  });

  it("does not throw when heartbeat fails", async () => {
    const sendHeartbeat = vi.fn().mockRejectedValue(new Error("timeout"));
    const client = { sendHeartbeat } as unknown as NomOSApiClient;

    const hook = createMessageReceivedHook(client);
    await expect(hook(
      { content: "Hello", from: "user" },
      { agentId: "agent-1" },
    )).resolves.toBeUndefined();
  });
});
