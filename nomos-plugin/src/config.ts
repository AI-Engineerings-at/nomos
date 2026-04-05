// nomos-plugin/src/config.ts
import type { OpenClawPluginApi } from "./types.js";

export interface NomOSPluginConfig {
  apiUrl: string;
  apiKey: string;
  agentsDir: string;
}

const DEFAULTS: NomOSPluginConfig = {
  apiUrl: "http://nomos-api:8000",
  apiKey: "",
  agentsDir: "./data/agents",
};

export function getPluginConfig(api: OpenClawPluginApi): NomOSPluginConfig {
  const raw = api.pluginConfig ?? {};

  // API key: ENV takes priority over pluginConfig (more secure, no config file exposure)
  const envApiKey = typeof process !== "undefined" ? process.env["NOMOS_PLUGIN_API_KEY"] : undefined;
  const configApiKey = typeof raw["apiKey"] === "string" ? raw["apiKey"] : "";
  const apiKey = envApiKey || configApiKey || DEFAULTS.apiKey;

  return {
    apiUrl: typeof raw["apiUrl"] === "string" ? raw["apiUrl"] : DEFAULTS.apiUrl,
    apiKey,
    agentsDir: typeof raw["agentsDir"] === "string" ? raw["agentsDir"] : DEFAULTS.agentsDir,
  };
}
