// nomos-plugin/src/index.ts
import type { OpenClawPluginApi } from "./types.js";
import { getPluginConfig } from "./config.js";
import { NomOSApiClient } from "./api-client.js";
import { wrapHook, wrapSyncHook } from "./error-handler.js";
import { createBeforeAgentStartHook } from "./hooks/before-agent-start.js";
import { createBeforeToolCallHook } from "./hooks/before-tool-call.js";
import { createToolResultPersistHook } from "./hooks/tool-result-persist.js";
import { createMessageSendingHook } from "./hooks/message-sending.js";
import { createAfterToolCallHook } from "./hooks/after-tool-call.js";
import { createMessageReceivedHook } from "./hooks/message-received.js";
import { createGatewayStartHook } from "./hooks/gateway-start.js";
import { createSessionStartHook } from "./hooks/session-start.js";
import { createSessionEndHook } from "./hooks/session-end.js";
import { createAgentEndHook } from "./hooks/agent-end.js";
import { createOnErrorHook } from "./hooks/on-error.js";

export default function register(api: OpenClawPluginApi): void {
  const config = getPluginConfig(api);
  const client = new NomOSApiClient(config.apiUrl);
  const logger = api.logger;
  const wrapOpts = { client, logger };

  // Sequential hooks (can block/modify) — HIGH PRIORITY
  api.on("before_agent_start",
    wrapHook("before_agent_start", createBeforeAgentStartHook(client), wrapOpts),
    { priority: 100 });

  api.on("before_tool_call",
    wrapHook("before_tool_call", createBeforeToolCallHook(client), wrapOpts),
    { priority: 100 });

  api.on("message_sending",
    wrapHook("message_sending", createMessageSendingHook(client), wrapOpts),
    { priority: 100 });

  // Synchronous hook (NO async!)
  api.on("tool_result_persist",
    wrapSyncHook("tool_result_persist", createToolResultPersistHook(), { logger }),
    { priority: 100 });

  // Parallel hooks (fire-and-forget)
  api.on("gateway_start",
    wrapHook("gateway_start", createGatewayStartHook(client, config), wrapOpts));

  api.on("after_tool_call",
    wrapHook("after_tool_call", createAfterToolCallHook(client), wrapOpts));

  api.on("message_received",
    wrapHook("message_received", createMessageReceivedHook(client), wrapOpts));

  api.on("session_start",
    wrapHook("session_start", createSessionStartHook(client), wrapOpts));

  api.on("session_end",
    wrapHook("session_end", createSessionEndHook(client), wrapOpts));

  api.on("agent_end",
    wrapHook("agent_end", createAgentEndHook(client), wrapOpts));

  // Error handler hook — auto-pause + incident (Art. 14 EU AI Act)
  api.on("on_error",
    wrapHook("on_error", createOnErrorHook(client), wrapOpts));

  // Banner
  logger.info("");
  logger.info("  ┌──────────────────────────────────────────────────────────┐");
  logger.info("  │  NomOS v2 — EU AI Act + DSGVO Compliance Active          │");
  logger.info("  │                                                          │");
  logger.info(`  │  API:     ${config.apiUrl.padEnd(47)}│`);
  logger.info("  │  Hooks:   11 registered (compliance, audit, PII, budget) │");
  logger.info("  │  License: FCL — 3 agents free, full functionality        │");
  logger.info("  └──────────────────────────────────────────────────────────┘");
  logger.info("");
}
