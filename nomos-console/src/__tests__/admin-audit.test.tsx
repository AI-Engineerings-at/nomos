import { createPageTest } from './page-test-factory';
import AuditPage from '@/app/admin/audit/page';
import { mockAudit, mockAuditEmpty } from './fixtures';

createPageTest({
  name: 'Admin Audit',
  component: AuditPage,
  mockPath: '/audit',
  dataFixture: mockAudit,
  emptyFixture: mockAuditEmpty,
  expectedText: /audit.title|agent.created/i,
});
