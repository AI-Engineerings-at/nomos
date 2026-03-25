/**
 * NomOS Select — Dropdown with keyboard navigation.
 * WCAG 2.2 AA: associated label, keyboard accessible, aria attributes.
 * Uses native <select> for maximum accessibility and mobile compatibility.
 */
'use client';

import { forwardRef, useId, type SelectHTMLAttributes } from 'react';

interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'id'> {
  /** Visible label text. Always shown. */
  label: string;
  /** Options to display in the dropdown. */
  options: SelectOption[];
  /** Placeholder text shown as first disabled option. */
  placeholder?: string;
  /** Error message displayed below the select. */
  error?: string;
  /** Helper text displayed below the select when there is no error. */
  hint?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { label, options, placeholder, error, hint, className = '', required, ...props },
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
      <div className="relative">
        <select
          ref={ref}
          id={id}
          className={[
            'w-full px-3 py-2 text-sm appearance-none',
            'bg-[var(--color-card)] text-[var(--color-text)]',
            'border rounded-[var(--radius)]',
            'transition-all duration-[var(--transition)]',
            'focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-[var(--color-focus-ring)]',
            'focus-visible:border-[var(--color-primary)]',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'pr-10',
            hasError
              ? 'border-[var(--color-error)] focus-visible:outline-[var(--color-error)]'
              : 'border-[var(--color-border)]',
          ].join(' ')}
          aria-invalid={hasError}
          aria-describedby={describedBy}
          aria-required={required}
          required={required}
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option key={option.value} value={option.value} disabled={option.disabled}>
              {option.label}
            </option>
          ))}
        </select>
        {/* Dropdown chevron icon */}
        <svg
          className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-muted)] pointer-events-none"
          xmlns="http://www.w3.org/2000/svg"
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
      </div>
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
