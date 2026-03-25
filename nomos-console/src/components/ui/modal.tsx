/**
 * NomOS Modal — Accessible dialog with focus trap and ESC to close.
 * WCAG 2.2 AA: focus trap, ESC key, aria-modal, role="dialog",
 * returns focus to trigger element on close.
 */
'use client';

import { useEffect, useRef, useCallback, type ReactNode } from 'react';

interface ModalProps {
  /** Whether the modal is open. */
  open: boolean;
  /** Called when the modal should close (ESC key, backdrop click, close button). */
  onClose: () => void;
  /** Dialog title displayed in the header. */
  title: string;
  /** Optional description for screen readers. */
  description?: string;
  /** Modal content. */
  children: ReactNode;
  /** Optional footer content (buttons). */
  footer?: ReactNode;
  /** Maximum width class. Defaults to max-w-lg. */
  maxWidth?: string;
}

export function Modal({
  open,
  onClose,
  title,
  description,
  children,
  footer,
  maxWidth = 'max-w-lg',
}: ModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // Save and restore focus
  useEffect(() => {
    if (open) {
      previousFocusRef.current = document.activeElement as HTMLElement;
      // Focus the dialog container after render
      const timer = window.setTimeout(() => {
        dialogRef.current?.focus();
      }, 0);
      return () => window.clearTimeout(timer);
    } else if (previousFocusRef.current) {
      previousFocusRef.current.focus();
      previousFocusRef.current = null;
    }
  }, [open]);

  // Lock body scroll when open
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = '';
      };
    }
  }, [open]);

  // ESC key to close
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        onClose();
      }

      // Focus trap: cycle Tab within the dialog
      if (e.key === 'Tab' && dialogRef.current) {
        const focusableElements = dialogRef.current.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
        );
        if (focusableElements.length === 0) return;

        const first = focusableElements[0];
        const last = focusableElements[focusableElements.length - 1];

        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    },
    [onClose],
  );

  // Click on backdrop to close
  const handleBackdropClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget) {
        onClose();
      }
    },
    [onClose],
  );

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ animation: 'modal-backdrop-in 150ms ease forwards' }}
      role="presentation"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={handleBackdropClick}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        aria-describedby={description ? 'modal-description' : undefined}
        tabIndex={-1}
        onKeyDown={handleKeyDown}
        className={[
          'relative z-10 w-full',
          maxWidth,
          'bg-[var(--color-card)] border border-[var(--color-border)]',
          'rounded-[var(--radius-lg)] shadow-[var(--shadow-modal)]',
          'focus:outline-none',
        ].join(' ')}
        style={{ animation: 'modal-content-in 150ms ease forwards' }}
      >
        {/* Header */}
        <div className="flex items-start justify-between p-6 pb-0">
          <div>
            <h2
              id="modal-title"
              className="text-lg font-bold text-[var(--color-text)]"
            >
              {title}
            </h2>
            {description && (
              <p id="modal-description" className="mt-1 text-sm text-[var(--color-muted)]">
                {description}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className={[
              'p-1.5 rounded-[var(--radius-sm)]',
              'text-[var(--color-muted)] hover:text-[var(--color-text)]',
              'hover:bg-[var(--color-hover)]',
              'transition-colors duration-[var(--transition)]',
              'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]',
            ].join(' ')}
            aria-label="Dialog schliessen"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6">{children}</div>

        {/* Footer */}
        {footer && (
          <div className="flex items-center justify-end gap-3 p-6 pt-0">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
