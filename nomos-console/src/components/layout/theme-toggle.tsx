/**
 * NomOS Theme Toggle — Sun/Moon icon.
 * Stores preference in localStorage, respects OS preference on first visit.
 * WCAG 2.2 AA: keyboard accessible, aria-label, visible focus ring.
 */
'use client';

import { useEffect } from 'react';
import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';

export function ThemeToggle() {
  const { theme, setTheme, language } = useNomosStore();

  // Initialize theme from localStorage or OS preference on mount
  useEffect(() => {
    const stored = localStorage.getItem('nomos-theme');
    if (stored === 'dark' || stored === 'light') {
      setTheme(stored);
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setTheme('dark');
    } else {
      setTheme('light');
    }
  }, [setTheme]);

  // Listen for OS preference changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    function handleChange(e: MediaQueryListEvent) {
      // Only follow OS preference if user hasn't explicitly set one
      if (!localStorage.getItem('nomos-theme')) {
        setTheme(e.matches ? 'dark' : 'light');
      }
    }
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [setTheme]);

  const toggleTheme = () => {
    const next = theme === 'light' ? 'dark' : 'light';
    setTheme(next);
  };

  const label = theme === 'light'
    ? t('header.theme.dark', language)
    : t('header.theme.light', language);

  return (
    <button
      onClick={toggleTheme}
      className={[
        'p-2 rounded-[var(--radius)]',
        'text-[var(--color-muted)] hover:text-[var(--color-text)]',
        'hover:bg-[var(--color-hover)]',
        'transition-colors duration-[var(--transition)]',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]',
      ].join(' ')}
      aria-label={label}
      title={label}
    >
      {theme === 'light' ? (
        /* Moon icon — switch to dark */
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
        </svg>
      ) : (
        /* Sun icon — switch to light */
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="5" />
          <line x1="12" y1="1" x2="12" y2="3" />
          <line x1="12" y1="21" x2="12" y2="23" />
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
          <line x1="1" y1="12" x2="3" y2="12" />
          <line x1="21" y1="12" x2="23" y2="12" />
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        </svg>
      )}
    </button>
  );
}
