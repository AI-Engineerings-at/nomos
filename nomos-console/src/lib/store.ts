/**
 * NomOS Zustand Store — Global client state.
 * Theme, language, user session, toast notifications.
 */
import { create } from 'zustand';
import type { Language } from './i18n';

/** User role determines which layout and navigation items are shown. */
export type UserRole = 'admin' | 'user' | 'officer';

/** Authenticated user info extracted from JWT. */
export interface NomosUser {
  id: string;
  email: string;
  name: string;
  role: UserRole;
}

/** Toast notification shown in the bottom-right corner. */
export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration: number;
}

export type Theme = 'light' | 'dark';

interface NomosState {
  // Theme
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;

  // Language
  language: Language;
  setLanguage: (lang: Language) => void;

  // User
  user: NomosUser | null;
  setUser: (user: NomosUser | null) => void;

  // Toast notifications
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;

  // Sidebar
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;

  // Speech (TTS/STT)
  speechRate: number;
  setSpeechRate: (rate: number) => void;
  speechEnabled: boolean;
  setSpeechEnabled: (enabled: boolean) => void;
}

let toastCounter = 0;

function generateToastId(): string {
  toastCounter += 1;
  return `toast-${Date.now()}-${toastCounter}`;
}

export const useNomosStore = create<NomosState>()((set) => ({
  // Theme — defaults applied during hydration in layout
  theme: 'light' as Theme,
  setTheme: (theme: Theme) => {
    set({ theme });
    if (typeof window !== 'undefined') {
      localStorage.setItem('nomos-theme', theme);
      document.documentElement.setAttribute('data-theme', theme);
    }
  },
  toggleTheme: () => {
    set((state: NomosState) => {
      const next = state.theme === 'light' ? 'dark' : 'light';
      if (typeof window !== 'undefined') {
        localStorage.setItem('nomos-theme', next);
        document.documentElement.setAttribute('data-theme', next);
      }
      return { theme: next };
    });
  },

  // Language — default German
  language: 'de',
  setLanguage: (language: Language) => {
    set({ language });
    if (typeof window !== 'undefined') {
      localStorage.setItem('nomos-lang', language);
      document.documentElement.lang = language;
    }
  },

  // User
  user: null,
  setUser: (user: NomosUser | null) => set({ user }),

  // Toasts
  toasts: [],
  addToast: (toast: Omit<Toast, 'id'>) => {
    const id = generateToastId();
    set((state: NomosState) => ({
      toasts: [...state.toasts, { ...toast, id }],
    }));
    // Auto-remove after duration
    if (typeof window !== 'undefined') {
      window.setTimeout(() => {
        set((state: NomosState) => ({
          toasts: state.toasts.filter((t: Toast) => t.id !== id),
        }));
      }, toast.duration);
    }
  },
  removeToast: (id: string) =>
    set((state: NomosState) => ({
      toasts: state.toasts.filter((t: Toast) => t.id !== id),
    })),

  // Sidebar
  sidebarCollapsed: false,
  setSidebarCollapsed: (collapsed: boolean) => set({ sidebarCollapsed: collapsed }),

  // Speech — defaults loaded from localStorage on hydration
  speechRate: 1.0,
  setSpeechRate: (rate: number) => {
    const clamped = Math.max(0.5, Math.min(2.0, rate));
    set({ speechRate: clamped });
    if (typeof window !== 'undefined') {
      localStorage.setItem('nomos-speech-rate', String(clamped));
    }
  },
  speechEnabled: true,
  setSpeechEnabled: (enabled: boolean) => {
    set({ speechEnabled: enabled });
    if (typeof window !== 'undefined') {
      localStorage.setItem('nomos-speech-enabled', enabled ? 'true' : 'false');
    }
  },
}));
