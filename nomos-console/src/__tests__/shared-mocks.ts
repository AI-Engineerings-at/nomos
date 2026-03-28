/**
 * Shared mock setup values used across page tests.
 * Import these in test files after setting up vi.mock().
 */
import { vi } from 'vitest';
import React from 'react';

export const storeBase = {
  language: 'de' as const,
  theme: 'dark' as const,
  setTheme: vi.fn(), toggleTheme: vi.fn(), setLanguage: vi.fn(),
  user: null, setUser: vi.fn(),
  toasts: [], addToast: vi.fn(), removeToast: vi.fn(),
  sidebarCollapsed: false, setSidebarCollapsed: vi.fn(),
  speechRate: 1.0, setSpeechRate: vi.fn(), speechEnabled: true, setSpeechEnabled: vi.fn(),
};

export const authBase = {
  user: { id: 'u-1', email: 'a@b.c', name: 'Joe Admin', role: 'admin' as const },
  loading: false, error: null,
  login: vi.fn(), verifyTotp: vi.fn(), logout: vi.fn(),
};
