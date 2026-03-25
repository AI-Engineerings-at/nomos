/**
 * NomOS MicButton — Speech-to-text input via browser SpeechRecognition.
 * Shows a pulsing red dot while listening.
 * Second click or recognized result stops listening.
 * Graceful degradation: hidden when STT is not supported.
 * WCAG 2.2 AA: focus-visible, aria-label, keyboard accessible.
 * i18n: label adapts to current language.
 */
'use client';

import { useState, useEffect, useCallback } from 'react';
import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import * as stt from '@/lib/speech/stt';

interface MicButtonProps {
  /** Called when speech is recognized. Consumer should fill the target input. */
  onResult: (text: string) => void;
  /** If true, keep listening after each result (push-to-talk style = false). */
  continuous?: boolean;
  /** Optional extra CSS classes. */
  className?: string;
  /** Visual size variant. Defaults to 'md'. */
  size?: 'sm' | 'md';
}

export function MicButton({ onResult, continuous = false, className = '', size = 'md' }: MicButtonProps) {
  const { language, speechEnabled } = useNomosStore();
  const [listening, setListening] = useState(false);
  const [supported, setSupported] = useState(false);

  useEffect(() => {
    setSupported(stt.isSupported());
  }, []);

  // Stop listening if component unmounts
  useEffect(() => {
    return () => {
      if (listening) {
        stt.stopListening();
      }
    };
  }, [listening]);

  const handleClick = useCallback(() => {
    if (listening) {
      stt.stopListening();
      setListening(false);
      return;
    }

    const lang = language === 'de' ? 'de-DE' : 'en-US';
    setListening(true);

    stt.startListening({
      lang,
      continuous,
      onResult: (text: string) => {
        onResult(text);
        if (!continuous) {
          setListening(false);
        }
      },
      onError: () => {
        setListening(false);
      },
    });
  }, [listening, language, continuous, onResult]);

  // Do not render if STT is not supported or speech is globally disabled
  if (!supported || !speechEnabled) {
    return null;
  }

  const iconSize = size === 'sm' ? 'w-4 h-4' : 'w-5 h-5';
  const padding = size === 'sm' ? 'p-1.5' : 'p-2';
  const ariaLabel = listening
    ? (language === 'de' ? 'Spracheingabe stoppen' : 'Stop voice input')
    : t('speech.voiceInput', language);

  return (
    <button
      type="button"
      onClick={handleClick}
      className={[
        padding,
        'rounded-[var(--radius)] transition-colors relative',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]',
        listening
          ? 'text-[var(--color-error)] bg-[var(--color-error-light)]'
          : 'text-[var(--color-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-hover)]',
        className,
      ].join(' ')}
      aria-label={ariaLabel}
      aria-pressed={listening}
    >
      {/* Pulsing red dot indicator when listening */}
      {listening && (
        <span
          className="absolute top-0.5 right-0.5 w-2.5 h-2.5 bg-[var(--color-error)] rounded-full animate-pulse"
          aria-hidden="true"
        />
      )}
      <svg
        className={iconSize}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
        />
      </svg>
    </button>
  );
}
