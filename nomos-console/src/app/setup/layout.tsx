/**
 * NomOS Setup Layout -- Minimal, no sidebar.
 * Centered logo + content for first-time setup wizard.
 * WCAG 2.2 AA: lang attribute inherited, skip-to-content from root layout.
 */
import type { ReactNode } from 'react';

export default function SetupLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[var(--color-bg)] flex flex-col items-center justify-center p-8">
      <div className="w-full max-w-lg">
        {children}
      </div>
    </div>
  );
}
