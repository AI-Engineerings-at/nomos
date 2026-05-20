// nomos-plugin/src/hooks/after-tool-call.ts
import type { NomOSApiClient } from "../api-client.js";
import type { HookAfterToolCallEvent } from "../types.js";

export function createAfterToolCallHook(
  client: NomOSApiClient,
): (event: HookAfterToolCallEvent, ctx: Record<string, unknown>) => Promise<void> {
  return async (event, ctx) => {
    const agentId = (ctx["agentId"] as string) ?? "unknown";

    // Fire-and-forget audit entry — hash chain.
    // M4 (0.3.0, audit D-#11): silent swallow used to mean "tool
    // completed but no audit trace, no operator alert". Log to the
    // gateway console so a clustered audit failure becomes visible.
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
    } catch (err) {
      console.warn(
        `[nomos-plugin] after-tool-call audit post failed (agent=${agentId}, tool=${event.toolName}): ${(err as Error).message}`,
      );
    }
  };
}
