/**
 * NomOS plugin configuration.
 */

import type { OpenClawPluginApi } from "./types.js";

export interface NomOSPluginConfig {
  apiUrl: string;
  agentsDir: string;
}

const DEFAULTS: NomOSPluginConfig = {
  apiUrl: "http://localhost:8060",
  agentsDir: "./data/agents",
};

export function getPluginConfig(api: OpenClawPluginApi): NomOSPluginConfig {
  const raw = api.pluginConfig ?? {};
  return {
    apiUrl: typeof raw["apiUrl"] === "string" ? raw["apiUrl"] : DEFAULTS.apiUrl,
    agentsDir: typeof raw["agentsDir"] === "string" ? raw["agentsDir"] : DEFAULTS.agentsDir,
  };
}
