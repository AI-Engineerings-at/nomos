/**
 * NomOS User Layout — Simplified sidebar for regular users.
 * Accessible to users with role "user" or "admin" (admin can also chat).
 * Error Boundary wraps the entire content area.
 */
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { Sidebar } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';
import { ErrorBoundary } from '@/components/ui/error-boundary';

export default function UserLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, loading } = useAuth();
  const { language } = useNomosStore();

  // Redirect unauthenticated users
  const allowed = user?.role === 'user' || user?.role === 'admin';
  useEffect(() => {
    if (!loading && !allowed) {
      router.replace('/login');
    }
  }, [allowed, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--color-bg)]">
        <div className="animate-pulse text-[var(--color-muted)]">
          {t('loading.default', language)}
        </div>
      </div>
    );
  }

  if (!allowed) return null;

  return (
    <div className="min-h-screen bg-[var(--color-bg)]">
      <Sidebar />
      <div className="lg:ml-[var(--sidebar-width)]">
        <Header />
        <ErrorBoundary>
          <main id="main-content" className="p-6" aria-label={t('a11y.mainContent', language)}>
            {children}
          </main>
        </ErrorBoundary>
      </div>
    </div>
  );
}
