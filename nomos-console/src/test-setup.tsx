/**
 * Vitest global test setup.
 * Mocks browser APIs and Next.js modules that are unavailable in jsdom.
 */
import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';
import React from 'react';

// ---------------------------------------------------------------------------
// Mock next/navigation
// ---------------------------------------------------------------------------
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    prefetch: vi.fn(),
    refresh: vi.fn(),
  })),
  usePathname: vi.fn(() => '/admin'),
  useSearchParams: vi.fn(() => new URLSearchParams()),
  useParams: vi.fn(() => ({ id: 'agent-001' })),
  redirect: vi.fn(),
}));

// ---------------------------------------------------------------------------
// Mock next/image — render a plain <img> element
// ---------------------------------------------------------------------------
vi.mock('next/image', () => ({
  __esModule: true,
  default: (props: any) => {
    // eslint-disable-next-line @next/next/no-img-element, jsx-a11y/alt-text
    return <img {...props} />;
  },
}));

// ---------------------------------------------------------------------------
// Mock window APIs not available in jsdom
// ---------------------------------------------------------------------------
if (typeof window !== 'undefined') {
  // requestAnimationFrame
  if (!window.requestAnimationFrame) {
    window.requestAnimationFrame = ((cb: FrameRequestCallback) => {
      return window.setTimeout(() => cb(Date.now()), 0);
    }) as typeof window.requestAnimationFrame;
  }
  if (!window.cancelAnimationFrame) {
    window.cancelAnimationFrame = ((id: number) => {
      window.clearTimeout(id);
    }) as typeof window.cancelAnimationFrame;
  }

  // SpeechSynthesis stub
  if (!window.speechSynthesis) {
    Object.defineProperty(window, 'speechSynthesis', {
      value: {
        speak: vi.fn(),
        cancel: vi.fn(),
        getVoices: () => [],
        speaking: false,
        paused: false,
        pending: false,
      },
    });
  }

  // SpeechRecognition stub
  if (!(window as unknown as Record<string, unknown>).SpeechRecognition &&
      !(window as unknown as Record<string, unknown>).webkitSpeechRecognition) {
    class MockSpeechRecognition {
      start = vi.fn();
      stop = vi.fn();
      abort = vi.fn();
      onresult: ((e: unknown) => void) | null = null;
      onerror: ((e: unknown) => void) | null = null;
      onend: (() => void) | null = null;
      lang = 'de-DE';
      continuous = false;
      interimResults = false;
    }
    (window as unknown as Record<string, unknown>).SpeechRecognition = MockSpeechRecognition;
    (window as unknown as Record<string, unknown>).webkitSpeechRecognition = MockSpeechRecognition;
  }

  // scrollIntoView stub (jsdom doesn't implement it)
  if (!Element.prototype.scrollIntoView) {
    Element.prototype.scrollIntoView = vi.fn();
  }
}

// ---------------------------------------------------------------------------
// Global NomOS Library Mocks
// ---------------------------------------------------------------------------

// Mock @/lib/api — Prevent real network calls
vi.mock('@/lib/api', () => {
  class ApiError extends Error {
    status: number;
    statusText: string;
    detail: string;
    code?: string;
    constructor(status: number, statusText: string, detail: string, code?: string) {
      super(detail);
      this.name = 'ApiError';
      this.status = status;
      this.statusText = statusText;
      this.detail = detail;
      this.code = code;
    }
  }
  return {
    api: {
      get: vi.fn().mockResolvedValue({}),
      post: vi.fn().mockResolvedValue({}),
      put: vi.fn().mockResolvedValue({}),
      patch: vi.fn().mockResolvedValue({}),
      delete: vi.fn().mockResolvedValue({}),
    },
    ApiError,
    fetcher: vi.fn(),
  };
});

// Mock @/lib/auth
vi.mock('@/lib/auth', () => ({
  useAuth: vi.fn(() => ({
    user: null,
    loading: false,
    error: null,
    login: vi.fn(),
    verifyTotp: vi.fn(),
    logout: vi.fn(),
  })),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock @/lib/hooks
vi.mock('@/lib/hooks', async (importOriginal) => {
  const actual = await importOriginal() as any;
  return {
    ...actual,
    useFetch: vi.fn(() => ({
      data: null,
      loading: false,
      error: null,
      reload: vi.fn(),
    })),
    getGreetingKey: vi.fn(actual.getGreetingKey),
    formatEur: vi.fn(actual.formatEur),
    formatDate: vi.fn(actual.formatDate),
  };
});

// Mock @/lib/store
vi.mock('@/lib/store', () => ({
  useNomosStore: vi.fn(() => ({
    language: 'de',
    theme: 'dark',
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
  })),
}));

// Mock @/lib/i18n
vi.mock('@/lib/i18n', () => ({
  t: vi.fn((key: string) => key),
  getStoredLanguage: vi.fn(() => 'de'),
  setStoredLanguage: vi.fn(),
}));

// Mock global components
vi.mock('@/components/ui/error-boundary', () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

