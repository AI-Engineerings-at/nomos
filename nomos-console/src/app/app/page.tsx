/**
 * NomOS — Meine Mitarbeiter (User Dashboard).
 * Simplified agent cards showing only assigned agents.
 * Chat + Pause buttons per agent. Open tasks count.
 * NO compliance, NO costs, NO settings — user-focused view.
 * Data from: GET /api/fleet, GET /api/tasks (filtered by user)
 *
 * 4 States: Loading (Skeleton), Empty (CTA), Error (ErrorBoundary), Data
 * WCAG 2.2 AA: focus-visible, aria-labels, keyboard nav
 * i18n: All text via translation keys
 */
'use client';

import { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useNomosStore } from '@/lib/store';
import { useAuth } from '@/lib/auth';
import { t } from '@/lib/i18n';
import { useFetch, getGreetingKey } from '@/lib/hooks';
import { api, ApiError } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { SkeletonBadge, Skeleton } from '@/components/ui/skeleton';
import type { FleetResponse, TaskListResponse, Agent } from '@/lib/types';
import { agentStatusToBadge } from '@/lib/types';

function UserDashboardSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-busy="true">
      <span className="sr-only">{t('loading.team', 'de')}</span>
      <Skeleton width="w-64" height="h-8" />
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
        <SkeletonBadge />
        <SkeletonBadge />
        <SkeletonBadge />
      </div>
    </div>
  );
}

/** Agent card for user view — simplified with chat + pause. */
function AgentCard({
  agent,
  taskCount,
  lang,
  onChat,
  onPause,
  onResume,
  pausing,
}: {
  agent: Agent;
  taskCount: number;
  lang: 'de' | 'en';
  onChat: () => void;
  onPause: () => void;
  onResume: () => void;
  pausing: boolean;
}) {
  const badgeStatus = agentStatusToBadge(agent.status);
  const isPaused = agent.status === 'paused';
  const canInteract = agent.status === 'running' || agent.status === 'paused';

  return (
    <Card hoverable>
      <div className="space-y-4">
        {/* Header: Avatar + Name + Status */}
        <div className="flex items-center gap-3">
          <div
            className="w-12 h-12 rounded-[var(--radius)] flex items-center justify-center text-white text-lg font-bold shrink-0"
            style={{ backgroundColor: 'var(--color-primary)' }}
            aria-hidden="true"
          >
            {agent.name.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-bold text-[var(--color-text)] truncate">{agent.name}</p>
            <p className="text-xs text-[var(--color-muted)] truncate">{agent.role}</p>
          </div>
          <Badge status={badgeStatus} />
        </div>

        {/* Open tasks count */}
        {taskCount > 0 && (
          <div className="flex items-center gap-2 text-xs text-[var(--color-muted)]">
            <svg className="w-3.5 h-3.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            <span>
              {taskCount} {t('empty.tasks', lang) === 'Keine offenen Aufgaben.' ? 'offene Aufgaben' : 'open tasks'}
            </span>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-2">
          <Button
            variant="primary"
            size="sm"
            onClick={onChat}
            disabled={!canInteract}
            className="flex-1"
            aria-label={`${t('profile.chat', lang)}: ${agent.name}`}
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            {t('profile.chat', lang)}
          </Button>
          <Button
            variant={isPaused ? 'secondary' : 'ghost'}
            size="sm"
            onClick={isPaused ? onResume : onPause}
            loading={pausing}
            disabled={!canInteract}
            aria-label={`${isPaused ? t('action.resume', lang) : t('action.pause', lang)}: ${agent.name}`}
          >
            {isPaused ? (
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            ) : (
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
          </Button>
        </div>
      </div>
    </Card>
  );
}

function UserDashboardContent() {
  const { language, addToast } = useNomosStore();
  const { user } = useAuth();
  const router = useRouter();
  const fleet = useFetch<FleetResponse>('/fleet');
  const tasks = useFetch<TaskListResponse>('/tasks');

  const handlePauseResume = useCallback(async (agentId: string, action: 'pause' | 'resume') => {
    try {
      await api.post(`/agents/${agentId}/${action}`);
      addToast({
        type: 'success',
        message: action === 'pause' ? t('toast.agentPaused', language) : t('toast.agentResumed', language),
        duration: 4000,
      });
      fleet.reload();
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : t('error.serverError', language);
      addToast({ type: 'error', message: msg, duration: 6000 });
    }
  }, [language, addToast, fleet]);

  if (fleet.loading) {
    return <UserDashboardSkeleton />;
  }

  const agents = fleet.data?.agents ?? [];
  const allTasks = tasks.data?.tasks ?? [];

  // Count open tasks per agent
  const taskCountByAgent = new Map<string, number>();
  for (const task of allTasks) {
    if (task.status !== 'done') {
      taskCountByAgent.set(task.agent_id, (taskCountByAgent.get(task.agent_id) ?? 0) + 1);
    }
  }

  const greetingKey = getGreetingKey();
  const greeting = t(greetingKey, language);
  const userName = user?.name.split(' ')[0] ?? '';

  return (
    <div className="space-y-6">
      {/* Greeting */}
      <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
        {greeting}, {userName}.
      </h1>

      {agents.length === 0 ? (
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
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              taskCount={taskCountByAgent.get(agent.id) ?? 0}
              lang={language}
              onChat={() => router.push(`/app/chat/${agent.id}`)}
              onPause={() => handlePauseResume(agent.id, 'pause')}
              onResume={() => handlePauseResume(agent.id, 'resume')}
              pausing={false}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function UserDashboardPage() {
  return (
    <ErrorBoundary>
      <UserDashboardContent />
    </ErrorBoundary>
  );
}
