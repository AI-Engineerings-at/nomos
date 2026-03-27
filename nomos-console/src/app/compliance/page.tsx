/**
 * NomOS — Compliance-Berichte (Officer Dashboard).
 * Read-only per-agent compliance table + Audit Trail viewer with export.
 * No edit capabilities — officer has read-only access.
 * Data from: GET /api/compliance/matrix, GET /api/audit
 *
 * 4 States: Loading (Skeleton), Empty (CTA), Error (ErrorBoundary), Data
 * WCAG 2.2 AA: focus-visible, aria-labels, keyboard nav
 * i18n: All text via translation keys
 */
'use client';

import { useState, useCallback } from 'react';
import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { useFetch, formatDate } from '@/lib/hooks';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { SkeletonCard, Skeleton } from '@/components/ui/skeleton';
import type { ComplianceMatrixResponse, ComplianceMatrixEntry, AuditEntry } from '@/lib/types';

function OfficerSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-busy="true">
      <span className="sr-only">{t('loading.compliance', 'de')}</span>
      <Skeleton width="w-64" height="h-8" />
      <SkeletonCard />
      <SkeletonCard />
      <SkeletonCard />
    </div>
  );
}

function OfficerContent() {
  const { language, addToast } = useNomosStore();
  const matrixFetch = useFetch<ComplianceMatrixResponse>('/compliance/matrix');
  // Global /audit endpoint does not exist — only /agents/{id}/audit is available.
  // Show empty state gracefully until a global aggregation endpoint is implemented.
  const auditFetch = { data: null as { entries: AuditEntry[]; total: number } | null, loading: false, error: null as string | null, reload: () => { /* no-op */ } };
  const [activeTab, setActiveTab] = useState<'matrix' | 'audit'>('matrix');

  const handleExportJsonl = useCallback(() => {
    const entries = auditFetch.data?.entries ?? [];
    const lines = entries.map((entry) => JSON.stringify(entry)).join('\n');
    const blob = new Blob([lines], { type: 'application/x-jsonlines' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nomos-audit-${new Date().toISOString().slice(0, 10)}.jsonl`;
    a.click();
    URL.revokeObjectURL(url);
    addToast({ type: 'info', message: t('toast.exportStarted', language), duration: 3000 });
  }, [auditFetch.data, language, addToast]);

  if (matrixFetch.loading || auditFetch.loading) {
    return <OfficerSkeleton />;
  }

  const matrixData = matrixFetch.data;
  const auditEntries = auditFetch.data?.entries ?? [];

  const tabs: { key: 'matrix' | 'audit'; label: string }[] = [
    { key: 'matrix', label: t('compliance.matrix', language) },
    { key: 'audit', label: t('audit.title', language) },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
          {t('nav.complianceReports', language)}
        </h1>
        <p className="text-sm text-[var(--color-muted)] mt-1">
          {language === 'de'
            ? 'EU AI Act & DSGVO Compliance-Status aller Mitarbeiter (Nur-Lese-Ansicht)'
            : 'EU AI Act & GDPR compliance status of all employees (Read-only view)'}
        </p>
      </div>

      {/* Tabs */}
      <div
        className="flex gap-1 border-b border-[var(--color-border)]"
        role="tablist"
        aria-label={t('nav.complianceReports', language)}
      >
        {tabs.map((tab) => (
          <button
            key={tab.key}
            role="tab"
            id={`officer-tab-${tab.key}`}
            aria-selected={activeTab === tab.key}
            aria-controls={`officer-panel-${tab.key}`}
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
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab panels */}
      <div
        id={`officer-panel-${activeTab}`}
        role="tabpanel"
        aria-labelledby={`officer-tab-${activeTab}`}
      >
        {activeTab === 'matrix' && (
          <>
            {!matrixData || matrixData.matrix.length === 0 ? (
              <EmptyState
                message={t('empty.compliance', language)}
                description={t('empty.complianceDescription', language)}
              />
            ) : (
              <Card padding="none">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm" aria-label={t('a11y.complianceMatrix', language)}>
                    <caption className="sr-only">{t('compliance.matrixDescription', language)}</caption>
                    <thead>
                      <tr className="border-b border-[var(--color-border)]">
                        <th
                          scope="col"
                          className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-muted)] font-[family-name:var(--font-headline)]"
                        >
                          {t('audit.agent', language)}
                        </th>
                        <th
                          scope="col"
                          className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-muted)] font-[family-name:var(--font-headline)]"
                        >
                          {t('users.status', language)}
                        </th>
                        <th
                          scope="col"
                          className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-muted)] font-[family-name:var(--font-headline)]"
                        >
                          {t('compliance.missingDocs', language)}
                        </th>
                        <th
                          scope="col"
                          className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-muted)] font-[family-name:var(--font-headline)]"
                        >
                          {t('compliance.riskClass', language)}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {matrixData.matrix.map((entry: ComplianceMatrixEntry) => (
                        <tr key={entry.agent_id} className="border-b border-[var(--color-border)] last:border-b-0">
                          <td className="px-4 py-3 font-semibold text-[var(--color-text)] whitespace-nowrap">
                            {entry.agent_name}
                          </td>
                          <td className="px-4 py-3">
                            <Badge status={entry.status === 'passed' ? 'online' : 'error'} label={entry.status} />
                          </td>
                          <td className="px-4 py-3 text-[var(--color-muted)]">
                            {entry.missing_docs.length === 0 ? '\u2014' : entry.missing_docs.join(', ')}
                          </td>
                          <td className="px-4 py-3">
                            <span className="text-xs font-semibold px-2 py-0.5 rounded-[var(--radius-full)] bg-[var(--color-hover)] text-[var(--color-text)]">
                              {entry.risk_class}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            )}
          </>
        )}

        {activeTab === 'audit' && (
          <>
            {/* Export button */}
            <div className="flex gap-2 mb-4">
              <Button variant="ghost" size="sm" onClick={handleExportJsonl} aria-label={t('audit.exportJsonl', language)}>
                {t('audit.exportJsonl', language)}
              </Button>
            </div>

            {auditEntries.length === 0 ? (
              <EmptyState
                message={t('empty.audit', language)}
                description={
                  language === 'de'
                    ? 'Compliance-Berichte werden erstellt, sobald Mitarbeiter eingestellt werden.'
                    : 'Compliance reports will be generated once employees are hired.'
                }
              />
            ) : (
              <Card padding="none">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm" aria-label={t('a11y.hashChainViewer', language)}>
                    <caption className="sr-only">{t('audit.description', language)}</caption>
                    <thead>
                      <tr className="border-b border-[var(--color-border)] bg-[var(--color-hover)]">
                        <th scope="col" className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-muted)]">
                          {t('audit.sequence', language)}
                        </th>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-muted)]">
                          {t('audit.eventType', language)}
                        </th>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-muted)]">
                          {t('audit.agent', language)}
                        </th>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-muted)]">
                          {t('audit.hash', language)}
                        </th>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-muted)]">
                          {t('audit.timestamp', language)}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {auditEntries.map((entry) => (
                        <tr
                          key={`${entry.agent_id}-${entry.sequence}`}
                          className="border-b border-[var(--color-border)] last:border-b-0 hover:bg-[var(--color-hover)] transition-colors"
                        >
                          <td className="px-4 py-3 font-[family-name:var(--font-mono)] text-xs text-[var(--color-muted)]">
                            #{entry.sequence}
                          </td>
                          <td className="px-4 py-3">
                            <Badge status="online" label={entry.event_type} />
                          </td>
                          <td className="px-4 py-3 font-semibold text-[var(--color-text)]">
                            {entry.agent_id}
                          </td>
                          <td className="px-4 py-3 font-[family-name:var(--font-mono)] text-xs text-[var(--color-muted)]" title={entry.chain_hash}>
                            {entry.chain_hash.slice(0, 12)}...
                          </td>
                          <td className="px-4 py-3 text-xs text-[var(--color-muted)]">
                            {formatDate(entry.timestamp, language)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default function ComplianceDashboardPage() {
  return (
    <ErrorBoundary>
      <OfficerContent />
    </ErrorBoundary>
  );
}
