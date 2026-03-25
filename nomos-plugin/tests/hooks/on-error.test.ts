// nomos-plugin/tests/hooks/on-error.test.ts
import { describe, it, expect, vi } from "vitest";
import { createOnErrorHook } from "../../src/hooks/on-error.js";
import type { NomOSApiClient } from "../../src/api-client.js";

describe("on_error hook", () => {
  it("auto-pauses agent and reports incident on error", async () => {
    const pauseAgent = vi.fn().mockResolvedValue(true);
    const reportIncident = vi.fn().mockResolvedValue(true);
    const addAuditEntry = vi.fn().mockResolvedValue({ hash: "err-hash" });
    const client = { pauseAgent, reportIncident, addAuditEntry } as unknown as NomOSApiClient;

    const hook = createOnErrorHook(client);
    await hook(
      { error: new Error("boom"), hookName: "before_tool_call", agentId: "agent-1" },
      { agentId: "agent-1" },
    );

    expect(pauseAgent).toHaveBeenCalledWith("agent-1");
    expect(reportIncident).toHaveBeenCalledOnce();
    expect(reportIncident.mock.calls[0][0]).toBe("agent-1");
    expect(reportIncident.mock.calls[0][2]).toBe("high");
    expect(addAuditEntry).toHaveBeenCalledOnce();
    expect(addAuditEntry.mock.calls[0][0].event_type).toBe("kill_switch.user_pause");
    expect(addAuditEntry.mock.calls[0][0].payload.auto_paused).toBe(true);
  });

  it("uses agentId from ctx when event has none", async () => {
    const pauseAgent = vi.fn().mockResolvedValue(true);
    const reportIncident = vi.fn().mockResolvedValue(true);
    const addAuditEntry = vi.fn().mockResolvedValue({ hash: "hash" });
    const client = { pauseAgent, reportIncident, addAuditEntry } as unknown as NomOSApiClient;

    const hook = createOnErrorHook(client);
    await hook(
      { error: "string error" },
      { agentId: "ctx-agent" },
    );

    expect(pauseAgent).toHaveBeenCalledWith("ctx-agent");
  });

  it("handles string errors correctly", async () => {
    const pauseAgent = vi.fn().mockResolvedValue(true);
    const reportIncident = vi.fn().mockResolvedValue(true);
    const addAuditEntry = vi.fn().mockResolvedValue({ hash: "hash" });
    const client = { pauseAgent, reportIncident, addAuditEntry } as unknown as NomOSApiClient;

    const hook = createOnErrorHook(client);
    await hook(
      { error: "something broke", hookName: "after_tool_call" },
      { agentId: "agent-2" },
    );

    expect(reportIncident.mock.calls[0][1]).toContain("something broke");
    expect(addAuditEntry.mock.calls[0][0].payload.error).toBe("something broke");
  });
});
