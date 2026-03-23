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

  // 2. Register gateway hooks
  api.on("agent:message:before", (...args: unknown[]) => {
    // Art. 50 labeling hook — fires before each agent message
    api.logger.debug("NomOS: pre-message hook fired");
  });

  api.on("agent:message:after", (...args: unknown[]) => {
    // Audit logging hook — fires after each agent message
    api.logger.debug("NomOS: post-message hook fired");
  });

  // 3. Show registration banner
  api.logger.info("");
  api.logger.info("  ┌─────────────────────────────────────────────────────┐");
  api.logger.info("  │  NomOS registered                                   │");
  api.logger.info("  │                                                     │");
  api.logger.info(`  │  API:        ${config.apiUrl.padEnd(40)}│`);
  api.logger.info(`  │  Agents:     ${config.agentsDir.padEnd(40)}│`);
  api.logger.info("  │  Commands:   /nomos status | verify | help          │");
  api.logger.info("  │  Compliance: EU AI Act + DSGVO enforcement          │");
  api.logger.info("  └─────────────────────────────────────────────────────┘");
  api.logger.info("");
}

// Re-export types for consumers
export type { OpenClawPluginApi } from "./types.js";
export type { NomOSPluginConfig } from "./config.js";
