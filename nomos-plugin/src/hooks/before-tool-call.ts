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
    if (budget.error) {
      // API error — log and continue (don't block on transient failures).
      // M4 (0.3.0, audit D-#1): wrap audit-entry POSTs in try/catch so a
      // failed audit write doesn't propagate up and kill the hook itself.
      // Silent failure is acceptable here ONLY because the audit POST is
      // best-effort and the gateway logs the catch.
      try {
        await client.addAuditEntry({
          agent_id: agentId,
          event_type: "tool.call_allowed",
          payload: { tool: event.toolName, budget_error: budget.error },
        });
      } catch (err) {
        console.warn(`[nomos-plugin] audit-entry post failed (agent=${agentId}): ${(err as Error).message}`);
      }
    } else if (!budget.allowed) {
      if (budget.status === "unknown_agent") {
        // Unknown agent — log warning, don't block
        try {
          await client.addAuditEntry({
            agent_id: agentId,
            event_type: "tool.call_allowed",
            payload: { tool: event.toolName, budget_warning: "unknown_agent" },
          });
        } catch (err) {
          console.warn(`[nomos-plugin] audit-entry post failed (agent=${agentId}): ${(err as Error).message}`);
        }
      } else {
        return {
          block: true,
          blockReason: `Budget ueberschritten (${agentId}). Remaining: EUR ${budget.remaining ?? 0}. Agent wird pausiert.`,
        };
      }
    }

    // 2. Destructive tool check — requires approval
    if (DESTRUCTIVE_TOOLS.has(event.toolName)) {
      return {
        block: true,
        blockReason: `Approval erforderlich: "${event.toolName}" ist eine kritische Aktion. Warten auf Freigabe.`,
      };
    }

    // 3. Audit entry (non-blocking but logged on failure — M4 audit D-#1)
    try {
      await client.addAuditEntry({
        agent_id: agentId,
        event_type: "tool.call_allowed",
        payload: { tool: event.toolName, params_keys: Object.keys(event.params) },
      });
    } catch (err) {
      console.warn(`[nomos-plugin] audit-entry post failed (agent=${agentId}): ${(err as Error).message}`);
    }

    return undefined;
  };
}
