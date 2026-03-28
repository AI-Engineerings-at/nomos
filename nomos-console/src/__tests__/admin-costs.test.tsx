import { createPageTest } from './page-test-factory';
import CostsPage from '@/app/admin/costs/page';
import { mockCosts, mockCostsEmpty } from './fixtures';

createPageTest({
  name: 'Admin Costs',
  component: CostsPage,
  mockPath: '/costs',
  dataFixture: mockCosts,
  emptyFixture: mockCostsEmpty,
  expectedText: /costs.title|42.5/i,
});
