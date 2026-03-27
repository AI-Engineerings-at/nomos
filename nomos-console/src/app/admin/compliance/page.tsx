/**
 * NomOS — Rechts-Check (Compliance Matrix) admin panel.
 * Per-agent compliance summary table showing status, missing docs, risk class.
 * Data from: GET /api/compliance/matrix
 *
 * 4 States: Loading (Skeleton), Empty (CTA), Error (ErrorBoundary), Data
 * WCAG 2.2 AA: focus-visible, aria-labels, keyboard nav
 * i18n: All text via translation keys
 */
'use client';

import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { useFetch } from '@/lib/hooks';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { SkeletonCard, Skeleton } from '@/components/ui/skeleton';
import type { ComplianceMatrixResponse, ComplianceMatrixEntry } from '@/lib/types';

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

  if (matrix.loading) return <ComplianceSkeleton />;

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
  if (!data || data.matrix.length === 0) {
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
          {t('compliance.title', language)}
        </h1>
        <p className="text-sm text-[var(--color-muted)] mt-1">{t('compliance.description', language)}</p>
      </div>

      <Card padding="none">
        <div className="overflow-x-auto">
          <table className="w-full text-sm" aria-label={t('a11y.complianceMatrix', language)}>
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                <th scope="col" className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-muted)]">
                  {t('audit.agent', language)}
                </th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-muted)]">
                  {t('users.status', language)}
                </th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-muted)]">
                  {t('compliance.missingDocs', language)}
                </th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[var(--color-muted)]">
                  {t('compliance.riskClass', language)}
                </th>
              </tr>
            </thead>
            <tbody>
              {data.matrix.map((entry: ComplianceMatrixEntry) => (
                <tr key={entry.agent_id} className="border-b border-[var(--color-border)] last:border-b-0">
                  <td className="px-4 py-3 font-semibold text-[var(--color-text)]">{entry.agent_name}</td>
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
