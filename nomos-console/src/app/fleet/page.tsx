import Link from "next/link";

export default function FleetPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Fleet Management</h1>
      <p className="text-gray-500 mb-8">
        Verwalten Sie Ihre AI-Mitarbeiter. Nutzen Sie die CLI fuer erweiterte Funktionen.
      </p>
      <div className="grid gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="font-semibold text-lg mb-2">Neuen Mitarbeiter einstellen</h2>
          <p className="text-gray-500 text-sm mb-4">
            Erstellen Sie einen neuen AI-Agenten mit vollstaendiger EU AI Act Compliance.
          </p>
          <code className="block bg-gray-900 text-green-400 p-4 rounded text-sm">
            nomos hire --name &quot;Mani Ruf&quot; --role &quot;external-secretary&quot; \<br />
            &nbsp;&nbsp;--company &quot;Ihre Firma GmbH&quot; --email &quot;agent@firma.at&quot; \<br />
            &nbsp;&nbsp;--output-dir ./agents/mani-ruf<br /><br />
            nomos gate --agent-dir ./agents/mani-ruf
          </code>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="font-semibold text-lg mb-2">Compliance pruefen</h2>
          <code className="block bg-gray-900 text-green-400 p-4 rounded text-sm">
            nomos verify --agent-dir ./agents/mani-ruf
          </code>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="font-semibold text-lg mb-2">Audit Trail verifizieren</h2>
          <p className="text-gray-500 text-sm mb-4">
            Kryptographisch nachweisbarer Audit Trail (SHA-256 Hash Chain).
          </p>
          <code className="block bg-gray-900 text-green-400 p-4 rounded text-sm">
            nomos audit --agent-dir ./agents/mani-ruf --verify
          </code>
        </div>
      </div>
      <div className="mt-8">
        <Link href="/" className="text-blue-600 hover:underline">Zurueck zur Uebersicht</Link>
      </div>
    </div>
  );
}
