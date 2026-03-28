import { createPageTest } from './page-test-factory';
import AppDashboardPage from '@/app/app/page';
import { mockFleet, mockFleetEmpty } from './fixtures';

createPageTest({
  name: 'App Dashboard',
  component: AppDashboardPage,
  mockPath: '/fleet',
  dataFixture: mockFleet,
  emptyFixture: mockFleetEmpty,
  expectedText: /app.dashboard.title|Max Social/i,
});
