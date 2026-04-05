/**
 * NomOS — Gesundheitscheck (Diagnostics) admin panel.
 * Container Health status cards (API, DB, Gateway), Heartbeat board.
 * Memory/CPU indicators from heartbeat data.
 * Data from: GET /health, heartbeat data from fleet
 *
 * 4 States: Loading (Skeleton), Empty (CTA), Error (ErrorBoundary), Data
 * WCAG 2.2 AA: focus-visible, aria-labels, keyboard nav
 * i18n: All text via translation keys
 */
'use client';

import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { useFetch, formatDate } from '@/lib/hooks';
import { Card, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { SkeletonCard, Skeleton } from '@/components/ui/skeleton';
import type { HealthResponse, FleetResponse } from '@/lib/types';
import { agentStatusToBadge } from '@/lib/types';

function DiagnosticsSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-busy="true">
      <span className="sr-only">{t('loading.diagnostics', 'de')}</span>
      <Skeleton width="w-64" height="h-8" />
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
      <SkeletonCard />
    </div>
  );
}

/** Status badge mapping for health — API returns 'ok', services use 'healthy'/'degraded'/'unhealthy'. */
function healthBadgeStatus(status: string): 'online' | 'paused' | 'error' {
  switch (status) {
    case 'ok':
    case 'healthy': return 'online';
    case 'degraded': return 'paused';
    default: return 'error';
  }
}

function healthLabel(status: string, lang: 'de' | 'en'): string {
  switch (status) {
    case 'ok':
    case 'healthy': return t('diagnostics.healthy', lang);
    case 'degraded': return t('diagnostics.degraded', lang);
    default: return t('diagnostics.unhealthy', lang);
  }
}

function DiagnosticsContent() {
  const { language } = useNomosStore();
  const health = useFetch<HealthResponse>('/health');
  const fleet = useFetch<FleetResponse>('/fleet');

  if (health.loading || fleet.loading) {
    return <DiagnosticsSkeleton />;
  }

  if (health.error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
          {t('diagnostics.title', language)}
        </h1>
        <Card>
          <p className="text-sm text-[var(--color-error)]">{health.error}</p>
          <Button variant="secondary" onClick={health.reload} className="mt-4">
            {t('action.retry', language)}
          </Button>
        </Card>
      </div>
    );
  }

  const healthData = health.data;
  const agents = fleet.data?.agents ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
            {t('diagnostics.title', language)}
          </h1>
          <p className="text-sm text-[var(--color-muted)] mt-1">{t('diagnostics.description', language)}</p>
        </div>
        <Button variant="ghost" size="sm" onClick={health.reload} aria-label={t('action.retry', language)}>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </Button>
      </div>

      {/* Overall status */}
      {healthData && (
        <Card>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Badge
                status={healthBadgeStatus(healthData.status)}
                label={healthLabel(healthData.status, language)}
              />
              <span className="text-sm text-[var(--color-text)] font-semibold">
                {healthData.service}
              </span>
            </div>
            <span className="text-xs text-[var(--color-muted)] font-[family-name:var(--font-mono)]">
              v{healthData.version}
            </span>
          </div>
        </Card>
      )}

      {/* Services info */}
      <Card>
        <CardHeader title={t('diagnostics.services', language)} />
        <p className="text-sm text-[var(--color-muted)] mt-2">
          {t('diagnostics.servicesInfo', language)}
        </p>
      </Card>

      {/* Heartbeat Board */}
      <Card padding="none">
        <div className="p-6 pb-0">
          <CardHeader
            title={t('diagnostics.heartbeat', language)}
            description={t('diagnostics.heartbeatDescription', language)}
          />
        </div>
        <div className="mt-4">
          {agents.length === 0 ? (
            <EmptyState
              message={t('empty.team', language)}
              description={t('empty.teamDescription', language)}
            />
          ) : (
            <div role="list" aria-label={t('diagnostics.heartbeat', language)}>
              {agents.map((agent) => {
                const badgeStatus = agentStatusToBadge(agent.status);
                return (
                  <div
                    key={agent.id}
                    className="flex items-center gap-4 px-6 py-4 border-b border-[var(--color-border)] last:border-b-0"
                    role="listitem"
                  >
                    {/* Avatar */}
                    <div
                      className="w-10 h-10 rounded-[var(--radius)] flex items-center justify-center text-white text-sm font-bold shrink-0"
                      style={{ backgroundColor: 'var(--color-primary)' }}
                      aria-hidden="true"
                    >
                      {agent.name.charAt(0).toUpperCase()}
                    </div>
                    {/* Name + Role */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-[var(--color-text)] truncate">{agent.name}</p>
                      <p className="text-xs text-[var(--color-muted)] truncate">{agent.role}</p>
                    </div>
                    {/* Last seen */}
                    <div className="text-xs text-[var(--color-muted)] shrink-0 hidden sm:block">
                      <span className="font-semibold">{t('diagnostics.lastSeen', language)}:</span>{' '}
                      {agent.heartbeat_at ? formatDate(agent.heartbeat_at, language) : '—'}
                    </div>
                    {/* Status */}
                    <Badge status={badgeStatus} />
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

export default function DiagnosticsPage() {
  return (
    <ErrorBoundary>
      <DiagnosticsContent />
    </ErrorBoundary>
  );
}
