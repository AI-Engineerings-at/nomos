/**
 * Tests for utility functions: formatDate, formatEur, getGreetingKey, agentStatusToBadge.
 */
import { describe, it, expect, vi } from 'vitest';
import { formatDate, formatEur, getGreetingKey } from '@/lib/hooks';
import { agentStatusToBadge } from '@/lib/types';

// ---------------------------------------------------------------------------
// formatDate
// ---------------------------------------------------------------------------
describe('formatDate', () => {
  it('formats a date string in German locale', () => {
    const result = formatDate('2026-03-27T14:30:00Z', 'de');
    expect(result).toBeTruthy();
    expect(typeof result).toBe('string');
    // Should contain typical German date separators
    expect(result).toMatch(/\d{2}\.\d{2}\.\d{4}/);
  });

  it('formats a date string in English locale', () => {
    const result = formatDate('2026-03-27T14:30:00Z', 'en');
    expect(result).toBeTruthy();
    expect(typeof result).toBe('string');
    // Should contain typical US date separators
    expect(result).toMatch(/\d{2}\/\d{2}\/\d{4}/);
  });
});

// ---------------------------------------------------------------------------
// formatEur
// ---------------------------------------------------------------------------
describe('formatEur', () => {
  it('formats zero correctly', () => {
    const result = formatEur(0);
    expect(result).toContain('0');
    // EUR symbol or text
    expect(result).toMatch(/EUR|€/);
  });

  it('formats a positive amount', () => {
    const result = formatEur(1234.56);
    expect(result).toBeTruthy();
    expect(result).toMatch(/1[.,]?234/);
  });

  it('formats a negative amount', () => {
    const result = formatEur(-50);
    expect(result).toMatch(/-|50/);
  });
});

// ---------------------------------------------------------------------------
// getGreetingKey
// ---------------------------------------------------------------------------
describe('getGreetingKey', () => {
  it('returns a morning greeting before 12', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-03-27T08:00:00'));
    expect(getGreetingKey()).toBe('dashboard.greeting.morning');
    vi.useRealTimers();
  });

  it('returns an afternoon greeting between 12 and 18', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-03-27T14:00:00'));
    expect(getGreetingKey()).toBe('dashboard.greeting.afternoon');
    vi.useRealTimers();
  });

  it('returns an evening greeting after 18', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-03-27T20:00:00'));
    expect(getGreetingKey()).toBe('dashboard.greeting.evening');
    vi.useRealTimers();
  });
});

// ---------------------------------------------------------------------------
// agentStatusToBadge
// ---------------------------------------------------------------------------
describe('agentStatusToBadge', () => {
  it('maps running to online', () => {
    expect(agentStatusToBadge('running')).toBe('online');
  });

  it('maps paused to paused', () => {
    expect(agentStatusToBadge('paused')).toBe('paused');
  });

  it('maps killed to killed', () => {
    expect(agentStatusToBadge('killed')).toBe('killed');
  });

  it('maps deploying to deploying', () => {
    expect(agentStatusToBadge('deploying')).toBe('deploying');
  });

  it('maps error to error', () => {
    expect(agentStatusToBadge('error')).toBe('error');
  });

  it('maps created to deploying', () => {
    expect(agentStatusToBadge('created')).toBe('deploying');
  });

  it('maps retired to offline', () => {
    expect(agentStatusToBadge('retired')).toBe('offline');
  });

  it('maps unknown status to offline', () => {
    expect(agentStatusToBadge('unknown')).toBe('offline');
    expect(agentStatusToBadge('')).toBe('offline');
  });
});
