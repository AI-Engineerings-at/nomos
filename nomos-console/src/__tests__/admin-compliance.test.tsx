import { createPageTest } from './page-test-factory';
import CompliancePage from '@/app/admin/compliance/page';
import { mockComplianceMatrix, mockComplianceMatrixEmpty } from './fixtures';

createPageTest({
  name: 'Admin Compliance',
  component: CompliancePage,
  mockPath: '/compliance/matrix',
  dataFixture: mockComplianceMatrix,
  emptyFixture: mockComplianceMatrixEmpty,
  expectedText: /compliance.title|Max Social/i,
});
