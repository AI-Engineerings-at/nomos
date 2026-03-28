/**
 * NomOS test utilities — shared render helpers and mock factories.
 */
import React, { type ReactElement } from 'react';
import { render, type RenderOptions } from '@testing-library/react';
import { vi } from 'vitest';

// ---------------------------------------------------------------------------
// Mock state for useFetch
// ---------------------------------------------------------------------------
export interface MockFetchState<T = unknown> {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

export function mockFetchLoading(): MockFetchState {
  return { data: null, loading: true, error: null, reload: vi.fn() };
}

export function mockFetchError(msg = 'Server nicht erreichbar'): MockFetchState {
  return { data: null, loading: false, error: msg, reload: vi.fn() };
}

export function mockFetchEmpty<T>(emptyData: T): MockFetchState<T> {
  return { data: emptyData, loading: false, error: null, reload: vi.fn() };
}

export function mockFetchData<T>(data: T): MockFetchState<T> {
  return { data, loading: false, error: null, reload: vi.fn() };
}

// ---------------------------------------------------------------------------
// Mock store — minimal Zustand store values
// ---------------------------------------------------------------------------
export const defaultStoreValues = {
  theme: 'dark' as const,
  setTheme: vi.fn(),
  toggleTheme: vi.fn(),
  language: 'de' as const,
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

// ---------------------------------------------------------------------------
// Mock auth context values
// ---------------------------------------------------------------------------
export const defaultAuthValues = {
  user: { id: 'u-1', email: 'admin@nomos.local', name: 'Joe Admin', role: 'admin' as const },
  loading: false,
  error: null,
  login: vi.fn().mockResolvedValue({ requires2FA: false }),
  verifyTotp: vi.fn().mockResolvedValue(undefined),
  logout: vi.fn().mockResolvedValue(undefined),
};

// ---------------------------------------------------------------------------
// Render helper
// ---------------------------------------------------------------------------
export function renderPage(ui: ReactElement, options?: RenderOptions) {
  return render(ui, { ...options });
}

export { render };
