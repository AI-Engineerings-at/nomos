/**
 * NomOS Language Toggle — DE|EN switch.
 * Stores preference in localStorage.
 * WCAG 2.2 AA: keyboard accessible, aria-label, visible focus ring.
 */
'use client';

import { useEffect } from 'react';
import { useNomosStore } from '@/lib/store';
import { t, getStoredLanguage, type Language } from '@/lib/i18n';

export function LangToggle() {
  const { language, setLanguage } = useNomosStore();

  // Initialize language from localStorage on mount
  useEffect(() => {
    const stored = getStoredLanguage();
    setLanguage(stored);
    document.documentElement.lang = stored;
  }, [setLanguage]);

  const toggle = () => {
    const next: Language = language === 'de' ? 'en' : 'de';
    setLanguage(next);
    document.documentElement.lang = next;
  };

  return (
    <button
      onClick={toggle}
      className={[
        'px-2.5 py-1.5 rounded-[var(--radius)]',
        'text-xs font-bold tracking-wider',
        'text-[var(--color-muted)] hover:text-[var(--color-text)]',
        'hover:bg-[var(--color-hover)]',
        'border border-[var(--color-border)]',
        'transition-colors duration-[var(--transition)]',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]',
        'font-[family-name:var(--font-headline)]',
      ].join(' ')}
      aria-label={t('header.lang.toggle', language)}
      title={t('header.lang.toggle', language)}
    >
      <span className={language === 'de' ? 'text-[var(--color-text)] font-extrabold' : ''}>
        DE
      </span>
      <span className="mx-1 text-[var(--color-border)]" aria-hidden="true">|</span>
      <span className={language === 'en' ? 'text-[var(--color-text)] font-extrabold' : ''}>
        EN
      </span>
    </button>
  );
}
