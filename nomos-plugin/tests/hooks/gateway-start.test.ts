// nomos-plugin/tests/hooks/gateway-start.test.ts
import { describe, it, expect, vi, beforeAll, afterAll } from "vitest";
import { createGatewayStartHook } from "../../src/hooks/gateway-start.js";
import { NomOSApiClient } from "../../src/api-client.js";
import { createMockApiServer } from "../helpers/mock-api.js";
import type { NomOSPluginConfig } from "../../src/config.js";

let server: ReturnType<typeof createMockApiServer>;
let client: NomOSApiClient;
const config: NomOSPluginConfig = { apiUrl: "http://localhost:19880", agentsDir: "./data/agents" };

beforeAll(async () => {
  server = createMockApiServer(19880);
  await server.start();
  client = new NomOSApiClient("http://localhost:19880");
});

afterAll(async () => { await server.stop(); });

describe("gateway_start hook", () => {
  it("performs health check without errors", async () => {
    const hook = createGatewayStartHook(client, config);
    await expect(hook({ version: "1.0" }, {})).resolves.toBeUndefined();
  });

  it("logs banner via logger in context", async () => {
    const logger = { info: vi.fn(), warn: vi.fn(), error: vi.fn(), debug: vi.fn() };
    const hook = createGatewayStartHook(client, config);
    await hook({ version: "1.0" }, { logger });
    expect(logger.info).toHaveBeenCalled();
  });

  it("does not throw when API is unreachable", async () => {
    const badClient = new NomOSApiClient("http://localhost:1");
    const hook = createGatewayStartHook(badClient, config);
    await expect(hook({ version: "1.0" }, {})).resolves.toBeUndefined();
  });
});
