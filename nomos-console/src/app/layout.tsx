/**
 * NomOS Root Layout — Providers, fonts, theme initialization.
 * Sets lang="de" by default. Loads Montserrat, Geist Sans, Geist Mono.
 */
import type { Metadata, Viewport } from 'next';
import '@fontsource/montserrat/400.css';
import '@fontsource/montserrat/600.css';
import '@fontsource/montserrat/700.css';
import '@fontsource/montserrat/800.css';
import '@fontsource/geist-sans/400.css';
import '@fontsource/geist-sans/500.css';
import '@fontsource/geist-sans/600.css';
import '@fontsource/geist-mono/400.css';
import '@fontsource/geist-mono/500.css';
import '@/styles/globals.css';
import { Providers } from './providers';
import { ThemeScript } from './theme-script';

export const metadata: Metadata = {
  title: 'NomOS — Ihr Team im Griff',
  description: 'Compliance Control Plane fuer Ihre KI-Mitarbeiter. EU AI Act & DSGVO konform.',
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#FAFAFA' },
    { media: '(prefers-color-scheme: dark)', color: '#0B0C0F' },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de" suppressHydrationWarning>
      <head>
        <ThemeScript />
      </head>
      <body className="min-h-screen bg-[var(--color-bg)] text-[var(--color-text)] antialiased">
        {/* Skip to content — WCAG 2.2 AA requirement */}
        <a href="#main-content" className="skip-to-content">
          Zum Hauptinhalt springen
        </a>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
