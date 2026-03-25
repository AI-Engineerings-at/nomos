// nomos-plugin/tests/api-client.test.ts
import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { NomOSApiClient } from "../src/api-client.js";
import { createMockApiServer } from "./helpers/mock-api.js";

let server: ReturnType<typeof createMockApiServer>;
let client: NomOSApiClient;

beforeAll(async () => {
  server = createMockApiServer(19876);
  await server.start();
  client = new NomOSApiClient("http://localhost:19876");
});

afterAll(async () => {
  await server.stop();
});

describe("NomOSApiClient", () => {
  it("checks compliance gate — passed", async () => {
    const result = await client.checkCompliance("agent-1");
    expect(result.passed).toBe(true);
    expect(result.missing).toEqual([]);
  });

  it("adds audit entry and returns hash", async () => {
    const result = await client.addAuditEntry({
      agent_id: "agent-1",
      event_type: "tool.called",
      payload: { tool: "web_search" },
    });
    expect(result.hash).toBeTruthy();
    expect(typeof result.hash).toBe("string");
  });

  it("filters PII from text", async () => {
    const result = await client.filterPII("Email: max@example.com");
    expect(result.filtered).not.toContain("max@example.com");
    expect(result.found.length).toBeGreaterThan(0);
  });

  it("checks budget — allowed", async () => {
    const result = await client.checkBudget("agent-1", 0.05);
    expect(result.allowed).toBe(true);
  });

  it("handles API errors gracefully", async () => {
    const badClient = new NomOSApiClient("http://localhost:1");
    const result = await badClient.checkCompliance("agent-1");
    expect(result.passed).toBe(false);
    expect(result.error).toBeTruthy();
  });
});
