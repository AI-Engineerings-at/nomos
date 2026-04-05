// nomos-plugin/src/api-client.ts

export interface AuditEntry {
  agent_id: string;
  event_type: string;
  payload: Record<string, unknown>;
}

export interface ComplianceResult {
  passed: boolean;
  missing: string[];
  error?: string;
}

export interface PIIFilterResult {
  filtered: string;
  pii_count: number;
  matches: Array<{ type: string; start: number; end: number }>;
}

export interface BudgetResult {
  allowed: boolean;
  remaining: number;
  error?: string;
  status?: string;   // "normal" | "warning" | "exceeded" | "unknown_agent"
  reason?: string;
}

export interface AuditResult {
  hash: string;
  id?: number;
}

export class NomOSApiClient {
  private readonly headers: Record<string, string>;

  constructor(private readonly baseUrl: string, apiKey?: string) {
    this.headers = {
      "Content-Type": "application/json",
      ...(apiKey ? { "X-NomOS-API-Key": apiKey } : {}),
    };
  }

  async checkCompliance(agentId: string): Promise<ComplianceResult> {
    try {
      const res = await fetch(`${this.baseUrl}/api/compliance/gate`, {
        method: "POST",
        headers: this.headers,
        body: JSON.stringify({ agent_id: agentId }),
      });
      if (!res.ok) return { passed: false, missing: [], error: `HTTP ${res.status}` };
      const data = await res.json();
      // API returns ComplianceResponse { status, missing_documents, errors, warnings }
      // Map to internal ComplianceResult format
      return {
        passed: data.status === "passed",
        missing: data.missing_documents ?? [],
        error: data.errors?.length > 0 ? data.errors.join(", ") : undefined,
      };
    } catch (err) {
      return { passed: false, missing: [], error: String(err) };
    }
  }

  async addAuditEntry(entry: AuditEntry): Promise<AuditResult> {
    try {
      const res = await fetch(`${this.baseUrl}/api/audit/entry`, {
        method: "POST",
        headers: this.headers,
        body: JSON.stringify(entry),
      });
      return await res.json() as AuditResult;
    } catch {
      return { hash: "" };
    }
  }

  async filterPII(text: string): Promise<PIIFilterResult> {
    try {
      const res = await fetch(`${this.baseUrl}/api/pii/filter`, {
        method: "POST",
        headers: this.headers,
        body: JSON.stringify({ text }),
      });
      return await res.json() as PIIFilterResult;
    } catch {
      return { filtered: text, pii_count: 0, matches: [] };
    }
  }

  async checkBudget(agentId: string, estimatedCost: number): Promise<BudgetResult> {
    try {
      const res = await fetch(`${this.baseUrl}/api/budget/check`, {
        method: "POST",
        headers: this.headers,
        body: JSON.stringify({ agent_id: agentId, estimated_cost: estimatedCost }),
      });
      if (!res.ok) {
        return { allowed: false, remaining: 0, error: `HTTP ${res.status}` };
      }
      return await res.json() as BudgetResult;
    } catch {
      return { allowed: false, remaining: 0, error: "API unreachable" };
    }
  }

  async sendHeartbeat(agentId: string, status: Record<string, unknown>): Promise<boolean> {
    try {
      const res = await fetch(`${this.baseUrl}/api/agents/${agentId}/heartbeat`, {
        method: "POST",
        headers: this.headers,
        body: JSON.stringify({ metrics: status }),
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  async healthCheck(): Promise<boolean> {
    try {
      const res = await fetch(`${this.baseUrl}/health`, {
        method: "GET",
        headers: this.headers,
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  async pauseAgent(agentId: string): Promise<boolean> {
    try {
      const res = await fetch(`${this.baseUrl}/api/agents/${agentId}/pause`, {
        method: "POST",
        headers: this.headers,
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  async reportIncident(agentId: string, description: string, severity: string): Promise<boolean> {
    try {
      const res = await fetch(`${this.baseUrl}/api/incidents`, {
        method: "POST",
        headers: this.headers,
        body: JSON.stringify({
          log_entry: description,
          agent_id: agentId,
          context: { severity, source: "nomos-plugin" },
        }),
      });
      return res.ok;
    } catch {
      return false;
    }
  }
}
