import { createPageTest } from './page-test-factory';
import UsersPage from '@/app/admin/users/page';
import { mockUsers, mockUsersEmpty } from './fixtures';

createPageTest({
  name: 'Admin Users',
  component: UsersPage,
  mockPath: '/users',
  dataFixture: mockUsers,
  emptyFixture: mockUsersEmpty,
  expectedText: /users.title|admin@nomos.local/i,
});
