/** English translations — NomOS Console */
import type { TranslationKey } from './de';

export const en: Record<TranslationKey, string> = {
  // Meta
  'app.title': 'NomOS — Your Team Under Control',
  'app.description': 'Compliance Control Plane for your AI employees',

  // Navigation — Employee Metaphor
  'nav.dashboard': 'Overview',
  'nav.myTeam': 'My Team',
  'nav.hire': 'Hire',
  'nav.approvals': 'Approvals',
  'nav.costs': 'Costs',
  'nav.compliance': 'Legal Check',
  'nav.audit': 'Audit Log',
  'nav.diagnostics': 'Health Check',
  'nav.users': 'Users',
  'nav.settings': 'Settings',
  'nav.myAgents': 'My Employees',
  'nav.tasks': 'Tasks',
  'nav.help': 'Help',
  'nav.complianceReports': 'Compliance Reports',

  // Auth
  'auth.login': 'Sign In',
  'auth.logout': 'Sign Out',
  'auth.email': 'Email address',
  'auth.password': 'Password',
  'auth.submit': 'Sign In',
  'auth.forgotPassword': 'Forgot password?',
  'auth.loginTitle': 'Welcome to NomOS',
  'auth.loginSubtitle': 'Sign in to manage your team.',
  'auth.totpTitle': 'Two-Factor Authentication',
  'auth.totpSubtitle': 'Enter the 6-digit code from your authenticator app.',
  'auth.totpLabel': 'Authentication code',
  'auth.totpSubmit': 'Confirm',
  'auth.invalidCredentials': 'Invalid email or password. Please try again.',
  'auth.accountLocked': 'Your account has been locked. Please wait 15 minutes or contact your administrator.',
  'auth.totpInvalid': 'The code you entered is invalid. Please check your authenticator app.',
  'auth.sessionExpired': 'Your session has expired. Please sign in again.',

  // Header
  'header.theme.light': 'Light mode',
  'header.theme.dark': 'Dark mode',
  'header.theme.toggle': 'Toggle color scheme',
  'header.lang.toggle': 'Switch language',
  'header.user.menu': 'User menu',
  'header.user.profile': 'My Profile',
  'header.user.settings': 'Settings',

  // Common Actions
  'action.retry': 'Retry',
  'action.cancel': 'Cancel',
  'action.save': 'Save',
  'action.delete': 'Delete',
  'action.edit': 'Edit',
  'action.create': 'Create',
  'action.close': 'Close',
  'action.confirm': 'Confirm',
  'action.back': 'Back',
  'action.next': 'Next',
  'action.search': 'Search',
  'action.filter': 'Filter',
  'action.export': 'Export',
  'action.contactAdmin': 'Contact administrator',

  // Status — Employee Metaphor
  'status.online': 'Active',
  'status.paused': 'Paused',
  'status.offline': 'Offline',
  'status.killed': 'Terminated',
  'status.deploying': 'Onboarding',
  'status.error': 'Disrupted',

  // Errors — Brand Voice: direct, honest, helpful
  'error.title': 'Something went wrong',
  'error.description': 'An unexpected error occurred. Our team has been notified.',
  'error.network': 'Connection to the server was lost. Please check your network.',
  'error.notFound': 'This page could not be found.',
  'error.forbidden': 'You do not have permission for this action.',
  'error.serverError': 'The server could not process your request. Please try again later.',
  'error.timeout': 'The request took too long. Please try again.',
  'error.validation': 'Please check your input.',
  'error.reportSent': 'The error has been reported automatically.',

  // Empty States — helpful with CTA
  'empty.team': 'No employees hired yet.',
  'empty.teamCta': 'Hire now',
  'empty.tasks': 'No open tasks.',
  'empty.tasksCta': 'Create task',
  'empty.approvals': 'No pending approvals.',
  'empty.audit': 'No audit entries yet.',
  'empty.generic': 'Nothing to see here yet.',

  // Loading
  'loading.default': 'Loading...',
  'loading.team': 'Loading team...',
  'loading.data': 'Fetching data...',

  // Table
  'table.noResults': 'No results found.',
  'table.sortAsc': 'Sort ascending',
  'table.sortDesc': 'Sort descending',

  // Toast
  'toast.success': 'Success',
  'toast.error': 'Error',
  'toast.warning': 'Warning',
  'toast.info': 'Info',

  // Accessibility
  'a11y.skipToContent': 'Skip to main content',
  'a11y.mainContent': 'Main content',
  'a11y.navigation': 'Main navigation',
  'a11y.closeDialog': 'Close dialog',
  'a11y.openMenu': 'Open menu',
  'a11y.closeMenu': 'Close menu',
  'a11y.logoAlt': 'NomOS Eagle Logo',
  'a11y.required': 'Required field',
};
