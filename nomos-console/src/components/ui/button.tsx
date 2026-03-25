/**
 * NomOS Button — Primary, Secondary, Danger, Ghost variants.
 * WCAG 2.2 AA: visible focus ring, keyboard accessible.
 * All buttons use Montserrat (via headline inheritance) for labels.
 */
'use client';

import { forwardRef, type ButtonHTMLAttributes } from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: [
    'bg-[var(--color-primary)] text-white',
    'hover:bg-[var(--color-primary-hover)]',
    'active:bg-[var(--color-secondary)]',
    'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-[var(--color-primary)]',
  ].join(' '),
  secondary: [
    'bg-transparent text-[var(--color-text)] border border-[var(--color-border)]',
    'hover:bg-[var(--color-hover)] hover:border-[var(--color-muted)]',
    'active:bg-[var(--color-border)]',
    'disabled:opacity-50 disabled:cursor-not-allowed',
  ].join(' '),
  danger: [
    'bg-[var(--color-error)] text-white',
    'hover:bg-[#DC2626]',
    'active:bg-[#B91C1C]',
    'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-[var(--color-error)]',
  ].join(' '),
  ghost: [
    'bg-transparent text-[var(--color-text)]',
    'hover:bg-[var(--color-hover)]',
    'active:bg-[var(--color-border)]',
    'disabled:opacity-50 disabled:cursor-not-allowed',
  ].join(' '),
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-sm gap-1.5',
  md: 'px-4 py-2 text-sm gap-2',
  lg: 'px-6 py-3 text-base gap-2.5',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'primary', size = 'md', loading = false, className = '', children, disabled, ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      className={[
        'inline-flex items-center justify-center font-semibold',
        'rounded-[var(--radius)] transition-all duration-[var(--transition)]',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]',
        'select-none whitespace-nowrap',
        'font-[family-name:var(--font-headline)]',
        variantStyles[variant],
        sizeStyles[size],
        className,
      ].join(' ')}
      disabled={disabled || loading}
      aria-busy={loading}
      {...props}
    >
      {loading && (
        <svg
          className="animate-spin h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {children}
    </button>
  );
});
