/**
 * Test: /setup page -- 4-step First-Time Setup Wizard.
 * Tests: loading, redirect when not needed, step 1 display, step navigation.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { useRouter } from 'next/navigation';

import { useNomosStore } from '@/lib/store';
import { api } from '@/lib/api';
import SetupPage from '@/app/setup/page';

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

const mockRouter = {
  push: vi.fn(),
  replace: vi.fn(),
  back: vi.fn(),
  prefetch: vi.fn(),
  refresh: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(useNomosStore).mockReturnValue(storeDefaults as any);
  vi.mocked(useRouter).mockReturnValue(mockRouter as any);
});

describe('SetupPage', () => {
  it('shows loading state while checking system status', () => {
    // api.get never resolves -> stays in loading
    vi.mocked(api.get).mockReturnValue(new Promise(() => {}));
    const { container } = render(React.createElement(SetupPage));
    expect(container.querySelector('.animate-pulse')).toBeTruthy();
  });

  it('redirects to /login when setup_required is false', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ setup_required: false });
    render(React.createElement(SetupPage));
    await waitFor(() => {
      expect(mockRouter.replace).toHaveBeenCalledWith('/login');
    });
  });

  it('shows step 1 (vault key) when setup is required', async () => {
    // First call: system/status -> setup_required: true
    // Second call: unseal-key endpoint
    vi.mocked(api.get)
      .mockResolvedValueOnce({ setup_required: true })
      .mockResolvedValueOnce({ unseal_key: 'test-unseal-key-123', auto_unseal: false });

    render(React.createElement(SetupPage));

    await waitFor(() => {
      expect(screen.getByText('setup.title')).toBeTruthy();
    });

    // Wait for unseal key to load
    await waitFor(() => {
      expect(screen.getByText('test-unseal-key-123')).toBeTruthy();
    });

    // Checkbox and next button should be present
    expect(screen.getByText('setup.step1.checkbox')).toBeTruthy();
    expect(screen.getByText('action.next')).toBeTruthy();
  });

  it('disables next button until checkbox is checked in step 1', async () => {
    vi.mocked(api.get)
      .mockResolvedValueOnce({ setup_required: true })
      .mockResolvedValueOnce({ unseal_key: 'test-key', auto_unseal: false });

    render(React.createElement(SetupPage));

    await waitFor(() => {
      expect(screen.getByText('test-key')).toBeTruthy();
    });

    // Next button should be disabled
    const nextButton = screen.getByText('action.next');
    expect(nextButton).toBeDisabled();

    // Check the checkbox
    const checkbox = screen.getByRole('checkbox');
    fireEvent.click(checkbox);

    // Next button should now be enabled
    expect(nextButton).not.toBeDisabled();
  });

  it('shows step 1 warning banner', async () => {
    vi.mocked(api.get)
      .mockResolvedValueOnce({ setup_required: true })
      .mockResolvedValueOnce({ unseal_key: 'key-abc', auto_unseal: false });

    render(React.createElement(SetupPage));

    await waitFor(() => {
      expect(screen.getByText('setup.step1.warning')).toBeTruthy();
    });
  });

  it('shows error and retry when unseal-key fetch fails', async () => {
    vi.mocked(api.get)
      .mockResolvedValueOnce({ setup_required: true })
      .mockRejectedValueOnce(new Error('Network error'));

    render(React.createElement(SetupPage));

    await waitFor(() => {
      expect(screen.getByText('action.retry')).toBeTruthy();
    });
  });

  it('shows progress indicator', async () => {
    vi.mocked(api.get)
      .mockResolvedValueOnce({ setup_required: true })
      .mockResolvedValueOnce({ unseal_key: 'key', auto_unseal: false });

    render(React.createElement(SetupPage));

    await waitFor(() => {
      expect(screen.getByText('setup.stepLabel 1/4')).toBeTruthy();
    });
  });

  it('shows brand elements (logo, title, accent line)', async () => {
    vi.mocked(api.get)
      .mockResolvedValueOnce({ setup_required: true })
      .mockResolvedValueOnce({ unseal_key: 'key', auto_unseal: false });

    render(React.createElement(SetupPage));

    await waitFor(() => {
      // Logo image
      const logo = screen.getByAltText('a11y.logoAlt');
      expect(logo).toBeTruthy();
      // Title
      expect(screen.getByText('setup.title')).toBeTruthy();
      // Subtitle
      expect(screen.getByText('setup.subtitle')).toBeTruthy();
    });
  });
});
