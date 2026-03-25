/**
 * NomOS — Vorfaelle (Incidents) admin panel.
 * Incident timeline with severity badges, 72h DSGVO countdown timer,
 * status flow: detected -> reported -> resolved, resolve button.
 * Data from: GET/PATCH /api/incidents
 *
 * 4 States: Loading (Skeleton), Empty (CTA), Error (ErrorBoundary), Data
 * WCAG 2.2 AA: focus-visible, aria-labels, keyboard nav
 * i18n: All text via translation keys
 */
'use client';

import { useState, useCallback, useEffect } from 'react';
import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { useFetch, formatDate } from '@/lib/hooks';
import { api, ApiError } from '@/lib/api';
import { Card, CardHeader } from '@/components/ui/card';
import { Badge, type BadgeStatus } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { SkeletonCard, Skeleton } from '@/components/ui/skeleton';
import type { IncidentListResponse, IncidentEntry } from '@/lib/types';

function IncidentsSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-busy="true">
      <span className="sr-only">{t('loading.incidents', 'de')}</span>
      <Skeleton width="w-64" height="h-8" />
      <SkeletonCard />
      <SkeletonCard />
      <SkeletonCard />
    </div>
  );
}

function severityBadge(severity: string): BadgeStatus {
  switch (severity.toLowerCase()) {
    case 'critical': return 'error';
    case 'high': return 'error';
    case 'medium': return 'paused';
    case 'low': return 'online';
    default: return 'paused';
  }
}

function severityLabel(severity: string, lang: 'de' | 'en'): string {
  switch (severity.toLowerCase()) {
    case 'critical': return t('incidents.severityCritical', lang);
    case 'high': return t('incidents.severityHigh', lang);
    case 'medium': return t('incidents.severityMedium', lang);
    case 'low': return t('incidents.severityLow', lang);
    default: return severity;
  }
}

function statusBadge(status: IncidentEntry['status']): BadgeStatus {
  switch (status) {
    case 'detected': return 'error';
    case 'reported': return 'paused';
    case 'resolved': return 'online';
  }
}

function statusLabel(status: IncidentEntry['status'], lang: 'de' | 'en'): string {
  switch (status) {
    case 'detected': return t('incidents.detected', lang);
    case 'reported': return t('incidents.reported', lang);
    case 'resolved': return t('incidents.resolved', lang);
  }
}

/** 72h DSGVO countdown timer. */
function DsgvoCountdown({ deadline, lang }: { deadline: string; lang: 'de' | 'en' }) {
  const [hoursLeft, setHoursLeft] = useState<number>(0);

  useEffect(() => {
    function calcHours() {
      const deadlineMs = new Date(deadline).getTime();
      const nowMs = Date.now();
      const diffHours = Math.max(0, (deadlineMs - nowMs) / (1000 * 60 * 60));
      setHoursLeft(Math.round(diffHours * 10) / 10);
    }
    calcHours();
    const interval = window.setInterval(calcHours, 60_000); // Update every minute
    return () => window.clearInterval(interval);
  }, [deadline]);

  const isExpired = hoursLeft <= 0;
  const isUrgent = hoursLeft > 0 && hoursLeft <= 24;

  const label = isExpired
    ? t('incidents.deadlineExpired', lang)
    : t('incidents.hoursRemaining', lang).replace('{hours}', String(hoursLeft));

  const bgColor = isExpired
    ? 'bg-[var(--color-error-light)]'
    : isUrgent
      ? 'bg-[var(--color-warning-light)]'
      : 'bg-[var(--color-hover)]';

  const textColor = isExpired
    ? 'text-[var(--color-error)]'
    : isUrgent
      ? 'text-[var(--color-warning)]'
      : 'text-[var(--color-muted)]';

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-[var(--radius-sm)] text-xs font-semibold ${bgColor} ${textColor}`}
      role="timer"
      aria-label={t('a11y.countdownTimer', lang)}
      aria-live="polite"
    >
      <svg className="w-3.5 h-3.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      {label}
    </div>
  );
}

/** Status flow visualization. */
function StatusFlow({ status }: { status: IncidentEntry['status'] }) {
  const steps: IncidentEntry['status'][] = ['detected', 'reported', 'resolved'];
  const currentIndex = steps.indexOf(status);

  return (
    <div className="flex items-center gap-1" aria-hidden="true">
      {steps.map((step, index) => (
        <div key={step} className="flex items-center gap-1">
          <div
            className={[
              'w-2 h-2 rounded-full transition-colors',
              index <= currentIndex ? 'bg-[var(--color-primary)]' : 'bg-[var(--color-border)]',
            ].join(' ')}
          />
          {index < steps.length - 1 && (
            <div
              className={[
                'w-4 h-0.5 transition-colors',
                index < currentIndex ? 'bg-[var(--color-primary)]' : 'bg-[var(--color-border)]',
              ].join(' ')}
            />
          )}
        </div>
      ))}
    </div>
  );
}

function IncidentCard({
  incident,
  lang,
  onResolve,
  resolving,
}: {
  incident: IncidentEntry;
  lang: 'de' | 'en';
  onResolve: () => void;
  resolving: boolean;
}) {
  const isResolvable = incident.status !== 'resolved';

  return (
    <Card>
      <div className="flex flex-col gap-4">
        {/* Header row */}
        <div className="flex items-start justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge status={severityBadge(incident.severity)} label={severityLabel(incident.severity, lang)} />
            <Badge status={statusBadge(incident.status)} label={statusLabel(incident.status, lang)} />
            <StatusFlow status={incident.status} />
          </div>
          <span className="text-xs text-[var(--color-muted)] shrink-0">
            {formatDate(incident.detected_at, lang)}
          </span>
        </div>

        {/* Description */}
        <div className="space-y-1">
          <p className="text-sm font-semibold text-[var(--color-text)]">{incident.incident_type}</p>
          <p className="text-sm text-[var(--color-muted)]">{incident.description}</p>
          <p className="text-xs text-[var(--color-muted)]">
            {t('audit.agent', lang)}: {incident.agent_id}
          </p>
        </div>

        {/* DSGVO deadline + actions */}
        <div className="flex items-center justify-between flex-wrap gap-2">
          {incident.status !== 'resolved' && (
            <DsgvoCountdown deadline={incident.report_deadline} lang={lang} />
          )}
          {isResolvable && (
            <Button
              variant="secondary"
              size="sm"
              onClick={onResolve}
              loading={resolving}
              aria-label={`${t('incidents.resolve', lang)}: ${incident.incident_type}`}
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              {t('incidents.resolve', lang)}
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}

function IncidentsContent() {
  const { language, addToast } = useNomosStore();
  const incidentsFetch = useFetch<IncidentListResponse>('/incidents');
  const [resolvingId, setResolvingId] = useState<number | null>(null);

  const handleResolve = useCallback(async (incident: IncidentEntry) => {
    setResolvingId(incident.id);
    try {
      await api.patch(`/incidents/${incident.id}`, { status: 'resolved' });
      addToast({
        type: 'success',
        message: t('toast.incidentResolved', language),
        duration: 4000,
      });
      incidentsFetch.reload();
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : t('error.serverError', language);
      addToast({ type: 'error', message: msg, duration: 6000 });
    } finally {
      setResolvingId(null);
    }
  }, [language, addToast, incidentsFetch]);

  if (incidentsFetch.loading) {
    return <IncidentsSkeleton />;
  }

  const incidents = incidentsFetch.data?.incidents ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
          {t('incidents.title', language)}
        </h1>
        <p className="text-sm text-[var(--color-muted)] mt-1">{t('incidents.description', language)}</p>
      </div>

      {/* Incidents timeline */}
      {incidents.length === 0 ? (
        <EmptyState
          message={t('incidents.noIncidents', language)}
          description={t('incidents.noIncidentsDescription', language)}
        />
      ) : (
        <div className="space-y-4" role="list" aria-label={t('a11y.incidentTimeline', language)}>
          {incidents.map((incident) => (
            <div key={incident.id} role="listitem">
              <IncidentCard
                incident={incident}
                lang={language}
                onResolve={() => handleResolve(incident)}
                resolving={resolvingId === incident.id}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function IncidentsPage() {
  return (
    <ErrorBoundary>
      <IncidentsContent />
    </ErrorBoundary>
  );
}
