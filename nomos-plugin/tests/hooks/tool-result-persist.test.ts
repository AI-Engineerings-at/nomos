// nomos-plugin/tests/hooks/tool-result-persist.test.ts
import { describe, it, expect } from "vitest";
import { createToolResultPersistHook } from "../../src/hooks/tool-result-persist.js";

describe("tool_result_persist hook (SYNC)", () => {
  const hook = createToolResultPersistHook();

  it("masks email addresses", () => {
    const result = hook(
      { toolName: "search", message: { role: "tool", content: "Contact max@example.com for info" } },
      {},
    );
    expect(result?.message.content).not.toContain("max@example.com");
    expect(result?.message.content).toContain("[EMAIL_REDACTED]");
  });

  it("masks phone numbers", () => {
    const result = hook(
      { toolName: "search", message: { role: "tool", content: "Call +43 1 234 5678" } },
      {},
    );
    expect(result?.message.content).not.toContain("+43 1 234 5678");
    expect(result?.message.content).toContain("[PHONE_REDACTED]");
  });

  it("masks IBAN", () => {
    const result = hook(
      { toolName: "search", message: { role: "tool", content: "IBAN: AT611904300234573201" } },
      {},
    );
    expect(result?.message.content).not.toContain("AT611904300234573201");
    expect(result?.message.content).toContain("[IBAN_REDACTED]");
  });

  it("returns unchanged message when no PII found", () => {
    const result = hook(
      { toolName: "search", message: { role: "tool", content: "No personal data here" } },
      {},
    );
    expect(result).toBeUndefined();
  });
});
