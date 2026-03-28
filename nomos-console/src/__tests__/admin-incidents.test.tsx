import { createPageTest } from './page-test-factory';
import IncidentsPage from '@/app/admin/incidents/page';
import { mockIncidents, mockIncidentsEmpty } from './fixtures';

createPageTest({
  name: 'Admin Incidents',
  component: IncidentsPage,
  mockPath: '/incidents',
  dataFixture: mockIncidents,
  emptyFixture: mockIncidentsEmpty,
  expectedText: /incidents.title|pii_leak/i,
});
