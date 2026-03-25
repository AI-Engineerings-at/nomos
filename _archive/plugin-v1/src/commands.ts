/**
 * NomOS slash command handler.
 */

import type { PluginCommandContext, PluginCommandResult, OpenClawPluginApi } from "./types.js";
import type { NomOSPluginConfig } from "./config.js";
import { getPluginConfig } from "./config.js";

export async function handleSlashCommand(
  ctx: PluginCommandContext,
  api: OpenClawPluginApi,
): Promise<PluginCommandResult> {
  const args = (ctx.args ?? "").trim().split(/\s+/);
  const subcommand = args[0]?.toLowerCase() ?? "help";
  const config = getPluginConfig(api);

  switch (subcommand) {
    case "status":
      return await handleStatus(config);
    case "verify":
      return await handleVerify(config, args[1]);
    case "help":
    default:
      return {
        text: [
          "**NomOS Commands:**",
          "`/nomos status` — Fleet compliance overview",
          "`/nomos verify <agent-id>` — Verify agent compliance + audit chain",
          "`/nomos help` — Show this help",
        ].join("\n"),
      };
  }
}

async function handleStatus(config: NomOSPluginConfig): Promise<PluginCommandResult> {
  try {
    const response = await fetch(`${config.apiUrl}/api/fleet`);
    if (!response.ok) {
      return { text: `NomOS API error: ${response.status} ${response.statusText}` };
    }
    const data = (await response.json()) as {
      agents: Array<{ id: string; name: string; status: string; compliance_status: string }>;
      total: number;
    };

    if (data.total === 0) {
      return { text: "**NomOS Fleet:** No agents registered. Use `nomos hire` to create one." };
    }

    const lines = [
      `**NomOS Fleet** (${data.total} agent${data.total > 1 ? "s" : ""})`,
      "",
      "| Agent | Role | Status | Compliance |",
      "|-------|------|--------|------------|",
    ];

    for (const agent of data.agents) {
      const compIcon =
        agent.compliance_status === "passed"
          ? "pass"
          : agent.compliance_status === "blocked"
            ? "BLOCKED"
            : "WARNING";
      lines.push(
        `| ${agent.name} | ${agent.id} | ${agent.status} | ${compIcon} ${agent.compliance_status} |`,
      );
    }

    return { text: lines.join("\n") };
  } catch {
    return { text: `NomOS API unreachable at ${config.apiUrl}. Is the API running?` };
  }
}

async function handleVerify(
  config: NomOSPluginConfig,
  agentId?: string,
): Promise<PluginCommandResult> {
  if (!agentId) {
    return { text: "Usage: `/nomos verify <agent-id>`" };
  }

  try {
    const [complianceResp, auditResp] = await Promise.all([
      fetch(`${config.apiUrl}/api/agents/${agentId}/compliance`),
      fetch(`${config.apiUrl}/api/audit/verify/${agentId}`),
    ]);

    if (!complianceResp.ok) {
      return { text: `Agent "${agentId}" not found.` };
    }

    const compliance = (await complianceResp.json()) as {
      status: string;
      missing_documents: string[];
      errors: string[];
    };
    const audit = auditResp.ok
      ? ((await auditResp.json()) as { valid: boolean; entries_checked: number; errors: string[] })
      : null;

    const lines = [
      `**Verification: ${agentId}**`,
      "",
      `Compliance: ${compliance.status === "passed" ? "PASSED" : compliance.status === "blocked" ? "BLOCKED" : "WARNING"}`,
    ];

    if (compliance.missing_documents.length > 0) {
      lines.push(`Missing docs: ${compliance.missing_documents.join(", ")}`);
    }
    if (compliance.errors.length > 0) {
      lines.push(`Errors: ${compliance.errors.join("; ")}`);
    }

    if (audit) {
      lines.push(
        `Audit Chain: ${audit.valid ? "VALID" : "INVALID"} (${audit.entries_checked} entries)`,
      );
      if (audit.errors.length > 0) {
        lines.push(`Chain errors: ${audit.errors.join("; ")}`);
      }
    }

    return { text: lines.join("\n") };
  } catch {
    return { text: `NomOS API unreachable at ${config.apiUrl}.` };
  }
}
