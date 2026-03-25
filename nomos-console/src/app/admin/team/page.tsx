/**
 * NomOS — Mein Team (My Team) panel.
 * Agent card grid with filter, sort, FCL badge, and hire CTA.
 * Data from: /api/fleet, /api/costs
 *
 * 4 States: Loading (Skeleton), Empty (CTA), Error (ErrorBoundary), Data
 * WCAG 2.2 AA: focus-visible, aria-labels, keyboard nav
 * i18n: All text via translation keys
 */
'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { useFetch, formatEur } from '@/lib/hooks';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { SkeletonBadge } from '@/components/ui/skeleton';
import type { FleetResponse, CostOverviewResponse, Agent } from '@/lib/types';
import { agentStatusToBadge } from '@/lib/types';

type FilterStatus = 'all' | 'running' | 'paused' | 'offline';
type SortKey = 'name' | 'status' | 'cost';

function BudgetBar({ used, limit }: { used: number; limit: number }) {
  const percent = limit > 0 ? Math.min((used / limit) * 100, 100) : 0;
  const getColor = (): string => {
    if (percent >= 90) return 'var(--color-error)';
    if (percent >= 70) return 'var(--color-warning)';
    return 'var(--color-success)';
  };

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs text-[var(--color-muted)]">
        <span>{formatEur(used)}</span>
        <span>{formatEur(limit)}</span>
      </div>
      <div
        className="w-full h-2 bg-[var(--color-hover)] rounded-[var(--radius-full)] overflow-hidden"
        role="progressbar"
        aria-valuenow={Math.round(percent)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Budget: ${Math.round(percent)}%`}
      >
        <div
          className="h-full rounded-[var(--radius-full)] transition-all duration-300"
          style={{ width: `${percent}%`, backgroundColor: getColor() }}
        />
      </div>
    </div>
  );
}

function AgentCard({
  agent,
  costUsed,
  costLimit,
  onClick,
  lang,
}: {
  agent: Agent;
  costUsed: number;
  costLimit: number;
  onClick: () => void;
  lang: 'de' | 'en';
}) {
  const badgeStatus = agentStatusToBadge(agent.status);
  const isCompliant = agent.compliance_status === 'compliant';

  return (
    <Card
      hoverable
      className="flex flex-col gap-4"
      onClick={onClick}
      role="button"
      tabIndex={0}
      aria-label={`${agent.name} — ${agent.role}`}
      onKeyDown={(e: React.KeyboardEvent) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
    >
      {/* Header: Avatar + Name + Status */}
      <div className="flex items-start gap-3">
        {/* Pixel-art placeholder: colored circle */}
        <div
          className="w-12 h-12 rounded-[var(--radius)] flex items-center justify-center text-white text-lg font-bold shrink-0"
          style={{ backgroundColor: 'var(--color-primary)' }}
          aria-hidden="true"
        >
          {agent.name.charAt(0).toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-base font-bold text-[var(--color-text)] truncate font-[family-name:var(--font-headline)]">
            {agent.name}
          </h3>
          <p className="text-sm text-[var(--color-muted)] truncate">{agent.role}</p>
        </div>
        <Badge status={badgeStatus} />
      </div>

      {/* Budget bar */}
      <BudgetBar used={costUsed} limit={costLimit} />

      {/* Compliance badge */}
      <div className="flex items-center justify-between">
        <span
          className={[
            'inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-semibold rounded-[var(--radius-full)]',
            isCompliant
              ? 'bg-[var(--color-success-light)] text-[var(--color-success)]'
              : 'bg-[var(--color-error-light)] text-[var(--color-error)]',
          ].join(' ')}
          role="status"
        >
          <svg
            className="w-3 h-3"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={2.5}
            aria-hidden="true"
          >
            {isCompliant ? (
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            )}
          </svg>
          {isCompliant ? t('team.compliant', lang) : t('team.nonCompliant', lang)}
        </span>
        <span className="text-xs text-[var(--color-muted)] font-[family-name:var(--font-mono)]">
          {formatEur(costUsed)}/{lang === 'de' ? 'Mo.' : 'mo.'}
        </span>
      </div>
    </Card>
  );
}

function TeamSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-busy="true">
      <span className="sr-only">Wird geladen...</span>
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <div className="h-7 w-40 skeleton-shimmer rounded-[var(--radius-sm)]" />
          <div className="h-4 w-64 skeleton-shimmer rounded-[var(--radius-sm)]" />
        </div>
        <div className="h-10 w-48 skeleton-shimmer rounded-[var(--radius)]" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonBadge key={i} />
        ))}
      </div>
    </div>
  );
}

function TeamContent() {
  const { language } = useNomosStore();
  const router = useRouter();
  const [filter, setFilter] = useState<FilterStatus>('all');
  const [sortKey, setSortKey] = useState<SortKey>('name');

  const fleet = useFetch<FleetResponse>('/fleet');
  const costs = useFetch<CostOverviewResponse>('/costs');

  const agents = fleet.data?.agents ?? [];
  const costMap = useMemo(() => {
    const map = new Map<string, { used: number; limit: number }>();
    if (costs.data) {
      for (const c of costs.data.costs) {
        map.set(c.agent_id, { used: c.total_cost_eur, limit: c.budget_limit_eur });
      }
    }
    return map;
  }, [costs.data]);

  // Filter
  const filteredAgents = useMemo(() => {
    return agents.filter((a) => {
      if (filter === 'all') return true;
      if (filter === 'running') return a.status === 'running';
      if (filter === 'paused') return a.status === 'paused';
      if (filter === 'offline') return a.status === 'killed' || a.status === 'error';
      return true;
    });
  }, [agents, filter]);

  // Sort
  const sortedAgents = useMemo(() => {
    return [...filteredAgents].sort((a, b) => {
      switch (sortKey) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'status':
          return a.status.localeCompare(b.status);
        case 'cost': {
          const costA = costMap.get(a.id)?.used ?? 0;
          const costB = costMap.get(b.id)?.used ?? 0;
          return costB - costA;
        }
        default:
          return 0;
      }
    });
  }, [filteredAgents, sortKey, costMap]);

  if (fleet.loading || costs.loading) {
    return <TeamSkeleton />;
  }

  const filterOptions: { key: FilterStatus; labelKey: 'team.filterAll' | 'team.filterOnline' | 'team.filterPaused' | 'team.filterOffline' }[] = [
    { key: 'all', labelKey: 'team.filterAll' },
    { key: 'running', labelKey: 'team.filterOnline' },
    { key: 'paused', labelKey: 'team.filterPaused' },
    { key: 'offline', labelKey: 'team.filterOffline' },
  ];

  const sortOptions: { key: SortKey; labelKey: 'team.sortName' | 'team.sortStatus' | 'team.sortCost' }[] = [
    { key: 'name', labelKey: 'team.sortName' },
    { key: 'status', labelKey: 'team.sortStatus' },
    { key: 'cost', labelKey: 'team.sortCost' },
  ];

  const fclCount = agents.length;
  const fclLimit = 3;

  return (
    <div className="space-y-6">
      {/* Header with title + hire button */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
            {t('team.title', language)}
          </h1>
          <p className="text-sm text-[var(--color-muted)] mt-1">{t('team.description', language)}</p>
        </div>
        <div className="flex items-center gap-3">
          {/* FCL Badge */}
          <span
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-[var(--radius-full)] bg-[var(--color-primary-light)] text-[var(--color-primary)]"
            role="status"
            aria-label={`${fclCount}/${fclLimit} ${t('team.fclBadge', language)}`}
          >
            {fclCount}/{fclLimit} {t('team.fclBadge', language)}
          </span>
          <Button onClick={() => router.push('/admin/hire')} aria-label={t('team.hireNew', language)}>
            {t('team.hireNew', language)}
          </Button>
        </div>
      </div>

      {/* Filter + Sort controls */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        {/* Status filter tabs */}
        <div
          className="inline-flex items-center rounded-[var(--radius)] border border-[var(--color-border)] overflow-hidden"
          role="tablist"
          aria-label={t('a11y.filterByStatus', language)}
        >
          {filterOptions.map((opt) => (
            <button
              key={opt.key}
              role="tab"
              aria-selected={filter === opt.key}
              onClick={() => setFilter(opt.key)}
              className={[
                'px-3 py-1.5 text-sm font-medium transition-colors duration-[var(--transition)]',
                'focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-[var(--color-focus-ring)]',
                filter === opt.key
                  ? 'bg-[var(--color-primary)] text-white'
                  : 'text-[var(--color-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-hover)]',
              ].join(' ')}
            >
              {t(opt.labelKey, language)}
            </button>
          ))}
        </div>

        {/* Sort select */}
        <div className="flex items-center gap-2">
          <label
            htmlFor="team-sort"
            className="text-xs text-[var(--color-muted)] font-medium whitespace-nowrap"
          >
            {t('a11y.sortBy', language)}:
          </label>
          <select
            id="team-sort"
            value={sortKey}
            onChange={(e) => setSortKey(e.target.value as SortKey)}
            className={[
              'px-2 py-1.5 text-sm bg-[var(--color-card)] text-[var(--color-text)]',
              'border border-[var(--color-border)] rounded-[var(--radius)]',
              'focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-[var(--color-focus-ring)]',
            ].join(' ')}
          >
            {sortOptions.map((opt) => (
              <option key={opt.key} value={opt.key}>
                {t(opt.labelKey, language)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Agent Grid */}
      {agents.length === 0 ? (
        <EmptyState
          message={t('empty.team', language)}
          description={t('empty.teamDescription', language)}
          ctaLabel={t('empty.teamCta', language)}
          onCtaClick={() => router.push('/admin/hire')}
        />
      ) : sortedAgents.length === 0 ? (
        <EmptyState
          message={t('table.noResults', language)}
        />
      ) : (
        <div
          className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4"
          role="list"
          aria-label={t('team.title', language)}
        >
          {sortedAgents.map((agent) => {
            const cost = costMap.get(agent.id) ?? { used: 0, limit: 0 };
            return (
              <div key={agent.id} role="listitem">
                <AgentCard
                  agent={agent}
                  costUsed={cost.used}
                  costLimit={cost.limit}
                  lang={language}
                  onClick={() => router.push(`/admin/team/${agent.id}`)}
                />
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function TeamPage() {
  return (
    <ErrorBoundary>
      <TeamContent />
    </ErrorBoundary>
  );
}
