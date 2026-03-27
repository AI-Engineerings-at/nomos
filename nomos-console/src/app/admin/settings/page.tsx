/**
 * NomOS — Einstellungen (Settings) admin panel.
 * Editable system config: Gateway URL, Retention days, PII filter mode, LLM API keys.
 * Reads via GET /api/settings, writes via PATCH /api/settings (admin-only).
 *
 * 4 States: Loading (Skeleton), Empty (CTA), Error (retry), Data
 * WCAG 2.2 AA: focus-visible, aria-labels, keyboard nav
 * i18n: All text via translation keys
 */
'use client';

import { useState } from 'react';
import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { useFetch } from '@/lib/hooks';
import { api, ApiError } from '@/lib/api';
import { Card, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { Skeleton } from '@/components/ui/skeleton';
import type { SystemSettings, SettingsUpdateRequest } from '@/lib/types';

function SettingsSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-busy="true">
      <span className="sr-only">{t('loading.settings', 'de')}</span>
      <Skeleton width="w-64" height="h-8" />
      <div className="space-y-4">
        <Skeleton width="w-full" height="h-20" />
        <Skeleton width="w-full" height="h-20" />
        <Skeleton width="w-full" height="h-20" />
        <Skeleton width="w-full" height="h-20" />
      </div>
    </div>
  );
}

/** Badge to indicate whether a secret key is configured. */
function KeyStatusBadge({ isSet, lang }: { isSet: boolean; lang: 'de' | 'en' }) {
  return isSet ? (
    <Badge status="online" label={t('settings.keyConfigured', lang)} className="shrink-0" />
  ) : (
    <Badge status="offline" label={t('settings.keyNotConfigured', lang)} className="shrink-0" />
  );
}

function SettingsContent() {
  const { language, addToast } = useNomosStore();
  const settingsFetch = useFetch<SystemSettings>('/settings');

  // Form state — null means "not changed by user"
  const [gatewayUrl, setGatewayUrl] = useState<string | null>(null);
  const [retentionDays, setRetentionDays] = useState<string | null>(null);
  const [piiFilterMode, setPiiFilterMode] = useState<string | null>(null);
  const [openaiKey, setOpenaiKey] = useState('');
  const [anthropicKey, setAnthropicKey] = useState('');
  const [nvidiaKey, setNvidiaKey] = useState('');
  const [saving, setSaving] = useState(false);

  if (settingsFetch.loading) {
    return <SettingsSkeleton />;
  }

  if (settingsFetch.error || !settingsFetch.data) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
          {t('settings.title', language)}
        </h1>
        <Card>
          <p className="text-sm text-[var(--color-error)]">
            {settingsFetch.error ?? t('error.serverError', language)}
          </p>
          <Button variant="secondary" onClick={settingsFetch.reload} className="mt-4">
            {t('action.retry', language)}
          </Button>
        </Card>
      </div>
    );
  }

  const config = settingsFetch.data;

  // Effective display values: user edits take precedence over fetched data
  const displayGatewayUrl = gatewayUrl ?? config.gateway_url;
  const displayRetentionDays = retentionDays ?? String(config.retention_days);
  const displayPiiMode = piiFilterMode ?? config.pii_filter_mode;

  const handleSave = async () => {
    setSaving(true);
    try {
      const updates: SettingsUpdateRequest = {};
      if (gatewayUrl !== null) updates.gateway_url = gatewayUrl;
      if (retentionDays !== null) {
        const days = parseInt(retentionDays, 10);
        if (!isNaN(days) && days > 0) updates.retention_days = days;
      }
      if (piiFilterMode !== null) updates.pii_filter_mode = piiFilterMode;
      if (openaiKey.trim()) updates.openai_api_key = openaiKey.trim();
      if (anthropicKey.trim()) updates.anthropic_api_key = anthropicKey.trim();
      if (nvidiaKey.trim()) updates.nvidia_api_key = nvidiaKey.trim();

      await api.patch<SystemSettings>('/settings', updates);

      // Clear key fields after successful save
      setOpenaiKey('');
      setAnthropicKey('');
      setNvidiaKey('');

      addToast({ type: 'success', message: t('toast.settingsSaved', language), duration: 4000 });
      settingsFetch.reload();
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : t('error.serverError', language);
      addToast({ type: 'error', message: msg, duration: 6000 });
    } finally {
      setSaving(false);
    }
  };

  const piiOptions = [
    { value: 'strict', label: t('settings.piiStrict', language) },
    { value: 'standard', label: t('settings.piiStandard', language) },
    { value: 'off', label: t('settings.piiOff', language) },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
          {t('settings.title', language)}
        </h1>
        <p className="text-sm text-[var(--color-muted)] mt-1">
          {t('settings.description', language)}
        </p>
      </div>

      {/* Connection section */}
      <Card>
        <CardHeader title={t('settings.section.gateway', language)} />
        <div className="mt-4">
          <Input
            label={t('settings.gatewayUrl', language)}
            value={displayGatewayUrl}
            onChange={(e) => setGatewayUrl(e.target.value)}
            placeholder="http://openclaw-gateway:18789"
            type="url"
          />
        </div>
      </Card>

      {/* Data management section */}
      <Card>
        <CardHeader title={t('settings.section.data', language)} />
        <div className="mt-4">
          <Input
            label={t('settings.retentionDays', language)}
            value={displayRetentionDays}
            onChange={(e) => setRetentionDays(e.target.value)}
            type="number"
            min={1}
          />
        </div>
      </Card>

      {/* Privacy section */}
      <Card>
        <CardHeader title={t('settings.section.privacy', language)} />
        <div className="mt-4">
          <Select
            label={t('settings.piiFilterMode', language)}
            value={displayPiiMode}
            onChange={(e) => setPiiFilterMode(e.target.value)}
            options={piiOptions}
          />
        </div>
      </Card>

      {/* LLM API Keys section */}
      <Card>
        <CardHeader title={t('settings.section.llmKeys', language)} />
        <div className="mt-4 space-y-6">
          {/* OpenAI */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-[var(--color-text)]">
                {t('settings.openaiKey', language)}
              </span>
              <KeyStatusBadge isSet={config.openai_api_key_set} lang={language} />
            </div>
            <Input
              label={t('settings.openaiKeyNew', language)}
              value={openaiKey}
              onChange={(e) => setOpenaiKey(e.target.value)}
              type="password"
              placeholder={config.openai_api_key_set ? '••••••••••••' : 'sk-...'}
              autoComplete="new-password"
            />
          </div>

          {/* Anthropic */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-[var(--color-text)]">
                {t('settings.anthropicKey', language)}
              </span>
              <KeyStatusBadge isSet={config.anthropic_api_key_set} lang={language} />
            </div>
            <Input
              label={t('settings.anthropicKeyNew', language)}
              value={anthropicKey}
              onChange={(e) => setAnthropicKey(e.target.value)}
              type="password"
              placeholder={config.anthropic_api_key_set ? '••••••••••••' : 'sk-ant-...'}
              autoComplete="new-password"
            />
          </div>

          {/* NVIDIA */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-[var(--color-text)]">
                {t('settings.nvidiaKey', language)}
              </span>
              <KeyStatusBadge isSet={config.nvidia_api_key_set} lang={language} />
            </div>
            <Input
              label={t('settings.nvidiaKeyNew', language)}
              value={nvidiaKey}
              onChange={(e) => setNvidiaKey(e.target.value)}
              type="password"
              placeholder={config.nvidia_api_key_set ? '••••••••••••' : 'nvapi-...'}
              autoComplete="new-password"
            />
          </div>
        </div>
      </Card>

      {/* Save button */}
      <div className="flex justify-end">
        <Button
          variant="primary"
          onClick={handleSave}
          disabled={saving}
          aria-busy={saving}
        >
          {saving ? t('settings.saving', language) : t('action.save', language)}
        </Button>
      </div>
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
