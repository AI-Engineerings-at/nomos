import { fetchFleet } from "@/lib/api";
import Link from "next/link";

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    passed: "bg-green-100 text-green-800",
    blocked: "bg-red-100 text-red-800",
    warning: "bg-yellow-100 text-yellow-800",
    pending: "bg-gray-100 text-gray-800",
    created: "bg-blue-100 text-blue-800",
  };
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[status] ?? "bg-gray-100 text-gray-600"}`}>
      {status}
    </span>
  );
}

export default async function Home() {
  let fleet;
  let error: string | null = null;

  try {
    fleet = await fetchFleet();
  } catch (e) {
    error = e instanceof Error ? e.message : "API nicht erreichbar";
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">NomOS Fleet</h1>
          <p className="text-gray-500 mt-1">
            AI-Mitarbeiter verwalten — EU AI Act konform
          </p>
        </div>
        <Link
          href="/fleet"
          className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg text-lg font-semibold transition-colors"
        >
          Mitarbeiter einstellen
        </Link>
      </div>

      {error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 font-medium">API nicht erreichbar</p>
          <p className="text-red-600 text-sm mt-1">{error}</p>
          <p className="text-gray-500 text-sm mt-2">
            Starten Sie die API mit: <code className="bg-gray-100 px-1 rounded">docker compose up -d</code>
          </p>
        </div>
      ) : fleet && fleet.total === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
          <p className="text-gray-500 text-lg">Noch keine AI-Mitarbeiter eingestellt.</p>
          <p className="text-gray-400 mt-2">
            Nutzen Sie den gruenen Button oder: <code className="bg-gray-100 px-1 rounded">nomos hire</code>
          </p>
        </div>
      ) : fleet ? (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Name</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Rolle</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Risiko</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Status</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Compliance</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Erstellt</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {fleet.agents.map((agent) => (
                <tr key={agent.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <Link href={`/agent/${agent.id}`} className="text-blue-600 hover:underline font-medium">
                      {agent.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{agent.role}</td>
                  <td className="px-4 py-3"><StatusBadge status={agent.risk_class} /></td>
                  <td className="px-4 py-3"><StatusBadge status={agent.status} /></td>
                  <td className="px-4 py-3"><StatusBadge status={agent.compliance_status} /></td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {new Date(agent.created_at).toLocaleDateString("de-AT")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="px-4 py-3 bg-gray-50 text-sm text-gray-500">
            {fleet.total} Agent{fleet.total !== 1 ? "en" : ""} registriert
          </div>
        </div>
      ) : null}
    </div>
  );
}
