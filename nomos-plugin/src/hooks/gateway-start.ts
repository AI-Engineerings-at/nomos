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

    // Health check — fire-and-forget
    try {
      const healthy = await client.healthCheck();
      if (logger) {
        logger.info(`[NomOS] Gateway started — API health: ${healthy ? "OK" : "UNREACHABLE"}`);
        logger.info(`[NomOS] API URL: ${config.apiUrl}`);
        logger.info(`[NomOS] Agents Dir: ${config.agentsDir}`);
      }
    } catch {
      if (logger) {
        logger.info("[NomOS] Gateway started — API health check failed (will retry)");
      }
    }
  };
}
