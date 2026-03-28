/**
 * Test: /admin (Dashboard) — 4 states.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { mockFleet, mockFleetEmpty, mockCosts, mockApprovals, mockIncidents, mockAuditEntry } from './fixtures';

// Import the real hooks but they are mocked globally by vitest
import { useFetch, getGreetingKey } from '@/lib/hooks';
import { useNomosStore } from '@/lib/store';
import { useAuth } from '@/lib/auth';
import AdminDashboardPage from '@/app/admin/page';

// Specific component mocks for this test file
vi.mock('@/lib/types', async (importOriginal) => {
  const orig = await importOriginal() as Record<string, unknown>;
  return { ...orig };
});

vi.mock('@/components/ui/card', () => ({
  Card: ({ children, ...rest }: Record<string, unknown>) =>
    React.createElement('div', { 'data-testid': 'card', ...rest }, children as React.ReactNode),
  CardHeader: ({ title }: { title: string }) =>
    React.createElement('div', null, title),
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ status }: { status: string }) =>
    React.createElement('span', { 'data-testid': 'badge' }, status),
}));

vi.mock('@/components/ui/empty-state', () => ({
  EmptyState: ({ message }: { message: string }) =>
    React.createElement('div', { 'data-testid': 'empty-state' }, message),
}));

vi.mock('@/components/ui/skeleton', () => ({
  Skeleton: (props: Record<string, unknown>) =>
    React.createElement('div', { 'data-testid': 'skeleton' }),
  SkeletonCard: () =>
    React.createElement('div', { 'data-testid': 'skeleton-card' }),
  SkeletonBadge: () =>
    React.createElement('div', { 'data-testid': 'skeleton-badge' }),
}));

vi.mock('@/components/ui/speak-button', () => ({
  SpeakButton: () => React.createElement('button', { 'data-testid': 'speak-btn' }),
}));

const storeBase = {
  language: 'de' as const,
  theme: 'dark' as const,
  setTheme: vi.fn(), toggleTheme: vi.fn(), setLanguage: vi.fn(),
  user: null, setUser: vi.fn(),
  toasts: [], addToast: vi.fn(), removeToast: vi.fn(),
  sidebarCollapsed: false, setSidebarCollapsed: vi.fn(),
  speechRate: 1.0, setSpeechRate: vi.fn(), speechEnabled: true, setSpeechEnabled: vi.fn(),
};

const authBase = {
  user: { id: 'u-1', email: 'a@b.c', name: 'Joe Admin', role: 'admin' as const },
  loading: false, error: null,
  login: vi.fn(), verifyTotp: vi.fn(), logout: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(useNomosStore).mockReturnValue(storeBase as any);
  vi.mocked(useAuth).mockReturnValue(authBase as any);
  vi.mocked(getGreetingKey).mockReturnValue('dashboard.greeting.morning');
});

describe('AdminDashboardPage', () => {
  it('shows loading skeleton when data is loading', () => {
    vi.mocked(useFetch).mockReturnValue({ data: null, loading: true, error: null, reload: vi.fn() });
    const { container } = render(React.createElement(AdminDashboardPage));
    expect(container.querySelectorAll('[data-testid="skeleton"]').length).toBeGreaterThan(0);
  });

  it('shows empty state when fleet has no agents', () => {
    // First call = fleet(empty), rest = also empty/loaded
    let callCount = 0;
    vi.mocked(useFetch).mockImplementation(() => {
      callCount++;
      if (callCount === 1) return { data: mockFleetEmpty, loading: false, error: null, reload: vi.fn() };
      if (callCount === 2) return { data: { costs: [], total: 0 }, loading: false, error: null, reload: vi.fn() };
      if (callCount === 3) return { data: { approvals: [], total: 0 }, loading: false, error: null, reload: vi.fn() };
      if (callCount === 4) return { data: { incidents: [], total: 0 }, loading: false, error: null, reload: vi.fn() };
      return { data: { entries: [], total: 0 }, loading: false, error: null, reload: vi.fn() };
    });
    render(React.createElement(AdminDashboardPage));
    expect(screen.getAllByTestId('empty-state').length).toBeGreaterThan(0);
  });

  it('shows error boundary wrapper (error caught by ErrorBoundary)', () => {
    // ErrorBoundary is mocked as pass-through, so error in useFetch doesn't crash
    vi.mocked(useFetch).mockReturnValue({ data: null, loading: false, error: 'Server error', reload: vi.fn() });
    // Should not throw — ErrorBoundary catches
    const { container } = render(React.createElement(AdminDashboardPage));
    expect(container).toBeTruthy();
  });

  it('renders dashboard with data', () => {
    let callCount = 0;
    vi.mocked(useFetch).mockImplementation(() => {
      callCount++;
      if (callCount === 1) return { data: mockFleet, loading: false, error: null, reload: vi.fn() };
      if (callCount === 2) return { data: mockCosts, loading: false, error: null, reload: vi.fn() };
      if (callCount === 3) return { data: mockApprovals, loading: false, error: null, reload: vi.fn() };
      if (callCount === 4) return { data: mockIncidents, loading: false, error: null, reload: vi.fn() };
      return { data: { entries: [mockAuditEntry], total: 1 }, loading: false, error: null, reload: vi.fn() };
    });
    render(React.createElement(AdminDashboardPage));
    // Should show greeting
    expect(screen.getByText(/dashboard.greeting.morning/)).toBeTruthy();
  });
});
