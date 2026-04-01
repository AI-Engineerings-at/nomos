/**
 * Shared test fixtures — realistic mock data matching API types.
 */
import type {
  Agent,
  FleetResponse,
  CostOverviewResponse,
  CostEntry,
  ApprovalListResponse,
  ApprovalEntry,
  IncidentListResponse,
  IncidentEntry,
  AuditEntry,
  AuditResponse,
  ComplianceMatrixEntry,
  ComplianceMatrixResponse,
  UserAccount,
  UserListResponse,
  SystemSettings,
  TaskEntry,
  TaskListResponse,
  HealthResponse,
  ComplianceEntry,
} from '@/lib/types';

export const mockAgent: Agent = {
  id: 'agent-001',
  name: 'Max Social',
  role: 'Social Media Manager',
  company: 'TestGmbH',
  email: 'max@test.local',
  risk_class: 'limited',
  status: 'running',
  manifest_hash: 'abc123def456',
  compliance_status: 'passed',
  heartbeat_at: '2026-03-27T10:00:00Z',
  created_at: '2026-03-20T09:00:00Z',
  updated_at: '2026-03-27T10:00:00Z',
};

export const mockAgent2: Agent = {
  id: 'agent-002',
  name: 'Lisa Research',
  role: 'Researcher',
  company: 'TestGmbH',
  email: 'lisa@test.local',
  risk_class: 'minimal',
  status: 'paused',
  manifest_hash: 'xyz789',
  compliance_status: 'failed',
  heartbeat_at: '2026-03-27T09:30:00Z',
  created_at: '2026-03-21T09:00:00Z',
  updated_at: '2026-03-27T09:30:00Z',
};

export const mockFleet: FleetResponse = {
  agents: [mockAgent, mockAgent2],
  total: 2,
};

export const mockFleetEmpty: FleetResponse = {
  agents: [],
  total: 0,
};

export const mockCostEntry: CostEntry = {
  agent_id: 'agent-001',
  total_cost_eur: 42.5,
  budget_limit_eur: 100,
  budget_status: 'normal',
  percent_used: 42.5,
};

export const mockCosts: CostOverviewResponse = {
  costs: [
    mockCostEntry,
    {
      agent_id: 'agent-002',
      total_cost_eur: 18.0,
      budget_limit_eur: 50,
      budget_status: 'normal',
      percent_used: 36,
    },
  ],
  total: 2,
};

export const mockCostsEmpty: CostOverviewResponse = {
  costs: [],
  total: 0,
};

export const mockApproval: ApprovalEntry = {
  id: 'appr-001',
  agent_id: 'agent-001',
  action: 'send_email',
  description: 'Send newsletter to 500 subscribers',
  status: 'pending',
  requested_at: '2026-03-27T09:00:00Z',
  resolved_at: null,
  resolved_by: null,
  timeout_minutes: 30,
};

export const mockApprovals: ApprovalListResponse = {
  approvals: [mockApproval],
  total: 1,
};

export const mockApprovalsEmpty: ApprovalListResponse = {
  approvals: [],
  total: 0,
};

export const mockIncident: IncidentEntry = {
  id: 1,
  agent_id: 'agent-001',
  incident_type: 'pii_leak',
  description: 'PII detected in outgoing response',
  severity: 'high',
  status: 'detected',
  detected_at: '2026-03-27T08:00:00Z',
  report_deadline: '2026-03-30T08:00:00Z',
};

export const mockIncidents: IncidentListResponse = {
  incidents: [mockIncident],
  total: 1,
};

export const mockIncidentsEmpty: IncidentListResponse = {
  incidents: [],
  total: 0,
};

export const mockAuditEntry: AuditEntry = {
  sequence: 1,
  event_type: 'agent.created',
  agent_id: 'agent-001',
  data: { name: 'Max Social' },
  chain_hash: 'sha256:abcdef1234567890',
  timestamp: '2026-03-27T09:00:00Z',
};

export const mockAudit: AuditResponse = {
  agent_id: 'agent-001',
  entries: [mockAuditEntry],
  total: 1,
};

export const mockAuditEmpty: AuditResponse = {
  agent_id: 'agent-001',
  entries: [],
  total: 0,
};

export const mockComplianceMatrix: ComplianceMatrixResponse = {
  matrix: [
    {
      agent_id: 'agent-001',
      agent_name: 'Max Social',
      status: 'passed',
      missing_docs: [],
      risk_class: 'limited',
    },
    {
      agent_id: 'agent-002',
      agent_name: 'Lisa Research',
      status: 'failed',
      missing_docs: ['risk_assessment', 'dsgvo_art_13'],
      risk_class: 'minimal',
    },
  ],
  total: 2,
};

export const mockComplianceMatrixEmpty: ComplianceMatrixResponse = {
  matrix: [],
  total: 0,
};

export const mockComplianceEntry: ComplianceEntry = {
  agent_id: 'agent-001',
  status: 'passed',
  missing_documents: [],
  errors: [],
  warnings: [],
};

export const mockUser: UserAccount = {
  id: 'u-1',
  email: 'admin@nomos.local',
  name: 'Joe Admin',
  role: 'admin',
  totp_enabled: true,
  session_timeout_hours: 8,
  is_active: true,
  max_tasks: 10,
  allowed_agents: ['agent-001', 'agent-002'],
  created_at: '2026-03-20T09:00:00Z',
};

export const mockUsers: UserListResponse = {
  users: [mockUser],
  total: 1,
};

export const mockUsersEmpty: UserListResponse = {
  users: [],
  total: 0,
};

export const mockSettings: SystemSettings = {
  gateway_url: 'http://gateway:8080',
  retention_days: 90,
  pii_filter_mode: 'strict',
  openai_api_key_set: true,
  anthropic_api_key_set: false,
  nvidia_api_key_set: false,
};

export const mockTask: TaskEntry = {
  id: 'task-001',
  agent_id: 'agent-001',
  description: 'Analyse social media engagement for Q1',
  status: 'running',
  priority: 'high',
  created_by: 'u-1',
  timeout_minutes: 60,
  cost_eur: 2.5,
  created_at: '2026-03-27T09:00:00Z',
  updated_at: '2026-03-27T09:30:00Z',
};

export const mockTasks: TaskListResponse = {
  tasks: [mockTask],
  total: 1,
};

export const mockTasksEmpty: TaskListResponse = {
  tasks: [],
  total: 0,
};

export const mockHealth: HealthResponse = {
  status: 'healthy',
  service: 'nomos-api',
  version: '0.1.0',
  vault: 'healthy',
};
