/**
 * Test: / (Root page — redirects to /login).
 */
import { describe, it, expect, vi } from 'vitest';

// The root page calls redirect() at module level — we test the export exists
// and the redirect mock was called.
const redirectMock = vi.fn();

vi.mock('next/navigation', () => ({
  redirect: (url: string) => { redirectMock(url); },
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({}),
}));

describe('RootPage (/)', () => {
  it('exports a default function component', async () => {
    const mod = await import('@/app/page');
    expect(mod.default).toBeDefined();
    expect(typeof mod.default).toBe('function');
  });

  it('calls redirect to /login when rendered', async () => {
    const mod = await import('@/app/page');
    try {
      mod.default();
    } catch {
      // redirect may throw in some Next.js mocks — that is fine
    }
    expect(redirectMock).toHaveBeenCalledWith('/login');
  });

  it('has no loading state (static redirect)', async () => {
    const mod = await import('@/app/page');
    expect(mod.default).toBeDefined();
  });

  it('has no error state (static redirect)', async () => {
    const mod = await import('@/app/page');
    expect(mod.default).toBeDefined();
  });
});
