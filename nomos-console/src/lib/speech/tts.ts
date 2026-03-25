/**
 * NomOS TTS — Browser-native Text-to-Speech using window.speechSynthesis.
 * Graceful degradation: returns silently if the browser does not support TTS.
 * Bilingual: supports 'de-DE' and 'en-US' voice selection.
 */

export interface TTSOptions {
  lang: 'de-DE' | 'en-US';
  rate: number; // 0.5 - 2.0, default 1.0
  onStart?: () => void;
  onEnd?: () => void;
}

/** Active utterance reference for stop(). */
let activeUtterance: SpeechSynthesisUtterance | null = null;

/**
 * Checks whether the browser supports the Web Speech API (synthesis).
 * Safe to call on the server (returns false).
 */
export function isSupported(): boolean {
  return (
    typeof window !== 'undefined' &&
    'speechSynthesis' in window &&
    typeof SpeechSynthesisUtterance !== 'undefined'
  );
}

/**
 * Returns available SpeechSynthesisVoice entries for a given language prefix.
 * Pass 'de' to match 'de-DE', 'de-AT', etc.
 * Returns an empty array if TTS is not supported.
 */
export function getVoices(lang: string): SpeechSynthesisVoice[] {
  if (!isSupported()) return [];
  return window.speechSynthesis
    .getVoices()
    .filter((v) => v.lang.startsWith(lang));
}

/**
 * Selects the best available voice for the given BCP 47 language tag.
 * Prefers a voice that matches the exact tag; falls back to any voice
 * whose language prefix matches; finally falls back to the default voice.
 */
function pickVoice(lang: 'de-DE' | 'en-US'): SpeechSynthesisVoice | null {
  const voices = window.speechSynthesis.getVoices();
  const prefix = lang.split('-')[0];

  // Exact match first
  const exact = voices.find((v) => v.lang === lang);
  if (exact) return exact;

  // Prefix match
  const prefixMatch = voices.find((v) => v.lang.startsWith(prefix));
  if (prefixMatch) return prefixMatch;

  // Default voice
  const defaultVoice = voices.find((v) => v.default);
  return defaultVoice ?? null;
}

/**
 * Speaks the given text using the Web Speech API.
 * Stops any currently playing utterance before starting.
 *
 * Clamps `rate` to the range [0.5, 2.0].
 * No-op when TTS is not supported.
 */
export function speak(text: string, options: TTSOptions): void {
  if (!isSupported()) return;

  // Stop anything currently playing
  stop();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = options.lang;
  utterance.rate = Math.max(0.5, Math.min(2.0, options.rate));

  const voice = pickVoice(options.lang);
  if (voice) {
    utterance.voice = voice;
  }

  if (options.onStart) {
    utterance.addEventListener('start', options.onStart);
  }

  const handleEnd = () => {
    activeUtterance = null;
    if (options.onEnd) options.onEnd();
  };

  utterance.addEventListener('end', handleEnd);
  utterance.addEventListener('error', handleEnd);

  activeUtterance = utterance;
  window.speechSynthesis.speak(utterance);
}

/**
 * Cancels any currently playing speech.
 */
export function stop(): void {
  if (!isSupported()) return;
  window.speechSynthesis.cancel();
  activeUtterance = null;
}

/**
 * Returns true if TTS is currently speaking.
 */
export function isSpeaking(): boolean {
  if (!isSupported()) return false;
  return window.speechSynthesis.speaking;
}
