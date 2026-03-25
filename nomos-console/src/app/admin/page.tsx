/**
 * NomOS Admin Dashboard — Main overview page.
 * Shows greeting, compliance health hero, 4 metric tiles, agent status board, recent activity, quick actions.
 * Data from: /api/fleet, /api/costs, /api/approvals, /api/incidents, /api/audit
 *
 * Design: "Trusted Control" — serious like online banking, warm like an office.
 * Inspired by: Cloudflare Security Dashboard, Kaspersky Overview, Grafana/Uptime Kuma.
 *
 * 4 States: Loading (Skeleton), Empty (CTA), Error (ErrorBoundary), Data
 * WCAG 2.2 AA: focus-visible, aria-labels, keyboard nav, live regions
 * i18n: All text via translation keys
 */
'use client';

import { useEffect, useRef, useState } from 'react';
import { useNomosStore } from '@/lib/store';
import { useAuth } from '@/lib/auth';
import { t } from '@/lib/i18n';
import { useFetch, getGreetingKey, formatEur, formatDate } from '@/lib/hooks';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { EmptyState } from '@/components/ui/empty-state';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { Skeleton, SkeletonCard } from '@/components/ui/skeleton';
import { SpeakButton } from '@/components/ui/speak-button';
import { useRouter } from 'next/navigation';
import type { FleetResponse, CostOverviewResponse, ApprovalListResponse, IncidentListResponse, AuditEntry } from '@/lib/types';
import { agentStatusToBadge } from '@/lib/types';

// ---------------------------------------------------------------------------
// Animated number counter hook
// ---------------------------------------------------------------------------
function useCountUp(target: number, duration = 800): number {
  const [value, setValue] = useState(0);
  const startRef = useRef<number | null>(null);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    startRef.current = null;
    const animate = (timestamp: number) => {
      if (startRef.current === null) startRef.current = timestamp;
      const elapsed = timestamp - startRef.current;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(eased * target));
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      }
    };
    rafRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target, duration]);

  return value;
}

// ---------------------------------------------------------------------------
// SVG Icon components (inline, no external deps)
// ---------------------------------------------------------------------------
function IconUsers({ className = 'w-6 h-6' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
    </svg>
  );
}

function IconWallet({ className = 'w-6 h-6' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="1" y="4" width="22" height="16" rx="2" ry="2" />
      <path d="M1 10h22" />
    </svg>
  );
}

function IconClipboard({ className = 'w-6 h-6' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2" />
      <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
    </svg>
  );
}

function IconAlert({ className = 'w-6 h-6' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  );
}

function IconShield({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  );
}

function IconPlus({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  );
}

function IconFileText({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
      <polyline points="14,2 14,8 20,8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
    </svg>
  );
}

function IconBarChart({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <line x1="12" y1="20" x2="12" y2="10" />
      <line x1="18" y1="20" x2="18" y2="4" />
      <line x1="6" y1="20" x2="6" y2="16" />
    </svg>
  );
}

function IconActivity({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="22,12 18,12 15,21 9,3 6,12 2,12" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Compliance Health Bar — HERO ELEMENT
// Full-width gradient bar from #4262FF to #31F1A8
// ---------------------------------------------------------------------------
function ComplianceHealthHero({
  percentage,
  description,
  perfectText,
}: {
  percentage: number;
  description: string;
  perfectText: string;
}) {
  const animatedPercent = useCountUp(percentage, 1200);
  const isPerfect = percentage === 100;

  return (
    <div
      className={[
        'relative overflow-hidden rounded-[var(--radius-lg)] p-6 sm:p-8',
        isPerfect ? 'compliance-perfect' : '',
      ].join(' ')}
      style={{
        background: 'linear-gradient(135deg, #4262FF 0%, #3451DB 40%, #2a45a8 70%, #1a3080 100%)',
      }}
    >
      {/* Subtle accent glow overlay */}
      <div
        className="absolute top-0 right-0 w-1/2 h-full opacity-20 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse at 70% 30%, #31F1A8, transparent 70%)',
        }}
        aria-hidden="true"
      />

      <div className="relative z-10 flex flex-col sm:flex-row items-start sm:items-center gap-6">
        {/* Shield icon */}
        <div
          className="flex items-center justify-center w-14 h-14 rounded-[var(--radius)] shrink-0"
          style={{ backgroundColor: 'rgba(255,255,255,0.15)' }}
          aria-hidden="true"
        >
          <IconShield className="w-7 h-7 text-white" />
        </div>

        <div className="flex-1 min-w-0">
          {/* Score + label row */}
          <div className="flex items-baseline gap-3 mb-2">
            <span
              className="text-4xl sm:text-5xl font-extrabold text-white font-[family-name:var(--font-headline)] tabular-nums"
              aria-hidden="true"
            >
              {animatedPercent}%
            </span>
            <span className="text-sm font-medium text-white/70 font-[family-name:var(--font-headline)] uppercase tracking-wider">
              Compliance Health
            </span>
          </div>

          {/* Progress bar */}
          <div
            className="w-full h-2.5 bg-white/15 rounded-[var(--radius-full)] overflow-hidden mb-3"
            role="progressbar"
            aria-valuenow={percentage}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`Compliance: ${percentage}%`}
          >
            <div
              className="h-full rounded-[var(--radius-full)] transition-all duration-1000 ease-out health-bar-gradient"
              style={{ width: `${Math.min(percentage, 100)}%` }}
            />
          </div>

          {/* Description text */}
          <p className="text-sm text-white/70 max-w-xl">
            {isPerfect ? perfectText : description}
          </p>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Metric Tile — icon, animated number, label, subtitle
// ---------------------------------------------------------------------------
function MetricTile({
  icon,
  label,
  value,
  subtitle,
  accentColor,
  onClick,
  ariaLabel,
  animationClass,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  subtitle: string;
  accentColor: string;
  onClick?: () => void;
  ariaLabel: string;
  animationClass: string;
}) {
  const isNumeric = typeof value === 'number';
  const animatedValue = useCountUp(isNumeric ? value : 0, 700);

  return (
    <div
      className={[
        'metric-tile bg-[var(--color-card)] border border-[var(--color-border)]',
        'rounded-[var(--radius-lg)] shadow-[var(--shadow-card)] p-5',
        onClick ? 'cursor-pointer' : '',
        animationClass,
      ].join(' ')}
      onClick={onClick}
      onKeyDown={onClick ? (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(); }
      } : undefined}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      aria-label={ariaLabel}
    >
      {/* Icon circle */}
      <div
        className="w-10 h-10 rounded-[var(--radius)] flex items-center justify-center mb-4"
        style={{ backgroundColor: `${accentColor}12`, color: accentColor }}
        aria-hidden="true"
      >
        {icon}
      </div>

      {/* Value */}
      <p className="text-3xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)] tabular-nums leading-none">
        {isNumeric ? animatedValue : value}
      </p>

      {/* Label */}
      <p className="text-sm font-semibold text-[var(--color-text)] mt-2 font-[family-name:var(--font-headline)]">
        {label}
      </p>

      {/* Subtitle */}
      <p className="text-xs text-[var(--color-muted)] mt-0.5">
        {subtitle}
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Agent Status Board Row — Uptime Kuma style
// ---------------------------------------------------------------------------
function AgentStatusRow({
  name,
  role,
  status,
  costEur,
  budgetEur,
  budgetOfLabel,
  onClick,
}: {
  name: string;
  role: string;
  status: string;
  costEur: number;
  budgetEur: number;
  budgetOfLabel: string;
  onClick: () => void;
}) {
  const badgeStatus = agentStatusToBadge(status);
  const isOnline = status === 'running';
  const budgetPercent = budgetEur > 0 ? Math.min((costEur / budgetEur) * 100, 100) : 0;

  // Avatar colors based on first letter hash
  const avatarColors = [
    '#4262FF', '#31F1A8', '#F59E0B', '#EF4444', '#10B981',
    '#8B5CF6', '#EC4899', '#06B6D4', '#F97316', '#6366F1',
  ];
  const colorIndex = name.charCodeAt(0) % avatarColors.length;
  const avatarColor = avatarColors[colorIndex];

  // Status dot color
  const dotColorMap: Record<string, string> = {
    running: 'var(--color-success)',
    paused: 'var(--color-warning)',
    killed: 'var(--color-muted)',
    deploying: 'var(--color-primary)',
    error: 'var(--color-error)',
  };
  const dotColor = dotColorMap[status] ?? 'var(--color-error)';

  return (
    <button
      onClick={onClick}
      className={[
        'agent-row-hover w-full flex items-center gap-3 px-4 py-3',
        'border-b border-[var(--color-border)] last:border-b-0',
        'focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-[var(--color-focus-ring)]',
        'text-left',
      ].join(' ')}
      aria-label={`${name} — ${role}`}
    >
      {/* Status dot */}
      <div className="relative shrink-0" aria-hidden="true">
        <span
          className={[
            'block w-2.5 h-2.5 rounded-full',
            isOnline ? 'status-dot-pulse' : '',
          ].join(' ')}
          style={{ backgroundColor: dotColor }}
        />
      </div>

      {/* Avatar */}
      <div
        className="w-9 h-9 rounded-full flex items-center justify-center text-white text-sm font-bold shrink-0"
        style={{ backgroundColor: avatarColor }}
        aria-hidden="true"
      >
        {name.charAt(0).toUpperCase()}
      </div>

      {/* Name + role */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-[var(--color-text)] truncate">{name}</p>
        <p className="text-xs text-[var(--color-muted)] truncate">{role}</p>
      </div>

      {/* Badge */}
      <Badge status={badgeStatus} />

      {/* Budget mini bar */}
      <div className="hidden sm:flex flex-col items-end gap-1 shrink-0 w-24">
        <span className="text-xs text-[var(--color-muted)] font-[family-name:var(--font-mono)] whitespace-nowrap">
          {formatEur(costEur)} {budgetOfLabel} {formatEur(budgetEur)}
        </span>
        <div className="w-full h-1.5 bg-[var(--color-hover)] rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${budgetPercent}%`,
              backgroundColor:
                budgetPercent >= 90
                  ? 'var(--color-error)'
                  : budgetPercent >= 70
                    ? 'var(--color-warning)'
                    : 'var(--color-success)',
            }}
          />
        </div>
      </div>
    </button>
  );
}

// ---------------------------------------------------------------------------
// Activity Feed Entry — Grafana-style compact timeline
// ---------------------------------------------------------------------------
function ActivityTimelineEntry({
  entry,
  lang,
}: {
  entry: AuditEntry;
  lang: 'de' | 'en';
}) {
  return (
    <div className="flex items-start gap-3 px-4 py-2.5 border-b border-[var(--color-border)] last:border-b-0 hover:bg-[var(--color-hover)] transition-colors duration-[var(--transition)]">
      {/* Timeline dot + line */}
      <div className="flex flex-col items-center pt-1.5 shrink-0" aria-hidden="true">
        <span className="block w-2 h-2 rounded-full bg-[var(--color-primary)]" />
        <span className="block w-px flex-1 bg-[var(--color-border)] mt-1" />
      </div>

      <div className="flex-1 min-w-0 pb-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-[var(--color-text)] truncate">
            {entry.agent_id}
          </span>
          <span
            className="inline-block px-1.5 py-0.5 text-[10px] font-medium rounded bg-[var(--color-primary-light)] text-[var(--color-primary)] uppercase tracking-wide font-[family-name:var(--font-mono)]"
          >
            {entry.event_type}
          </span>
        </div>
        <p className="text-xs text-[var(--color-muted)] mt-0.5 font-[family-name:var(--font-mono)]">
          {formatDate(entry.timestamp, lang)}
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Quick Action Button
// ---------------------------------------------------------------------------
function QuickActionButton({
  icon,
  label,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={[
        'quick-action-btn flex items-center gap-3 px-4 py-3 rounded-[var(--radius)]',
        'text-sm font-medium text-[var(--color-text)]',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]',
      ].join(' ')}
    >
      <span className="text-[var(--color-primary)]" aria-hidden="true">{icon}</span>
      {label}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------
function DashboardSkeleton() {
  return (
    <div className="space-y-6 dashboard-bg" role="status" aria-busy="true" aria-label="Dashboard wird geladen">
      <span className="sr-only">Wird geladen...</span>
      {/* Greeting skeleton */}
      <Skeleton width="w-64" height="h-9" />
      {/* Compliance hero skeleton */}
      <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-[var(--radius-lg)] p-8 space-y-4">
        <div className="flex items-center gap-4">
          <Skeleton width="w-14" height="h-14" />
          <div className="flex-1 space-y-3">
            <Skeleton width="w-32" height="h-10" />
            <Skeleton width="w-full" height="h-2.5" />
            <Skeleton width="w-2/3" height="h-4" />
          </div>
        </div>
      </div>
      {/* Metric tiles skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
      {/* Status board + Activity */}
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
        <div className="xl:col-span-3"><SkeletonCard /></div>
        <div className="xl:col-span-2"><SkeletonCard /></div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Dashboard Content
// ---------------------------------------------------------------------------
function DashboardContent() {
  const { language } = useNomosStore();
  const { user } = useAuth();
  const router = useRouter();

  const fleet = useFetch<FleetResponse>('/fleet');
  const costs = useFetch<CostOverviewResponse>('/costs');
  const approvals = useFetch<ApprovalListResponse>('/approvals');
  const incidents = useFetch<IncidentListResponse>('/incidents');
  // Note: global /audit endpoint not available — activity feed uses fleet events for now
  const audit = { data: null as { entries: AuditEntry[] } | null, loading: false, error: null };

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

  // Compliance health
  const compliantCount = agents.filter((a) => a.compliance_status === 'compliant').length;
  const compliancePercent = agents.length > 0 ? Math.round((compliantCount / agents.length) * 100) : 0;

  // Cost map + budget map for status board
  const costMap = new Map<string, number>();
  const budgetMap = new Map<string, number>();
  if (costs.data) {
    for (const c of costs.data.costs) {
      costMap.set(c.agent_id, c.total_cost_eur);
      budgetMap.set(c.agent_id, c.budget_limit_eur);
    }
  }

  const greetingKey = getGreetingKey();
  const greeting = t(greetingKey, language);
  const userName = user?.name.split(' ')[0] ?? '';

  const hasAgents = agents.length > 0;

  return (
    <div className="space-y-8 dashboard-bg">
      {/* ── Greeting ─────────────────────────────────────────────────── */}
      <div className="flex items-center gap-3" data-tour="dashboard">
        <h1 className="text-3xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)] metric-animate">
          {greeting}, {userName}.
        </h1>
        <SpeakButton text={`${greeting}, ${userName}.`} size="md" />
      </div>

      {/* ── Compliance Health Hero ──────────────────────────────────── */}
      {hasAgents ? (
        <ComplianceHealthHero
          percentage={compliancePercent}
          description={t('dashboard.complianceHealthDescription', language)}
          perfectText={t('dashboard.compliancePerfect', language)}
        />
      ) : (
        <Card>
          <div className="flex items-center gap-4 p-2">
            <div className="text-[var(--color-primary)]">
              <IconShield className="w-8 h-8" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
                {t('dashboard.complianceHealth', language)}
              </h3>
              <p className="text-sm text-[var(--color-muted)]">
                {t('empty.complianceDescription', language)}
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* ── Accent Divider ──────────────────────────────────────────── */}
      <hr className="accent-divider" aria-hidden="true" />

      {/* ── 4 Metric Tiles ─────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <MetricTile
          icon={<IconUsers />}
          label={t('dashboard.agents', language)}
          value={agents.length}
          subtitle={`${onlineCount} ${t('dashboard.active', language)}`}
          accentColor="#4262FF"
          onClick={() => router.push('/admin/team')}
          ariaLabel={`${t('dashboard.agents', language)}: ${agents.length}`}
          animationClass="metric-animate"
        />
        <MetricTile
          icon={<IconWallet />}
          label={t('dashboard.costs', language)}
          value={formatEur(totalCost)}
          subtitle={t('dashboard.perMonth', language)}
          accentColor="#31F1A8"
          onClick={() => router.push('/admin/costs')}
          ariaLabel={`${t('dashboard.costs', language)}: ${formatEur(totalCost)}`}
          animationClass="metric-animate-delay-1"
        />
        <MetricTile
          icon={<IconClipboard />}
          label={t('dashboard.approvals', language)}
          value={pendingApprovals}
          subtitle={t('dashboard.open', language)}
          accentColor="#F59E0B"
          onClick={() => router.push('/admin/approvals')}
          ariaLabel={`${t('dashboard.approvals', language)}: ${pendingApprovals} ${t('dashboard.open', language)}`}
          animationClass="metric-animate-delay-2"
        />
        <MetricTile
          icon={<IconAlert />}
          label={t('dashboard.incidents', language)}
          value={activeIncidents}
          subtitle={t('dashboard.active', language)}
          accentColor="#EF4444"
          ariaLabel={`${t('dashboard.incidents', language)}: ${activeIncidents} ${t('dashboard.active', language)}`}
          animationClass="metric-animate-delay-3"
        />
      </div>

      {/* ── Status Board + Activity Feed ───────────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
        {/* Agent Status Board — 3 columns wide */}
        <Card padding="none" className="xl:col-span-3">
          <div className="p-5 pb-0 flex items-center gap-3 border-b border-[var(--color-border)]">
            <div className="text-[var(--color-primary)]" aria-hidden="true">
              <IconActivity />
            </div>
            <div className="pb-4">
              <h3 className="text-base font-bold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
                {t('dashboard.statusBoard', language)}
              </h3>
              <p className="text-xs text-[var(--color-muted)]">
                {t('dashboard.statusBoardDescription', language)}
              </p>
            </div>
          </div>
          <div>
            {hasAgents ? (
              <div role="list" aria-label={t('dashboard.statusBoard', language)}>
                {agents.map((agent) => (
                  <AgentStatusRow
                    key={agent.id}
                    name={agent.name}
                    role={agent.role}
                    status={agent.status}
                    costEur={costMap.get(agent.id) ?? 0}
                    budgetEur={budgetMap.get(agent.id) ?? 0}
                    budgetOfLabel={t('dashboard.budgetOf', language)}
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

        {/* Recent Activity Feed — 2 columns wide */}
        <Card padding="none" className="xl:col-span-2">
          <div className="p-5 pb-0 flex items-center gap-3 border-b border-[var(--color-border)]">
            <div className="text-[var(--color-primary)]" aria-hidden="true">
              <IconFileText />
            </div>
            <div className="pb-4">
              <h3 className="text-base font-bold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
                {t('dashboard.recentActivity', language)}
              </h3>
              <p className="text-xs text-[var(--color-muted)]">
                {t('dashboard.recentActivityDescription', language)}
              </p>
            </div>
          </div>
          <div>
            {audit.data && audit.data.entries.length > 0 ? (
              <div role="log" aria-label={t('dashboard.recentActivity', language)} aria-live="polite">
                {audit.data.entries.slice(0, 10).map((entry) => (
                  <ActivityTimelineEntry
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

      {/* ── Accent Divider ──────────────────────────────────────────── */}
      <hr className="accent-divider" aria-hidden="true" />

      {/* ── Quick Actions Bar ──────────────────────────────────────── */}
      <div>
        <h2 className="text-sm font-semibold text-[var(--color-muted)] uppercase tracking-wider mb-3 font-[family-name:var(--font-headline)]">
          {t('dashboard.quickActions', language)}
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
          <QuickActionButton
            icon={<IconPlus />}
            label={t('dashboard.quickAction.hire', language)}
            onClick={() => router.push('/admin/hire')}
          />
          <QuickActionButton
            icon={<IconShield />}
            label={t('dashboard.quickAction.compliance', language)}
            onClick={() => router.push('/admin/compliance')}
          />
          <QuickActionButton
            icon={<IconBarChart />}
            label={t('dashboard.quickAction.costs', language)}
            onClick={() => router.push('/admin/costs')}
          />
          <QuickActionButton
            icon={<IconFileText />}
            label={t('dashboard.quickAction.audit', language)}
            onClick={() => router.push('/admin/audit')}
          />
        </div>
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
