import { createPageTest } from './page-test-factory';
import ComplianceDashboardPage from '@/app/compliance/page';
import { mockComplianceMatrix, mockComplianceMatrixEmpty } from './fixtures';

createPageTest({
  name: 'Compliance Dashboard',
  component: ComplianceDashboardPage,
  mockPath: '/compliance/matrix',
  dataFixture: mockComplianceMatrix,
  emptyFixture: mockComplianceMatrixEmpty,
  expectedText: /compliance.title|Max Social/i,
});
