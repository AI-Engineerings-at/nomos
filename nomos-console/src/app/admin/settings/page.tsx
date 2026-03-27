/**
 * NomOS — Einstellungen (Settings) admin panel.
 * Display system config: Gateway URL, Retention days, PII filter mode.
 * Read-only display of server-side configuration via GET /api/settings.
 *
 * 4 States: Loading (Skeleton), Empty (CTA), Error (retry), Data
 * WCAG 2.2 AA: focus-visible, aria-labels, keyboard nav
 * i18n: All text via translation keys
 */
'use client';

import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { useFetch } from '@/lib/hooks';
import { Card, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { Skeleton } from '@/components/ui/skeleton';
import type { SystemSettings } from '@/lib/types';

function SettingsSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-busy="true">
      <span className="sr-only">{t('loading.settings', 'de')}</span>
      <Skeleton width="w-64" height="h-8" />
      <div className="space-y-4">
        <Skeleton width="w-full" height="h-20" />
        <Skeleton width="w-full" height="h-20" />
        <Skeleton width="w-full" height="h-20" />
      </div>
    </div>
  );
}

function piiModeLabel(mode: SystemSettings['pii_filter_mode'], lang: 'de' | 'en'): string {
  switch (mode) {
    case 'strict': return t('settings.piiStrict', lang);
    case 'standard': return t('settings.piiStandard', lang);
    case 'off': return t('settings.piiOff', lang);
  }
}

function piiModeBadge(mode: SystemSettings['pii_filter_mode']): 'online' | 'paused' | 'error' {
  switch (mode) {
    case 'strict': return 'online';
    case 'standard': return 'paused';
    case 'off': return 'error';
  }
}

/** A single settings section with label + value. */
function SettingsField({
  label,
  value,
  badge,
}: {
  label: string;
  value: string;
  badge?: { status: 'online' | 'paused' | 'error'; label: string };
}) {
  return (
    <div className="flex items-start justify-between py-4 border-b border-[var(--color-border)] last:border-b-0">
      <div className="space-y-1 min-w-0 flex-1">
        <p className="text-sm font-semibold text-[var(--color-text)]">{label}</p>
        <p className="text-sm text-[var(--color-muted)] font-[family-name:var(--font-mono)] break-all">{value}</p>
      </div>
      {badge && (
        <Badge status={badge.status} label={badge.label} className="shrink-0 ml-4" />
      )}
    </div>
  );
}

function SettingsContent() {
  const { language } = useNomosStore();
  const settings = useFetch<SystemSettings>('/settings');

  if (settings.loading) {
    return <SettingsSkeleton />;
  }

  if (settings.error || !settings.data) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
          {t('settings.title', language)}
        </h1>
        <Card>
          <p className="text-sm text-[var(--color-error)]">{settings.error ?? t('error.serverError', language)}</p>
          <Button variant="secondary" onClick={settings.reload} className="mt-4">
            {t('action.retry', language)}
          </Button>
        </Card>
      </div>
    );
  }

  const config = settings.data;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
          {t('settings.title', language)}
        </h1>
        <p className="text-sm text-[var(--color-muted)] mt-1">{t('settings.description', language)}</p>
      </div>

      {/* Read-only notice */}
      <div
        className="flex items-center gap-3 px-4 py-3 bg-[var(--color-warning-light)] border border-[var(--color-warning)] rounded-[var(--radius)] text-sm text-[var(--color-text)]"
        role="status"
      >
        <svg className="w-5 h-5 text-[var(--color-warning)] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>{t('settings.readOnly', language)}</span>
      </div>

      {/* Connection section */}
      <Card>
        <CardHeader title={t('settings.section.gateway', language)} />
        <div className="mt-2">
          <SettingsField label={t('settings.gatewayUrl', language)} value={config.gateway_url} />
        </div>
      </Card>

      {/* Data management section */}
      <Card>
        <CardHeader title={t('settings.section.data', language)} />
        <div className="mt-2">
          <SettingsField
            label={t('settings.retentionDays', language)}
            value={`${config.retention_days} ${language === 'de' ? 'Tage' : 'days'}`}
          />
        </div>
      </Card>

      {/* Privacy section */}
      <Card>
        <CardHeader title={t('settings.section.privacy', language)} />
        <div className="mt-2">
          <SettingsField
            label={t('settings.piiFilterMode', language)}
            value={piiModeLabel(config.pii_filter_mode, language)}
            badge={{
              status: piiModeBadge(config.pii_filter_mode),
              label: config.pii_filter_mode.toUpperCase(),
            }}
          />
        </div>
      </Card>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <ErrorBoundary>
      <SettingsContent />
    </ErrorBoundary>
  );
}
