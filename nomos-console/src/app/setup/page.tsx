/**
 * NomOS -- First-Time Setup Wizard (/setup).
 * 4-step wizard: Vault Unseal Key -> Admin + 2FA -> LLM Provider -> Done.
 * Only shown when GET /api/system/status -> setup_required: true.
 *
 * 4 States: Loading (skeleton), Empty (N/A for wizard), Error (inline + retry), Data (form).
 * WCAG 2.2 AA: focus-visible, aria-labels, keyboard nav, progress indicator, live regions.
 * i18n: All text via translation keys -- DE + EN.
 */
'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { api, ApiError } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import type { TranslationKey } from '@/lib/i18n';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface SystemStatus {
  setup_required: boolean;
}

interface UnsealKeyResponse {
  unseal_key: string;
  auto_unseal: boolean;
}

interface BootstrapResponse {
  user_id: string;
  recovery_key: string;
}

interface TwoFASetupResponse {
  qr_code: string;
  secret: string;
}

interface ProxyStatus {
  status: string;
}

type SetupStep = 1 | 2 | 3 | 4;

// Provider options for step 3
type LlmProvider = 'nvidia' | 'openai' | 'anthropic';

interface ProviderOption {
  id: LlmProvider;
  labelKey: TranslationKey;
  recommended: boolean;
}

const PROVIDER_OPTIONS: ProviderOption[] = [
  { id: 'nvidia', labelKey: 'settings.nvidiaKey', recommended: true },
  { id: 'openai', labelKey: 'settings.openaiKey', recommended: false },
  { id: 'anthropic', labelKey: 'settings.anthropicKey', recommended: false },
];

// ---------------------------------------------------------------------------
// Password strength
// ---------------------------------------------------------------------------

interface PasswordStrength {
  score: number; // 0-4
  labelKey: TranslationKey;
  color: string;
}

function evaluatePasswordStrength(password: string): PasswordStrength {
  let score = 0;
  if (password.length >= 12) score += 1;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score += 1;
  if (/\d/.test(password)) score += 1;
  if (/[^a-zA-Z0-9]/.test(password)) score += 1;

  const levels: { labelKey: TranslationKey; color: string }[] = [
    { labelKey: 'setup.step2.strengthWeak', color: 'var(--color-error)' },
    { labelKey: 'setup.step2.strengthFair', color: 'var(--color-warning)' },
    { labelKey: 'setup.step2.strengthGood', color: 'var(--color-warning)' },
    { labelKey: 'setup.step2.strengthStrong', color: 'var(--color-success)' },
    { labelKey: 'setup.step2.strengthExcellent', color: 'var(--color-success)' },
  ];

  return { score, ...levels[score] };
}

// ---------------------------------------------------------------------------
// Progress indicator
// ---------------------------------------------------------------------------

function SetupProgress({ currentStep, totalSteps, lang }: { currentStep: number; totalSteps: number; lang: 'de' | 'en' }) {
  return (
    <div className="space-y-3" role="group" aria-label={t('a11y.wizardProgress', lang)}>
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-[var(--color-text)]">
          {t('setup.stepLabel', lang)} {currentStep}/{totalSteps}
        </span>
        <span className="text-sm text-[var(--color-muted)]">
          {Math.round((currentStep / totalSteps) * 100)}%
        </span>
      </div>
      <div className="flex gap-2">
        {Array.from({ length: totalSteps }).map((_, i) => (
          <div
            key={i}
            className={[
              'flex-1 h-2 rounded-[var(--radius-full)] transition-all duration-300',
              i < currentStep ? 'bg-[var(--color-primary)]' : 'bg-[var(--color-hover)]',
            ].join(' ')}
            aria-hidden="true"
          />
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Checkmark icon
// ---------------------------------------------------------------------------

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={3} aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Main wizard
// ---------------------------------------------------------------------------

function SetupWizardContent() {
  const router = useRouter();
  const { language, theme } = useNomosStore();
  const logoSrc = theme === 'dark' ? '/logo-new-white.png' : '/logo-new.png';

  // Global state
  const [step, setStep] = useState<SetupStep>(1);
  const [checking, setChecking] = useState(true);
  const [checkError, setCheckError] = useState<string | null>(null);

  // Step 1: Vault key
  const [unsealKey, setUnsealKey] = useState<string | null>(null);
  const [autoUnseal, setAutoUnseal] = useState(false);
  const [unsealLoading, setUnsealLoading] = useState(false);
  const [unsealError, setUnsealError] = useState<string | null>(null);
  const [keyCopied, setKeyCopied] = useState(false);
  const [keyConfirmed, setKeyConfirmed] = useState(false);

  // Step 2a: Admin account
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [adminLoading, setAdminLoading] = useState(false);
  const [adminError, setAdminError] = useState<string | null>(null);
  const [recoveryKey, setRecoveryKey] = useState<string | null>(null);
  const [recoveryConfirmed, setRecoveryConfirmed] = useState(false);

  // Step 2b: 2FA
  const [show2FA, setShow2FA] = useState(false);
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [totpCode, setTotpCode] = useState('');
  const [totpLoading, setTotpLoading] = useState(false);
  const [totpError, setTotpError] = useState<string | null>(null);
  const [totpVerified, setTotpVerified] = useState(false);
  const [twofaSkipped, setTwofaSkipped] = useState(false);

  // Step 3: LLM Provider
  const [selectedProvider, setSelectedProvider] = useState<LlmProvider>('nvidia');
  const [apiKey, setApiKey] = useState('');
  const [providerTestLoading, setProviderTestLoading] = useState(false);
  const [providerTestResult, setProviderTestResult] = useState<'success' | 'fail' | null>(null);
  const [providerTestError, setProviderTestError] = useState<string | null>(null);
  const [providerSkipped, setProviderSkipped] = useState(false);
  const [providerConfigured, setProviderConfigured] = useState(false);

  // ---------------------------------------------------------------------------
  // Check system status on mount
  // ---------------------------------------------------------------------------

  useEffect(() => {
    let cancelled = false;
    async function checkStatus() {
      try {
        const status = await api.get<SystemStatus>('/system/status');
        if (!cancelled) {
          if (!status.setup_required) {
            router.replace('/login');
          } else {
            setChecking(false);
          }
        }
      } catch (err) {
        if (!cancelled) {
          // If we cannot reach the API, still show the wizard
          // (the user may need to set up the system)
          setCheckError(
            err instanceof ApiError
              ? err.detail
              : t('error.network', language),
          );
          setChecking(false);
        }
      }
    }
    checkStatus();
    return () => { cancelled = true; };
  }, [router, language]);

  // ---------------------------------------------------------------------------
  // Step 1: Fetch unseal key
  // ---------------------------------------------------------------------------

  const fetchUnsealKey = useCallback(async () => {
    setUnsealLoading(true);
    setUnsealError(null);
    try {
      const data = await api.get<UnsealKeyResponse>('/system/unseal-key');
      setUnsealKey(data.unseal_key);
      setAutoUnseal(data.auto_unseal);
    } catch (err) {
      setUnsealError(
        err instanceof ApiError
          ? err.detail
          : t('error.network', language),
      );
    } finally {
      setUnsealLoading(false);
    }
  }, [language]);

  useEffect(() => {
    if (step === 1 && !checking && !unsealKey && !unsealError) {
      fetchUnsealKey();
    }
  }, [step, checking, unsealKey, unsealError, fetchUnsealKey]);

  // ---------------------------------------------------------------------------
  // Step 1: Copy key
  // ---------------------------------------------------------------------------

  const handleCopyKey = useCallback(async () => {
    if (!unsealKey) return;
    try {
      await navigator.clipboard.writeText(unsealKey);
      setKeyCopied(true);
    } catch {
      // Fallback: select text so user can copy manually
      setKeyCopied(false);
    }
  }, [unsealKey]);

  // ---------------------------------------------------------------------------
  // Step 2a: Create admin
  // ---------------------------------------------------------------------------

  const handleCreateAdmin = useCallback(async () => {
    setAdminError(null);
    // Validate
    if (!email.trim()) {
      setAdminError(t('setup.step2.errorEmailRequired', language));
      return;
    }
    if (password.length < 12) {
      setAdminError(t('setup.step2.errorPasswordLength', language));
      return;
    }
    if (password !== passwordConfirm) {
      setAdminError(t('setup.step2.errorPasswordMismatch', language));
      return;
    }

    setAdminLoading(true);
    try {
      const result = await api.post<BootstrapResponse>('/users/bootstrap', {
        email,
        password,
      });
      setRecoveryKey(result.recovery_key);
    } catch (err) {
      setAdminError(
        err instanceof ApiError
          ? err.detail
          : t('error.serverError', language),
      );
    } finally {
      setAdminLoading(false);
    }
  }, [email, password, passwordConfirm, language]);

  // ---------------------------------------------------------------------------
  // Step 2b: Setup 2FA
  // ---------------------------------------------------------------------------

  const handleSetup2FA = useCallback(async () => {
    setTotpLoading(true);
    setTotpError(null);
    try {
      const data = await api.post<TwoFASetupResponse>('/auth/2fa/setup');
      setQrCode(data.qr_code);
      setShow2FA(true);
    } catch (err) {
      setTotpError(
        err instanceof ApiError
          ? err.detail
          : t('error.serverError', language),
      );
    } finally {
      setTotpLoading(false);
    }
  }, [language]);

  const handleVerify2FA = useCallback(async () => {
    if (totpCode.length !== 6) return;
    setTotpLoading(true);
    setTotpError(null);
    try {
      await api.post('/auth/2fa/verify', { code: totpCode });
      setTotpVerified(true);
    } catch (err) {
      setTotpError(
        err instanceof ApiError
          ? err.detail
          : t('auth.totpInvalid', language),
      );
    } finally {
      setTotpLoading(false);
    }
  }, [totpCode, language]);

  // ---------------------------------------------------------------------------
  // Step 3: Test LLM provider
  // ---------------------------------------------------------------------------

  const handleTestProvider = useCallback(async () => {
    setProviderTestLoading(true);
    setProviderTestResult(null);
    setProviderTestError(null);
    try {
      // Save the key first
      const keyField = `${selectedProvider}_api_key`;
      await api.patch('/settings', { [keyField]: apiKey });

      // Then test the connection
      const status = await api.get<ProxyStatus>('/proxy/status');
      if (status.status === 'ok' || status.status === 'healthy') {
        setProviderTestResult('success');
        setProviderConfigured(true);
      } else {
        setProviderTestResult('fail');
        setProviderTestError(t('setup.step3.testFail', language));
      }
    } catch (err) {
      setProviderTestResult('fail');
      setProviderTestError(
        err instanceof ApiError
          ? err.detail
          : t('setup.step3.testFail', language),
      );
    } finally {
      setProviderTestLoading(false);
    }
  }, [selectedProvider, apiKey, language]);

  // ---------------------------------------------------------------------------
  // Navigation
  // ---------------------------------------------------------------------------

  const canProceedStep1 = keyConfirmed && unsealKey !== null;

  const canProceedStep2 = recoveryKey !== null && recoveryConfirmed && (totpVerified || twofaSkipped);

  const goToStep = (s: SetupStep) => setStep(s);

  // ---------------------------------------------------------------------------
  // Password strength
  // ---------------------------------------------------------------------------

  const pwStrength = evaluatePasswordStrength(password);

  // ---------------------------------------------------------------------------
  // Render: Loading check
  // ---------------------------------------------------------------------------

  if (checking) {
    return (
      <div className="flex flex-col items-center gap-4">
        <div className="animate-pulse w-16 h-16 rounded-full bg-[var(--color-hover)]" />
        <p className="text-sm text-[var(--color-muted)]">{t('loading.default', language)}</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Brand header */}
      <div className="text-center">
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
          {t('setup.title', language)}
        </h1>
        <p className="mt-2 text-sm text-[var(--color-muted)]">
          {t('setup.subtitle', language)}
        </p>
        {/* Accent line */}
        <div
          className="mx-auto mt-4 w-12 h-[2px] rounded-full"
          style={{ background: 'var(--color-accent)' }}
          aria-hidden="true"
        />
      </div>

      {/* System status error banner */}
      {checkError && (
        <div className="p-4 rounded-[var(--radius)] bg-[var(--color-warning-light)] border border-[var(--color-warning)]" role="alert">
          <p className="text-sm text-[var(--color-text)]">{checkError}</p>
        </div>
      )}

      {/* Progress */}
      <SetupProgress currentStep={step} totalSteps={4} lang={language} />

      {/* ================================================================= */}
      {/* Step 1: Vault Unseal Key                                          */}
      {/* ================================================================= */}

      {step === 1 && (
        <Card className="space-y-6">
          <h2 className="text-lg font-bold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
            {t('setup.step1.title', language)}
          </h2>
          <p className="text-sm text-[var(--color-muted)]">
            {t('setup.step1.description', language)}
          </p>

          {/* Warning */}
          <div className="p-4 rounded-[var(--radius)] bg-[var(--color-warning-light)] border border-[var(--color-warning)]" role="alert">
            <p className="text-sm font-semibold text-[var(--color-text)]">
              {t('setup.step1.warning', language)}
            </p>
          </div>

          {/* Unseal key display */}
          {unsealLoading && (
            <div className="space-y-2">
              <div className="h-12 rounded-[var(--radius)] bg-[var(--color-hover)] animate-pulse" />
            </div>
          )}

          {unsealError && (
            <div className="p-4 rounded-[var(--radius)] bg-[var(--color-error-light)] border border-[var(--color-error)]" role="alert">
              <p className="text-sm text-[var(--color-error)]">{unsealError}</p>
              <Button variant="secondary" size="sm" className="mt-2" onClick={fetchUnsealKey}>
                {t('action.retry', language)}
              </Button>
            </div>
          )}

          {unsealKey && (
            <>
              <div className="relative">
                <pre
                  className="p-4 rounded-[var(--radius)] bg-[var(--color-hover)] border border-[var(--color-border)] text-sm font-[family-name:var(--font-mono)] text-[var(--color-text)] overflow-x-auto select-all"
                  aria-label={t('setup.step1.title', language)}
                >
                  {unsealKey}
                </pre>
                <Button
                  variant="secondary"
                  size="sm"
                  className="absolute top-2 right-2"
                  onClick={handleCopyKey}
                  aria-label={t('setup.step1.copy', language)}
                >
                  {keyCopied ? t('setup.step1.copied', language) : t('setup.step1.copy', language)}
                </Button>
              </div>

              {autoUnseal && (
                <p className="text-xs text-[var(--color-muted)]">
                  {t('setup.step4.autoUnseal', language)}
                </p>
              )}

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={keyConfirmed}
                  onChange={(e) => setKeyConfirmed(e.target.checked)}
                  className="w-4 h-4 rounded accent-[var(--color-primary)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]"
                />
                <span className="text-sm text-[var(--color-text)]">
                  {t('setup.step1.checkbox', language)}
                </span>
              </label>
            </>
          )}
        </Card>
      )}

      {/* ================================================================= */}
      {/* Step 2: Admin Account + 2FA                                       */}
      {/* ================================================================= */}

      {step === 2 && (
        <Card className="space-y-6">
          {/* Step 2a: Create admin (before recovery key) */}
          {!recoveryKey && (
            <>
              <h2 className="text-lg font-bold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
                {t('setup.step2.title', language)}
              </h2>

              <Input
                label={t('setup.step2.email', language)}
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="admin@example.com"
              />

              <div className="space-y-2">
                <Input
                  label={t('setup.step2.password', language)}
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  hint={t('setup.step2.passwordHint', language)}
                />
                {/* Password strength indicator */}
                {password.length > 0 && (
                  <div className="space-y-1">
                    <div className="flex gap-1">
                      {Array.from({ length: 4 }).map((_, i) => (
                        <div
                          key={i}
                          className="flex-1 h-1.5 rounded-full transition-all duration-300"
                          style={{
                            backgroundColor: i < pwStrength.score
                              ? pwStrength.color
                              : 'var(--color-hover)',
                          }}
                          aria-hidden="true"
                        />
                      ))}
                    </div>
                    <p className="text-xs" style={{ color: pwStrength.color }}>
                      {t(pwStrength.labelKey, language)}
                    </p>
                  </div>
                )}
              </div>

              <Input
                label={t('setup.step2.confirm', language)}
                type="password"
                value={passwordConfirm}
                onChange={(e) => setPasswordConfirm(e.target.value)}
                required
                error={
                  passwordConfirm.length > 0 && password !== passwordConfirm
                    ? t('setup.step2.errorPasswordMismatch', language)
                    : undefined
                }
              />

              {adminError && (
                <div className="p-3 rounded-[var(--radius)] bg-[var(--color-error-light)] border border-[var(--color-error)]" role="alert">
                  <p className="text-sm text-[var(--color-error)]">{adminError}</p>
                </div>
              )}

              <Button
                onClick={handleCreateAdmin}
                loading={adminLoading}
                disabled={!email.trim() || password.length < 12 || password !== passwordConfirm}
              >
                {t('action.create', language)}
              </Button>
            </>
          )}

          {/* Step 2a continued: Show recovery key */}
          {recoveryKey && !show2FA && !twofaSkipped && (
            <>
              <h2 className="text-lg font-bold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
                {t('setup.step2.recoveryTitle', language)}
              </h2>

              <div className="p-4 rounded-[var(--radius)] bg-[var(--color-warning-light)] border border-[var(--color-warning)]" role="alert">
                <p className="text-sm font-semibold text-[var(--color-text)]">
                  {t('setup.step2.recoveryWarning', language)}
                </p>
              </div>

              <pre className="p-4 rounded-[var(--radius)] bg-[var(--color-hover)] border border-[var(--color-border)] text-sm font-[family-name:var(--font-mono)] text-[var(--color-text)] select-all">
                {recoveryKey}
              </pre>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={recoveryConfirmed}
                  onChange={(e) => setRecoveryConfirmed(e.target.checked)}
                  className="w-4 h-4 rounded accent-[var(--color-primary)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]"
                />
                <span className="text-sm text-[var(--color-text)]">
                  {t('setup.step2.recoveryCheckbox', language)}
                </span>
              </label>

              {/* 2FA section */}
              <div className="pt-4 border-t border-[var(--color-border)] space-y-3">
                <h3 className="text-base font-bold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
                  {t('setup.step2b.title', language)}
                </h3>
                <p className="text-sm text-[var(--color-muted)]">
                  {t('setup.step2b.description', language)}
                </p>
                <div className="flex gap-3">
                  <Button onClick={handleSetup2FA} loading={totpLoading} disabled={!recoveryConfirmed}>
                    {t('setup.step2b.activate', language)}
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => setTwofaSkipped(true)}
                    disabled={!recoveryConfirmed}
                  >
                    {t('setup.step2b.skip', language)}
                  </Button>
                </div>
              </div>
            </>
          )}

          {/* Step 2b: 2FA QR code and verify */}
          {show2FA && !totpVerified && (
            <>
              <h2 className="text-lg font-bold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
                {t('setup.step2b.title', language)}
              </h2>

              {qrCode && (
                <div className="flex justify-center">
                  {/* QR code is a data URI */}
                  <img
                    src={qrCode}
                    alt={t('setup.step2b.qrAlt', language)}
                    className="w-48 h-48 rounded-[var(--radius)] border border-[var(--color-border)]"
                  />
                </div>
              )}

              <Input
                label={t('setup.step2b.code', language)}
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="000000"
                required
                error={totpError ?? undefined}
              />

              <Button
                onClick={handleVerify2FA}
                loading={totpLoading}
                disabled={totpCode.length !== 6}
              >
                {t('setup.step2b.verify', language)}
              </Button>
            </>
          )}

          {/* Step 2b: 2FA verified */}
          {totpVerified && (
            <div className="flex items-center gap-3 p-4 rounded-[var(--radius)] bg-[var(--color-success-light)] border border-[var(--color-success)]" role="status">
              <CheckIcon className="w-5 h-5 text-[var(--color-success)]" />
              <p className="text-sm font-medium text-[var(--color-text)]">
                {t('setup.step2b.verified', language)}
              </p>
            </div>
          )}
        </Card>
      )}

      {/* ================================================================= */}
      {/* Step 3: LLM Provider                                              */}
      {/* ================================================================= */}

      {step === 3 && (
        <Card className="space-y-6">
          <h2 className="text-lg font-bold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
            {t('setup.step3.title', language)}
          </h2>
          <p className="text-sm text-[var(--color-muted)]">
            {t('setup.step3.description', language)}
          </p>

          {/* Provider selection */}
          <div className="space-y-2" role="radiogroup" aria-label={t('setup.step3.title', language)}>
            {PROVIDER_OPTIONS.map((provider) => (
              <label
                key={provider.id}
                className={[
                  'flex items-center gap-3 p-3 rounded-[var(--radius)] border cursor-pointer transition-all duration-[var(--transition)]',
                  selectedProvider === provider.id
                    ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)]'
                    : 'border-[var(--color-border)] hover:border-[var(--color-muted)]',
                ].join(' ')}
              >
                <input
                  type="radio"
                  name="llm-provider"
                  value={provider.id}
                  checked={selectedProvider === provider.id}
                  onChange={() => setSelectedProvider(provider.id)}
                  className="w-4 h-4 accent-[var(--color-primary)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]"
                />
                <span className="text-sm text-[var(--color-text)]">
                  {t(provider.labelKey, language)}
                  {provider.recommended && (
                    <span className="ml-2 text-xs text-[var(--color-primary)] font-medium">
                      ({t('setup.step3.recommended', language)})
                    </span>
                  )}
                </span>
              </label>
            ))}
          </div>

          {/* API Key input */}
          <Input
            label={t('setup.step3.apiKeyLabel', language)}
            type="password"
            value={apiKey}
            onChange={(e) => {
              setApiKey(e.target.value);
              setProviderTestResult(null);
              setProviderTestError(null);
            }}
            placeholder="sk-..."
          />

          {/* Test result */}
          {providerTestResult === 'success' && (
            <div className="flex items-center gap-3 p-3 rounded-[var(--radius)] bg-[var(--color-success-light)] border border-[var(--color-success)]" role="status">
              <CheckIcon className="w-5 h-5 text-[var(--color-success)]" />
              <p className="text-sm font-medium text-[var(--color-text)]">{t('setup.step3.testSuccess', language)}</p>
            </div>
          )}

          {providerTestResult === 'fail' && (
            <div className="p-3 rounded-[var(--radius)] bg-[var(--color-error-light)] border border-[var(--color-error)]" role="alert">
              <p className="text-sm text-[var(--color-error)]">{providerTestError}</p>
            </div>
          )}

          <div className="flex gap-3">
            <Button
              onClick={handleTestProvider}
              loading={providerTestLoading}
              disabled={!apiKey.trim()}
            >
              {t('setup.step3.test', language)}
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                setProviderSkipped(true);
                goToStep(4);
              }}
            >
              {t('setup.step3.skip', language)}
            </Button>
          </div>
        </Card>
      )}

      {/* ================================================================= */}
      {/* Step 4: Done                                                      */}
      {/* ================================================================= */}

      {step === 4 && (
        <Card className="space-y-6">
          <h2 className="text-lg font-bold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
            {t('setup.step4.title', language)}
          </h2>

          {/* Summary list */}
          <div className="space-y-3" role="list" aria-label={t('setup.step4.title', language)}>
            {/* Vault */}
            <div className="flex items-center gap-3" role="listitem">
              <CheckIcon className="w-5 h-5 text-[var(--color-success)]" />
              <span className="text-sm text-[var(--color-text)]">{t('setup.step4.vault', language)}</span>
            </div>
            {/* Admin */}
            <div className="flex items-center gap-3" role="listitem">
              <CheckIcon className="w-5 h-5 text-[var(--color-success)]" />
              <span className="text-sm text-[var(--color-text)]">{t('setup.step4.admin', language)}</span>
            </div>
            {/* 2FA */}
            <div className="flex items-center gap-3" role="listitem">
              {totpVerified ? (
                <CheckIcon className="w-5 h-5 text-[var(--color-success)]" />
              ) : (
                <div className="w-5 h-5 rounded-full border-2 border-[var(--color-muted)]" aria-hidden="true" />
              )}
              <span className="text-sm text-[var(--color-text)]">
                {t('setup.step4.twofa', language)}
                {twofaSkipped && (
                  <span className="ml-2 text-xs text-[var(--color-muted)]">
                    ({t('setup.step2b.skip', language)})
                  </span>
                )}
              </span>
            </div>
            {/* Provider */}
            <div className="flex items-center gap-3" role="listitem">
              {providerConfigured ? (
                <CheckIcon className="w-5 h-5 text-[var(--color-success)]" />
              ) : (
                <div className="w-5 h-5 rounded-full border-2 border-[var(--color-muted)]" aria-hidden="true" />
              )}
              <span className="text-sm text-[var(--color-text)]">
                {t('setup.step4.provider', language)}
                {providerSkipped && (
                  <span className="ml-2 text-xs text-[var(--color-muted)]">
                    ({t('setup.step3.skip', language)})
                  </span>
                )}
              </span>
            </div>
          </div>

          <Button size="lg" className="w-full" onClick={() => router.push('/admin')}>
            {t('setup.step4.start', language)}
          </Button>
        </Card>
      )}

      {/* ================================================================= */}
      {/* Navigation buttons                                                */}
      {/* ================================================================= */}

      {step < 4 && (
        <div className="flex justify-between">
          {step > 1 ? (
            <Button variant="secondary" onClick={() => goToStep((step - 1) as SetupStep)}>
              {t('action.back', language)}
            </Button>
          ) : (
            <div /> // Spacer
          )}
          {step === 1 && (
            <Button onClick={() => goToStep(2)} disabled={!canProceedStep1}>
              {t('action.next', language)}
            </Button>
          )}
          {step === 2 && (
            <Button onClick={() => goToStep(3)} disabled={!canProceedStep2}>
              {t('action.next', language)}
            </Button>
          )}
          {step === 3 && providerConfigured && (
            <Button onClick={() => goToStep(4)}>
              {t('action.next', language)}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

export default function SetupPage() {
  return (
    <ErrorBoundary>
      <SetupWizardContent />
    </ErrorBoundary>
  );
}
