/**
 * NomOS Sidebar — Navigation with role-based items.
 * Eagle logo top-left with subtle #31F1A8 accent line underneath.
 * Admin/User/Officer see different navigation items.
 * WCAG 2.2 AA: semantic nav, keyboard navigation, aria-current.
 */
'use client';

import { usePathname } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import { useNomosStore, type UserRole } from '@/lib/store';
import { useAuth } from '@/lib/auth';
import { t } from '@/lib/i18n';
import type { TranslationKey } from '@/lib/i18n';

interface NavItem {
  labelKey: TranslationKey;
  href: string;
  /** SVG path(s) for the icon. */
  iconPath: string;
  /** Optional data-tour attribute for onboarding tour highlighting. */
  tourId?: string;
}

const adminNavItems: NavItem[] = [
  {
    labelKey: 'nav.dashboard',
    href: '/admin',
    iconPath: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
  },
  {
    labelKey: 'nav.myTeam',
    href: '/admin/team',
    iconPath: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
    tourId: 'my-team',
  },
  {
    labelKey: 'nav.hire',
    href: '/admin/hire',
    iconPath: 'M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z',
    tourId: 'hire',
  },
  {
    labelKey: 'nav.approvals',
    href: '/admin/approvals',
    iconPath: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
  },
  {
    labelKey: 'nav.costs',
    href: '/admin/costs',
    iconPath: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  },
  {
    labelKey: 'nav.compliance',
    href: '/admin/compliance',
    iconPath: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
    tourId: 'compliance',
  },
  {
    labelKey: 'nav.audit',
    href: '/admin/audit',
    iconPath: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01',
  },
  {
    labelKey: 'nav.diagnostics',
    href: '/admin/diagnostics',
    iconPath: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z',
  },
  {
    labelKey: 'nav.users',
    href: '/admin/users',
    iconPath: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z',
  },
  {
    labelKey: 'nav.settings',
    href: '/admin/settings',
    iconPath: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z',
  },
];

const userNavItems: NavItem[] = [
  {
    labelKey: 'nav.myAgents',
    href: '/app',
    iconPath: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
  },
  {
    labelKey: 'nav.tasks',
    href: '/app/tasks',
    iconPath: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
  },
  {
    labelKey: 'nav.help',
    href: '/app/help',
    iconPath: 'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  },
];

const officerNavItems: NavItem[] = [
  {
    labelKey: 'nav.complianceReports',
    href: '/compliance',
    iconPath: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
  },
  {
    labelKey: 'nav.audit',
    href: '/compliance/audit',
    iconPath: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01',
  },
];

function getNavItems(role: UserRole): NavItem[] {
  switch (role) {
    case 'admin':
      return adminNavItems;
    case 'user':
      return userNavItems;
    case 'officer':
      return officerNavItems;
  }
}

export function Sidebar() {
  const pathname = usePathname();
  const { language, theme } = useNomosStore();
  const { user } = useAuth();

  if (!user) return null;

  const navItems = getNavItems(user.role);
  const logoSrc = theme === 'dark' ? '/logo-new-white.png' : '/logo-new.png';

  return (
    <aside
      className={[
        'hidden lg:flex flex-col',
        'w-[var(--sidebar-width)] h-screen',
        'bg-[var(--color-card)] border-r border-[var(--color-border)]',
        'fixed left-0 top-0 z-30',
      ].join(' ')}
    >
      {/* Logo section with accent line */}
      <div className="p-5 pb-0">
        <Link
          href={user.role === 'admin' ? '/admin' : user.role === 'officer' ? '/compliance' : '/app'}
          className="flex items-center gap-3 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--color-focus-ring)] rounded-[var(--radius-sm)]"
        >
          <Image
            src={logoSrc}
            alt={t('a11y.logoAlt', language)}
            width={36}
            height={36}
            className="w-9 h-9"
            priority
          />
          <span className="text-xl font-bold text-[var(--color-text)] font-[family-name:var(--font-headline)] tracking-tight">
            NomOS
          </span>
        </Link>
        {/* Subtle #31F1A8 accent line — brand marker */}
        <div
          className="mt-4 h-[1px] rounded-full"
          style={{ background: 'var(--color-accent)' }}
          aria-hidden="true"
        />
      </div>

      {/* Navigation */}
      <nav
        className="flex-1 overflow-y-auto px-3 py-4"
        aria-label={t('a11y.navigation', language)}
      >
        <ul className="space-y-1" role="list">
          {navItems.map((item) => {
            const isActive = item.href === '/'
              ? pathname === item.href
              : pathname === item.href || pathname.startsWith(item.href + '/');

            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={[
                    'flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius)] text-sm',
                    'transition-colors duration-[var(--transition)]',
                    'focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-[var(--color-focus-ring)]',
                    isActive
                      ? 'bg-[var(--color-primary-light)] text-[var(--color-primary)] font-semibold'
                      : 'text-[var(--color-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-hover)]',
                  ].join(' ')}
                  aria-current={isActive ? 'page' : undefined}
                  {...(item.tourId ? { 'data-tour': item.tourId } : {})}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="w-5 h-5 shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={isActive ? 2.5 : 2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <path d={item.iconPath} />
                  </svg>
                  <span>{t(item.labelKey, language)}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer — version info */}
      <div className="p-4 border-t border-[var(--color-border)]">
        <p className="text-xs text-[var(--color-muted)] font-[family-name:var(--font-mono)]">
          NomOS Console v0.1.0
        </p>
      </div>
    </aside>
  );
}
