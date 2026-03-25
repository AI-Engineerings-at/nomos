/**
 * NomOS Login Form — Email + Password + Submit + Error display.
 * Brand Voice: professional, warm, direct.
 * WCAG 2.2 AA: labeled inputs, error announcements, keyboard accessible.
 */
'use client';

import { useState, useCallback, type FormEvent } from 'react';
import { useAuth } from '@/lib/auth';
import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

interface LoginFormProps {
  /** Called when login succeeds and 2FA is required. */
  onRequires2FA: () => void;
  /** Called when login succeeds without 2FA. */
  onSuccess: () => void;
}

export function LoginForm({ onRequires2FA, onSuccess }: LoginFormProps) {
  const { login, error: authError } = useAuth();
  const { language } = useNomosStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      setValidationError(null);

      // Client-side validation
      if (!email.trim()) {
        setValidationError(
          language === 'de'
            ? 'Bitte geben Sie Ihre E-Mail-Adresse ein.'
            : 'Please enter your email address.',
        );
        return;
      }
      if (!password) {
        setValidationError(
          language === 'de'
            ? 'Bitte geben Sie Ihr Passwort ein.'
            : 'Please enter your password.',
        );
        return;
      }

      setLoading(true);
      try {
        const result = await login(email, password);
        if (result.requires2FA) {
          onRequires2FA();
        } else {
          onSuccess();
        }
      } catch {
        // Error is already set in auth context
      } finally {
        setLoading(false);
      }
    },
    [email, password, login, onRequires2FA, onSuccess, language],
  );

  const displayError = validationError || authError;

  return (
    <form onSubmit={handleSubmit} className="space-y-5" noValidate>
      {/* Error alert */}
      {displayError && (
        <div
          className={[
            'p-4 rounded-[var(--radius)]',
            'bg-[var(--color-error-light)] border border-[var(--color-error)]',
            'text-sm text-[var(--color-error)]',
          ].join(' ')}
          role="alert"
          aria-live="assertive"
        >
          {displayError}
        </div>
      )}

      <Input
        label={t('auth.email', language)}
        type="email"
        autoComplete="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        placeholder={language === 'de' ? 'name@firma.de' : 'name@company.com'}
        disabled={loading}
      />

      <Input
        label={t('auth.password', language)}
        type="password"
        autoComplete="current-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        placeholder={language === 'de' ? 'Ihr Passwort' : 'Your password'}
        disabled={loading}
      />

      <Button
        type="submit"
        variant="primary"
        size="lg"
        loading={loading}
        className="w-full"
      >
        {t('auth.submit', language)}
      </Button>
    </form>
  );
}
