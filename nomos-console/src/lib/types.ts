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
  status: 'created' | 'running' | 'paused' | 'killed' | 'retired' | 'deploying' | 'error';
  manifest_hash: string;
  compliance_status: string;
  heartbeat_at: string | null;
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
  status: 'pending' | 'approved' | 'denied' | 'expired';
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

/** Compliance matrix entry — per-agent summary from API. */
export interface ComplianceMatrixEntry {
  agent_id: string;
  agent_name: string;
  status: string;
  missing_docs: string[];
  risk_class: string;
}

/** Compliance matrix response from GET /api/compliance/matrix. */
export interface ComplianceMatrixResponse {
  matrix: ComplianceMatrixEntry[];
  total: number;
}

/** Overall health response — matches GET /health. */
export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  vault: string;
}

/** NomOS user account for admin management. */
export interface UserAccount {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user' | 'officer';
  totp_enabled: boolean;
  session_timeout_hours: number;
  is_active: boolean;
  max_tasks: number;
  allowed_agents: string[];
  created_at: string;
}

/** User list response. */
export interface UserListResponse {
  users: UserAccount[];
  total: number;
}

/** System settings configuration. */
export interface SystemSettings {
  gateway_url: string;
  retention_days: number;
  pii_filter_mode: string;
  openai_api_key_set: boolean;
  anthropic_api_key_set: boolean;
  nvidia_api_key_set: boolean;
}

/** Partial settings update — only provided fields are changed. */
export interface SettingsUpdateRequest {
  gateway_url?: string;
  retention_days?: number;
  pii_filter_mode?: string;
  openai_api_key?: string;
  anthropic_api_key?: string;
  nvidia_api_key?: string;
}

/** Task entry. */
export interface TaskEntry {
  id: string;
  agent_id: string;
  description: string;
  status: 'queued' | 'assigned' | 'running' | 'review' | 'done' | 'failed';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  created_by: string | null;
  timeout_minutes: number;
  cost_eur: number;
  created_at: string;
  updated_at: string;
}

/** Task list response. */
export interface TaskListResponse {
  tasks: TaskEntry[];
  total: number;
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
    case 'created':
      return 'deploying';
    case 'retired':
      return 'offline';
    default:
      return 'offline';
  }
}
