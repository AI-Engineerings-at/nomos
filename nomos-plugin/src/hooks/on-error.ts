// nomos-plugin/src/hooks/on-error.ts
import type { NomOSApiClient } from "../api-client.js";

export interface OnErrorEvent {
  error: Error | string;
  hookName?: string;
  agentId?: string;
}

/**
 * on_error hook — auto-pauses the agent and reports an incident.
 *
 * This hook is triggered by the error-handler wrapper when any other hook
 * throws an error. It ensures EU AI Act Art. 14 compliance by automatically
 * pausing agents that encounter errors and creating incident records.
 */
export function createOnErrorHook(client: NomOSApiClient) {
  return async (
    event: OnErrorEvent,
    ctx: Record<string, unknown>,
  ): Promise<void> => {
    const agentId = event.agentId ?? (ctx["agentId"] as string) ?? "unknown";
    const message = event.error instanceof Error ? event.error.message : String(event.error);
    const hookName = event.hookName ?? "unknown";

    // Auto-pause the agent to prevent further damage
    await client.pauseAgent(agentId);

    // Report the incident for audit trail
    await client.reportIncident(
      agentId,
      `Auto-pause triggered: hook "${hookName}" error: ${message}`,
      "high",
    );

    // Log to audit chain
    await client.addAuditEntry({
      agent_id: agentId,
      event_type: "kill_switch.user_pause",
      payload: {
        trigger: "on_error",
        hook: hookName,
        error: message,
        auto_paused: true,
      },
    });
  };
}
