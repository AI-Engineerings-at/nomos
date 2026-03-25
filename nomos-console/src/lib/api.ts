/**
 * NomOS API Client — Typed fetch wrapper with error handling.
 * All API calls go through this client for consistent auth, error handling, and typing.
 */

/** API error with structured information for user-facing messages. */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly statusText: string,
    public readonly detail: string,
    public readonly code?: string,
  ) {
    super(detail);
    this.name = 'ApiError';
  }
}

/** Shape of a structured API error response from the NomOS API. */
interface ApiErrorResponse {
  detail: string;
  code?: string;
}

/** Base URL for the NomOS API. In dev: Next.js proxy (/api). In Docker: env var. */
function getBaseUrl(): string {
  if (typeof window !== 'undefined') {
    // Browser: always use same-origin proxy (Next.js rewrite handles routing)
    return '/api';
  }
  // Server-side: direct connection
  return (process.env.NOMOS_API_URL || 'http://localhost:8060') + '/api';
}

/** Default request timeout in milliseconds. */
const DEFAULT_TIMEOUT_MS = 30_000;

/** Maximum retry attempts for transient failures. */
const MAX_RETRIES = 2;

/** HTTP status codes that should trigger a retry. */
const RETRYABLE_STATUS_CODES = new Set([502, 503, 504]);

/**
 * Typed fetch wrapper with auth, timeout, retries, and error handling.
 *
 * - Reads JWT from HttpOnly cookie (sent automatically by the browser).
 * - Retries on 502/503/504 with exponential backoff.
 * - Throws ApiError with structured detail for UI consumption.
 */
export async function apiFetch<T>(
  path: string,
  options: RequestInit & { timeout?: number } = {},
): Promise<T> {
  const { timeout = DEFAULT_TIMEOUT_MS, ...fetchOptions } = options;
  const url = `${getBaseUrl()}${path}`;

  const headers = new Headers(fetchOptions.headers);
  if (!headers.has('Content-Type') && fetchOptions.body) {
    headers.set('Content-Type', 'application/json');
  }
  headers.set('Accept', 'application/json');

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        ...fetchOptions,
        headers,
        credentials: 'same-origin',
        signal: controller.signal,
      });

      window.clearTimeout(timeoutId);

      if (response.ok) {
        // Handle 204 No Content
        if (response.status === 204) {
          return undefined as T;
        }
        return (await response.json()) as T;
      }

      // Parse error response
      let detail = response.statusText;
      let code: string | undefined;
      try {
        const errorBody = (await response.json()) as ApiErrorResponse;
        detail = errorBody.detail || detail;
        code = errorBody.code;
      } catch {
        // Response body was not JSON — use statusText
      }

      const apiError = new ApiError(response.status, response.statusText, detail, code);

      // Retry on transient server errors
      if (RETRYABLE_STATUS_CODES.has(response.status) && attempt < MAX_RETRIES) {
        lastError = apiError;
        // Exponential backoff: 500ms, 1000ms
        await delay(500 * Math.pow(2, attempt));
        continue;
      }

      throw apiError;
    } catch (error) {
      window.clearTimeout(timeoutId);

      if (error instanceof ApiError) {
        throw error;
      }

      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new ApiError(0, 'Timeout', 'Die Anfrage hat zu lange gedauert.', 'TIMEOUT');
      }

      if (error instanceof TypeError) {
        // Network error (e.g., server unreachable)
        if (attempt < MAX_RETRIES) {
          lastError = error;
          await delay(500 * Math.pow(2, attempt));
          continue;
        }
        throw new ApiError(
          0,
          'Network Error',
          'Die Verbindung zum Server ist unterbrochen.',
          'NETWORK_ERROR',
        );
      }

      throw error;
    }
  }

  // Should not reach here, but satisfy TypeScript
  throw lastError ?? new Error('Unbekannter Fehler');
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

/** Convenience methods for common HTTP verbs. */
export const api = {
  get<T>(path: string, options?: RequestInit & { timeout?: number }): Promise<T> {
    return apiFetch<T>(path, { ...options, method: 'GET' });
  },

  post<T>(path: string, body?: unknown, options?: RequestInit & { timeout?: number }): Promise<T> {
    return apiFetch<T>(path, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  },

  put<T>(path: string, body?: unknown, options?: RequestInit & { timeout?: number }): Promise<T> {
    return apiFetch<T>(path, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    });
  },

  patch<T>(path: string, body?: unknown, options?: RequestInit & { timeout?: number }): Promise<T> {
    return apiFetch<T>(path, {
      ...options,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    });
  },

  delete<T>(path: string, options?: RequestInit & { timeout?: number }): Promise<T> {
    return apiFetch<T>(path, { ...options, method: 'DELETE' });
  },
};
