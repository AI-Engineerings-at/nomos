// nomos-plugin/src/config.ts
import type { OpenClawPluginApi } from "./types.js";

export interface NomOSPluginConfig {
  apiUrl: string;
  agentsDir: string;
}

const DEFAULTS: NomOSPluginConfig = {
  apiUrl: "http://nomos-api:8000",
  agentsDir: "./data/agents",
};

export function getPluginConfig(api: OpenClawPluginApi): NomOSPluginConfig {
  const raw = api.pluginConfig ?? {};
  return {
    apiUrl: typeof raw["apiUrl"] === "string" ? raw["apiUrl"] : DEFAULTS.apiUrl,
    agentsDir: typeof raw["agentsDir"] === "string" ? raw["agentsDir"] : DEFAULTS.agentsDir,
  };
}
