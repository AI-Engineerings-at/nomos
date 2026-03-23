import { fetchAgent, fetchCompliance, fetchAudit, fetchAuditVerify } from "@/lib/api";
import Link from "next/link";

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    passed: "bg-green-100 text-green-800",
    blocked: "bg-red-100 text-red-800",
    warning: "bg-yellow-100 text-yellow-800",
    created: "bg-blue-100 text-blue-800",
  };
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[status] ?? "bg-gray-100 text-gray-600"}`}>
      {status}
    </span>
  );
}

export default async function AgentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let agent, compliance, audit, verify;
  let error: string | null = null;

  try {
    [agent, compliance, audit, verify] = await Promise.all([
      fetchAgent(id),
      fetchCompliance(id),
      fetchAudit(id),
      fetchAuditVerify(id),
    ]);
  } catch (e) {
    error = e instanceof Error ? e.message : "Fehler beim Laden";
  }

  if (error || !agent) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800 font-medium">Agent nicht gefunden</p>
        <p className="text-red-600 text-sm">{error}</p>
        <Link href="/" className="text-blue-600 hover:underline mt-4 block">Zurueck</Link>
      </div>
    );
  }

  return (
    <div>
      <Link href="/" className="text-blue-600 hover:underline text-sm">&larr; Fleet</Link>

      <div className="mt-4 mb-8">
        <h1 className="text-2xl font-bold">{agent.name}</h1>
        <p className="text-gray-500">{agent.role} &mdash; {agent.company}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="text-sm text-gray-500 mb-1">Status</p>
          <StatusBadge status={agent.status} />
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="text-sm text-gray-500 mb-1">Compliance</p>
          <StatusBadge status={agent.compliance_status} />
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="text-sm text-gray-500 mb-1">Audit Chain</p>
          {verify ? (
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${verify.valid ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
              {verify.valid ? `VALID (${verify.entries_checked} entries)` : "INVALID"}
            </span>
          ) : <span className="text-gray-400 text-sm">N/A</span>}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h2 className="font-semibold mb-2">Agent Details</h2>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-gray-500">ID</dt><dd className="font-mono">{agent.id}</dd></div>
            <div className="flex justify-between"><dt className="text-gray-500">Email</dt><dd>{agent.email}</dd></div>
            <div className="flex justify-between"><dt className="text-gray-500">Risiko</dt><dd><StatusBadge status={agent.risk_class} /></dd></div>
            <div className="flex justify-between"><dt className="text-gray-500">Manifest Hash</dt><dd className="font-mono text-xs">{agent.manifest_hash.slice(0, 16)}...</dd></div>
            <div className="flex justify-between"><dt className="text-gray-500">Erstellt</dt><dd>{new Date(agent.created_at).toLocaleString("de-AT")}</dd></div>
          </dl>
        </div>

        {compliance && (
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h2 className="font-semibold mb-2">Compliance Check</h2>
            <p className="mb-2"><StatusBadge status={compliance.status} /></p>
            {compliance.missing_documents.length > 0 && (
              <div className="mt-2">
                <p className="text-sm text-gray-500 mb-1">Fehlende Dokumente:</p>
                <ul className="list-disc list-inside text-sm text-red-600">
                  {compliance.missing_documents.map((d) => <li key={d}>{d}</li>)}
                </ul>
              </div>
            )}
            {compliance.errors.length > 0 && (
              <div className="mt-2">
                <p className="text-sm text-gray-500 mb-1">Fehler:</p>
                <ul className="list-disc list-inside text-sm text-red-600">
                  {compliance.errors.map((e, i) => <li key={i}>{e}</li>)}
                </ul>
              </div>
            )}
            {compliance.status === "passed" && (
              <p className="text-green-600 text-sm mt-2">Alle Compliance-Anforderungen erfuellt.</p>
            )}
          </div>
        )}
      </div>

      {audit && audit.entries.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
            <h2 className="font-semibold">Audit Trail</h2>
            {verify && (
              <span className={`text-xs font-medium ${verify.valid ? "text-green-600" : "text-red-600"}`}>
                Chain: {verify.valid ? "VALID" : "INVALID"} ({verify.entries_checked} entries)
              </span>
            )}
          </div>
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500">#</th>
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500">Event</th>
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500">Zeitpunkt</th>
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500">Hash</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {audit.entries.map((entry) => (
                <tr key={entry.sequence} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-sm text-gray-400">{entry.sequence}</td>
                  <td className="px-4 py-2 text-sm font-mono">{entry.event_type}</td>
                  <td className="px-4 py-2 text-sm text-gray-500">
                    {new Date(entry.timestamp).toLocaleString("de-AT")}
                  </td>
                  <td className="px-4 py-2 text-xs font-mono text-gray-400">{entry.chain_hash.slice(0, 16)}...</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
