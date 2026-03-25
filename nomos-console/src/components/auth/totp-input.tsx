/**
 * NomOS TOTP Input — 6-digit code input for 2FA.
 * Individual digit boxes with auto-advance and paste support.
 * WCAG 2.2 AA: labeled, keyboard accessible, error announcements.
 */
'use client';

import { useState, useCallback, useRef, type FormEvent, type KeyboardEvent, type ClipboardEvent } from 'react';
import { useAuth } from '@/lib/auth';
import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { Button } from '@/components/ui/button';

interface TotpInputProps {
  /** Called when TOTP verification succeeds. */
  onSuccess: () => void;
  /** Called when user wants to go back to the login form. */
  onBack: () => void;
}

const CODE_LENGTH = 6;

export function TotpInput({ onSuccess, onBack }: TotpInputProps) {
  const { verifyTotp, error: authError } = useAuth();
  const { language } = useNomosStore();
  const [digits, setDigits] = useState<string[]>(Array(CODE_LENGTH).fill(''));
  const [loading, setLoading] = useState(false);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const handleDigitChange = useCallback(
    (index: number, value: string) => {
      // Only accept digits
      const digit = value.replace(/\D/g, '').slice(-1);
      const newDigits = [...digits];
      newDigits[index] = digit;
      setDigits(newDigits);

      // Auto-advance to next input
      if (digit && index < CODE_LENGTH - 1) {
        inputRefs.current[index + 1]?.focus();
      }
    },
    [digits],
  );

  const handleKeyDown = useCallback(
    (index: number, e: KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Backspace' && !digits[index] && index > 0) {
        // Move back on backspace when current field is empty
        inputRefs.current[index - 1]?.focus();
      }
      if (e.key === 'ArrowLeft' && index > 0) {
        inputRefs.current[index - 1]?.focus();
      }
      if (e.key === 'ArrowRight' && index < CODE_LENGTH - 1) {
        inputRefs.current[index + 1]?.focus();
      }
    },
    [digits],
  );

  const handlePaste = useCallback(
    (e: ClipboardEvent<HTMLInputElement>) => {
      e.preventDefault();
      const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, CODE_LENGTH);
      if (pasted.length > 0) {
        const newDigits = [...digits];
        for (let i = 0; i < pasted.length; i++) {
          newDigits[i] = pasted[i];
        }
        setDigits(newDigits);
        // Focus last filled or the next empty
        const focusIndex = Math.min(pasted.length, CODE_LENGTH - 1);
        inputRefs.current[focusIndex]?.focus();
      }
    },
    [digits],
  );

  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      const code = digits.join('');
      if (code.length !== CODE_LENGTH) return;

      setLoading(true);
      try {
        await verifyTotp(code);
        onSuccess();
      } catch {
        // Error set in auth context
        // Clear digits for retry
        setDigits(Array(CODE_LENGTH).fill(''));
        inputRefs.current[0]?.focus();
      } finally {
        setLoading(false);
      }
    },
    [digits, verifyTotp, onSuccess],
  );

  const isComplete = digits.every((d) => d.length === 1);

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Error alert */}
      {authError && (
        <div
          className={[
            'p-4 rounded-[var(--radius)]',
            'bg-[var(--color-error-light)] border border-[var(--color-error)]',
            'text-sm text-[var(--color-error)]',
          ].join(' ')}
          role="alert"
          aria-live="assertive"
        >
          {authError}
        </div>
      )}

      <fieldset>
        <legend className="text-sm font-semibold text-[var(--color-text)] mb-3 font-[family-name:var(--font-headline)]">
          {t('auth.totpLabel', language)}
        </legend>
        <div className="flex gap-2 justify-center" role="group" aria-label={t('auth.totpLabel', language)}>
          {digits.map((digit, index) => (
            <input
              key={index}
              ref={(el) => { inputRefs.current[index] = el; }}
              type="text"
              inputMode="numeric"
              autoComplete={index === 0 ? 'one-time-code' : 'off'}
              maxLength={1}
              value={digit}
              onChange={(e) => handleDigitChange(index, e.target.value)}
              onKeyDown={(e) => handleKeyDown(index, e)}
              onPaste={index === 0 ? handlePaste : undefined}
              className={[
                'w-12 h-14 text-center text-xl font-bold',
                'bg-[var(--color-card)] text-[var(--color-text)]',
                'border border-[var(--color-border)] rounded-[var(--radius)]',
                'transition-all duration-[var(--transition)]',
                'focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-[var(--color-focus-ring)]',
                'focus-visible:border-[var(--color-primary)]',
                'font-[family-name:var(--font-mono)]',
              ].join(' ')}
              aria-label={
                language === 'de'
                  ? `Stelle ${index + 1} von ${CODE_LENGTH}`
                  : `Digit ${index + 1} of ${CODE_LENGTH}`
              }
              disabled={loading}
            />
          ))}
        </div>
      </fieldset>

      <div className="flex flex-col gap-3">
        <Button
          type="submit"
          variant="primary"
          size="lg"
          loading={loading}
          disabled={!isComplete}
          className="w-full"
        >
          {t('auth.totpSubmit', language)}
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="md"
          onClick={onBack}
          disabled={loading}
          className="w-full"
        >
          {t('action.back', language)}
        </Button>
      </div>
    </form>
  );
}
