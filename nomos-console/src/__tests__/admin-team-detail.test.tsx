import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { useFetch } from '@/lib/hooks';
import { useNomosStore } from '@/lib/store';
import { useAuth } from '@/lib/auth';
import { useParams } from 'next/navigation';
import { storeBase, authBase } from './shared-mocks';
import { mockAgent, mockAudit, mockCostEntry, mockComplianceEntry } from './fixtures';
import AgentProfilePage from '@/app/admin/team/[id]/page';

describe('AgentProfilePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useNomosStore).mockReturnValue(storeBase as any);
    vi.mocked(useAuth).mockReturnValue(authBase as any);
    vi.mocked(useParams).mockReturnValue({ id: 'agent-001' });
  });

  it('shows loading state', () => {
    vi.mocked(useFetch).mockImplementation((path) => {
      if (path.includes('/fleet/agent-001')) return { data: null, loading: true, error: null, reload: vi.fn() };
      return { data: null, loading: false, error: null, reload: vi.fn() };
    });
    const { container } = render(React.createElement(AgentProfilePage));
    expect(container.querySelector('[role="status"]') || container.querySelector('.animate-pulse')).toBeTruthy();
  });

  it('renders agent profile data', () => {
    vi.mocked(useFetch).mockImplementation((path) => {
      if (path.includes('/fleet/agent-001')) return { data: mockAgent, loading: false, error: null, reload: vi.fn() };
      if (path.includes('/audit')) return { data: mockAudit, loading: false, error: null, reload: vi.fn() };
      if (path.includes('/costs')) return { data: mockCostEntry, loading: false, error: null, reload: vi.fn() };
      if (path.includes('/compliance')) return { data: mockComplianceEntry, loading: false, error: null, reload: vi.fn() };
      return { data: null, loading: false, error: null, reload: vi.fn() };
    });

    render(React.createElement(AgentProfilePage));
    expect(screen.getAllByText(new RegExp(mockAgent.name, 'i')).length).toBeGreaterThan(0);
    expect(screen.getAllByText(new RegExp(mockAgent.role, 'i')).length).toBeGreaterThan(0);
  });
});
