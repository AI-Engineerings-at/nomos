/**
 * NomOS User Dashboard — Shows assigned agents and quick actions.
 */
'use client';

import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { Card, CardHeader } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';

export default function UserDashboardPage() {
  const { language } = useNomosStore();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
        {t('nav.myAgents', language)}
      </h1>

      <Card>
        <CardHeader
          title={t('nav.myAgents', language)}
          description={
            language === 'de'
              ? 'Ihre zugewiesenen KI-Mitarbeiter'
              : 'Your assigned AI employees'
          }
        />
        <div className="mt-4">
          <EmptyState
            message={
              language === 'de'
                ? 'Ihnen wurden noch keine Mitarbeiter zugewiesen.'
                : 'No employees have been assigned to you yet.'
            }
            description={
              language === 'de'
                ? 'Kontaktieren Sie Ihren Administrator, um KI-Mitarbeiter zugewiesen zu bekommen.'
                : 'Contact your administrator to get AI employees assigned.'
            }
          />
        </div>
      </Card>
    </div>
  );
}
