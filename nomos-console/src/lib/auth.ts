/**
 * NomOS Auth — Authentication context and utilities.
 * JWT is stored as HttpOnly cookie (set by the API on login).
 * This module provides React context for current user and role.
 */
'use client';

import {
  createContext,
  useContext,
  useCallback,
  useState,
  useEffect,
  type ReactNode,
} from 'react';
import React from 'react';
import { api, ApiError } from './api';
import { useNomosStore, type NomosUser } from './store';

interface AuthContextValue {
  user: NomosUser | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<{ requires2FA: boolean }>;
  verifyTotp: (code: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

interface LoginResponse {
  requires_2fa: boolean;
  user?: {
    id: string;
    email: string;
    name: string;
    role: 'admin' | 'user' | 'officer';
  };
}

interface MeResponse {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user' | 'officer';
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const { user, setUser } = useNomosStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Check session on mount — reads JWT from HttpOnly cookie
  useEffect(() => {
    let cancelled = false;
    async function checkSession() {
      try {
        const me = await api.get<MeResponse>('/auth/me');
        if (!cancelled) {
          setUser({
            id: me.id,
            email: me.email,
            name: me.name,
            role: me.role,
          });
        }
      } catch (err) {
        if (!cancelled) {
          // No valid session — user needs to log in
          setUser(null);
          // Only set error for non-401 failures
          if (err instanceof ApiError && err.status !== 401) {
            setError(err.detail);
          }
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }
    checkSession();
    return () => {
      cancelled = true;
    };
  }, [setUser]);

  const login = useCallback(
    async (email: string, password: string): Promise<{ requires2FA: boolean }> => {
      setError(null);
      try {
        const response = await api.post<LoginResponse>('/auth/login', { email, password });
        if (response.requires_2fa) {
          return { requires2FA: true };
        }
        if (response.user) {
          setUser({
            id: response.user.id,
            email: response.user.email,
            name: response.user.name,
            role: response.user.role,
          });
        }
        return { requires2FA: false };
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.detail);
        } else {
          setError('Ein unbekannter Fehler ist aufgetreten.');
        }
        throw err;
      }
    },
    [setUser],
  );

  const verifyTotp = useCallback(
    async (code: string): Promise<void> => {
      setError(null);
      try {
        const response = await api.post<{ user: MeResponse }>('/auth/totp/verify', { code });
        setUser({
          id: response.user.id,
          email: response.user.email,
          name: response.user.name,
          role: response.user.role,
        });
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.detail);
        } else {
          setError('Ein unbekannter Fehler ist aufgetreten.');
        }
        throw err;
      }
    },
    [setUser],
  );

  const logout = useCallback(async (): Promise<void> => {
    try {
      await api.post('/auth/logout');
    } catch {
      // Proceed with local logout even if API call fails
    } finally {
      setUser(null);
    }
  }, [setUser]);

  const value: AuthContextValue = {
    user,
    loading,
    error,
    login,
    verifyTotp,
    logout,
  };

  return React.createElement(AuthContext.Provider, { value }, children);
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
