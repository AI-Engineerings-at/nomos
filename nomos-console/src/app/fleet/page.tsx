"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function HirePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const form = new FormData(e.currentTarget);
    const data = {
      name: form.get("name") as string,
      role: form.get("role") as string,
      company: form.get("company") as string,
      email: form.get("email") as string,
      risk_class: form.get("risk_class") as string,
    };

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8060";
      const res = await fetch(`${API_URL}/api/agents`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Unbekannter Fehler" }));
        throw new Error(err.detail ?? `Fehler: ${res.status}`);
      }

      const agent = await res.json();
      router.push(`/agent/${agent.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler bei der Erstellung");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Neuen AI-Mitarbeiter einstellen</h1>
      <p className="text-gray-500 mb-8">
        Erstellen Sie einen EU AI Act konformen AI-Agenten. Alle Pflichtfelder ausfuellen.
      </p>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800 font-medium">Fehler</p>
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
            Name des Agenten *
          </label>
          <input
            id="name"
            name="name"
            type="text"
            required
            placeholder="z.B. Mani Ruf"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
          />
        </div>

        <div>
          <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-1">
            Rolle *
          </label>
          <input
            id="role"
            name="role"
            type="text"
            required
            placeholder="z.B. external-secretary"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
          />
        </div>

        <div>
          <label htmlFor="company" className="block text-sm font-medium text-gray-700 mb-1">
            Unternehmen *
          </label>
          <input
            id="company"
            name="company"
            type="text"
            required
            placeholder="z.B. AI Engineering"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
          />
        </div>

        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
            E-Mail *
          </label>
          <input
            id="email"
            name="email"
            type="email"
            required
            placeholder="z.B. agent@firma.at"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
          />
        </div>

        <div>
          <label htmlFor="risk_class" className="block text-sm font-medium text-gray-700 mb-1">
            Risikoeinstufung (EU AI Act Art. 6)
          </label>
          <select
            id="risk_class"
            name="risk_class"
            defaultValue="limited"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
          >
            <option value="minimal">Minimal</option>
            <option value="limited">Limited (Standard)</option>
            <option value="high">High</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg text-lg font-semibold transition-colors"
        >
          {loading ? "Wird erstellt..." : "Agent erstellen"}
        </button>
      </form>
    </div>
  );
}
