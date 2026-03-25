/**
 * NomOS Badge — Status indicators using Mitarbeiter-Metapher.
 * online=green (Aktiv), paused=yellow (Pausiert), offline=red (Offline), killed=gray (Gekuendigt).
 * WCAG: status is conveyed by both color AND text, not color alone.
 */
'use client';

export type BadgeStatus = 'online' | 'paused' | 'offline' | 'killed' | 'deploying' | 'error';

interface BadgeProps {
  status: BadgeStatus;
  /** Label text. If not provided, uses a default German label. */
  label?: string;
  /** Optional className override. */
  className?: string;
}

const statusConfig: Record<BadgeStatus, { dotColor: string; bgColor: string; textColor: string; defaultLabel: string }> = {
  online: {
    dotColor: 'bg-[var(--color-success)]',
    bgColor: 'bg-[var(--color-success-light)]',
    textColor: 'text-[var(--color-success)]',
    defaultLabel: 'Aktiv',
  },
  paused: {
    dotColor: 'bg-[var(--color-warning)]',
    bgColor: 'bg-[var(--color-warning-light)]',
    textColor: 'text-[var(--color-warning)]',
    defaultLabel: 'Pausiert',
  },
  offline: {
    dotColor: 'bg-[var(--color-error)]',
    bgColor: 'bg-[var(--color-error-light)]',
    textColor: 'text-[var(--color-error)]',
    defaultLabel: 'Offline',
  },
  killed: {
    dotColor: 'bg-[var(--color-muted)]',
    bgColor: 'bg-[var(--color-hover)]',
    textColor: 'text-[var(--color-muted)]',
    defaultLabel: 'Gekuendigt',
  },
  deploying: {
    dotColor: 'bg-[var(--color-primary)]',
    bgColor: 'bg-[var(--color-primary-light)]',
    textColor: 'text-[var(--color-primary)]',
    defaultLabel: 'Einarbeitung',
  },
  error: {
    dotColor: 'bg-[var(--color-error)]',
    bgColor: 'bg-[var(--color-error-light)]',
    textColor: 'text-[var(--color-error)]',
    defaultLabel: 'Gestoert',
  },
};

export function Badge({ status, label, className = '' }: BadgeProps) {
  const config = statusConfig[status];
  const displayLabel = label ?? config.defaultLabel;

  return (
    <span
      className={[
        'inline-flex items-center gap-1.5 px-2.5 py-1',
        'text-xs font-semibold rounded-[var(--radius-full)]',
        config.bgColor,
        config.textColor,
        className,
      ].join(' ')}
      role="status"
      aria-label={displayLabel}
    >
      <span
        className={`inline-block w-2 h-2 rounded-full ${config.dotColor}`}
        aria-hidden="true"
      />
      {displayLabel}
    </span>
  );
}
