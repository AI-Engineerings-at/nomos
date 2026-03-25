/**
 * NomOS Admin Dashboard — Overview page.
 * Shows team summary, compliance status, costs, and health.
 */
'use client';

import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { Card, CardHeader } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';
import { useRouter } from 'next/navigation';

export default function AdminDashboardPage() {
  const { language } = useNomosStore();
  const router = useRouter();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
        {t('nav.dashboard', language)}
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {/* Team overview card */}
        <Card>
          <CardHeader
            title={t('nav.myTeam', language)}
            description={
              language === 'de'
                ? 'Ihre KI-Mitarbeiter auf einen Blick'
                : 'Your AI employees at a glance'
            }
          />
          <div className="mt-4">
            <EmptyState
              message={t('empty.team', language)}
              description={
                language === 'de'
                  ? 'Stellen Sie Ihren ersten KI-Mitarbeiter ein, um loszulegen.'
                  : 'Hire your first AI employee to get started.'
              }
              ctaLabel={t('empty.teamCta', language)}
              onCtaClick={() => router.push('/admin/hire')}
            />
          </div>
        </Card>

        {/* Compliance card */}
        <Card>
          <CardHeader
            title={t('nav.compliance', language)}
            description={
              language === 'de'
                ? 'EU AI Act & DSGVO Status'
                : 'EU AI Act & GDPR Status'
            }
          />
          <div className="mt-4">
            <EmptyState
              message={
                language === 'de'
                  ? 'Noch keine Compliance-Daten.'
                  : 'No compliance data yet.'
              }
              description={
                language === 'de'
                  ? 'Compliance-Berichte werden erstellt, sobald Sie Mitarbeiter einstellen.'
                  : 'Compliance reports will be generated once you hire employees.'
              }
            />
          </div>
        </Card>

        {/* Costs card */}
        <Card>
          <CardHeader
            title={t('nav.costs', language)}
            description={
              language === 'de'
                ? 'Monatliche Kosten Ihrer KI-Mitarbeiter'
                : 'Monthly costs of your AI employees'
            }
          />
          <div className="mt-4">
            <EmptyState
              message={
                language === 'de'
                  ? 'Noch keine Kostendaten.'
                  : 'No cost data yet.'
              }
            />
          </div>
        </Card>
      </div>
    </div>
  );
}
