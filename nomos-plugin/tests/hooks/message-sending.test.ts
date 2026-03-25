// nomos-plugin/tests/hooks/message-sending.test.ts
import { describe, it, expect } from "vitest";
import { createMessageSendingHook } from "../../src/hooks/message-sending.js";
import type { NomOSApiClient } from "../../src/api-client.js";

const mockClient = {
  addAuditEntry: async () => ({ hash: "abc" }),
} as unknown as NomOSApiClient;

describe("message_sending hook", () => {
  it("inserts Art. 50 AI disclosure label into content", async () => {
    const hook = createMessageSendingHook(mockClient);
    const result = await hook(
      { content: "Here is the answer to your question.", to: "user" },
      { agentId: "agent-1" },
    );
    expect(result?.content).toContain("Diese Antwort wurde von KI generiert.");
    expect(result?.content).toContain("Here is the answer to your question.");
  });

  it("preserves original content fully", async () => {
    const hook = createMessageSendingHook(mockClient);
    const original = "Detailed response with special chars: <>!@#$%";
    const result = await hook(
      { content: original, to: "user" },
      { agentId: "agent-1" },
    );
    expect(result?.content).toContain(original);
  });

  it("does not duplicate label if already present", async () => {
    const hook = createMessageSendingHook(mockClient);
    const contentWithLabel = "Answer text.\n\n---\n*Diese Antwort wurde von KI generiert.*";
    const result = await hook(
      { content: contentWithLabel, to: "user" },
      { agentId: "agent-1" },
    );
    const matches = (result?.content ?? contentWithLabel).match(/Diese Antwort wurde von KI generiert/g);
    expect(matches?.length).toBe(1);
  });
});
