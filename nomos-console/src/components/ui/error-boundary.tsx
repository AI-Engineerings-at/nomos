/**
 * NomOS Error Boundary — Catches errors, shows friendly message, reports to API.
 * Brand Voice: direkt, ehrlich, hilfreich.
 * NEVER shows "Something went wrong" — always German-first with helpful next steps.
 */
'use client';

import { Component, type ErrorInfo, type ReactNode } from 'react';
import { Button } from './button';

interface ErrorBoundaryProps {
  /** Content to render when no error has occurred. */
  children: ReactNode;
  /** Optional custom fallback component. If not provided, the default error panel is shown. */
  fallback?: ReactNode;
  /** Optional callback when an error is caught. */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Report error to NomOS API for incident tracking
    this.reportError(error, errorInfo);

    // Call optional external error handler
    this.props.onError?.(error, errorInfo);
  }

  private reportError(error: Error, errorInfo: ErrorInfo): void {
    // Fire-and-forget error report to the API
    try {
      const payload = {
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        url: typeof window !== 'undefined' ? window.location.href : '',
        timestamp: new Date().toISOString(),
        userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : '',
      };

      if (typeof window !== 'undefined') {
        fetch('/api/incidents', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            log_entry: `Console error: ${payload.error} at ${payload.url}`,
            agent_id: 'console',
            context: payload,
          }),
          credentials: 'same-origin',
        }).catch(() => {
          // Silently fail — we cannot let the error reporter cause more errors
        });
      }
    } catch {
      // Silently fail
    }
  }

  private handleRetry = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div
          className="flex flex-col items-center justify-center p-8 text-center"
          role="alert"
        >
          {/* Error icon */}
          <div className="w-16 h-16 mb-4 rounded-full bg-[var(--color-error-light)] flex items-center justify-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="w-8 h-8 text-[var(--color-error)]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>

          <h3 className="text-lg font-bold text-[var(--color-text)] mb-2">
            Etwas ist schiefgegangen
          </h3>
          <p className="text-sm text-[var(--color-muted)] max-w-md mb-6">
            Ein unerwarteter Fehler ist aufgetreten. Der Fehler wurde automatisch gemeldet.
            Bitte versuchen Sie es erneut oder kontaktieren Sie den Administrator.
          </p>

          <div className="flex gap-3">
            <Button variant="primary" onClick={this.handleRetry}>
              Erneut versuchen
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                if (typeof window !== 'undefined') {
                  window.location.href = '/admin';
                }
              }}
            >
              Zur Uebersicht
            </Button>
          </div>

          {/* Error details for admins — collapsible */}
          {this.state.error && (
            <details className="mt-6 w-full max-w-lg text-left">
              <summary className="text-xs text-[var(--color-muted)] cursor-pointer hover:text-[var(--color-text)] transition-colors">
                Technische Details anzeigen
              </summary>
              <pre className="mt-2 p-3 text-xs bg-[var(--color-hover)] rounded-[var(--radius)] overflow-x-auto text-[var(--color-muted)] font-[family-name:var(--font-mono)]">
                {this.state.error.message}
                {this.state.error.stack && `\n\n${this.state.error.stack}`}
              </pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}
