/**
 * NomOS — Mitarbeiter-Profil (Employee Profile) panel.
 * Detail view: profile header, action buttons, 5 tabs.
 * Data from: /api/fleet/{id}, /api/agents/{id}/audit, /api/costs/{id}, /api/agents/{id}/compliance
 *
 * 4 States: Loading (Skeleton), Empty (per-tab), Error (ErrorBoundary), Data
 * WCAG 2.2 AA: focus-visible, aria-labels, keyboard nav, tabpanel
 * i18n: All text via translation keys
 */
'use client';

import { useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { useFetch, formatEur, formatDate } from '@/lib/hooks';
import { api, ApiError } from '@/lib/api';
import { Card, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { SkeletonCard, Skeleton } from '@/components/ui/skeleton';
import type { Agent, AuditEntry, CostEntry, ComplianceEntry } from '@/lib/types';
import { agentStatusToBadge } from '@/lib/types';

type ProfileTab = 'activity' | 'protocol' | 'costs' | 'compliance' | 'config';

function ProfileBudgetBar({ used, limit }: { used: number; limit: number }) {
  const percent = limit > 0 ? Math.min((used / limit) * 100, 100) : 0;
  const getColor = (): string => {
    if (percent >= 90) return 'var(--color-error)';
    if (percent >= 70) return 'var(--color-warning)';
    return 'var(--color-success)';
  };

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <span className="text-[var(--color-muted)]">{formatEur(used)} / {formatEur(limit)}</span>
        <span className="font-semibold text-[var(--color-text)]">{Math.round(percent)}%</span>
      </div>
      <div
        className="w-full h-3 bg-[var(--color-hover)] rounded-[var(--radius-full)] overflow-hidden"
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

/** Compliance document checklist (14 required documents). */
const COMPLIANCE_DOCS = [
  'risk_assessment', 'data_protection_impact', 'transparency_notice',
  'human_oversight_plan', 'technical_documentation', 'quality_management',
  'ai_act_registration', 'dsgvo_art_13', 'dsgvo_art_14', 'dsgvo_art_22',
  'ai_act_art_50', 'incident_response_plan', 'monitoring_plan', 'audit_trail_config',
] as const;

function ComplianceChecklist({
  missingDocs,
  lang,
}: {
  missingDocs: string[];
  lang: 'de' | 'en';
}) {
  const missingSet = new Set(missingDocs);

  return (
    <div className="space-y-2" role="list" aria-label={t('profile.complianceChecklist', lang)}>
      {COMPLIANCE_DOCS.map((doc) => {
        const isPresent = !missingSet.has(doc);
        return (
          <div
            key={doc}
            className="flex items-center gap-3 px-3 py-2 rounded-[var(--radius)] hover:bg-[var(--color-hover)] transition-colors"
            role="listitem"
          >
            <div
              className={[
                'w-5 h-5 rounded-full flex items-center justify-center shrink-0',
                isPresent ? 'bg-[var(--color-success)]' : 'bg-[var(--color-error)]',
              ].join(' ')}
              aria-hidden="true"
            >
              <svg className="w-3 h-3 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={3}>
                {isPresent ? (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                )}
              </svg>
            </div>
            <span className="text-sm text-[var(--color-text)]">
              {doc.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
            </span>
            <span className="sr-only">{isPresent ? 'vorhanden' : 'fehlt'}</span>
          </div>
        );
      })}
    </div>
  );
}

function ProfileSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-busy="true">
      <span className="sr-only">Wird geladen...</span>
      <div className="flex items-center gap-4">
        <Skeleton width="w-16" height="h-16" rounded />
        <div className="space-y-2 flex-1">
          <Skeleton width="w-48" height="h-6" />
          <Skeleton width="w-32" height="h-4" />
        </div>
      </div>
      <SkeletonCard />
      <SkeletonCard />
    </div>
  );
}

function ProfileContent() {
  const params = useParams();
  const agentId = params.id as string;
  const router = useRouter();
  const { language } = useNomosStore();
  const { addToast } = useNomosStore();
  const [activeTab, setActiveTab] = useState<ProfileTab>('activity');
  const [pauseLoading, setPauseLoading] = useState(false);

  const agentFetch = useFetch<Agent>(`/fleet/${agentId}`);
  const auditFetch = useFetch<{ entries: AuditEntry[]; total: number }>(`/agents/${agentId}/audit`);
  const costFetch = useFetch<CostEntry>(`/costs/${agentId}`);
  const complianceFetch = useFetch<ComplianceEntry>(`/agents/${agentId}/compliance`);

  if (agentFetch.loading) {
    return <ProfileSkeleton />;
  }

  if (agentFetch.error || !agentFetch.data) {
    return (
      <EmptyState
        message={agentFetch.error ?? t('error.notFound', language)}
        ctaLabel={t('action.back', language)}
        onCtaClick={() => router.push('/admin/team')}
      />
    );
  }

  const agent = agentFetch.data;
  const badgeStatus = agentStatusToBadge(agent.status);
  const isCompliant = agent.compliance_status === 'compliant';
  const costUsed = costFetch.data?.total_cost_eur ?? 0;
  const costLimit = costFetch.data?.budget_limit_eur ?? 0;

  const handlePause = async () => {
    setPauseLoading(true);
    try {
      const newStatus = agent.status === 'paused' ? 'running' : 'paused';
      await api.patch(`/fleet/${agentId}`, { status: newStatus });
      addToast({
        type: 'success',
        message: newStatus === 'paused'
          ? t('toast.agentPaused', language)
          : t('toast.agentResumed', language),
        duration: 4000,
      });
      agentFetch.reload();
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : t('error.serverError', language);
      addToast({ type: 'error', message: msg, duration: 6000 });
    } finally {
      setPauseLoading(false);
    }
  };

  const tabs: { key: ProfileTab; labelKey: 'profile.tab.activity' | 'profile.tab.protocol' | 'profile.tab.costs' | 'profile.tab.compliance' | 'profile.tab.config' }[] = [
    { key: 'activity', labelKey: 'profile.tab.activity' },
    { key: 'protocol', labelKey: 'profile.tab.protocol' },
    { key: 'costs', labelKey: 'profile.tab.costs' },
    { key: 'compliance', labelKey: 'profile.tab.compliance' },
    { key: 'config', labelKey: 'profile.tab.config' },
  ];

  return (
    <div className="space-y-6">
      {/* Back button */}
      <button
        onClick={() => router.push('/admin/team')}
        className="inline-flex items-center gap-2 text-sm text-[var(--color-muted)] hover:text-[var(--color-text)] transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)] rounded-[var(--radius-sm)]"
        aria-label={t('action.back', language)}
      >
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        {t('action.back', language)}
      </button>

      {/* Profile Header */}
      <Card>
        <div className="flex flex-col sm:flex-row sm:items-start gap-4">
          {/* Avatar */}
          <div
            className="w-16 h-16 rounded-[var(--radius-lg)] flex items-center justify-center text-white text-2xl font-bold shrink-0"
            style={{ backgroundColor: 'var(--color-primary)' }}
            aria-hidden="true"
          >
            {agent.name.charAt(0).toUpperCase()}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
                {agent.name}
              </h1>
              <Badge status={badgeStatus} />
              <span
                className={[
                  'inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold rounded-[var(--radius-full)]',
                  isCompliant
                    ? 'bg-[var(--color-success-light)] text-[var(--color-success)]'
                    : 'bg-[var(--color-error-light)] text-[var(--color-error)]',
                ].join(' ')}
                role="status"
              >
                {isCompliant ? t('team.compliant', language) : t('team.nonCompliant', language)}
              </span>
            </div>
            <p className="text-sm text-[var(--color-muted)] mt-1">{agent.role} — {agent.company}</p>

            {/* Budget bar */}
            <div className="mt-3 max-w-md">
              <ProfileBudgetBar used={costUsed} limit={costLimit} />
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap gap-2 shrink-0">
            <Button
              variant={agent.status === 'paused' ? 'primary' : 'secondary'}
              size="sm"
              onClick={handlePause}
              loading={pauseLoading}
              aria-label={agent.status === 'paused' ? t('action.resume', language) : t('profile.pause', language)}
            >
              {agent.status === 'paused' ? t('action.resume', language) : t('profile.pause', language)}
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => router.push(`/app/chat/${agentId}`)}
            >
              {t('profile.chat', language)}
            </Button>
            <Button variant="secondary" size="sm" disabled>
              {t('profile.assignTask', language)}
            </Button>
          </div>
        </div>
      </Card>

      {/* Tabs */}
      <div
        className="flex gap-1 border-b border-[var(--color-border)] overflow-x-auto"
        role="tablist"
        aria-label={t('profile.title', language)}
      >
        {tabs.map((tab) => (
          <button
            key={tab.key}
            role="tab"
            id={`tab-${tab.key}`}
            aria-selected={activeTab === tab.key}
            aria-controls={`tabpanel-${tab.key}`}
            onClick={() => setActiveTab(tab.key)}
            className={[
              'px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors duration-[var(--transition)]',
              'focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-[var(--color-focus-ring)]',
              'border-b-2 -mb-[1px]',
              activeTab === tab.key
                ? 'border-[var(--color-primary)] text-[var(--color-primary)]'
                : 'border-transparent text-[var(--color-muted)] hover:text-[var(--color-text)] hover:border-[var(--color-border)]',
            ].join(' ')}
          >
            {t(tab.labelKey, language)}
          </button>
        ))}
      </div>

      {/* Tab Panels */}
      <div
        id={`tabpanel-${activeTab}`}
        role="tabpanel"
        aria-labelledby={`tab-${activeTab}`}
      >
        {/* Activity Tab */}
        {activeTab === 'activity' && (
          <Card padding="none">
            {auditFetch.loading ? (
              <div className="p-6"><SkeletonCard /></div>
            ) : auditFetch.data && auditFetch.data.entries.length > 0 ? (
              <div role="log" aria-label={t('profile.tab.activity', language)}>
                {auditFetch.data.entries.slice(0, 20).map((entry) => (
                  <div
                    key={`${entry.agent_id}-${entry.sequence}`}
                    className="flex items-start gap-3 px-4 py-3 border-b border-[var(--color-border)] last:border-b-0"
                  >
                    <div className="w-8 h-8 rounded-full bg-[var(--color-primary-light)] flex items-center justify-center shrink-0 mt-0.5">
                      <svg className="w-4 h-4 text-[var(--color-primary)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                        <circle cx="12" cy="12" r="10" />
                        <path d="M12 6v6l4 2" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-[var(--color-text)]">{entry.event_type}</p>
                      <p className="text-xs text-[var(--color-muted)] mt-0.5">{formatDate(entry.timestamp, language)}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState message={t('profile.noActivity', language)} />
            )}
          </Card>
        )}

        {/* Protocol Tab */}
        {activeTab === 'protocol' && (
          <Card padding="none">
            {auditFetch.loading ? (
              <div className="p-6"><SkeletonCard /></div>
            ) : auditFetch.data && auditFetch.data.entries.length > 0 ? (
              <div className="divide-y divide-[var(--color-border)]">
                {auditFetch.data.entries.map((entry) => (
                  <div key={`${entry.agent_id}-${entry.sequence}`} className="px-4 py-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-[var(--color-text)]">#{entry.sequence}</span>
                      <span className="text-xs text-[var(--color-muted)]">{formatDate(entry.timestamp, language)}</span>
                    </div>
                    <p className="text-sm text-[var(--color-muted)] mt-1">{entry.event_type}</p>
                    <p className="text-xs text-[var(--color-muted)] font-[family-name:var(--font-mono)] mt-1 truncate">
                      Hash: {entry.chain_hash}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState message={t('empty.audit', language)} />
            )}
          </Card>
        )}

        {/* Costs Tab */}
        {activeTab === 'costs' && (
          <div className="space-y-4">
            <Card>
              <CardHeader title={t('profile.budget', language)} />
              <div className="mt-4">
                {costFetch.data ? (
                  <div className="space-y-4">
                    <ProfileBudgetBar used={costUsed} limit={costLimit} />
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs text-[var(--color-muted)]">{t('profile.budgetUsed', language)}</p>
                        <p className="text-lg font-bold text-[var(--color-text)]">{formatEur(costUsed)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-[var(--color-muted)]">{t('profile.budgetRemaining', language)}</p>
                        <p className="text-lg font-bold text-[var(--color-text)]">{formatEur(Math.max(costLimit - costUsed, 0))}</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <EmptyState message={t('profile.noCosts', language)} />
                )}
              </div>
            </Card>
          </div>
        )}

        {/* Compliance Tab */}
        {activeTab === 'compliance' && (
          <Card>
            <CardHeader
              title={t('profile.complianceChecklist', language)}
              description={`${COMPLIANCE_DOCS.length} ${language === 'de' ? 'Dokumente erforderlich' : 'documents required'}`}
            />
            <div className="mt-4">
              <ComplianceChecklist
                missingDocs={complianceFetch.data?.missing_documents ?? []}
                lang={language}
              />
            </div>
          </Card>
        )}

        {/* Config Tab */}
        {activeTab === 'config' && (
          <div className="space-y-4">
            <Card>
              <CardHeader title={t('profile.currentConfig', language)} />
              <div className="mt-4">
                <pre className="p-4 text-xs bg-[var(--color-hover)] rounded-[var(--radius)] overflow-x-auto text-[var(--color-text)] font-[family-name:var(--font-mono)]">
                  {JSON.stringify({
                    id: agent.id,
                    name: agent.name,
                    role: agent.role,
                    risk_class: agent.risk_class,
                    status: agent.status,
                    company: agent.company,
                    email: agent.email,
                    manifest_hash: agent.manifest_hash,
                  }, null, 2)}
                </pre>
              </div>
            </Card>
            <Card>
              <CardHeader
                title={t('profile.configHistory', language)}
                action={
                  <Button variant="secondary" size="sm" disabled aria-label={t('profile.rollback', language)}>
                    {t('profile.rollback', language)}
                  </Button>
                }
              />
              <div className="mt-4">
                <p className="text-sm text-[var(--color-muted)]">
                  {language === 'de'
                    ? 'Konfigurationshistorie wird in einer zukuenftigen Version verfuegbar sein.'
                    : 'Configuration history will be available in a future version.'}
                </p>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

export default function AgentProfilePage() {
  return (
    <ErrorBoundary>
      <ProfileContent />
    </ErrorBoundary>
  );
}
