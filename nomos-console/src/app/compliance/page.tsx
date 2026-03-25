/**
 * NomOS — Compliance-Berichte (Officer Dashboard).
 * Read-only Compliance Matrix + Audit Trail viewer with export.
 * No edit capabilities — officer has read-only access.
 * Data from: GET /api/compliance/matrix, GET /api/audit
 *
 * 4 States: Loading (Skeleton), Empty (CTA), Error (ErrorBoundary), Data
 * WCAG 2.2 AA: focus-visible, aria-labels, keyboard nav
 * i18n: All text via translation keys
 */
'use client';

import { useState, useCallback, useMemo } from 'react';
import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { useFetch, formatDate } from '@/lib/hooks';
import { Card, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { SkeletonCard, Skeleton } from '@/components/ui/skeleton';
import type { ComplianceMatrixResponse, ComplianceMatrixCell, AuditEntry } from '@/lib/types';

/** Status to visual mapping. */
function statusLabel(status: ComplianceMatrixCell['status'], lang: 'de' | 'en'): string {
  switch (status) {
    case 'valid': return t('compliance.valid', lang);
    case 'expiring': return t('compliance.expiring', lang);
    case 'missing': return t('compliance.missing', lang);
  }
}

const statusColors: Record<ComplianceMatrixCell['status'], { bg: string; border: string }> = {
  valid: { bg: 'bg-[var(--color-success-light)]', border: 'border-[var(--color-success)]' },
  expiring: { bg: 'bg-[var(--color-warning-light)]', border: 'border-[var(--color-warning)]' },
  missing: { bg: 'bg-[var(--color-error-light)]', border: 'border-[var(--color-error)]' },
};

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
  const auditFetch = useFetch<{ entries: AuditEntry[]; total: number }>('/audit');
  const [activeTab, setActiveTab] = useState<'matrix' | 'audit'>('matrix');

  // Build matrix lookup
  const cellLookup = useMemo(() => {
    const lookup = new Map<string, Map<string, ComplianceMatrixCell>>();
    if (matrixFetch.data) {
      for (const cell of matrixFetch.data.matrix) {
        if (!lookup.has(cell.agent_id)) {
          lookup.set(cell.agent_id, new Map());
        }
        lookup.get(cell.agent_id)!.set(cell.document_type, cell);
      }
    }
    return lookup;
  }, [matrixFetch.data]);

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

      {/* Health Score */}
      {matrixData && matrixData.agents.length > 0 && (
        <Card>
          <CardHeader
            title={t('compliance.healthScore', language)}
            description={t('compliance.healthScoreDescription', language)}
          />
          <div className="mt-4 flex items-center gap-4">
            <span
              className="text-4xl font-extrabold font-[family-name:var(--font-headline)]"
              style={{
                color: matrixData.health_score >= 80
                  ? 'var(--color-success)'
                  : matrixData.health_score >= 50
                    ? 'var(--color-warning)'
                    : 'var(--color-error)',
              }}
            >
              {matrixData.health_score}%
            </span>
            <div
              className="flex-1 h-3 bg-[var(--color-hover)] rounded-[var(--radius-full)] overflow-hidden"
              role="progressbar"
              aria-valuenow={matrixData.health_score}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={t('a11y.complianceScore', language)}
            >
              <div
                className="h-full rounded-[var(--radius-full)] transition-all duration-500"
                style={{
                  width: `${Math.min(matrixData.health_score, 100)}%`,
                  backgroundColor: matrixData.health_score >= 80
                    ? 'var(--color-success)'
                    : matrixData.health_score >= 50
                      ? 'var(--color-warning)'
                      : 'var(--color-error)',
                }}
              />
            </div>
          </div>
        </Card>
      )}

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
            {!matrixData || matrixData.agents.length === 0 ? (
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
                        {matrixData.document_types.map((docType) => (
                          <th
                            key={docType}
                            scope="col"
                            className="px-4 py-3 text-center text-xs font-bold uppercase tracking-wider text-[var(--color-muted)] font-[family-name:var(--font-headline)]"
                          >
                            {docType}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {matrixData.agents.map((agentId) => {
                        const agentCells = cellLookup.get(agentId);
                        const agentName = agentCells?.values().next().value?.agent_name ?? agentId;
                        return (
                          <tr key={agentId} className="border-b border-[var(--color-border)] last:border-b-0">
                            <td className="px-4 py-3 font-semibold text-[var(--color-text)] whitespace-nowrap">
                              {agentName}
                            </td>
                            {matrixData.document_types.map((docType) => {
                              const cell = agentCells?.get(docType);
                              const status = cell?.status ?? 'missing';
                              const colors = statusColors[status];
                              return (
                                <td key={docType} className="px-4 py-3 text-center">
                                  <span
                                    className={[
                                      'inline-flex items-center justify-center min-w-[80px] px-3 py-1.5 rounded-[var(--radius-sm)]',
                                      'text-xs font-semibold border',
                                      colors.bg, colors.border,
                                    ].join(' ')}
                                    aria-label={`${agentName}: ${docType} — ${statusLabel(status, language)}`}
                                  >
                                    {statusLabel(status, language)}
                                  </span>
                                </td>
                              );
                            })}
                          </tr>
                        );
                      })}
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
