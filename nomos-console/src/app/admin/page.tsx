/**
 * NomOS Admin Dashboard — Main overview page.
 * Shows greeting, compliance health, 4 metric cards, agent status board, recent activity.
 * Data from: /api/fleet, /api/costs, /api/approvals, /api/incidents, /api/audit
 *
 * 4 States: Loading (Skeleton), Empty (CTA), Error (ErrorBoundary), Data
 * WCAG 2.2 AA: focus-visible, aria-labels, keyboard nav, live regions
 * i18n: All text via translation keys
 */
'use client';

import { useNomosStore } from '@/lib/store';
import { useAuth } from '@/lib/auth';
import { t } from '@/lib/i18n';
import { useFetch, getGreetingKey, formatEur, formatDate } from '@/lib/hooks';
import { Card, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { EmptyState } from '@/components/ui/empty-state';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { Skeleton, SkeletonCard } from '@/components/ui/skeleton';
import { useRouter } from 'next/navigation';
import type { FleetResponse, CostOverviewResponse, ApprovalListResponse, IncidentListResponse, AuditEntry } from '@/lib/types';
import { agentStatusToBadge } from '@/lib/types';

/** Compliance health percentage bar with color coding. */
function ComplianceHealthBar({ percentage }: { percentage: number }) {
  const getColor = (pct: number): string => {
    if (pct >= 80) return 'var(--color-success)';
    if (pct >= 50) return 'var(--color-warning)';
    return 'var(--color-error)';
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
          {percentage}%
        </span>
      </div>
      <div
        className="w-full h-3 bg-[var(--color-hover)] rounded-[var(--radius-full)] overflow-hidden"
        role="progressbar"
        aria-valuenow={percentage}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Compliance: ${percentage}%`}
      >
        <div
          className="h-full rounded-[var(--radius-full)] transition-all duration-500"
          style={{
            width: `${Math.min(percentage, 100)}%`,
            backgroundColor: getColor(percentage),
          }}
        />
      </div>
    </div>
  );
}

/** A single metric card showing icon, value, and label. */
function MetricCard({
  label,
  value,
  subtitle,
  accentColor,
  onClick,
  ariaLabel,
}: {
  label: string;
  value: string | number;
  subtitle: string;
  accentColor: string;
  onClick?: () => void;
  ariaLabel: string;
}) {
  return (
    <Card
      hoverable={Boolean(onClick)}
      className={onClick ? 'cursor-pointer' : ''}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      aria-label={ariaLabel}
      onKeyDown={onClick ? (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      } : undefined}
    >
      <div className="flex items-start gap-4">
        <div
          className="w-3 h-12 rounded-[var(--radius-full)] shrink-0"
          style={{ backgroundColor: accentColor }}
          aria-hidden="true"
        />
        <div className="flex-1 min-w-0">
          <p className="text-sm text-[var(--color-muted)] font-medium">{label}</p>
          <p className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)] mt-1">
            {value}
          </p>
          <p className="text-xs text-[var(--color-muted)] mt-1">{subtitle}</p>
        </div>
      </div>
    </Card>
  );
}

/** Agent status board row — like Uptime Kuma. */
function StatusBoardRow({
  name,
  role,
  status,
  costEur,
  onClick,
}: {
  name: string;
  role: string;
  status: string;
  costEur: number;
  onClick: () => void;
}) {
  const badgeStatus = agentStatusToBadge(status);

  return (
    <button
      onClick={onClick}
      className={[
        'w-full flex items-center gap-3 px-4 py-3',
        'hover:bg-[var(--color-hover)] transition-colors duration-[var(--transition)]',
        'border-b border-[var(--color-border)] last:border-b-0',
        'focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-[var(--color-focus-ring)]',
        'text-left',
      ].join(' ')}
      aria-label={`${name} — ${role}`}
    >
      {/* Colored avatar circle */}
      <div
        className="w-10 h-10 rounded-[var(--radius)] flex items-center justify-center text-white text-sm font-bold shrink-0"
        style={{ backgroundColor: 'var(--color-primary)' }}
        aria-hidden="true"
      >
        {name.charAt(0).toUpperCase()}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-[var(--color-text)] truncate">{name}</p>
        <p className="text-xs text-[var(--color-muted)] truncate">{role}</p>
      </div>
      <Badge status={badgeStatus} />
      <span className="text-xs text-[var(--color-muted)] font-[family-name:var(--font-mono)] whitespace-nowrap">
        {formatEur(costEur)}
      </span>
    </button>
  );
}

/** Activity feed entry. */
function ActivityEntry({
  entry,
  lang,
}: {
  entry: AuditEntry;
  lang: 'de' | 'en';
}) {
  return (
    <div className="flex items-start gap-3 px-4 py-3 border-b border-[var(--color-border)] last:border-b-0">
      <div
        className="w-2 h-2 mt-2 rounded-full bg-[var(--color-primary)] shrink-0"
        aria-hidden="true"
      />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-[var(--color-text)]">
          <span className="font-semibold">{entry.agent_id}</span>
          {' — '}
          <span className="text-[var(--color-muted)]">{entry.event_type}</span>
        </p>
        <p className="text-xs text-[var(--color-muted)] mt-0.5">
          {formatDate(entry.timestamp, lang)}
        </p>
      </div>
    </div>
  );
}

/** Loading skeleton for the dashboard. */
function DashboardSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-busy="true" aria-label="Dashboard wird geladen">
      <span className="sr-only">Wird geladen...</span>
      {/* Greeting skeleton */}
      <Skeleton width="w-64" height="h-8" />
      {/* Compliance bar skeleton */}
      <SkeletonCard />
      {/* Metric cards skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
      {/* Status board + Activity */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    </div>
  );
}

function DashboardContent() {
  const { language } = useNomosStore();
  const { user } = useAuth();
  const router = useRouter();

  const fleet = useFetch<FleetResponse>('/fleet');
  const costs = useFetch<CostOverviewResponse>('/costs');
  const approvals = useFetch<ApprovalListResponse>('/approvals');
  const incidents = useFetch<IncidentListResponse>('/incidents');
  const audit = useFetch<{ entries: AuditEntry[]; total: number }>('/audit');

  const isLoading = fleet.loading || costs.loading || approvals.loading || incidents.loading;

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  // Calculate metrics
  const agents = fleet.data?.agents ?? [];
  const onlineCount = agents.filter((a) => a.status === 'running').length;
  const totalCost = costs.data?.costs.reduce((sum, c) => sum + c.total_cost_eur, 0) ?? 0;
  const pendingApprovals = approvals.data?.approvals.filter((a) => a.status === 'pending').length ?? 0;
  const activeIncidents = incidents.data?.incidents.filter((i) => i.status !== 'resolved').length ?? 0;

  // Compliance health: calculate from fleet compliance statuses
  const compliantCount = agents.filter((a) => a.compliance_status === 'compliant').length;
  const compliancePercent = agents.length > 0 ? Math.round((compliantCount / agents.length) * 100) : 0;

  // Cost map for status board
  const costMap = new Map<string, number>();
  if (costs.data) {
    for (const c of costs.data.costs) {
      costMap.set(c.agent_id, c.total_cost_eur);
    }
  }

  const greetingKey = getGreetingKey();
  const greeting = t(greetingKey, language);
  const userName = user?.name.split(' ')[0] ?? '';

  const hasAgents = agents.length > 0;

  return (
    <div className="space-y-6">
      {/* Greeting */}
      <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
        {greeting}, {userName}.
      </h1>

      {/* Compliance Health Bar */}
      <Card>
        <CardHeader
          title={t('dashboard.complianceHealth', language)}
          description={t('dashboard.complianceHealthDescription', language)}
        />
        <div className="mt-4">
          {hasAgents ? (
            <ComplianceHealthBar percentage={compliancePercent} />
          ) : (
            <p className="text-sm text-[var(--color-muted)]">
              {t('empty.complianceDescription', language)}
            </p>
          )}
        </div>
      </Card>

      {/* 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <MetricCard
          label={t('dashboard.agents', language)}
          value={agents.length}
          subtitle={`${onlineCount} ${t('dashboard.active', language)}`}
          accentColor="var(--color-primary)"
          onClick={() => router.push('/admin/team')}
          ariaLabel={`${t('dashboard.agents', language)}: ${agents.length}`}
        />
        <MetricCard
          label={t('dashboard.costs', language)}
          value={formatEur(totalCost)}
          subtitle={t('dashboard.perMonth', language)}
          accentColor="var(--color-accent)"
          onClick={() => router.push('/admin/costs')}
          ariaLabel={`${t('dashboard.costs', language)}: ${formatEur(totalCost)}`}
        />
        <MetricCard
          label={t('dashboard.approvals', language)}
          value={pendingApprovals}
          subtitle={t('dashboard.open', language)}
          accentColor="var(--color-warning)"
          onClick={() => router.push('/admin/approvals')}
          ariaLabel={`${t('dashboard.approvals', language)}: ${pendingApprovals} ${t('dashboard.open', language)}`}
        />
        <MetricCard
          label={t('dashboard.incidents', language)}
          value={activeIncidents}
          subtitle={t('dashboard.active', language)}
          accentColor="var(--color-error)"
          ariaLabel={`${t('dashboard.incidents', language)}: ${activeIncidents} ${t('dashboard.active', language)}`}
        />
      </div>

      {/* Status Board + Recent Activity */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Agent Status Board */}
        <Card padding="none">
          <div className="p-6 pb-0">
            <CardHeader
              title={t('dashboard.statusBoard', language)}
              description={t('dashboard.statusBoardDescription', language)}
            />
          </div>
          <div className="mt-4">
            {hasAgents ? (
              <div role="list" aria-label={t('dashboard.statusBoard', language)}>
                {agents.map((agent) => (
                  <StatusBoardRow
                    key={agent.id}
                    name={agent.name}
                    role={agent.role}
                    status={agent.status}
                    costEur={costMap.get(agent.id) ?? 0}
                    onClick={() => router.push(`/admin/team/${agent.id}`)}
                  />
                ))}
              </div>
            ) : (
              <EmptyState
                message={t('empty.team', language)}
                description={t('empty.teamDescription', language)}
                ctaLabel={t('empty.teamCta', language)}
                onCtaClick={() => router.push('/admin/hire')}
              />
            )}
          </div>
        </Card>

        {/* Recent Activity Feed */}
        <Card padding="none">
          <div className="p-6 pb-0">
            <CardHeader
              title={t('dashboard.recentActivity', language)}
              description={t('dashboard.recentActivityDescription', language)}
            />
          </div>
          <div className="mt-4">
            {audit.data && audit.data.entries.length > 0 ? (
              <div role="log" aria-label={t('dashboard.recentActivity', language)} aria-live="polite">
                {audit.data.entries.slice(0, 10).map((entry) => (
                  <ActivityEntry
                    key={`${entry.agent_id}-${entry.sequence}`}
                    entry={entry}
                    lang={language}
                  />
                ))}
              </div>
            ) : (
              <EmptyState
                message={t('empty.activity', language)}
                description={t('empty.activityDescription', language)}
              />
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}

export default function AdminDashboardPage() {
  return (
    <ErrorBoundary>
      <DashboardContent />
    </ErrorBoundary>
  );
}
