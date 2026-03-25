/**
 * NomOS Speech Settings — Configure TTS/STT behavior.
 * Source: Browser-native (default and only option for Schicht 1).
 * Speed: Slow (0.7) / Normal (1.0) / Fast (1.3).
 * Language follows app language.
 * Test button speaks a sample sentence.
 * Settings persisted via Zustand store to localStorage.
 *
 * WCAG 2.2 AA: focus-visible, keyboard nav, aria-labels.
 * i18n: All text via translation keys.
 */
'use client';

import { useCallback } from 'react';
import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { Card, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import * as tts from '@/lib/speech/tts';
import * as stt from '@/lib/speech/stt';

type SpeedPreset = 'slow' | 'normal' | 'fast';

const SPEED_MAP: Record<SpeedPreset, number> = {
  slow: 0.7,
  normal: 1.0,
  fast: 1.3,
};

function rateToPreset(rate: number): SpeedPreset {
  if (rate <= 0.75) return 'slow';
  if (rate >= 1.25) return 'fast';
  return 'normal';
}

export function SpeechSettings() {
  const { language, speechRate, setSpeechRate, speechEnabled, setSpeechEnabled } = useNomosStore();

  const currentPreset = rateToPreset(speechRate);
  const ttsSupported = typeof window !== 'undefined' && tts.isSupported();
  const sttSupported = typeof window !== 'undefined' && stt.isSupported();

  const handleTest = useCallback(() => {
    const testText = language === 'de'
      ? 'Hallo, ich bin NomOS.'
      : 'Hello, I am NomOS.';

    const lang = language === 'de' ? 'de-DE' : 'en-US';
    tts.speak(testText, { lang, rate: speechRate });
  }, [language, speechRate]);

  return (
    <Card className="space-y-6">
      <CardHeader
        title={t('speech.settings.title', language)}
        description={t('speech.settings.description', language)}
      />

      {/* Enable/Disable */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-[var(--color-text)]">
            {t('speech.settings.enabled', language)}
          </p>
          <p className="text-xs text-[var(--color-muted)] mt-0.5">
            {t('speech.settings.enabledDescription', language)}
          </p>
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={speechEnabled}
          aria-label={t('speech.settings.enabled', language)}
          onClick={() => setSpeechEnabled(!speechEnabled)}
          className={[
            'relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full',
            'transition-colors duration-200',
            'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]',
            speechEnabled ? 'bg-[var(--color-primary)]' : 'bg-[var(--color-border)]',
          ].join(' ')}
        >
          <span
            className={[
              'inline-block h-4 w-4 rounded-full bg-white shadow-sm transition-transform duration-200',
              speechEnabled ? 'translate-x-6' : 'translate-x-1',
            ].join(' ')}
            aria-hidden="true"
          />
        </button>
      </div>

      {/* Source (informational) */}
      <div>
        <p className="text-sm font-semibold text-[var(--color-text)]">
          {t('speech.settings.source', language)}
        </p>
        <p className="text-xs text-[var(--color-muted)] mt-1">
          {t('speech.settings.sourceBrowser', language)}
        </p>
        <div className="flex gap-2 mt-2">
          {ttsSupported && (
            <span className="inline-flex items-center gap-1 text-xs text-[var(--color-success)] font-medium">
              <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              TTS
            </span>
          )}
          {sttSupported && (
            <span className="inline-flex items-center gap-1 text-xs text-[var(--color-success)] font-medium">
              <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              STT
            </span>
          )}
          {!ttsSupported && !sttSupported && (
            <span className="text-xs text-[var(--color-error)] font-medium">
              {t('speech.settings.notSupported', language)}
            </span>
          )}
        </div>
      </div>

      {/* Speed selection */}
      <div className="space-y-2">
        <p className="text-sm font-semibold text-[var(--color-text)]">
          {t('speech.settings.speed', language)}
        </p>
        <div
          className="flex gap-2"
          role="radiogroup"
          aria-label={t('speech.settings.speed', language)}
        >
          {(['slow', 'normal', 'fast'] as SpeedPreset[]).map((preset) => {
            const speedKey = `speech.settings.speed.${preset}` as const;
            return (
              <button
                key={preset}
                type="button"
                role="radio"
                aria-checked={currentPreset === preset}
                onClick={() => setSpeechRate(SPEED_MAP[preset])}
                disabled={!speechEnabled}
                className={[
                  'flex-1 px-4 py-2 text-sm rounded-[var(--radius)] border-2 transition-all duration-[var(--transition)]',
                  'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]',
                  'disabled:opacity-50 disabled:cursor-not-allowed',
                  currentPreset === preset
                    ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)] text-[var(--color-primary)] font-semibold'
                    : 'border-[var(--color-border)] text-[var(--color-muted)] hover:border-[var(--color-muted)]',
                ].join(' ')}
              >
                {t(speedKey, language)}
              </button>
            );
          })}
        </div>
      </div>

      {/* Language info */}
      <div>
        <p className="text-sm font-semibold text-[var(--color-text)]">
          {t('speech.settings.language', language)}
        </p>
        <p className="text-xs text-[var(--color-muted)] mt-1">
          {t('speech.settings.languageFollows', language)}
        </p>
        <p className="text-sm text-[var(--color-text)] mt-1 font-medium">
          {language === 'de' ? 'Deutsch (DE)' : 'English (EN)'}
        </p>
      </div>

      {/* Test button */}
      <Button
        variant="secondary"
        size="sm"
        onClick={handleTest}
        disabled={!speechEnabled || !ttsSupported}
        aria-label={t('speech.settings.test', language)}
      >
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
        </svg>
        {t('speech.settings.test', language)}
      </Button>
    </Card>
  );
}
