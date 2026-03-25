// nomos-plugin/tests/hooks/before-agent-start.test.ts
import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { createBeforeAgentStartHook } from "../../src/hooks/before-agent-start.js";
import { NomOSApiClient } from "../../src/api-client.js";
import { createMockApiServer } from "../helpers/mock-api.js";

let server: ReturnType<typeof createMockApiServer>;
let client: NomOSApiClient;

beforeAll(async () => {
  server = createMockApiServer(19877);
  await server.start();
  client = new NomOSApiClient("http://localhost:19877");
});

afterAll(async () => { await server.stop(); });

describe("before_agent_start hook", () => {
  it("returns prependContext with compliance notice when gate passes", async () => {
    const hook = createBeforeAgentStartHook(client);
    const result = await hook(
      { prompt: "You are a helpful assistant" },
      { agentId: "agent-1" },
    );
    expect(result?.prependContext).toContain("NomOS Compliance");
  });

  it("blocks agent when compliance check fails", async () => {
    const failClient = {
      checkCompliance: async () => ({ passed: false, missing: ["DPIA", "Art. 50"] }),
    } as unknown as NomOSApiClient;

    const hook = createBeforeAgentStartHook(failClient);
    const result = await hook(
      { prompt: "You are an assistant" },
      { agentId: "agent-fail" },
    );
    expect(result?.prependContext).toContain("BLOCKED");
    expect(result?.prependContext).toContain("DPIA");
  });

  it("handles missing agentId gracefully", async () => {
    const hook = createBeforeAgentStartHook(client);
    const result = await hook(
      { prompt: "You are a helpful assistant" },
      {},
    );
    expect(result?.prependContext).toContain("NomOS Compliance");
  });
});
