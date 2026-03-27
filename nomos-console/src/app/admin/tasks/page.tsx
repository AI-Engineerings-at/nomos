/**
 * NomOS — Aufgaben (Tasks) admin panel.
 * Task board with columns by status: queued, assigned, running, review, done.
 * Each task as card with agent, description, priority badge.
 * Status change via dropdown.
 * Data from: GET/PATCH /api/tasks
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
import { api, ApiError } from '@/lib/api';
import { Card, CardHeader } from '@/components/ui/card';
import { Badge, type BadgeStatus } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Modal } from '@/components/ui/modal';
import { EmptyState } from '@/components/ui/empty-state';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { SkeletonCard, Skeleton } from '@/components/ui/skeleton';
import type { TaskListResponse, TaskEntry, FleetResponse } from '@/lib/types';

const TASK_STATUSES: TaskEntry['status'][] = ['queued', 'assigned', 'running', 'review', 'done', 'failed'];

function TasksSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-busy="true">
      <span className="sr-only">{t('loading.tasks', 'de')}</span>
      <Skeleton width="w-64" height="h-8" />
      <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-5 gap-4">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    </div>
  );
}

function statusColumnLabel(status: TaskEntry['status'], lang: 'de' | 'en'): string {
  switch (status) {
    case 'queued': return t('tasks.queued', lang);
    case 'assigned': return t('tasks.assigned', lang);
    case 'running': return t('tasks.running', lang);
    case 'review': return t('tasks.review', lang);
    case 'done': return t('tasks.done', lang);
    case 'failed': return t('tasks.failed', lang);
  }
}

function priorityBadge(priority: TaskEntry['priority']): BadgeStatus {
  switch (priority) {
    case 'urgent': return 'error';
    case 'high': return 'error';
    case 'normal': return 'paused';
    case 'low': return 'online';
  }
}

function priorityLabel(priority: TaskEntry['priority'], lang: 'de' | 'en'): string {
  switch (priority) {
    case 'urgent': return t('tasks.priorityUrgent', lang);
    case 'high': return t('tasks.priorityHigh', lang);
    case 'normal': return t('tasks.priorityNormal', lang);
    case 'low': return t('tasks.priorityLow', lang);
  }
}

function statusColumnColor(status: TaskEntry['status']): string {
  switch (status) {
    case 'queued': return 'var(--color-muted)';
    case 'assigned': return 'var(--color-primary)';
    case 'running': return 'var(--color-warning)';
    case 'review': return 'var(--color-accent)';
    case 'done': return 'var(--color-success)';
    case 'failed': return 'var(--color-error)';
  }
}

/** Single task card within a column. */
function TaskCard({
  task,
  lang,
  onStatusChange,
}: {
  task: TaskEntry;
  lang: 'de' | 'en';
  onStatusChange: (taskId: string, newStatus: TaskEntry['status']) => void;
}) {
  return (
    <Card padding="sm" className="space-y-2">
      {/* Priority + Agent */}
      <div className="flex items-center justify-between gap-2">
        <Badge status={priorityBadge(task.priority)} label={priorityLabel(task.priority, lang)} />
        <span className="text-[10px] text-[var(--color-muted)] font-[family-name:var(--font-mono)] truncate">
          {task.agent_id}
        </span>
      </div>

      {/* Description */}
      <p className="text-sm font-semibold text-[var(--color-text)] line-clamp-2">{task.description}</p>

      {/* Timestamp */}
      <p className="text-[10px] text-[var(--color-muted)]">
        {formatDate(task.created_at, lang)}
      </p>

      {/* Status change dropdown */}
      {task.status !== 'done' && (
        <select
          className={[
            'w-full mt-1 text-xs px-2 py-1',
            'bg-[var(--color-card)] text-[var(--color-text)]',
            'border border-[var(--color-border)] rounded-[var(--radius-sm)]',
            'focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-[var(--color-focus-ring)]',
          ].join(' ')}
          value={task.status}
          onChange={(e) => onStatusChange(task.id, e.target.value as TaskEntry['status'])}
          aria-label={`${t('tasks.changeStatus', lang)}: ${task.description}`}
        >
          {TASK_STATUSES.map((s) => (
            <option key={s} value={s}>
              {statusColumnLabel(s, lang)}
            </option>
          ))}
        </select>
      )}
    </Card>
  );
}

interface CreateTaskForm {
  description: string;
  agent_id: string;
  priority: TaskEntry['priority'];
}

function TasksContent() {
  const { language, addToast } = useNomosStore();
  const tasksFetch = useFetch<TaskListResponse>('/tasks');
  const fleetFetch = useFetch<FleetResponse>('/fleet');
  const [showCreate, setShowCreate] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<CreateTaskForm>({
    description: '',
    agent_id: '',
    priority: 'normal',
  });

  // Group tasks by status
  const tasksByStatus = useMemo(() => {
    const groups: Record<TaskEntry['status'], TaskEntry[]> = {
      queued: [],
      assigned: [],
      running: [],
      review: [],
      done: [],
      failed: [],
    };
    for (const task of tasksFetch.data?.tasks ?? []) {
      groups[task.status].push(task);
    }
    return groups;
  }, [tasksFetch.data]);

  const handleStatusChange = useCallback(async (taskId: string, newStatus: TaskEntry['status']) => {
    try {
      await api.patch(`/tasks/${taskId}`, { status: newStatus });
      addToast({ type: 'success', message: t('toast.taskUpdated', language), duration: 3000 });
      tasksFetch.reload();
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : t('error.serverError', language);
      addToast({ type: 'error', message: msg, duration: 6000 });
    }
  }, [language, addToast, tasksFetch]);

  const handleCreate = useCallback(async () => {
    if (!form.description.trim()) return;
    setSaving(true);
    try {
      await api.post('/tasks', {
        description: form.description,
        agent_id: form.agent_id || undefined,
        priority: form.priority,
      });
      addToast({ type: 'success', message: t('toast.taskCreated', language), duration: 4000 });
      setShowCreate(false);
      setForm({ description: '', agent_id: '', priority: 'normal' });
      tasksFetch.reload();
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : t('error.serverError', language);
      addToast({ type: 'error', message: msg, duration: 6000 });
    } finally {
      setSaving(false);
    }
  }, [form, language, addToast, tasksFetch]);

  if (tasksFetch.loading) {
    return <TasksSkeleton />;
  }

  const totalTasks = tasksFetch.data?.tasks.length ?? 0;
  const agents = fleetFetch.data?.agents ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
            {t('tasks.title', language)}
          </h1>
          <p className="text-sm text-[var(--color-muted)] mt-1">{t('tasks.description', language)}</p>
        </div>
        <Button variant="primary" onClick={() => setShowCreate(true)} aria-label={t('tasks.createTask', language)}>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          {t('tasks.createTask', language)}
        </Button>
      </div>

      {totalTasks === 0 ? (
        <EmptyState
          message={t('tasks.noTasks', language)}
          description={t('tasks.noTasksDescription', language)}
          ctaLabel={t('tasks.createTask', language)}
          onCtaClick={() => setShowCreate(true)}
        />
      ) : (
        /* Kanban-style columns */
        <div
          className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-5 gap-4"
          aria-label={t('a11y.taskBoard', language)}
        >
          {TASK_STATUSES.map((status) => (
            <div key={status} className="space-y-3">
              {/* Column header */}
              <div className="flex items-center gap-2">
                <div
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: statusColumnColor(status) }}
                  aria-hidden="true"
                />
                <h3 className="text-sm font-bold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
                  {statusColumnLabel(status, language)}
                </h3>
                <span className="text-xs text-[var(--color-muted)] font-[family-name:var(--font-mono)]">
                  {tasksByStatus[status].length}
                </span>
              </div>

              {/* Task cards */}
              <div className="space-y-2" role="list" aria-label={statusColumnLabel(status, language)}>
                {tasksByStatus[status].map((task) => (
                  <div key={task.id} role="listitem">
                    <TaskCard task={task} lang={language} onStatusChange={handleStatusChange} />
                  </div>
                ))}
              </div>
            </div>
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
            <Button variant="primary" onClick={handleCreate} loading={saving} disabled={!form.description.trim()}>
              {t('action.create', language)}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label={t('tasks.taskDescription', language)}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            required
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
          <Select
            label={t('tasks.priority', language)}
            options={[
              { value: 'low', label: t('tasks.priorityLow', language) },
              { value: 'normal', label: t('tasks.priorityNormal', language) },
              { value: 'high', label: t('tasks.priorityHigh', language) },
              { value: 'urgent', label: t('tasks.priorityUrgent', language) },
            ]}
            value={form.priority}
            onChange={(e) => setForm({ ...form, priority: e.target.value as TaskEntry['priority'] })}
          />
        </div>
      </Modal>
    </div>
  );
}

export default function AdminTasksPage() {
  return (
    <ErrorBoundary>
      <TasksContent />
    </ErrorBoundary>
  );
}
