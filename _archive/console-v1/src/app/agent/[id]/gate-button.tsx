"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function GateButton({ agentId, complianceStatus }: { agentId: string; complianceStatus: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  if (complianceStatus === "passed") {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <p className="text-green-800 font-medium">Compliance: PASSED</p>
        <p className="text-green-600 text-sm">Alle Compliance-Dokumente vorhanden. Agent ist bereit.</p>
      </div>
    );
  }

  async function handleGate() {
    setLoading(true);
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8060";
      const res = await fetch(`${API_URL}/api/agents/${agentId}/gate`, { method: "POST" });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Fehler" }));
        throw new Error(err.detail);
      }
      const data = await res.json();
      setResult(data.status);
      router.refresh();
    } catch {
      setResult("error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
      <p className="text-yellow-800 font-medium">Compliance: BLOCKED</p>
      <p className="text-yellow-600 text-sm mb-3">Compliance-Dokumente muessen generiert werden.</p>
      <button
        onClick={handleGate}
        disabled={loading}
        className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-medium transition-colors"
      >
        {loading ? "Wird generiert..." : "Compliance-Dokumente generieren"}
      </button>
      {result === "passed" && (
        <p className="text-green-600 text-sm mt-2">Dokumente erfolgreich generiert!</p>
      )}
      {result === "error" && (
        <p className="text-red-600 text-sm mt-2">Fehler bei der Generierung.</p>
      )}
    </div>
  );
}
