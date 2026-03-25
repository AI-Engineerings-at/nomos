/**
 * NomOS — Freigaben (Approvals) panel.
 * Approval queue with pending/history tabs.
 * Each card: agent name, action type, description, time, approve/reject buttons.
 * Data from: GET /api/approvals, POST /api/approvals/{id}/approve, POST /api/approvals/{id}/reject
 *
 * 4 States: Loading (Skeleton), Empty (CTA), Error (ErrorBoundary), Data
 * WCAG 2.2 AA: focus-visible, aria-labels, keyboard nav
 * i18n: All text via translation keys
 */
'use client';

import { useState, useCallback } from 'react';
import { useNomosStore } from '@/lib/store';
import { useAuth } from '@/lib/auth';
import { t } from '@/lib/i18n';
import { useFetch, formatDate } from '@/lib/hooks';
import { api, ApiError } from '@/lib/api';
import { Card, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { SkeletonCard } from '@/components/ui/skeleton';
import type { ApprovalListResponse, ApprovalEntry } from '@/lib/types';

type ApprovalTab = 'pending' | 'history';

function ApprovalSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-busy="true">
      <span className="sr-only">Wird geladen...</span>
      <div className="space-y-2">
        <div className="h-7 w-40 skeleton-shimmer rounded-[var(--radius-sm)]" />
        <div className="h-4 w-72 skeleton-shimmer rounded-[var(--radius-sm)]" />
      </div>
      <div className="space-y-4">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    </div>
  );
}

function ApprovalCard({
  approval,
  onApprove,
  onReject,
  approving,
  rejecting,
  lang,
}: {
  approval: ApprovalEntry;
  onApprove: () => void;
  onReject: () => void;
  approving: boolean;
  rejecting: boolean;
  lang: 'de' | 'en';
}) {
  const isPending = approval.status === 'pending';

  return (
    <Card>
      <div className="flex flex-col sm:flex-row sm:items-start gap-4">
        <div className="flex-1 min-w-0 space-y-2">
          {/* Agent name + Action type */}
          <div className="flex items-center gap-2 flex-wrap">
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0"
              style={{ backgroundColor: 'var(--color-primary)' }}
              aria-hidden="true"
            >
              {approval.agent_id.charAt(0).toUpperCase()}
            </div>
            <div>
              <p className="text-sm font-semibold text-[var(--color-text)]">{approval.agent_id}</p>
              <p className="text-xs text-[var(--color-muted)]">{approval.action}</p>
            </div>
          </div>

          {/* Description */}
          <p className="text-sm text-[var(--color-text)]">{approval.description}</p>

          {/* Metadata */}
          <div className="flex items-center gap-4 text-xs text-[var(--color-muted)]">
            <span>{t('approvals.requestedAt', lang)}: {formatDate(approval.requested_at, lang)}</span>
            {approval.resolved_at && (
              <span>{t('approvals.decidedAt', lang)}: {formatDate(approval.resolved_at, lang)}</span>
            )}
            {approval.resolved_by && (
              <span>{t('approvals.decidedBy', lang)}: {approval.resolved_by}</span>
            )}
          </div>

          {/* Status badge for history entries */}
          {!isPending && (
            <Badge
              status={approval.status === 'approved' ? 'online' : 'offline'}
              label={approval.status === 'approved' ? t('approvals.approved', lang) : t('approvals.rejected', lang)}
            />
          )}
        </div>

        {/* Approve/Reject buttons — only for pending */}
        {isPending && (
          <div className="flex gap-2 shrink-0" aria-label={t('a11y.approvalActions', lang)}>
            <Button
              variant="primary"
              size="sm"
              onClick={onApprove}
              loading={approving}
              disabled={rejecting}
              aria-label={`${t('action.approve', lang)}: ${approval.description}`}
              className="bg-[var(--color-success)] hover:bg-[#0D9668]"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              {t('action.approve', lang)}
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={onReject}
              loading={rejecting}
              disabled={approving}
              aria-label={`${t('action.reject', lang)}: ${approval.description}`}
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
              {t('action.reject', lang)}
            </Button>
          </div>
        )}
      </div>
    </Card>
  );
}

function ApprovalsContent() {
  const { language, addToast } = useNomosStore();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<ApprovalTab>('pending');
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);
  const [actionType, setActionType] = useState<'approve' | 'reject' | null>(null);

  const approvalsFetch = useFetch<ApprovalListResponse>('/approvals');

  const handleAction = useCallback(async (id: string, action: 'approve' | 'reject') => {
    setActionInProgress(id);
    setActionType(action);

    try {
      const endpoint = `/approvals/${id}/${action}`;
      await api.post(endpoint, {
        resolved_by: user?.email ?? 'admin',
      });

      addToast({
        type: 'success',
        message: action === 'approve' ? t('toast.approved', language) : t('toast.rejected', language),
        duration: 4000,
      });

      approvalsFetch.reload();
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : t('error.serverError', language);
      addToast({ type: 'error', message: msg, duration: 6000 });
    } finally {
      setActionInProgress(null);
      setActionType(null);
    }
  }, [user, language, addToast, approvalsFetch]);

  if (approvalsFetch.loading) {
    return <ApprovalSkeleton />;
  }

  const allApprovals = approvalsFetch.data?.approvals ?? [];
  const pendingApprovals = allApprovals.filter((a) => a.status === 'pending');
  const historyApprovals = allApprovals.filter((a) => a.status !== 'pending');
  const displayApprovals = activeTab === 'pending' ? pendingApprovals : historyApprovals;

  const tabs: { key: ApprovalTab; label: string; count?: number }[] = [
    { key: 'pending', label: t('approvals.pending', language), count: pendingApprovals.length },
    { key: 'history', label: t('approvals.history', language) },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
          {t('approvals.title', language)}
        </h1>
        <p className="text-sm text-[var(--color-muted)] mt-1">{t('approvals.description', language)}</p>
      </div>

      {/* Tabs */}
      <div
        className="flex gap-1 border-b border-[var(--color-border)]"
        role="tablist"
        aria-label={t('approvals.title', language)}
      >
        {tabs.map((tab) => (
          <button
            key={tab.key}
            role="tab"
            id={`tab-${tab.key}`}
            aria-selected={activeTab === tab.key}
            aria-controls={`tabpanel-${tab.key}`}
            onClick={() => setActiveTab(tab.key)}
            className={[
              'px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors duration-[var(--transition)]',
              'focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-[var(--color-focus-ring)]',
              'border-b-2 -mb-[1px] inline-flex items-center gap-2',
              activeTab === tab.key
                ? 'border-[var(--color-primary)] text-[var(--color-primary)]'
                : 'border-transparent text-[var(--color-muted)] hover:text-[var(--color-text)] hover:border-[var(--color-border)]',
            ].join(' ')}
          >
            {tab.label}
            {tab.count !== undefined && tab.count > 0 && (
              <span
                className="inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 text-xs font-bold rounded-[var(--radius-full)] bg-[var(--color-primary)] text-white"
                aria-label={`${tab.count}`}
              >
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab panel */}
      <div
        id={`tabpanel-${activeTab}`}
        role="tabpanel"
        aria-labelledby={`tab-${activeTab}`}
      >
        {displayApprovals.length === 0 ? (
          <EmptyState
            message={t('empty.approvals', language)}
            description={t('empty.approvalsDescription', language)}
          />
        ) : (
          <div className="space-y-4" role="list" aria-label={activeTab === 'pending' ? t('approvals.pending', language) : t('approvals.history', language)}>
            {displayApprovals.map((approval) => (
              <div key={approval.id} role="listitem">
                <ApprovalCard
                  approval={approval}
                  onApprove={() => handleAction(approval.id, 'approve')}
                  onReject={() => handleAction(approval.id, 'reject')}
                  approving={actionInProgress === approval.id && actionType === 'approve'}
                  rejecting={actionInProgress === approval.id && actionType === 'reject'}
                  lang={language}
                />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function ApprovalsPage() {
  return (
    <ErrorBoundary>
      <ApprovalsContent />
    </ErrorBoundary>
  );
}
