import { createPageTest } from './page-test-factory';
import ApprovalsPage from '@/app/admin/approvals/page';
import { mockApprovals, mockApprovalsEmpty } from './fixtures';

createPageTest({
  name: 'Admin Approvals',
  component: ApprovalsPage,
  mockPath: '/approvals',
  dataFixture: mockApprovals,
  emptyFixture: mockApprovalsEmpty,
  expectedText: /approvals.title|send_email/i,
});
