/**
 * Test: /login page — 4 states.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';

// Import the real hooks but they are mocked globally by vitest
import { useAuth } from '@/lib/auth';
import { useNomosStore } from '@/lib/store';
import LoginPage from '@/app/login/page';

// Specific component mocks for this test file
vi.mock('@/components/auth/login-form', () => ({
  LoginForm: (props: Record<string, unknown>) =>
    React.createElement('div', { 'data-testid': 'login-form' }, 'LoginForm'),
}));

vi.mock('@/components/auth/totp-input', () => ({
  TotpInput: (props: Record<string, unknown>) =>
    React.createElement('div', { 'data-testid': 'totp-input' }, 'TotpInput'),
}));

const storeDefaults = {
  language: 'de' as const,
  theme: 'dark' as const,
  setTheme: vi.fn(),
  toggleTheme: vi.fn(),
  setLanguage: vi.fn(),
  user: null,
  setUser: vi.fn(),
  toasts: [],
  addToast: vi.fn(),
  removeToast: vi.fn(),
  sidebarCollapsed: false,
  setSidebarCollapsed: vi.fn(),
  speechRate: 1.0,
  setSpeechRate: vi.fn(),
  speechEnabled: true,
  setSpeechEnabled: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(useNomosStore).mockReturnValue(storeDefaults as any);
});

describe('LoginPage', () => {
  it('shows loading state while auth is checking', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null, loading: true, error: null,
      login: vi.fn(), verifyTotp: vi.fn(), logout: vi.fn(),
    });
    const { container } = render(React.createElement(LoginPage));
    // Loading state shows a pulse animation div
    expect(container.querySelector('.animate-pulse')).toBeTruthy();
  });

  it('shows login form when not authenticated', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null, loading: false, error: null,
      login: vi.fn(), verifyTotp: vi.fn(), logout: vi.fn(),
    });
    render(React.createElement(LoginPage));
    expect(screen.getByTestId('login-form')).toBeTruthy();
  });

  it('returns null when user is already authenticated (redirect pending)', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 'u-1', email: 'a@b.c', name: 'Admin', role: 'admin' },
      loading: false, error: null,
      login: vi.fn(), verifyTotp: vi.fn(), logout: vi.fn(),
    });
    const { container } = render(React.createElement(LoginPage));
    // Should render nothing (redirect will happen via useEffect)
    expect(container.innerHTML).toBe('');
  });

  it('shows brand elements in data/form state', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null, loading: false, error: null,
      login: vi.fn(), verifyTotp: vi.fn(), logout: vi.fn(),
    });
    render(React.createElement(LoginPage));
    // Title exists
    expect(screen.getByText('auth.loginTitle')).toBeTruthy();
    // Console version footer
    expect(screen.getByText(/NomOS Console/)).toBeTruthy();
  });
});
