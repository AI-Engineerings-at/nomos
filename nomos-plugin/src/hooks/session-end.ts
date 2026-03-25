// nomos-plugin/src/hooks/session-end.ts
import type { NomOSApiClient } from "../api-client.js";
import type { HookSessionEvent } from "../types.js";

export function createSessionEndHook(
  client: NomOSApiClient,
): (event: HookSessionEvent, ctx: Record<string, unknown>) => Promise<void> {
  return async (event, ctx) => {
    const agentId = (ctx["agentId"] as string) ?? event.agentId ?? "unknown";
    const startTime = ctx["sessionStartTime"] as number | undefined;
    const durationMs = startTime ? Date.now() - startTime : 0;

    try {
      await client.addAuditEntry({
        agent_id: agentId,
        event_type: "session.ended",
        payload: {
          session_key: event.sessionKey,
          duration_ms: durationMs,
        },
      });
    } catch {
      // Fire-and-forget: swallow errors silently
    }
  };
}
