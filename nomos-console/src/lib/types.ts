/**
 * NomOS Console — Shared TypeScript types matching API schemas.
 * These types mirror the Pydantic models in nomos-api/nomos_api/schemas.py.
 */

export interface Agent {
  id: string;
  name: string;
  role: string;
  company: string;
  email: string;
  risk_class: 'minimal' | 'limited' | 'high';
  status: 'running' | 'paused' | 'killed' | 'deploying' | 'error';
  manifest_hash: string;
  compliance_status: string;
  created_at: string;
  updated_at: string;
}

export interface FleetResponse {
  agents: Agent[];
  total: number;
}

export interface CostEntry {
  agent_id: string;
  total_cost_eur: number;
  budget_limit_eur: number;
  budget_status: string;
  percent_used: number;
}

export interface CostOverviewResponse {
  costs: CostEntry[];
  total: number;
}

export interface ApprovalEntry {
  id: string;
  agent_id: string;
  action: string;
  description: string;
  status: 'pending' | 'approved' | 'rejected' | 'expired';
  requested_at: string;
  resolved_at: string | null;
  resolved_by: string | null;
  timeout_minutes: number;
}

export interface ApprovalListResponse {
  approvals: ApprovalEntry[];
  total: number;
}

export interface IncidentEntry {
  id: number;
  agent_id: string;
  incident_type: string;
  description: string;
  severity: string;
  status: 'detected' | 'reported' | 'resolved';
  detected_at: string;
  report_deadline: string;
}

export interface IncidentListResponse {
  incidents: IncidentEntry[];
  total: number;
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

export interface ComplianceEntry {
  agent_id: string;
  status: string;
  missing_documents: string[];
  errors: string[];
  warnings: string[];
}

export interface ProxyChatRequest {
  agent_id: string;
  message: string;
  session_id?: string | null;
}

export interface ProxyChatResponse {
  response: string;
  session_id: string;
}

export interface ProxyStatusResponse {
  status: 'online' | 'offline';
  version: string | null;
  agents_count: number | null;
}

export interface AgentCreateRequest {
  name: string;
  role: string;
  company: string;
  email: string;
  risk_class: 'minimal' | 'limited' | 'high';
}

/** Chat message for local UI state. */
export interface ChatMessage {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: string;
}

/** Agent status mapped to Badge component status type. */
export type AgentBadgeStatus = 'online' | 'paused' | 'offline' | 'killed' | 'deploying' | 'error';

/** Map API agent status to Badge status. */
export function agentStatusToBadge(status: string): AgentBadgeStatus {
  switch (status) {
    case 'running':
      return 'online';
    case 'paused':
      return 'paused';
    case 'killed':
      return 'killed';
    case 'deploying':
      return 'deploying';
    case 'error':
      return 'error';
    default:
      return 'offline';
  }
}
