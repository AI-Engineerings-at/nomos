/**
 * NomOS Toast — Success/Error/Warning/Info notifications.
 * Renders in bottom-right corner. Auto-dismiss. Accessible live region.
 */
'use client';

import { useNomosStore, type Toast as ToastType } from '@/lib/store';

const iconMap: Record<ToastType['type'], { path: string; color: string }> = {
  success: {
    path: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
    color: 'text-[var(--color-success)]',
  },
  error: {
    path: 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    color: 'text-[var(--color-error)]',
  },
  warning: {
    path: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z',
    color: 'text-[var(--color-warning)]',
  },
  info: {
    path: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    color: 'text-[var(--color-primary)]',
  },
};

function ToastItem({ toast }: { toast: ToastType }) {
  const removeToast = useNomosStore((s) => s.removeToast);
  const icon = iconMap[toast.type];

  return (
    <div
      className={[
        'flex items-start gap-3 p-4 w-80',
        'bg-[var(--color-card)] border border-[var(--color-border)]',
        'rounded-[var(--radius)] shadow-[var(--shadow-card-hover)]',
      ].join(' ')}
      style={{ animation: 'toast-slide-in 200ms ease forwards' }}
      role="alert"
      aria-live="assertive"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className={`w-5 h-5 shrink-0 mt-0.5 ${icon.color}`}
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
        aria-hidden="true"
      >
        <path strokeLinecap="round" strokeLinejoin="round" d={icon.path} />
      </svg>
      <p className="text-sm text-[var(--color-text)] flex-1">{toast.message}</p>
      <button
        onClick={() => removeToast(toast.id)}
        className={[
          'p-1 rounded-[var(--radius-sm)] shrink-0',
          'text-[var(--color-muted)] hover:text-[var(--color-text)]',
          'hover:bg-[var(--color-hover)]',
          'transition-colors duration-[var(--transition)]',
          'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]',
        ].join(' ')}
        aria-label="Benachrichtigung schliessen"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          aria-hidden="true"
        >
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>
  );
}

/** Toast container — mount once in the root layout. */
export function ToastContainer() {
  const toasts = useNomosStore((s) => s.toasts);

  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2"
      aria-label="Benachrichtigungen"
      role="region"
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} />
      ))}
    </div>
  );
}
