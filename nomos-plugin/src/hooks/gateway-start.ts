// nomos-plugin/src/hooks/gateway-start.ts
import type { NomOSApiClient } from "../api-client.js";
import type { NomOSPluginConfig } from "../config.js";
import type { HookGatewayEvent, PluginLogger } from "../types.js";

export function createGatewayStartHook(
  client: NomOSApiClient,
  config: NomOSPluginConfig,
): (event: HookGatewayEvent, ctx: Record<string, unknown>) => Promise<void> {
  return async (event, ctx) => {
    const logger = ctx["logger"] as PluginLogger | undefined;

    // Health check — fire-and-forget. v0.4.0 (Q / audit D-#17): the
    // log message used to claim "will retry" but no retry path was
    // actually implemented in this hook. Each subsequent hook
    // (before-agent-start, before-tool-call, etc.) calls the API on
    // its own and so does its own implicit retry. Reword to be honest
    // about what actually happens, AND log the error type for ops.
    try {
      const healthy = await client.healthCheck();
      if (logger) {
        logger.info(`[NomOS] Gateway started — API health: ${healthy ? "OK" : "UNREACHABLE"}`);
        logger.info(`[NomOS] API URL: ${config.apiUrl}`);
        logger.info(`[NomOS] Agents Dir: ${config.agentsDir}`);
      }
    } catch (err) {
      if (logger) {
        logger.info(
          `[NomOS] Gateway started — initial API health check failed (${(err as Error).message || "unknown"}). ` +
            "Per-hook API calls will surface a real error if the API stays down.",
        );
      }
    }
  };
}
