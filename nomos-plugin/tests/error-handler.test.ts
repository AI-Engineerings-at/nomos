// nomos-plugin/tests/error-handler.test.ts
import { describe, it, expect, vi } from "vitest";
import { wrapHook, wrapSyncHook } from "../src/error-handler.js";
import type { NomOSApiClient } from "../src/api-client.js";

const mockClient = {
  reportIncident: vi.fn().mockResolvedValue(true),
} as unknown as NomOSApiClient;

const mockLogger = { info: vi.fn(), warn: vi.fn(), error: vi.fn(), debug: vi.fn() };

describe("wrapHook (async)", () => {
  it("passes through successful handler result", async () => {
    const handler = vi.fn().mockResolvedValue({ block: true });
    const wrapped = wrapHook("test_hook", handler, { client: mockClient, logger: mockLogger });

    const result = await wrapped({ toolName: "test" }, {});
    expect(result).toEqual({ block: true });
  });

  it("catches errors and reports incident", async () => {
    const handler = vi.fn().mockRejectedValue(new Error("boom"));
    const wrapped = wrapHook("test_hook", handler, { client: mockClient, logger: mockLogger });

    const result = await wrapped({ toolName: "test" }, {});
    expect(result).toBeUndefined();
    expect(mockLogger.error).toHaveBeenCalled();
    expect(mockClient.reportIncident).toHaveBeenCalled();
  });
});

describe("wrapSyncHook", () => {
  it("passes through successful sync result", () => {
    const handler = vi.fn().mockReturnValue({ message: { role: "tool", content: "ok" } });
    const wrapped = wrapSyncHook("persist_hook", handler, { logger: mockLogger });

    const result = wrapped({ toolName: "test", message: { role: "tool", content: "ok" } }, {});
    expect(result).toEqual({ message: { role: "tool", content: "ok" } });
  });

  it("catches sync errors and returns undefined", () => {
    const handler = vi.fn().mockImplementation(() => { throw new Error("sync boom"); });
    const wrapped = wrapSyncHook("persist_hook", handler, { logger: mockLogger });

    const result = wrapped({ toolName: "test", message: { role: "tool", content: "ok" } }, {});
    expect(result).toBeUndefined();
    expect(mockLogger.error).toHaveBeenCalled();
  });
});
