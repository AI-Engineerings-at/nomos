/**
 * NomOS Compliance Dashboard — Read-only compliance reports for officers.
 */
'use client';

import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { Card, CardHeader } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';

export default function ComplianceDashboardPage() {
  const { language } = useNomosStore();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
        {t('nav.complianceReports', language)}
      </h1>

      <Card>
        <CardHeader
          title={t('nav.complianceReports', language)}
          description={
            language === 'de'
              ? 'EU AI Act & DSGVO Compliance-Status aller Mitarbeiter'
              : 'EU AI Act & GDPR compliance status of all employees'
          }
        />
        <div className="mt-4">
          <EmptyState
            message={t('empty.audit', language)}
            description={
              language === 'de'
                ? 'Compliance-Berichte werden erstellt, sobald Mitarbeiter eingestellt werden.'
                : 'Compliance reports will be generated once employees are hired.'
            }
          />
        </div>
      </Card>
    </div>
  );
}
