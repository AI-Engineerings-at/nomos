// nomos-plugin/src/error-handler.ts
import type { NomOSApiClient } from "./api-client.js";
import type { PluginLogger } from "./types.js";

interface WrapOptions {
  client: NomOSApiClient;
  logger: PluginLogger;
  agentId?: string;
}

interface WrapSyncOptions {
  logger: PluginLogger;
}

export function wrapHook<E, R>(
  hookName: string,
  handler: (event: E, ctx: Record<string, unknown>) => Promise<R | void> | R | void,
  opts: WrapOptions,
): (event: E, ctx: Record<string, unknown>) => Promise<R | void> {
  return async (event, ctx) => {
    try {
      return await handler(event, ctx);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      opts.logger.error(`[NomOS] Hook "${hookName}" error: ${message}`);
      await opts.client.reportIncident(
        opts.agentId ?? (ctx["agentId"] as string) ?? "unknown",
        `Hook "${hookName}" threw: ${message}`,
        "high",
      );
      return undefined;
    }
  };
}

export function wrapSyncHook<E, R>(
  hookName: string,
  handler: (event: E, ctx: Record<string, unknown>) => R | void,
  opts: WrapSyncOptions,
): (event: E, ctx: Record<string, unknown>) => R | void {
  return (event, ctx) => {
    try {
      return handler(event, ctx);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      opts.logger.error(`[NomOS] Sync hook "${hookName}" error: ${message}`);
      return undefined;
    }
  };
}
