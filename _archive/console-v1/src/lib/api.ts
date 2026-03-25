/**
 * NomOS API client — fetches from the Fleet API.
 * API URL configurable via NEXT_PUBLIC_API_URL env var.
 */

// Server-side: use internal Docker URL if available, otherwise public URL
// Client-side: always uses NEXT_PUBLIC_API_URL (baked into browser bundle)
const API_URL = typeof window === "undefined"
  ? (process.env.NOMOS_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8060")
  : (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8060");

export interface Agent {
  id: string;
  name: string;
  role: string;
  company: string;
  email: string;
  risk_class: string;
  status: string;
  manifest_hash: string;
  compliance_status: string;
  created_at: string;
  updated_at: string;
}

export interface FleetResponse {
  agents: Agent[];
  total: number;
}

export interface ComplianceResponse {
  agent_id: string;
  status: string;
  missing_documents: string[];
  errors: string[];
  warnings: string[];
}

export interface AuditEntry {
  sequence: number;
  event_type: string;
  agent_id: string;
  data: Record<string, unknown>;
  chain_hash: string;
  timestamp: string;
}

export interface AuditResponse {
  agent_id: string;
  entries: AuditEntry[];
  total: number;
}

export interface AuditVerifyResponse {
  agent_id: string;
  valid: boolean;
  entries_checked: number;
  errors: string[];
}

export async function fetchFleet(): Promise<FleetResponse> {
  const res = await fetch(`${API_URL}/api/fleet`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Fleet API error: ${res.status}`);
  return res.json();
}

export async function fetchAgent(id: string): Promise<Agent> {
  const res = await fetch(`${API_URL}/api/fleet/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Agent not found: ${id}`);
  return res.json();
}

export async function fetchCompliance(id: string): Promise<ComplianceResponse> {
  const res = await fetch(`${API_URL}/api/agents/${id}/compliance`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Compliance check failed: ${id}`);
  return res.json();
}

export async function fetchAudit(id: string): Promise<AuditResponse> {
  const res = await fetch(`${API_URL}/api/agents/${id}/audit`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Audit fetch failed: ${id}`);
  return res.json();
}

export async function fetchAuditVerify(id: string): Promise<AuditVerifyResponse> {
  const res = await fetch(`${API_URL}/api/audit/verify/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Audit verify failed: ${id}`);
  return res.json();
}

export async function createAgent(data: {
  name: string;
  role: string;
  company: string;
  email: string;
  risk_class?: string;
}): Promise<Agent> {
  const res = await fetch(`${API_URL}/api/agents`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail ?? `Create failed: ${res.status}`);
  }
  return res.json();
}
