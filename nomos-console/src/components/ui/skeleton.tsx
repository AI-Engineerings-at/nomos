/**
 * NomOS Skeleton — Loading placeholder with animated shimmer.
 * Used instead of spinners for content-aware loading states.
 * WCAG: aria-busy on parent, role="status" with sr-only label.
 */
'use client';

interface SkeletonProps {
  /** Width class (e.g., "w-full", "w-32"). Defaults to "w-full". */
  width?: string;
  /** Height class (e.g., "h-4", "h-8"). Defaults to "h-4". */
  height?: string;
  /** Whether to use rounded-full for avatar shapes. */
  rounded?: boolean;
  /** Optional className. */
  className?: string;
}

export function Skeleton({
  width = 'w-full',
  height = 'h-4',
  rounded = false,
  className = '',
}: SkeletonProps) {
  return (
    <div
      className={[
        'skeleton-shimmer',
        width,
        height,
        rounded ? 'rounded-full' : 'rounded-[var(--radius-sm)]',
        className,
      ].join(' ')}
      aria-hidden="true"
    />
  );
}

/** Pre-built skeleton for a card with title + description + content. */
export function SkeletonCard() {
  return (
    <div
      className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-[var(--radius)] p-6 space-y-4"
      role="status"
      aria-busy="true"
    >
      <span className="sr-only">Wird geladen...</span>
      <Skeleton width="w-1/3" height="h-5" />
      <Skeleton width="w-2/3" height="h-3" />
      <div className="space-y-2 pt-2">
        <Skeleton height="h-3" />
        <Skeleton width="w-5/6" height="h-3" />
        <Skeleton width="w-4/6" height="h-3" />
      </div>
    </div>
  );
}

/** Pre-built skeleton for a table row. */
export function SkeletonTableRow({ columns = 4 }: { columns?: number }) {
  return (
    <tr aria-hidden="true">
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <Skeleton width={i === 0 ? 'w-3/4' : 'w-1/2'} height="h-3" />
        </td>
      ))}
    </tr>
  );
}

/** Pre-built skeleton for an agent / employee badge card. */
export function SkeletonBadge() {
  return (
    <div
      className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-[var(--radius)] p-4 flex items-center gap-4"
      role="status"
      aria-busy="true"
    >
      <span className="sr-only">Wird geladen...</span>
      <Skeleton width="w-12" height="h-12" rounded />
      <div className="flex-1 space-y-2">
        <Skeleton width="w-24" height="h-4" />
        <Skeleton width="w-16" height="h-3" />
      </div>
      <Skeleton width="w-16" height="h-6" className="rounded-full" />
    </div>
  );
}
