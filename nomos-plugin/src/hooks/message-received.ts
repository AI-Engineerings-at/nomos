// nomos-plugin/src/hooks/message-received.ts
import type { NomOSApiClient } from "../api-client.js";
import type { HookMessageEvent } from "../types.js";

export function createMessageReceivedHook(
  client: NomOSApiClient,
): (event: HookMessageEvent, ctx: Record<string, unknown>) => Promise<void> {
  return async (event, ctx) => {
    const agentId = (ctx["agentId"] as string) ?? "unknown";

    // Fire-and-forget heartbeat to signal active session
    try {
      await client.sendHeartbeat(agentId, { status: "active", event: "message_received" });
    } catch {
      // Fire-and-forget: swallow errors silently
    }
  };
}
