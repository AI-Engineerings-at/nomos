/**
 * NomOS Providers — Client-side providers wrapper.
 * Wraps AuthProvider and ToastContainer.
 */
'use client';

import type { ReactNode } from 'react';
import { AuthProvider } from '@/lib/auth';
import { ToastContainer } from '@/components/ui/toast';

export function Providers({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      {children}
      <ToastContainer />
    </AuthProvider>
  );
}
