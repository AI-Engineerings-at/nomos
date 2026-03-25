/**
 * NomOS — Aufgaben (Tasks) user view.
 * User's tasks only. Simple list with status badges.
 * Limited create task button.
 * Data from: GET /api/tasks (filtered by user)
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
import { api, ApiError } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Badge, type BadgeStatus } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Modal } from '@/components/ui/modal';
import { EmptyState } from '@/components/ui/empty-state';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { SkeletonCard, Skeleton } from '@/components/ui/skeleton';
import type { TaskListResponse, TaskEntry, FleetResponse } from '@/lib/types';

function UserTasksSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-busy="true">
      <span className="sr-only">{t('loading.tasks', 'de')}</span>
      <Skeleton width="w-64" height="h-8" />
      <SkeletonCard />
      <SkeletonCard />
      <SkeletonCard />
    </div>
  );
}

function taskStatusBadge(status: TaskEntry['status']): BadgeStatus {
  switch (status) {
    case 'queued': return 'paused';
    case 'assigned': return 'deploying';
    case 'running': return 'online';
    case 'review': return 'paused';
    case 'done': return 'online';
  }
}

function taskStatusLabel(status: TaskEntry['status'], lang: 'de' | 'en'): string {
  switch (status) {
    case 'queued': return t('tasks.queued', lang);
    case 'assigned': return t('tasks.assigned', lang);
    case 'running': return t('tasks.running', lang);
    case 'review': return t('tasks.review', lang);
    case 'done': return t('tasks.done', lang);
  }
}

function priorityBadge(priority: TaskEntry['priority']): BadgeStatus {
  switch (priority) {
    case 'critical': return 'error';
    case 'high': return 'error';
    case 'medium': return 'paused';
    case 'low': return 'online';
  }
}

function priorityLabel(priority: TaskEntry['priority'], lang: 'de' | 'en'): string {
  switch (priority) {
    case 'critical': return t('tasks.priorityCritical', lang);
    case 'high': return t('tasks.priorityHigh', lang);
    case 'medium': return t('tasks.priorityMedium', lang);
    case 'low': return t('tasks.priorityLow', lang);
  }
}

function UserTasksContent() {
  const { language, addToast } = useNomosStore();
  const tasksFetch = useFetch<TaskListResponse>('/tasks');
  const fleetFetch = useFetch<FleetResponse>('/fleet');
  const [showCreate, setShowCreate] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ title: '', description: '', agent_id: '' });

  const handleCreate = useCallback(async () => {
    if (!form.title.trim()) return;
    setSaving(true);
    try {
      await api.post('/tasks', {
        title: form.title,
        description: form.description,
        agent_id: form.agent_id || undefined,
        priority: 'medium',
      });
      addToast({ type: 'success', message: t('toast.taskCreated', language), duration: 4000 });
      setShowCreate(false);
      setForm({ title: '', description: '', agent_id: '' });
      tasksFetch.reload();
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : t('error.serverError', language);
      addToast({ type: 'error', message: msg, duration: 6000 });
    } finally {
      setSaving(false);
    }
  }, [form, language, addToast, tasksFetch]);

  if (tasksFetch.loading) {
    return <UserTasksSkeleton />;
  }

  const tasks = tasksFetch.data?.tasks ?? [];
  const agents = fleetFetch.data?.agents ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
            {t('tasks.title', language)}
          </h1>
          <p className="text-sm text-[var(--color-muted)] mt-1">{t('tasks.userDescription', language)}</p>
        </div>
        <Button variant="primary" size="sm" onClick={() => setShowCreate(true)} aria-label={t('tasks.createTask', language)}>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          {t('tasks.createTask', language)}
        </Button>
      </div>

      {/* Task list */}
      {tasks.length === 0 ? (
        <EmptyState
          message={t('tasks.noTasks', language)}
          description={t('tasks.noTasksDescription', language)}
          ctaLabel={t('tasks.createTask', language)}
          onCtaClick={() => setShowCreate(true)}
        />
      ) : (
        <div className="space-y-3" role="list" aria-label={t('a11y.taskBoard', language)}>
          {tasks.map((task) => (
            <Card key={task.id}>
              <div className="flex flex-col sm:flex-row sm:items-center gap-3" role="listitem">
                {/* Status + Priority badges */}
                <div className="flex items-center gap-2 shrink-0">
                  <Badge status={taskStatusBadge(task.status)} label={taskStatusLabel(task.status, language)} />
                  <Badge status={priorityBadge(task.priority)} label={priorityLabel(task.priority, language)} />
                </div>

                {/* Title + description */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-[var(--color-text)] truncate">{task.title}</p>
                  {task.description && (
                    <p className="text-xs text-[var(--color-muted)] truncate">{task.description}</p>
                  )}
                </div>

                {/* Agent + date */}
                <div className="text-xs text-[var(--color-muted)] shrink-0 text-right space-y-0.5">
                  <p className="font-semibold">{task.agent_name}</p>
                  <p>{formatDate(task.created_at, language)}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create task modal */}
      <Modal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        title={t('tasks.createTask', language)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowCreate(false)}>
              {t('action.cancel', language)}
            </Button>
            <Button variant="primary" onClick={handleCreate} loading={saving} disabled={!form.title.trim()}>
              {t('action.create', language)}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label={t('tasks.taskTitle', language)}
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            required
          />
          <Input
            label={t('tasks.taskDescription', language)}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
          <Select
            label={t('tasks.taskAgent', language)}
            options={[
              { value: '', label: '—' },
              ...agents.map((a) => ({ value: a.id, label: a.name })),
            ]}
            value={form.agent_id}
            onChange={(e) => setForm({ ...form, agent_id: e.target.value })}
          />
        </div>
      </Modal>
    </div>
  );
}

export default function UserTasksPage() {
  return (
    <ErrorBoundary>
      <UserTasksContent />
    </ErrorBoundary>
  );
}
