/**
 * NomOS Console — Shared React hooks for data fetching.
 * Provides consistent loading/error/data states across all panels.
 */
'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { api, ApiError } from './api';

/** State shape for any async data fetch. */
export interface FetchState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

/**
 * Generic hook for fetching data from an API endpoint.
 * Handles loading, error, and data states consistently.
 */
export function useFetch<T>(path: string, enabled = true): FetchState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const fetchData = useCallback(async () => {
    if (!enabled) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await api.get<T>(path);
      if (mountedRef.current) {
        setData(result);
      }
    } catch (err) {
      if (mountedRef.current) {
        if (err instanceof ApiError) {
          setError(err.detail);
        } else {
          setError('Ein unbekannter Fehler ist aufgetreten.');
        }
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [path, enabled]);

  useEffect(() => {
    mountedRef.current = true;
    fetchData();
    return () => {
      mountedRef.current = false;
    };
  }, [fetchData]);

  return { data, loading, error, reload: fetchData };
}

/** Returns a time-based greeting key for i18n. */
export function getGreetingKey(): 'dashboard.greeting.morning' | 'dashboard.greeting.afternoon' | 'dashboard.greeting.evening' {
  const hour = new Date().getHours();
  if (hour < 12) return 'dashboard.greeting.morning';
  if (hour < 18) return 'dashboard.greeting.afternoon';
  return 'dashboard.greeting.evening';
}

/** Formats a date string to a localized human-readable format. */
export function formatDate(dateStr: string, lang: 'de' | 'en'): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString(lang === 'de' ? 'de-DE' : 'en-US', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/** Formats a EUR amount consistently. */
export function formatEur(amount: number): string {
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
  }).format(amount);
}
