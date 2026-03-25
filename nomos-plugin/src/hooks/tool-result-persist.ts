// nomos-plugin/src/hooks/tool-result-persist.ts
// WICHTIG: Dieser Hook ist SYNCHRON — kein async, kein Promise!
import type { HookToolResultPersistEvent, HookToolResultPersistResult } from "../types.js";

const PII_PATTERNS: Array<{ pattern: RegExp; replacement: string }> = [
  { pattern: /[\w.+-]+@[\w.-]+\.\w{2,}/g, replacement: "[EMAIL_REDACTED]" },
  { pattern: /[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}/g, replacement: "[IBAN_REDACTED]" },
  { pattern: /\d{2,3}\/?\d{3,4}\/?\d{4,5}/g, replacement: "[TAX_ID_REDACTED]" },
  { pattern: /(\+?\d{1,4}[\s.-]?)?\(?\d{1,4}\)?[\s.-]?\d{2,4}[\s.-]?\d{2,9}/g, replacement: "[PHONE_REDACTED]" },
];

export function createToolResultPersistHook(): (
  event: HookToolResultPersistEvent,
  ctx: Record<string, unknown>,
) => HookToolResultPersistResult | void {
  return (event, _ctx) => {
    let content = event.message.content;
    let modified = false;

    for (const { pattern, replacement } of PII_PATTERNS) {
      const newContent = content.replace(pattern, replacement);
      if (newContent !== content) {
        modified = true;
        content = newContent;
      }
    }

    if (!modified) return undefined;

    return {
      message: { role: event.message.role, content },
    };
  };
}
