// nomos-plugin/src/hooks/agent-end.ts
import type { NomOSApiClient } from "../api-client.js";
import type { HookAgentEndEvent } from "../types.js";

export function createAgentEndHook(
  client: NomOSApiClient,
): (event: HookAgentEndEvent, ctx: Record<string, unknown>) => Promise<void> {
  return async (event, ctx) => {
    const agentId = (ctx["agentId"] as string) ?? event.agentId ?? "unknown";

    try {
      await client.addAuditEntry({
        agent_id: agentId,
        event_type: "agent.ended",
        payload: { status: "completed" },
      });
    } catch {
      // Fire-and-forget: swallow errors silently
    }
  };
}
