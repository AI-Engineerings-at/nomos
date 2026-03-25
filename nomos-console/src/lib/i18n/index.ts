/**
 * NomOS i18n — Bilingual DE/EN translation system.
 * Default language: German (DE).
 * Language preference stored in localStorage.
 */
import { de, type TranslationKey } from './de';
import { en } from './en';

export type Language = 'de' | 'en';

const translations: Record<Language, Record<TranslationKey, string>> = { de, en };

/**
 * Returns the translated string for a given key in the specified language.
 * Falls back to German if the key is missing in the target language.
 * Falls back to the key itself if missing entirely (should never happen with strict types).
 */
export function t(key: TranslationKey, lang: Language): string {
  return translations[lang]?.[key] ?? translations.de[key] ?? key;
}

/**
 * Reads the stored language preference from localStorage.
 * Defaults to 'de' if nothing is stored or if running on the server.
 */
export function getStoredLanguage(): Language {
  if (typeof window === 'undefined') return 'de';
  const stored = localStorage.getItem('nomos-lang');
  if (stored === 'en') return 'en';
  return 'de';
}

/**
 * Stores the language preference in localStorage.
 */
export function setStoredLanguage(lang: Language): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('nomos-lang', lang);
  document.documentElement.lang = lang;
}

export type { TranslationKey };
