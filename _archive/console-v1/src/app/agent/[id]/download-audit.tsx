"use client";

export default function DownloadAudit({ agentId }: { agentId: string }) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8060";

  return (
    <a
      href={`${apiUrl}/api/agents/${agentId}/audit/export`}
      download={`${agentId}-audit-chain.jsonl`}
      className="text-sm text-blue-600 hover:underline"
    >
      Audit Trail herunterladen (JSONL)
    </a>
  );
}
