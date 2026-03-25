/**
 * NomOS — Kosten (Costs) admin panel.
 * Total cost this month, per-agent breakdown, budget bars, daily trend chart (CSS only).
 * Data from: GET /api/costs
 *
 * 4 States: Loading (Skeleton), Empty (CTA), Error (ErrorBoundary), Data
 * WCAG 2.2 AA: focus-visible, aria-labels, keyboard nav
 * i18n: All text via translation keys
 */
'use client';

import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { useFetch, formatEur } from '@/lib/hooks';
import { Card, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { SkeletonCard, Skeleton } from '@/components/ui/skeleton';
import type { CostDetailResponse, CostEntry } from '@/lib/types';

function CostsSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-busy="true">
      <span className="sr-only">{t('loading.costs', 'de')}</span>
      <Skeleton width="w-64" height="h-8" />
      <SkeletonCard />
      <SkeletonCard />
      <SkeletonCard />
    </div>
  );
}

/** Budget bar for a single agent. */
function BudgetBar({ cost, lang }: { cost: CostEntry; lang: 'de' | 'en' }) {
  const percent = cost.budget_limit_eur > 0
    ? Math.min(Math.round((cost.total_cost_eur / cost.budget_limit_eur) * 100), 100)
    : 0;
  const barColor = percent > 90
    ? 'var(--color-error)'
    : percent > 70
      ? 'var(--color-warning)'
      : 'var(--color-success)';

  return (
    <div
      className="flex items-center gap-4 px-4 py-3 border-b border-[var(--color-border)] last:border-b-0"
      role="listitem"
    >
      {/* Agent avatar */}
      <div
        className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0"
        style={{ backgroundColor: 'var(--color-primary)' }}
        aria-hidden="true"
      >
        {cost.agent_id.charAt(0).toUpperCase()}
      </div>

      {/* Name + Budget bar */}
      <div className="flex-1 min-w-0 space-y-1.5">
        <div className="flex items-center justify-between text-sm">
          <span className="font-semibold text-[var(--color-text)] truncate">{cost.agent_id}</span>
          <span className="text-xs text-[var(--color-muted)] font-[family-name:var(--font-mono)] shrink-0">
            {formatEur(cost.total_cost_eur)} / {formatEur(cost.budget_limit_eur)}
          </span>
        </div>
        <div
          className="w-full h-2 rounded-full bg-[var(--color-hover)] overflow-hidden"
          role="progressbar"
          aria-valuenow={percent}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${t('a11y.budgetBar', lang)}: ${cost.agent_id} — ${percent}%`}
        >
          <div
            className="h-full rounded-full transition-all duration-300"
            style={{ width: `${percent}%`, backgroundColor: barColor }}
          />
        </div>
        <div className="text-xs text-[var(--color-muted)]">
          {t('costs.percentUsed', lang)}: {percent}%
        </div>
      </div>
    </div>
  );
}

/** CSS-only daily cost trend bar chart. */
function DailyTrendChart({
  data,
  lang,
}: {
  data: { date: string; cost_eur: number }[];
  lang: 'de' | 'en';
}) {
  if (data.length === 0) return null;

  const maxCost = Math.max(...data.map((d) => d.cost_eur), 1);

  return (
    <div aria-label={t('a11y.dailyCostChart', lang)} role="img">
      <div className="flex items-end gap-1 h-32">
        {data.map((entry) => {
          const heightPercent = Math.max((entry.cost_eur / maxCost) * 100, 2);
          const dayLabel = new Date(entry.date).toLocaleDateString(
            lang === 'de' ? 'de-DE' : 'en-US',
            { day: '2-digit', month: '2-digit' },
          );
          return (
            <div
              key={entry.date}
              className="flex-1 flex flex-col items-center gap-1 group"
              title={`${dayLabel}: ${formatEur(entry.cost_eur)}`}
            >
              <div
                className="w-full rounded-t-sm bg-[var(--color-primary)] group-hover:bg-[var(--color-primary-hover)] transition-colors"
                style={{ height: `${heightPercent}%`, minHeight: '2px' }}
                role="presentation"
                aria-hidden="true"
              />
            </div>
          );
        })}
      </div>
      {/* X-axis labels — show every 5th day */}
      <div className="flex items-center gap-1 mt-1">
        {data.map((entry, i) => (
          <div key={entry.date} className="flex-1 text-center">
            {i % 5 === 0 && (
              <span className="text-[10px] text-[var(--color-muted)]">
                {new Date(entry.date).getDate()}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function CostsContent() {
  const { language } = useNomosStore();
  const costs = useFetch<CostDetailResponse>('/costs');

  if (costs.loading) {
    return <CostsSkeleton />;
  }

  if (costs.error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
          {t('costs.title', language)}
        </h1>
        <Card>
          <p className="text-sm text-[var(--color-error)]">{costs.error}</p>
          <Button variant="secondary" onClick={costs.reload} className="mt-4">
            {t('action.retry', language)}
          </Button>
        </Card>
      </div>
    );
  }

  const data = costs.data;
  const costEntries = data?.costs ?? [];

  if (costEntries.length === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
          {t('costs.title', language)}
        </h1>
        <EmptyState
          message={t('empty.costs', language)}
          description={t('empty.costsDescription', language)}
        />
      </div>
    );
  }

  const totalCost = data?.total_cost_eur ?? costEntries.reduce((sum, c) => sum + c.total_cost_eur, 0);
  const dailyTrend = data?.daily_trend ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
          {t('costs.title', language)}
        </h1>
        <p className="text-sm text-[var(--color-muted)] mt-1">{t('costs.description', language)}</p>
      </div>

      {/* Total cost — big number */}
      <Card>
        <CardHeader
          title={t('costs.totalThisMonth', language)}
        />
        <div className="mt-3">
          <span
            className="text-4xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]"
            aria-label={`${t('costs.totalThisMonth', language)}: ${formatEur(totalCost)}`}
          >
            {formatEur(totalCost)}
          </span>
        </div>
      </Card>

      {/* Per-agent breakdown with budget bars */}
      <Card padding="none">
        <div className="p-6 pb-0">
          <CardHeader
            title={t('costs.perAgent', language)}
          />
        </div>
        <div className="mt-4" role="list" aria-label={t('a11y.costOverview', language)}>
          {costEntries.map((cost) => (
            <BudgetBar key={cost.agent_id} cost={cost} lang={language} />
          ))}
        </div>
      </Card>

      {/* Daily trend chart */}
      {dailyTrend.length > 0 && (
        <Card>
          <CardHeader
            title={t('costs.dailyTrend', language)}
            description={t('costs.dailyTrendDescription', language)}
          />
          <div className="mt-4">
            <DailyTrendChart data={dailyTrend} lang={language} />
          </div>
        </Card>
      )}
    </div>
  );
}

export default function CostsPage() {
  return (
    <ErrorBoundary>
      <CostsContent />
    </ErrorBoundary>
  );
}
