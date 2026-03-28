import { createPageTest } from './page-test-factory';
import AppTasksPage from '@/app/app/tasks/page';
import { mockTasks, mockTasksEmpty } from './fixtures';

createPageTest({
  name: 'App Tasks',
  component: AppTasksPage,
  mockPath: '/tasks',
  dataFixture: mockTasks,
  emptyFixture: mockTasksEmpty,
  expectedText: /tasks.title|analyse social media/i,
});
