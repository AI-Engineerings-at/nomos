import { createPageTest } from './page-test-factory';
import TasksPage from '@/app/admin/tasks/page';
import { mockTasks, mockTasksEmpty } from './fixtures';

createPageTest({
  name: 'Admin Tasks',
  component: TasksPage,
  mockPath: '/tasks',
  dataFixture: mockTasks,
  emptyFixture: mockTasksEmpty,
  expectedText: /tasks.title|analyse social media/i,
});
