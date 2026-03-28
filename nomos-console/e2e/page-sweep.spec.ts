import { test, expect } from '@playwright/test';

const ROUTES = [
  { path: '/admin', name: 'Dashboard', heading: /dashboard|willkommen|greeting/i },
  { path: '/admin/team', name: 'Team', heading: /team|mitarbeiter/i },
  { path: '/admin/hire', name: 'Hire', heading: /hire|einstellen/i },
  { path: '/admin/approvals', name: 'Approvals', heading: /approvals|freigaben/i },
  { path: '/admin/costs', name: 'Costs', heading: /costs|kosten/i },
  { path: '/admin/audit', name: 'Audit', heading: /audit|protokoll/i },
  { path: '/admin/compliance', name: 'Compliance', heading: /compliance|rechts-check/i },
  { path: '/admin/diagnostics', name: 'Diagnostics', heading: /diagnostics|gesundheitscheck/i },
  { path: '/admin/incidents', name: 'Incidents', heading: /incidents|vorfaelle/i },
  { path: '/admin/users', name: 'Users', heading: /users|nutzer/i },
  { path: '/admin/settings', name: 'Settings', heading: /settings|einstellungen/i },
  { path: '/admin/tasks', name: 'Tasks', heading: /tasks|aufgaben/i },
  { path: '/app', name: 'App Home', heading: /app|mitarbeiter/i },
  { path: '/app/tasks', name: 'User Tasks', heading: /tasks|aufgaben/i },
  { path: '/app/help', name: 'Help', heading: /help|hilfe/i },
  { path: '/compliance', name: 'Compliance Reports', heading: /compliance/i },
];

test.describe('Page Sweep', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the fleet API for all pages to avoid loading states sticking
    await page.route('**/api/fleet', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ agents: [], total: 0 }) });
    });
    // Mock other common endpoints
    await page.route('**/api/costs', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ costs: [], total: 0 }) });
    });
    await page.route('**/api/approvals', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ approvals: [], total: 0 }) });
    });
    await page.route('**/api/incidents', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ incidents: [], total: 0 }) });
    });
    await page.route('**/api/audit*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ entries: [], total: 0 }) });
    });
    await page.route('**/api/settings', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({
        gateway_url: 'http://test', retention_days: 30, pii_filter_mode: 'standard',
        openai_api_key_set: false, anthropic_api_key_set: false, nvidia_api_key_set: false
      }) });
    });
    await page.route('**/api/health', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ status: 'healthy' }) });
    });
    await page.route('**/api/compliance/matrix', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ matrix: [], total: 0 }) });
    });
    await page.route('**/api/users', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ users: [], total: 0 }) });
    });
    await page.route('**/api/tasks', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ tasks: [], total: 0 }) });
    });
  });

  for (const route of ROUTES) {
    test(`visits ${route.name} (${route.path})`, async ({ page }) => {
      await page.goto(route.path);
      // Wait for the heading to appear (ignoring case via regex)
      await expect(page.locator('h1')).toContainText(route.heading);
      // Check for Sidebar
      await expect(page.locator('nav')).toBeVisible();
    });
  }

  test('visits Agent Detail (/admin/team/agent-001)', async ({ page }) => {
    await page.route('**/api/fleet/agent-001', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ id: 'agent-001', name: 'Test Agent', role: 'Tester', status: 'running', compliance_status: 'passed' }) });
    });
    await page.route('**/api/agents/agent-001/audit', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ entries: [], total: 0 }) });
    });
    await page.route('**/api/costs/agent-001', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ total_cost_eur: 0, budget_limit_eur: 100 }) });
    });
    await page.route('**/api/agents/agent-001/compliance', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ status: 'passed', missing_documents: [] }) });
    });

    await page.goto('/admin/team/agent-001');
    await expect(page.locator('h1')).toContainText(/Test Agent/i);
  });

  test('visits Chat (/app/chat/agent-001)', async ({ page }) => {
    await page.route('**/api/fleet/agent-001', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ id: 'agent-001', name: 'Test Agent', role: 'Tester', status: 'running' }) });
    });
    await page.goto('/app/chat/agent-001');
    await expect(page.locator('h1')).toContainText(/Test Agent/i);
    // Check for chat input
    await expect(page.locator('textarea, input[type="text"]')).toBeVisible();
  });
});
