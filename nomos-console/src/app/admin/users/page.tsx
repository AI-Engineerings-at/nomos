/**
 * NomOS — Nutzer (Users) admin panel.
 * User list with role badges, create/edit modal, deactivate button.
 * Data from: GET/POST/PATCH/DELETE /api/users
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
import { Card, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Modal } from '@/components/ui/modal';
import { EmptyState } from '@/components/ui/empty-state';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { SkeletonCard, Skeleton } from '@/components/ui/skeleton';
import type { UserListResponse, UserAccount } from '@/lib/types';

function UsersSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-busy="true">
      <span className="sr-only">{t('loading.users', 'de')}</span>
      <Skeleton width="w-64" height="h-8" />
      <SkeletonCard />
      <SkeletonCard />
      <SkeletonCard />
    </div>
  );
}

function roleBadgeStatus(role: string): 'online' | 'paused' | 'deploying' {
  switch (role) {
    case 'admin': return 'online';
    case 'officer': return 'deploying';
    default: return 'paused';
  }
}

function roleLabel(role: string, lang: 'de' | 'en'): string {
  switch (role) {
    case 'admin': return t('users.roleAdmin', lang);
    case 'officer': return t('users.roleOfficer', lang);
    default: return t('users.roleUser', lang);
  }
}

interface UserFormData {
  name: string;
  email: string;
  password: string;
  role: 'admin' | 'user' | 'officer';
  max_tasks: number;
}

function UsersContent() {
  const { language, addToast } = useNomosStore();
  const usersFetch = useFetch<UserListResponse>('/users');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingUser, setEditingUser] = useState<UserAccount | null>(null);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState<UserFormData>({
    name: '',
    email: '',
    password: '',
    role: 'user',
    max_tasks: 10,
  });
  const [formErrors, setFormErrors] = useState<Partial<Record<keyof UserFormData, string>>>({});

  const resetForm = useCallback(() => {
    setFormData({ name: '', email: '', password: '', role: 'user', max_tasks: 10 });
    setFormErrors({});
  }, []);

  const openCreate = useCallback(() => {
    resetForm();
    setEditingUser(null);
    setShowCreateModal(true);
  }, [resetForm]);

  const openEdit = useCallback((user: UserAccount) => {
    setFormData({
      name: user.name,
      email: user.email,
      password: '',
      role: user.role,
      max_tasks: user.max_tasks,
    });
    setFormErrors({});
    setEditingUser(user);
    setShowCreateModal(true);
  }, []);

  const closeModal = useCallback(() => {
    setShowCreateModal(false);
    setEditingUser(null);
    resetForm();
  }, [resetForm]);

  const validateForm = useCallback((): boolean => {
    const errors: Partial<Record<keyof UserFormData, string>> = {};
    if (!formData.name.trim()) errors.name = t('error.validation', language);
    if (!formData.email.trim() || !formData.email.includes('@')) errors.email = t('error.validation', language);
    if (!editingUser && !formData.password.trim()) errors.password = t('error.validation', language);
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  }, [formData, editingUser, language]);

  const handleSave = useCallback(async () => {
    if (!validateForm()) return;
    setSaving(true);
    try {
      if (editingUser) {
        const body: Record<string, unknown> = {
          name: formData.name,
          email: formData.email,
          role: formData.role,
          max_tasks: formData.max_tasks,
        };
        if (formData.password.trim()) {
          body.password = formData.password;
        }
        await api.patch(`/users/${editingUser.id}`, body);
        addToast({ type: 'success', message: t('toast.userUpdated', language), duration: 4000 });
      } else {
        await api.post('/users', {
          name: formData.name,
          email: formData.email,
          password: formData.password,
          role: formData.role,
          max_tasks: formData.max_tasks,
        });
        addToast({ type: 'success', message: t('toast.userCreated', language), duration: 4000 });
      }
      closeModal();
      usersFetch.reload();
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : t('error.serverError', language);
      addToast({ type: 'error', message: msg, duration: 6000 });
    } finally {
      setSaving(false);
    }
  }, [validateForm, editingUser, formData, language, addToast, closeModal, usersFetch]);

  const handleToggleActive = useCallback(async (user: UserAccount) => {
    try {
      await api.patch(`/users/${user.id}`, { is_active: !user.is_active });
      addToast({
        type: 'success',
        message: user.is_active ? t('toast.userDeactivated', language) : t('toast.userActivated', language),
        duration: 4000,
      });
      usersFetch.reload();
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : t('error.serverError', language);
      addToast({ type: 'error', message: msg, duration: 6000 });
    }
  }, [language, addToast, usersFetch]);

  if (usersFetch.loading) {
    return <UsersSkeleton />;
  }

  const users = usersFetch.data?.users ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
            {t('users.title', language)}
          </h1>
          <p className="text-sm text-[var(--color-muted)] mt-1">{t('users.description', language)}</p>
        </div>
        <Button variant="primary" onClick={openCreate} aria-label={t('users.createUser', language)}>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          {t('users.createUser', language)}
        </Button>
      </div>

      {/* User list */}
      {users.length === 0 ? (
        <EmptyState
          message={t('users.noUsers', language)}
          description={t('users.noUsersDescription', language)}
          ctaLabel={t('users.createUser', language)}
          onCtaClick={openCreate}
        />
      ) : (
        <div className="space-y-3" role="list" aria-label={t('a11y.userManagement', language)}>
          {users.map((user) => (
            <Card key={user.id}>
              <div className="flex flex-col sm:flex-row sm:items-center gap-4" role="listitem">
                {/* Avatar */}
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-bold shrink-0"
                  style={{ backgroundColor: user.is_active ? 'var(--color-primary)' : 'var(--color-muted)' }}
                  aria-hidden="true"
                >
                  {(user.name ?? user.email ?? '?').charAt(0).toUpperCase()}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-[var(--color-text)]">{user.name ?? user.email}</span>
                    <Badge status={roleBadgeStatus(user.role)} label={roleLabel(user.role, language)} />
                    {!user.is_active && (
                      <Badge status="offline" label={t('users.inactive', language)} />
                    )}
                  </div>
                  <p className="text-xs text-[var(--color-muted)]">{user.email}</p>
                  <p className="text-xs text-[var(--color-muted)]">
                    {t('users.maxTasks', language)}: {user.max_tasks} | {t('users.createdAt', language)}: {formatDate(user.created_at, language)}
                  </p>
                </div>

                {/* Actions */}
                <div className="flex gap-2 shrink-0">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => openEdit(user)}
                    aria-label={`${t('action.edit', language)}: ${user.name ?? user.email}`}
                  >
                    {t('action.edit', language)}
                  </Button>
                  <Button
                    variant={user.is_active ? 'danger' : 'secondary'}
                    size="sm"
                    onClick={() => handleToggleActive(user)}
                    aria-label={`${user.is_active ? t('users.deactivate', language) : t('users.activate', language)}: ${user.name ?? user.email}`}
                  >
                    {user.is_active ? t('users.deactivate', language) : t('users.activate', language)}
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal
        open={showCreateModal}
        onClose={closeModal}
        title={editingUser ? t('users.editUser', language) : t('users.createUser', language)}
        footer={
          <>
            <Button variant="secondary" onClick={closeModal}>
              {t('action.cancel', language)}
            </Button>
            <Button variant="primary" onClick={handleSave} loading={saving}>
              {t('action.save', language)}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label={t('users.name', language)}
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            error={formErrors.name}
            required
          />
          <Input
            label={t('users.email', language)}
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            error={formErrors.email}
            required
          />
          <Input
            label={t('users.password', language)}
            type="password"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            error={formErrors.password}
            required={!editingUser}
            hint={editingUser ? (language === 'de' ? 'Leer lassen, um das Passwort nicht zu aendern' : 'Leave empty to keep current password') : undefined}
          />
          <Select
            label={t('users.role', language)}
            options={[
              { value: 'admin', label: t('users.roleAdmin', language) },
              { value: 'user', label: t('users.roleUser', language) },
              { value: 'officer', label: t('users.roleOfficer', language) },
            ]}
            value={formData.role}
            onChange={(e) => setFormData({ ...formData, role: e.target.value as UserFormData['role'] })}
          />
          <Input
            label={t('users.maxTasks', language)}
            type="number"
            value={String(formData.max_tasks)}
            onChange={(e) => setFormData({ ...formData, max_tasks: parseInt(e.target.value, 10) || 0 })}
          />
        </div>
      </Modal>
    </div>
  );
}

export default function UsersPage() {
  return (
    <ErrorBoundary>
      <UsersContent />
    </ErrorBoundary>
  );
}
