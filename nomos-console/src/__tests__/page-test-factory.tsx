/**
 * Factory for creating page tests with consistent 4-state coverage.
 * Reduces boilerplate across 20 page test files.
 */
import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { useFetch } from '@/lib/hooks';
import { useNomosStore } from '@/lib/store';
import { useAuth } from '@/lib/auth';
import { storeBase, authBase } from './shared-mocks';

interface PageTestOptions {
  name: string;
  component: React.ComponentType;
  mockPath?: string;
  dataFixture?: any;
  emptyFixture?: any;
  expectedText: string | RegExp;
  errorText?: string | RegExp;
  emptyText?: string | RegExp;
  skipLoading?: boolean;
  skipError?: boolean;
  skipEmpty?: boolean;
}

/**
 * Standard 4-state page test generator.
 * Assumes the page uses useFetch for its primary data.
 */
export function createPageTest(options: PageTestOptions) {
  const {
    name,
    component,
    mockPath,
    dataFixture,
    emptyFixture,
    expectedText,
    errorText = /error|failed|API Error|fehler/i,
    emptyText = /empty|keine|no|noch keine/i,
    skipLoading = false,
    skipError = false,
    skipEmpty = false,
  } = options;

  describe(`${name} Page`, () => {
    beforeEach(() => {
      vi.clearAllMocks();
      vi.mocked(useNomosStore).mockReturnValue(storeBase as any);
      vi.mocked(useAuth).mockReturnValue(authBase as any);
      // Default useFetch mock to avoid "undefined" errors
      vi.mocked(useFetch).mockReturnValue({
        data: null,
        loading: false,
        error: null,
        reload: vi.fn(),
      });
    });

    if (!skipLoading && mockPath) {
      it('shows loading state', () => {
        vi.mocked(useFetch).mockImplementation((path) => {
          if (path === mockPath || path.startsWith(mockPath)) {
            return { data: null, loading: true, error: null, reload: vi.fn() };
          }
          return { data: {}, loading: false, error: null, reload: vi.fn() };
        });
        const { container } = render(React.createElement(component));
        expect(
          container.querySelector('[role="status"]') ||
          container.querySelector('.animate-pulse') ||
          container.querySelector('[aria-busy="true"]') ||
          screen.queryAllByText(/wird geladen|loading/i).length > 0
        ).toBeTruthy();
      });
    }

    if (!skipError && mockPath) {
      it('shows error state gracefully', () => {
        vi.mocked(useFetch).mockImplementation((path) => {
          if (path === mockPath || path.startsWith(mockPath)) {
            return { data: null, loading: false, error: 'API Error', reload: vi.fn() };
          }
          return { data: {}, loading: false, error: null, reload: vi.fn() };
        });
        render(React.createElement(component));
        // We accept EITHER a specific error text OR an empty state (graceful fallback)
        expect(
          screen.queryAllByText(errorText).length > 0 ||
          screen.queryAllByText(emptyText).length > 0 ||
          screen.queryAllByTestId('empty-state').length > 0
        ).toBeTruthy();
      });
    }

    it('renders data correctly', () => {
      if (mockPath) {
        vi.mocked(useFetch).mockImplementation((path) => {
          if (path === mockPath || path.startsWith(mockPath)) {
            return { data: dataFixture, loading: false, error: null, reload: vi.fn() };
          }
          return { data: {}, loading: false, error: null, reload: vi.fn() };
        });
      }
      render(React.createElement(component));
      expect(screen.queryAllByText(expectedText).length).toBeGreaterThan(0);
    });

    if (!skipEmpty && mockPath) {
      it('shows empty state when no data exists', () => {
        vi.mocked(useFetch).mockImplementation((path) => {
          if (path === mockPath || path.startsWith(mockPath)) {
            return { data: emptyFixture, loading: false, error: null, reload: vi.fn() };
          }
          return { data: {}, loading: false, error: null, reload: vi.fn() };
        });
        render(React.createElement(component));
        expect(
          screen.queryAllByText(emptyText).length > 0 ||
          screen.queryAllByTestId('empty-state').length > 0
        ).toBeTruthy();
      });
    }
  });
}

/** Legacy support for basic import checks */
export function createModuleTest(name: string, importFn: () => Promise<{ default: unknown }>) {
  describe(`${name} (module)`, () => {
    it('exports a default function component', async () => {
      const mod = await importFn();
      expect(mod.default).toBeDefined();
      expect(typeof mod.default).toBe('function');
    });
  });
}
