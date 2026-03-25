/**
 * NomOS Empty State — Icon + message + CTA button.
 * Used when a section has no data yet.
 * Mitarbeiter-Metapher: helpful text with actionable next step.
 */
'use client';

import { Button, type ButtonVariant } from './button';

interface EmptyStateProps {
  /** Main message displayed prominently. */
  message: string;
  /** Optional description with more detail. */
  description?: string;
  /** CTA button label. If provided, the button is shown. */
  ctaLabel?: string;
  /** CTA button click handler. */
  onCtaClick?: () => void;
  /** CTA button variant. Defaults to primary. */
  ctaVariant?: ButtonVariant;
  /** Optional custom icon element. If not provided, a default empty-box icon is used. */
  icon?: React.ReactNode;
  /** Optional className. */
  className?: string;
}

function DefaultIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      className="w-16 h-16 text-[var(--color-border)]"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={1}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
      />
    </svg>
  );
}

export function EmptyState({
  message,
  description,
  ctaLabel,
  onCtaClick,
  ctaVariant = 'primary',
  icon,
  className = '',
}: EmptyStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center py-12 px-6 text-center ${className}`}
      role="status"
    >
      <div className="mb-4">{icon ?? <DefaultIcon />}</div>
      <h3 className="text-lg font-bold text-[var(--color-text)] mb-2">
        {message}
      </h3>
      {description && (
        <p className="text-sm text-[var(--color-muted)] max-w-md mb-6">
          {description}
        </p>
      )}
      {ctaLabel && onCtaClick && (
        <Button variant={ctaVariant} onClick={onCtaClick}>
          {ctaLabel}
        </Button>
      )}
    </div>
  );
}
