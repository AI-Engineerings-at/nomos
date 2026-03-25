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

/** Compliance matrix cell for one agent and one document. */
export interface ComplianceMatrixCell {
  agent_id: string;
  agent_name: string;
  document_type: string;
  status: 'valid' | 'expiring' | 'missing';
  last_updated: string | null;
  expires_at: string | null;
}

/** Full compliance matrix response from the API. */
export interface ComplianceMatrixResponse {
  matrix: ComplianceMatrixCell[];
  agents: string[];
  document_types: string[];
  health_score: number;
}

/** Health status for a system component. */
export interface HealthStatus {
  service: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  latency_ms: number;
  last_check: string;
  details: Record<string, unknown>;
}

/** Overall health response. */
export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  services: HealthStatus[];
  uptime_seconds: number;
  version: string;
}

/** Agent heartbeat entry. */
export interface HeartbeatEntry {
  agent_id: string;
  agent_name: string;
  last_seen: string;
  status: 'running' | 'paused' | 'killed' | 'deploying' | 'error';
  memory_mb: number;
  cpu_percent: number;
}

/** Daily cost data point for trend charts. */
export interface DailyCostEntry {
  date: string;
  cost_eur: number;
}

/** Full cost response with daily breakdown. */
export interface CostDetailResponse {
  costs: CostEntry[];
  total: number;
  total_cost_eur: number;
  budget_total_eur: number;
  daily_trend: DailyCostEntry[];
}

/** NomOS user account for admin management. */
export interface UserAccount {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user' | 'officer';
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
  pii_filter_mode: 'strict' | 'standard' | 'off';
}

/** Task entry. */
export interface TaskEntry {
  id: string;
  agent_id: string;
  agent_name: string;
  title: string;
  description: string;
  status: 'queued' | 'assigned' | 'running' | 'review' | 'done';
  priority: 'low' | 'medium' | 'high' | 'critical';
  created_by: string;
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
    default:
      return 'offline';
  }
}
