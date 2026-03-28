import { createPageTest } from './page-test-factory';
import DiagnosticsPage from '@/app/admin/diagnostics/page';
import { mockHealth } from './fixtures';

createPageTest({
  name: 'Admin Diagnostics',
  component: DiagnosticsPage,
  mockPath: '/health',
  dataFixture: mockHealth,
  emptyFixture: null, // Health usually isn't empty
  expectedText: /diagnostics.title|nomos-api/i,
});
