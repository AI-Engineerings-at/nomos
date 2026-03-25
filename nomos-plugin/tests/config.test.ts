// nomos-plugin/tests/config.test.ts
import { describe, it, expect } from "vitest";
import { getPluginConfig } from "../src/config.js";
import type { OpenClawPluginApi } from "../src/types.js";

function mockApi(pluginConfig?: Record<string, unknown>): OpenClawPluginApi {
  return {
    id: "nomos", name: "NomOS", config: {}, pluginConfig,
    logger: { info: () => {}, warn: () => {}, error: () => {}, debug: () => {} },
    registerCommand: () => {}, registerCli: () => {}, registerService: () => {},
    resolvePath: (p: string) => p, on: () => {},
  };
}

describe("getPluginConfig", () => {
  it("returns defaults when no pluginConfig", () => {
    const config = getPluginConfig(mockApi());
    expect(config.apiUrl).toBe("http://nomos-api:8000");
    expect(config.agentsDir).toBe("./data/agents");
  });

  it("uses custom apiUrl from pluginConfig", () => {
    const config = getPluginConfig(mockApi({ apiUrl: "http://custom:9000" }));
    expect(config.apiUrl).toBe("http://custom:9000");
  });

  it("ignores non-string values", () => {
    const config = getPluginConfig(mockApi({ apiUrl: 42 }));
    expect(config.apiUrl).toBe("http://nomos-api:8000");
  });
});
