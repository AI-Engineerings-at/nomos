/**
 * NomOS — OpenClaw Plugin for EU AI Act Compliance
 *
 * Registers at gateway startup, shows compliance banner,
 * provides /nomos slash commands and `openclaw nomos` CLI.
 */

import type { OpenClawPluginApi } from "./types.js";
import { getPluginConfig } from "./config.js";
import { handleSlashCommand } from "./commands.js";

export default function register(api: OpenClawPluginApi): void {
  const config = getPluginConfig(api);

  // 1. Register /nomos slash command
  api.registerCommand({
    name: "nomos",
    description: "NomOS compliance management (status, verify, help)",
    acceptsArgs: true,
    handler: (ctx) => handleSlashCommand(ctx, api),
  });

  // 2. Show registration banner
  api.logger.info("");
  api.logger.info("  ┌─────────────────────────────────────────────────────┐");
  api.logger.info("  │  NomOS registered                                   │");
  api.logger.info("  │                                                     │");
  api.logger.info(`  │  API:        ${config.apiUrl.padEnd(40)}│`);
  api.logger.info(`  │  Agents:     ${config.agentsDir.padEnd(40)}│`);
  api.logger.info("  │  Commands:   /nomos status | verify | help          │");
  api.logger.info("  │  Compliance: EU AI Act + DSGVO (gate + verify)      │");
  api.logger.info("  └─────────────────────────────────────────────────────┘");
  api.logger.info("");
}

// Re-export types for consumers
export type { OpenClawPluginApi } from "./types.js";
export type { NomOSPluginConfig } from "./config.js";
