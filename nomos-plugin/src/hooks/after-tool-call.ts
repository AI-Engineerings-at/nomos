// nomos-plugin/src/hooks/after-tool-call.ts
import type { NomOSApiClient } from "../api-client.js";
import type { HookAfterToolCallEvent } from "../types.js";

export function createAfterToolCallHook(
  client: NomOSApiClient,
): (event: HookAfterToolCallEvent, ctx: Record<string, unknown>) => Promise<void> {
  return async (event, ctx) => {
    const agentId = (ctx["agentId"] as string) ?? "unknown";

    // Fire-and-forget audit entry — hash chain
    try {
      await client.addAuditEntry({
        agent_id: agentId,
        event_type: "tool.completed",
        payload: {
          tool: event.toolName,
          params_keys: Object.keys(event.params),
          duration_ms: event.durationMs,
        },
      });
    } catch {
      // Fire-and-forget: swallow errors silently
    }
  };
}
