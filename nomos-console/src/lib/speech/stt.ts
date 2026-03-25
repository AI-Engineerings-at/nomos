/**
 * NomOS STT — Browser-native Speech-to-Text using SpeechRecognition API.
 * Graceful degradation: returns silently if the browser does not support STT.
 * Bilingual: supports 'de-DE' and 'en-US'.
 *
 * Note: SpeechRecognition is a webkit-prefixed API in most browsers.
 * We use the standard interface and the webkit prefix as fallback.
 */

/**
 * Minimal type declarations for the Web Speech API (recognition).
 * These are not yet part of the standard TypeScript DOM lib in all versions,
 * so we declare them locally to avoid type errors.
 */
interface NomSpeechRecognitionEvent extends Event {
  readonly results: {
    readonly length: number;
    [index: number]: {
      readonly isFinal: boolean;
      readonly length: number;
      [index: number]: { readonly transcript: string; readonly confidence: number };
    };
  };
}

interface NomSpeechRecognitionErrorEvent extends Event {
  readonly error: string;
  readonly message: string;
}

interface NomSpeechRecognition extends EventTarget {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  start(): void;
  stop(): void;
  abort(): void;
  addEventListener(type: 'result', listener: (event: NomSpeechRecognitionEvent) => void): void;
  addEventListener(type: 'error', listener: (event: NomSpeechRecognitionErrorEvent) => void): void;
  addEventListener(type: 'end', listener: () => void): void;
  addEventListener(type: string, listener: EventListenerOrEventListenerObject): void;
}

export interface STTOptions {
  lang: 'de-DE' | 'en-US';
  continuous: boolean;
  onResult: (text: string) => void;
  onError?: (error: string) => void;
}

/** Reference to the active recognition instance for stop(). */
let activeRecognition: NomSpeechRecognition | null = null;

/**
 * Returns the SpeechRecognition constructor if available, or null.
 * Handles the webkit prefix used by Chrome, Edge, and Safari.
 */
function getRecognitionConstructor(): (new () => NomSpeechRecognition) | null {
  if (typeof window === 'undefined') return null;

  const w = window as unknown as Record<string, unknown>;

  // Standard
  if ('SpeechRecognition' in window) {
    return w.SpeechRecognition as unknown as new () => NomSpeechRecognition;
  }

  // Webkit-prefixed (Chrome, Edge)
  if ('webkitSpeechRecognition' in window) {
    return w.webkitSpeechRecognition as unknown as new () => NomSpeechRecognition;
  }

  return null;
}

/**
 * Checks whether the browser supports the Web Speech API (recognition).
 * Safe to call on the server (returns false).
 */
export function isSupported(): boolean {
  return getRecognitionConstructor() !== null;
}

/**
 * Starts speech recognition. Calls `onResult` with each recognized text segment.
 * If `continuous` is false, recognition stops automatically after the first result.
 *
 * No-op if STT is not supported. Stops any already-active recognition first.
 */
export function startListening(options: STTOptions): void {
  const Ctor = getRecognitionConstructor();
  if (!Ctor) {
    options.onError?.('Speech recognition is not supported in this browser.');
    return;
  }

  // Stop any previous session
  stopListening();

  const recognition = new Ctor();
  recognition.lang = options.lang;
  recognition.continuous = options.continuous;
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.addEventListener('result', (event: NomSpeechRecognitionEvent) => {
    const last = event.results[event.results.length - 1];
    if (last?.isFinal) {
      const transcript = last[0]?.transcript ?? '';
      if (transcript) {
        options.onResult(transcript);
      }
    }
  });

  recognition.addEventListener('error', (event: NomSpeechRecognitionErrorEvent) => {
    // 'no-speech' and 'aborted' are expected when user stops manually
    if (event.error !== 'no-speech' && event.error !== 'aborted') {
      const errorMessages: Record<string, string> = {
        'not-allowed': 'Microphone access was denied. Please allow microphone access in your browser settings.',
        'network': 'A network error occurred during speech recognition.',
        'audio-capture': 'No microphone was found. Please connect a microphone and try again.',
        'service-not-allowed': 'Speech recognition service is not allowed.',
      };
      options.onError?.(errorMessages[event.error] ?? `Speech recognition error: ${event.error}`);
    }
    activeRecognition = null;
  });

  recognition.addEventListener('end', () => {
    activeRecognition = null;
  });

  activeRecognition = recognition;
  recognition.start();
}

/**
 * Stops the currently active speech recognition session.
 */
export function stopListening(): void {
  if (activeRecognition) {
    activeRecognition.stop();
    activeRecognition = null;
  }
}

/**
 * Returns true if speech recognition is currently active.
 */
export function isListening(): boolean {
  return activeRecognition !== null;
}
