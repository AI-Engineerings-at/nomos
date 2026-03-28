import { createPageTest } from './page-test-factory';
import HirePage from '@/app/admin/hire/page';
import { mockFleet } from './fixtures';

createPageTest({
  name: 'Admin Hire',
  component: HirePage,
  mockPath: '/fleet',
  dataFixture: mockFleet,
  emptyFixture: { agents: [], total: 0 },
  expectedText: 'hire.title',
  skipLoading: true,
  skipError: true,
  skipEmpty: true,
});
