/**
 * NomOS Input — Text input with label, error state, focus ring.
 * WCAG 2.2 AA: associated label, aria-describedby for errors, visible focus.
 */
'use client';

import { forwardRef, useId, type InputHTMLAttributes } from 'react';

interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'id'> {
  /** Visible label text. Always shown. */
  label: string;
  /** Error message displayed below the input. */
  error?: string;
  /** Helper text displayed below the input when there is no error. */
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, error, hint, className = '', required, ...props },
  ref,
) {
  const id = useId();
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;
  const hasError = Boolean(error);

  const describedBy = [
    hasError ? errorId : null,
    hint && !hasError ? hintId : null,
  ]
    .filter(Boolean)
    .join(' ') || undefined;

  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      <label
        htmlFor={id}
        className="text-sm font-semibold text-[var(--color-text)] font-[family-name:var(--font-headline)]"
      >
        {label}
        {required && (
          <span className="text-[var(--color-error)] ml-1" aria-hidden="true">
            *
          </span>
        )}
      </label>
      <input
        ref={ref}
        id={id}
        className={[
          'w-full px-3 py-2 text-sm',
          'bg-[var(--color-card)] text-[var(--color-text)]',
          'border rounded-[var(--radius)]',
          'transition-all duration-[var(--transition)]',
          'placeholder:text-[var(--color-muted)]',
          'focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-[var(--color-focus-ring)]',
          'focus-visible:border-[var(--color-primary)]',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          hasError
            ? 'border-[var(--color-error)] focus-visible:outline-[var(--color-error)]'
            : 'border-[var(--color-border)]',
        ].join(' ')}
        aria-invalid={hasError}
        aria-describedby={describedBy}
        aria-required={required}
        required={required}
        {...props}
      />
      {hasError && (
        <p id={errorId} className="text-xs text-[var(--color-error)]" role="alert">
          {error}
        </p>
      )}
      {hint && !hasError && (
        <p id={hintId} className="text-xs text-[var(--color-muted)]">
          {hint}
        </p>
      )}
    </div>
  );
});
