import { createPageTest } from './page-test-factory';
import HelpPage from '@/app/app/help/page';

createPageTest({
  name: 'App Help',
  component: HelpPage,
  expectedText: 'help.title',
  skipLoading: true,
  skipError: true,
  skipEmpty: true,
});
