// nomos-plugin/src/hooks/before-tool-call.ts
import type { NomOSApiClient } from "../api-client.js";
import type {
  HookBeforeToolCallEvent,
  HookBeforeToolCallResult,
} from "../types.js";

const DESTRUCTIVE_TOOLS = new Set([
  "file_delete", "file_write", "bash_rm", "database_drop",
  "email_send", "api_external", "data_export",
]);

export function createBeforeToolCallHook(
  client: NomOSApiClient,
): (event: HookBeforeToolCallEvent, ctx: Record<string, unknown>) => Promise<HookBeforeToolCallResult | void> {
  return async (event, ctx) => {
    const agentId = (ctx["agentId"] as string) ?? "unknown";

    // 1. Budget check
    const budget = await client.checkBudget(agentId, 0.01);
    if (!budget.allowed) {
      return {
        block: true,
        blockReason: `Budget ueberschritten (${agentId}). Remaining: EUR ${budget.remaining}. Agent wird pausiert.`,
      };
    }

    // 2. Destructive tool check — requires approval
    if (DESTRUCTIVE_TOOLS.has(event.toolName)) {
      return {
        block: true,
        blockReason: `Approval erforderlich: "${event.toolName}" ist eine kritische Aktion. Warten auf Freigabe.`,
      };
    }

    // 3. Audit entry (non-blocking)
    client.addAuditEntry({
      agent_id: agentId,
      event_type: "tool.call_allowed",
      payload: { tool: event.toolName, params_keys: Object.keys(event.params) },
    });

    return undefined;
  };
}
