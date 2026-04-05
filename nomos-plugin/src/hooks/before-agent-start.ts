// nomos-plugin/src/hooks/before-agent-start.ts
import type { NomOSApiClient } from "../api-client.js";
import type { HookBeforeAgentStartEvent, HookBeforeAgentStartResult } from "../types.js";

export function createBeforeAgentStartHook(
  client: NomOSApiClient,
): (event: HookBeforeAgentStartEvent, ctx: Record<string, unknown>) => Promise<HookBeforeAgentStartResult | void> {
  return async (event, ctx) => {
    const agentId = (ctx["agentId"] as string) ?? "unknown";
    const result = await client.checkCompliance(agentId);

    // API errors (401, network, timeout) should NOT block the agent.
    // Only block when compliance genuinely failed with specific missing documents.
    if (result.error) {
      return {
        prependContext: [
          "**[NomOS Compliance — Degraded]**",
          `Compliance API unreachable (${result.error}). Agent runs with reduced oversight.`,
          "Alle Aktionen werden lokal protokolliert.",
        ].join("\n"),
      };
    }

    if (!result.passed) {
      return {
        prependContext: [
          "**[NomOS] BLOCKED — Compliance Gate Failed**",
          `Agent "${agentId}" darf NICHT starten.`,
          `Fehlende Dokumente: ${result.missing.join(", ")}`,
          "Bitte vervollstaendigen Sie die Compliance-Konfiguration.",
          "STOP — fuehre KEINE Aktionen aus.",
        ].join("\n"),
      };
    }

    return {
      prependContext: [
        "**[NomOS Compliance Active]**",
        "EU AI Act + DSGVO Enforcement ist aktiv.",
        "Alle Aktionen werden protokolliert (Hash Chain).",
        "Destruktive Aktionen erfordern Genehmigung.",
      ].join("\n"),
    };
  };
}
