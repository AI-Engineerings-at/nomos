/**
 * NomOS SpeakButton — Reads adjacent text aloud using browser TTS.
 * Shows a pulsing speaker icon while speaking.
 * Second click stops playback.
 * Graceful degradation: hidden when TTS is not supported.
 * WCAG 2.2 AA: focus-visible, aria-label, keyboard accessible.
 * i18n: label adapts to current language.
 */
'use client';

import { useState, useEffect, useCallback } from 'react';
import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import * as tts from '@/lib/speech/tts';

interface SpeakButtonProps {
  /** The text that should be read aloud. */
  text: string;
  /** Optional extra CSS classes. */
  className?: string;
  /** Visual size variant. Defaults to 'sm'. */
  size?: 'sm' | 'md';
}

export function SpeakButton({ text, className = '', size = 'sm' }: SpeakButtonProps) {
  const { language, speechEnabled, speechRate } = useNomosStore();
  const [speaking, setSpeaking] = useState(false);
  const [supported, setSupported] = useState(false);

  useEffect(() => {
    setSupported(tts.isSupported());
  }, []);

  // Stop speech if component unmounts while speaking
  useEffect(() => {
    return () => {
      if (speaking) {
        tts.stop();
      }
    };
  }, [speaking]);

  const handleClick = useCallback(() => {
    if (speaking) {
      tts.stop();
      setSpeaking(false);
      return;
    }

    const lang = language === 'de' ? 'de-DE' : 'en-US';
    tts.speak(text, {
      lang,
      rate: speechRate,
      onStart: () => setSpeaking(true),
      onEnd: () => setSpeaking(false),
    });
  }, [speaking, text, language, speechRate]);

  // Do not render if TTS is not supported or speech is globally disabled
  if (!supported || !speechEnabled) {
    return null;
  }

  const iconSize = size === 'sm' ? 'w-4 h-4' : 'w-5 h-5';
  const padding = size === 'sm' ? 'p-1' : 'p-1.5';
  const ariaLabel = speaking
    ? (language === 'de' ? 'Vorlesen stoppen' : 'Stop reading')
    : t('speech.readAloud', language);

  return (
    <button
      type="button"
      onClick={handleClick}
      className={[
        padding,
        'rounded-[var(--radius-sm)] transition-colors',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]',
        speaking
          ? 'text-[var(--color-primary)] bg-[var(--color-primary-light)]'
          : 'text-[var(--color-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-card)]',
        className,
      ].join(' ')}
      aria-label={ariaLabel}
      aria-pressed={speaking}
    >
      <svg
        className={[iconSize, speaking ? 'animate-pulse' : ''].join(' ')}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
        />
      </svg>
    </button>
  );
}
