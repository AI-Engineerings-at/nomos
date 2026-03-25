// nomos-plugin/src/hooks/session-start.ts
import type { NomOSApiClient } from "../api-client.js";
import type { HookSessionEvent } from "../types.js";

export function createSessionStartHook(
  client: NomOSApiClient,
): (event: HookSessionEvent, ctx: Record<string, unknown>) => Promise<void> {
  return async (event, ctx) => {
    const agentId = (ctx["agentId"] as string) ?? event.agentId ?? "unknown";

    try {
      await client.addAuditEntry({
        agent_id: agentId,
        event_type: "session.started",
        payload: { session_key: event.sessionKey },
      });
    } catch {
      // Fire-and-forget: swallow errors silently
    }
  };
}
