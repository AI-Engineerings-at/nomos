/**
 * NomOS Admin Layout — Sidebar + Header + Content area.
 * Only accessible to users with role "admin".
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

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, loading } = useAuth();
  const { language } = useNomosStore();

  // Redirect non-admin users
  useEffect(() => {
    if (!loading && (!user || user.role !== 'admin')) {
      router.replace('/login');
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--color-bg)]">
        <div className="animate-pulse text-[var(--color-muted)]">
          {t('loading.default', language)}
        </div>
      </div>
    );
  }

  if (!user || user.role !== 'admin') return null;

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
