// nomos-plugin/src/hooks/message-sending.ts
import type { NomOSApiClient } from "../api-client.js";
import type { HookMessageEvent, HookMessageSendingResult } from "../types.js";

const AI_DISCLOSURE_LABEL = "Diese Antwort wurde von KI generiert.";

export function createMessageSendingHook(
  client: NomOSApiClient,
): (event: HookMessageEvent, ctx: Record<string, unknown>) => Promise<HookMessageSendingResult | void> {
  return async (event, ctx) => {
    const agentId = (ctx["agentId"] as string) ?? "unknown";

    // If label is already present, do not duplicate
    if (event.content.includes(AI_DISCLOSURE_LABEL)) {
      return undefined;
    }

    const labeledContent = `${event.content}\n\n---\n*${AI_DISCLOSURE_LABEL}*`;

    // Audit the disclosure (fire-and-forget)
    client.addAuditEntry({
      agent_id: agentId,
      event_type: "message.ai_disclosure",
      payload: { to: event.to ?? "unknown" },
    });

    return { content: labeledContent };
  };
}
