/**
 * NomOS Login Page — Email + Password + optional 2FA.
 * Full-page layout with Eagle logo and brand styling.
 * Redirects to appropriate dashboard on successful login.
 */
'use client';

import { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { useNomosStore } from '@/lib/store';
import { useAuth } from '@/lib/auth';
import { t } from '@/lib/i18n';
import { LoginForm } from '@/components/auth/login-form';
import { TotpInput } from '@/components/auth/totp-input';
import { ErrorBoundary } from '@/components/ui/error-boundary';

type LoginStep = 'credentials' | 'totp';

export default function LoginPage() {
  const router = useRouter();
  const { language, theme } = useNomosStore();
  const { user, loading } = useAuth();
  const [step, setStep] = useState<LoginStep>('credentials');

  // Redirect if already logged in
  useEffect(() => {
    if (!loading && user) {
      const destination = user.role === 'admin'
        ? '/admin'
        : user.role === 'officer'
          ? '/compliance'
          : '/app';
      router.replace(destination);
    }
  }, [user, loading, router]);

  const handleLoginSuccess = useCallback(() => {
    // User is set in auth context; the useEffect above will redirect
  }, []);

  const handleRequires2FA = useCallback(() => {
    setStep('totp');
  }, []);

  const handleTotpSuccess = useCallback(() => {
    // User is set in auth context; the useEffect above will redirect
  }, []);

  const handleTotpBack = useCallback(() => {
    setStep('credentials');
  }, []);

  const logoSrc = theme === 'dark' ? '/logo-new-white.png' : '/logo-new.png';

  // Don't render form if still checking session
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--color-bg)]">
        <div className="animate-pulse text-[var(--color-muted)]">
          {t('loading.default', language)}
        </div>
      </div>
    );
  }

  // Don't render if user is already logged in (redirect will happen)
  if (user) return null;

  return (
    <ErrorBoundary>
      <main
        id="main-content"
        className="min-h-screen flex items-center justify-center bg-[var(--color-bg)] px-4"
      >
        <div className="w-full max-w-md">
          {/* Brand header */}
          <div className="text-center mb-8">
            <div className="flex justify-center mb-4">
              <Image
                src={logoSrc}
                alt={t('a11y.logoAlt', language)}
                width={64}
                height={64}
                className="w-16 h-16"
                priority
              />
            </div>
            <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)] tracking-tight">
              {step === 'credentials'
                ? t('auth.loginTitle', language)
                : t('auth.totpTitle', language)
              }
            </h1>
            <p className="mt-2 text-sm text-[var(--color-muted)]">
              {step === 'credentials'
                ? t('auth.loginSubtitle', language)
                : t('auth.totpSubtitle', language)
              }
            </p>
            {/* Accent line */}
            <div
              className="mx-auto mt-4 w-12 h-[2px] rounded-full"
              style={{ background: 'var(--color-accent)' }}
              aria-hidden="true"
            />
          </div>

          {/* Login card */}
          <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-[var(--radius-lg)] shadow-[var(--shadow-card)] p-8">
            {step === 'credentials' ? (
              <LoginForm
                onSuccess={handleLoginSuccess}
                onRequires2FA={handleRequires2FA}
              />
            ) : (
              <TotpInput
                onSuccess={handleTotpSuccess}
                onBack={handleTotpBack}
              />
            )}
          </div>

          {/* Footer */}
          <p className="mt-6 text-center text-xs text-[var(--color-muted)] font-[family-name:var(--font-mono)]">
            NomOS Console v0.1.0
          </p>
        </div>
      </main>
    </ErrorBoundary>
  );
}
