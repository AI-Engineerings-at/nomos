/**
 * NomOS Header — Logo (Eagle), Theme toggle, Language toggle, User menu.
 * Fixed at the top. Shows user name + role.
 * WCAG 2.2 AA: semantic header, keyboard accessible controls.
 */
'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import Image from 'next/image';
import { useNomosStore } from '@/lib/store';
import { useAuth } from '@/lib/auth';
import { t } from '@/lib/i18n';
import { ThemeToggle } from './theme-toggle';
import { LangToggle } from './lang-toggle';

export function Header() {
  const { language, theme } = useNomosStore();
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Close menu on outside click or Escape
  useEffect(() => {
    if (!menuOpen) return;

    function handleClickOutside(e: MouseEvent) {
      if (
        menuRef.current &&
        !menuRef.current.contains(e.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(e.target as Node)
      ) {
        setMenuOpen(false);
      }
    }

    function handleEscape(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        setMenuOpen(false);
        buttonRef.current?.focus();
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [menuOpen]);

  const handleLogout = useCallback(async () => {
    setMenuOpen(false);
    await logout();
  }, [logout]);

  const roleLabels: Record<string, string> = {
    admin: 'Administrator',
    user: 'Nutzer',
    officer: 'Compliance Officer',
  };

  const logoSrc = theme === 'dark' ? '/logo-new-white.png' : '/logo-new.png';

  return (
    <header
      className={[
        'sticky top-0 z-40',
        'h-[var(--header-height)] px-6',
        'flex items-center justify-between',
        'bg-[var(--color-card)] border-b border-[var(--color-border)]',
        'shadow-[var(--shadow-card)]',
      ].join(' ')}
      role="banner"
    >
      {/* Logo — visible on smaller screens or when sidebar is collapsed */}
      <div className="flex items-center gap-3 lg:hidden">
        <Image
          src={logoSrc}
          alt={t('a11y.logoAlt', language)}
          width={32}
          height={32}
          className="w-8 h-8"
          priority
        />
        <span className="text-lg font-bold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
          NomOS
        </span>
      </div>

      {/* Spacer for desktop when sidebar is visible */}
      <div className="hidden lg:block" />

      {/* Right side controls */}
      <div className="flex items-center gap-2">
        <LangToggle />
        <ThemeToggle />

        {/* User menu */}
        {user && (
          <div className="relative ml-2">
            <button
              ref={buttonRef}
              onClick={() => setMenuOpen((prev) => !prev)}
              className={[
                'flex items-center gap-2 px-3 py-1.5 rounded-[var(--radius)]',
                'text-sm text-[var(--color-text)]',
                'hover:bg-[var(--color-hover)]',
                'transition-colors duration-[var(--transition)]',
                'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]',
              ].join(' ')}
              aria-expanded={menuOpen}
              aria-haspopup="true"
              aria-label={t('header.user.menu', language)}
            >
              {/* Avatar circle with initials */}
              <div className="w-7 h-7 rounded-full bg-[var(--color-primary)] flex items-center justify-center text-white text-xs font-bold">
                {user.name.charAt(0).toUpperCase()}
              </div>
              <span className="hidden sm:block font-medium">{user.name}</span>
              <svg
                className={`w-4 h-4 text-[var(--color-muted)] transition-transform duration-[var(--transition)] ${menuOpen ? 'rotate-180' : ''}`}
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
                  clipRule="evenodd"
                />
              </svg>
            </button>

            {menuOpen && (
              <div
                ref={menuRef}
                className={[
                  'absolute right-0 top-full mt-1 w-56',
                  'bg-[var(--color-card)] border border-[var(--color-border)]',
                  'rounded-[var(--radius)] shadow-[var(--shadow-card-hover)]',
                  'py-1',
                ].join(' ')}
                role="menu"
                aria-label={t('header.user.menu', language)}
              >
                {/* User info */}
                <div className="px-4 py-2 border-b border-[var(--color-border)]">
                  <p className="text-sm font-semibold text-[var(--color-text)]">{user.name}</p>
                  <p className="text-xs text-[var(--color-muted)]">{user.email}</p>
                  <p className="text-xs text-[var(--color-primary)] font-medium mt-0.5">
                    {roleLabels[user.role] ?? user.role}
                  </p>
                </div>

                <button
                  onClick={handleLogout}
                  className={[
                    'w-full text-left px-4 py-2 text-sm',
                    'text-[var(--color-error)] hover:bg-[var(--color-hover)]',
                    'transition-colors duration-[var(--transition)]',
                    'focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-[var(--color-focus-ring)]',
                  ].join(' ')}
                  role="menuitem"
                >
                  {t('auth.logout', language)}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
