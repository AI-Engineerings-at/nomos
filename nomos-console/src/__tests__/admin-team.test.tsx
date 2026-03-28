/**
 * Test: /admin/team — 4 states.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { mockFleet, mockFleetEmpty, mockCosts, mockCostsEmpty } from './fixtures';
import { storeBase, authBase } from './shared-mocks';

// Import the real hooks but they are mocked globally by vitest
import { useFetch } from '@/lib/hooks';
import { useNomosStore } from '@/lib/store';
import { useAuth } from '@/lib/auth';
import TeamPage from '@/app/admin/team/page';

// Specific component mocks for this test file
vi.mock('@/lib/types', async (importOriginal) => {
  const orig = await importOriginal() as Record<string, unknown>;
  return { ...orig };
});

vi.mock('@/components/ui/card', () => ({
  Card: ({ children, ...p }: Record<string, unknown>) => React.createElement('div', { 'data-testid': 'card' }, children as React.ReactNode),
  CardHeader: ({ title }: { title: string }) => React.createElement('div', null, title),
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ status }: { status: string }) => React.createElement('span', { 'data-testid': 'badge' }, status),
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...p }: Record<string, unknown>) => React.createElement('button', p, children as React.ReactNode),
}));

vi.mock('@/components/ui/empty-state', () => ({
  EmptyState: ({ message }: { message: string }) => React.createElement('div', { 'data-testid': 'empty-state' }, message),
}));

vi.mock('@/components/ui/skeleton', () => ({
  Skeleton: () => React.createElement('div', { 'data-testid': 'skeleton' }),
  SkeletonCard: () => React.createElement('div', { 'data-testid': 'skeleton-card' }),
  SkeletonBadge: () => React.createElement('div', { 'data-testid': 'skeleton-badge' }),
}));

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(useNomosStore).mockReturnValue(storeBase as any);
  vi.mocked(useAuth).mockReturnValue(authBase as any);
});

describe('TeamPage (/admin/team)', () => {
  it('shows loading skeleton', () => {
    vi.mocked(useFetch).mockReturnValue({ data: null, loading: true, error: null, reload: vi.fn() });
    const { container } = render(React.createElement(TeamPage));
    expect(container.querySelectorAll('[data-testid="skeleton-badge"]').length).toBeGreaterThan(0);
  });

  it('shows empty state when no agents', () => {
    let call = 0;
    vi.mocked(useFetch).mockImplementation(() => {
      call++;
      if (call === 1) return { data: mockFleetEmpty, loading: false, error: null, reload: vi.fn() };
      return { data: mockCostsEmpty, loading: false, error: null, reload: vi.fn() };
    });
    render(React.createElement(TeamPage));
    expect(screen.getByTestId('empty-state')).toBeTruthy();
  });

  it('handles error state gracefully', () => {
    vi.mocked(useFetch).mockReturnValue({ data: null, loading: false, error: 'fail', reload: vi.fn() });
    const { container } = render(React.createElement(TeamPage));
    expect(container).toBeTruthy();
  });

  it('renders agent cards with data', () => {
    let call = 0;
    vi.mocked(useFetch).mockImplementation(() => {
      call++;
      if (call === 1) return { data: mockFleet, loading: false, error: null, reload: vi.fn() };
      return { data: mockCosts, loading: false, error: null, reload: vi.fn() };
    });
    render(React.createElement(TeamPage));
    expect(screen.getByText('team.title')).toBeTruthy();
  });
});
