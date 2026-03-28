import { createPageTest } from './page-test-factory';
import SettingsPage from '@/app/admin/settings/page';
import { mockSettings } from './fixtures';

createPageTest({
  name: 'Admin Settings',
  component: SettingsPage,
  mockPath: '/settings',
  dataFixture: mockSettings,
  emptyFixture: null,
  expectedText: 'settings.title',
  skipEmpty: true,
});
