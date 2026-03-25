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
  found: Array<{ type: string; position: number[] }>;
}

export interface BudgetResult {
  allowed: boolean;
  remaining: number;
  error?: string;
}

export interface AuditResult {
  hash: string;
  id?: string;
}

export class NomOSApiClient {
  constructor(private readonly baseUrl: string) {}

  async checkCompliance(agentId: string): Promise<ComplianceResult> {
    try {
      const res = await fetch(`${this.baseUrl}/api/compliance/gate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId }),
      });
      if (!res.ok) return { passed: false, missing: [], error: `HTTP ${res.status}` };
      return await res.json() as ComplianceResult;
    } catch (err) {
      return { passed: false, missing: [], error: String(err) };
    }
  }

  async addAuditEntry(entry: AuditEntry): Promise<AuditResult> {
    try {
      const res = await fetch(`${this.baseUrl}/api/audit/entry`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      return await res.json() as PIIFilterResult;
    } catch {
      return { filtered: text, found: [] };
    }
  }

  async checkBudget(agentId: string, estimatedCost: number): Promise<BudgetResult> {
    try {
      const res = await fetch(`${this.baseUrl}/api/budget/check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId, estimated_cost: estimatedCost }),
      });
      return await res.json() as BudgetResult;
    } catch {
      return { allowed: false, remaining: 0, error: "API unreachable" };
    }
  }

  async sendHeartbeat(agentId: string, status: Record<string, unknown>): Promise<boolean> {
    try {
      const res = await fetch(`${this.baseUrl}/api/agents/${agentId}/heartbeat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(status),
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  async healthCheck(): Promise<boolean> {
    try {
      const res = await fetch(`${this.baseUrl}/api/health`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
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
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId, description, severity }),
      });
      return res.ok;
    } catch {
      return false;
    }
  }
}
