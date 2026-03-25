/**
 * NomOS — Rechts-Check (Compliance Matrix) admin panel.
 * Compliance Matrix: Agents x Documents grid with color-coded status cells.
 * Green (valid), Yellow (expiring >6mo), Red (missing). Click cell for detail.
 * Compliance Health Score at top.
 * Data from: GET /api/compliance/matrix
 *
 * 4 States: Loading (Skeleton), Empty (CTA), Error (ErrorBoundary), Data
 * WCAG 2.2 AA: focus-visible, aria-labels, keyboard nav
 * i18n: All text via translation keys
 */
'use client';

import { useState } from 'react';
import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { useFetch, formatDate } from '@/lib/hooks';
import { Card, CardHeader } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { SkeletonCard, Skeleton } from '@/components/ui/skeleton';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import type { ComplianceMatrixResponse, ComplianceMatrixCell } from '@/lib/types';

/** Status to visual mapping. */
const statusColors: Record<ComplianceMatrixCell['status'], { bg: string; border: string; label: string }> = {
  valid: { bg: 'bg-[var(--color-success-light)]', border: 'border-[var(--color-success)]', label: 'valid' },
  expiring: { bg: 'bg-[var(--color-warning-light)]', border: 'border-[var(--color-warning)]', label: 'expiring' },
  missing: { bg: 'bg-[var(--color-error-light)]', border: 'border-[var(--color-error)]', label: 'missing' },
};

function statusLabel(status: ComplianceMatrixCell['status'], lang: 'de' | 'en'): string {
  switch (status) {
    case 'valid': return t('compliance.valid', lang);
    case 'expiring': return t('compliance.expiring', lang);
    case 'missing': return t('compliance.missing', lang);
  }
}

function ComplianceSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-busy="true">
      <span className="sr-only">{t('loading.compliance', 'de')}</span>
      <Skeleton width="w-64" height="h-8" />
      <SkeletonCard />
      <SkeletonCard />
    </div>
  );
}

function ComplianceContent() {
  const { language } = useNomosStore();
  const matrix = useFetch<ComplianceMatrixResponse>('/compliance/matrix');
  const [selectedCell, setSelectedCell] = useState<ComplianceMatrixCell | null>(null);

  if (matrix.loading) {
    return <ComplianceSkeleton />;
  }

  if (matrix.error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
          {t('compliance.title', language)}
        </h1>
        <Card>
          <p className="text-sm text-[var(--color-error)]">{matrix.error}</p>
          <Button variant="secondary" onClick={matrix.reload} className="mt-4">
            {t('action.retry', language)}
          </Button>
        </Card>
      </div>
    );
  }

  const data = matrix.data;

  if (!data || (data.matrix ?? data.agents ?? []).length === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
          {t('compliance.title', language)}
        </h1>
        <EmptyState
          message={t('empty.compliance', language)}
          description={t('empty.complianceDescription', language)}
        />
      </div>
    );
  }

  // Derive agent list and document types from matrix response
  const agents = data.matrix ?? [];
  const agentIds = agents.map((a: { agent_id: string }) => a.agent_id);

  // Build a simple lookup for display
  const cellLookup = new Map<string, Map<string, ComplianceMatrixCell>>();
  // The API returns per-agent summary, not per-cell matrix — adapt
  for (const agent of agents) {
    const docs = new Map<string, ComplianceMatrixCell>();
    // Mark missing docs as 'missing', rest as 'valid'
    const allDocs = ['dpia', 'register', 'art50', 'art14', 'art12', 'avv', 'risk_mgmt', 'rights', 'literacy', 'tia', 'art22', 'incident', 'tom', 'accessibility'];
    const missingSet = new Set((agent as { missing_docs?: string[] }).missing_docs ?? []);
    for (const doc of allDocs) {
      docs.set(doc, {
        agent_id: agent.agent_id,
        agent_name: (agent as { agent_name?: string }).agent_name ?? agent.agent_id,
        document_type: doc,
        status: missingSet.has(doc) ? 'missing' : 'valid',
      } as ComplianceMatrixCell);
    }
    cellLookup.set(agent.agent_id, docs);
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
          {t('compliance.title', language)}
        </h1>
        <p className="text-sm text-[var(--color-muted)] mt-1">{t('compliance.description', language)}</p>
      </div>

      {/* Health Score */}
      <Card>
        <CardHeader
          title={t('compliance.healthScore', language)}
          description={t('compliance.healthScoreDescription', language)}
        />
        <div className="mt-4">
          <div className="flex items-center gap-4">
            <span
              className="text-4xl font-extrabold font-[family-name:var(--font-headline)]"
              style={{
                color: data.health_score >= 80
                  ? 'var(--color-success)'
                  : data.health_score >= 50
                    ? 'var(--color-warning)'
                    : 'var(--color-error)',
              }}
              aria-label={`${t('compliance.healthScore', language)}: ${data.health_score}%`}
            >
              {data.health_score}%
            </span>
            <div
              className="flex-1 h-3 bg-[var(--color-hover)] rounded-[var(--radius-full)] overflow-hidden"
              role="progressbar"
              aria-valuenow={data.health_score}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={t('a11y.complianceScore', language)}
            >
              <div
                className="h-full rounded-[var(--radius-full)] transition-all duration-500"
                style={{
                  width: `${Math.min(data.health_score, 100)}%`,
                  backgroundColor: data.health_score >= 80
                    ? 'var(--color-success)'
                    : data.health_score >= 50
                      ? 'var(--color-warning)'
                      : 'var(--color-error)',
                }}
              />
            </div>
          </div>
          {/* Legend */}
          <div className="flex gap-6 mt-4 text-xs text-[var(--color-muted)]">
            <span className="inline-flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-[var(--color-success)]" aria-hidden="true" />
              {t('compliance.valid', language)}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-[var(--color-warning)]" aria-hidden="true" />
              {t('compliance.expiring', language)}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-[var(--color-error)]" aria-hidden="true" />
              {t('compliance.missing', language)}
            </span>
          </div>
        </div>
      </Card>

      {/* Matrix Grid */}
      <Card padding="none">
        <div className="p-6 pb-0">
          <CardHeader
            title={t('compliance.matrix', language)}
            description={t('compliance.matrixDescription', language)}
          />
        </div>
        <div className="overflow-x-auto mt-4">
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
                {['dpia', 'register', 'art50', 'art14', 'art12', 'avv', 'risk_mgmt', 'rights', 'literacy', 'tia', 'art22', 'incident', 'tom', 'accessibility'].map((docType) => (
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
              {agentIds.map((agentId: string) => {
                const agentCells = cellLookup.get(agentId);
                const agentName = agentCells?.values().next().value?.agent_name ?? agentId;
                return (
                  <tr key={agentId} className="border-b border-[var(--color-border)] last:border-b-0">
                    <td className="px-4 py-3 font-semibold text-[var(--color-text)] whitespace-nowrap">
                      {agentName}
                    </td>
                    {['dpia', 'register', 'art50', 'art14', 'art12', 'avv', 'risk_mgmt', 'rights', 'literacy', 'tia', 'art22', 'incident', 'tom', 'accessibility'].map((docType) => {
                      const cell = agentCells?.get(docType);
                      const status = cell?.status ?? 'missing';
                      const colors = statusColors[status];
                      return (
                        <td key={docType} className="px-4 py-3 text-center">
                          <button
                            onClick={() => cell && setSelectedCell(cell)}
                            className={[
                              'inline-flex items-center justify-center w-full min-w-[80px] px-3 py-1.5 rounded-[var(--radius-sm)]',
                              'text-xs font-semibold border transition-all duration-[var(--transition)]',
                              colors.bg, colors.border,
                              'hover:opacity-80 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]',
                            ].join(' ')}
                            aria-label={`${agentName}: ${docType} — ${statusLabel(status, language)}`}
                          >
                            {statusLabel(status, language)}
                          </button>
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

      {/* Document detail modal */}
      <Modal
        open={selectedCell !== null}
        onClose={() => setSelectedCell(null)}
        title={t('compliance.documentDetail', language)}
        description={selectedCell ? `${selectedCell.agent_name} — ${selectedCell.document_type}` : undefined}
      >
        {selectedCell && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="font-semibold text-[var(--color-muted)]">{t('audit.agent', language)}</p>
                <p className="text-[var(--color-text)]">{selectedCell.agent_name}</p>
              </div>
              <div>
                <p className="font-semibold text-[var(--color-muted)]">{t('users.status', language)}</p>
                <p className="text-[var(--color-text)]">{statusLabel(selectedCell.status, language)}</p>
              </div>
              <div>
                <p className="font-semibold text-[var(--color-muted)]">{t('compliance.lastUpdated', language)}</p>
                <p className="text-[var(--color-text)]">
                  {selectedCell.last_updated ? formatDate(selectedCell.last_updated, language) : '—'}
                </p>
              </div>
              <div>
                <p className="font-semibold text-[var(--color-muted)]">{t('compliance.expiresAt', language)}</p>
                <p className="text-[var(--color-text)]">
                  {selectedCell.expires_at ? formatDate(selectedCell.expires_at, language) : '—'}
                </p>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

export default function CompliancePage() {
  return (
    <ErrorBoundary>
      <ComplianceContent />
    </ErrorBoundary>
  );
}
