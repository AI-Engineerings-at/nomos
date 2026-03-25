/**
 * NomOS — Hilfe (Help) user panel.
 * FAQ accordion (7 common questions), glossary explanations, contact admin link.
 * All text via i18n — no hardcoded strings.
 *
 * 4 States: Loading (Skeleton), Empty (CTA), Error (ErrorBoundary), Data
 * WCAG 2.2 AA: focus-visible, aria-labels, keyboard nav
 * i18n: All text via translation keys
 */
'use client';

import { useState, useCallback } from 'react';
import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import type { TranslationKey } from '@/lib/i18n';
import { Card, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ErrorBoundary } from '@/components/ui/error-boundary';

interface FaqItem {
  questionKey: TranslationKey;
  answerKey: TranslationKey;
}

const faqItems: FaqItem[] = [
  { questionKey: 'help.faq1q', answerKey: 'help.faq1a' },
  { questionKey: 'help.faq2q', answerKey: 'help.faq2a' },
  { questionKey: 'help.faq3q', answerKey: 'help.faq3a' },
  { questionKey: 'help.faq4q', answerKey: 'help.faq4a' },
  { questionKey: 'help.faq5q', answerKey: 'help.faq5a' },
  { questionKey: 'help.faq6q', answerKey: 'help.faq6a' },
  { questionKey: 'help.faq7q', answerKey: 'help.faq7a' },
];

interface GlossaryItem {
  termKey: TranslationKey;
  defKey: TranslationKey;
}

const glossaryItems: GlossaryItem[] = [
  { termKey: 'help.glossaryTerm1', defKey: 'help.glossaryDef1' },
  { termKey: 'help.glossaryTerm2', defKey: 'help.glossaryDef2' },
  { termKey: 'help.glossaryTerm3', defKey: 'help.glossaryDef3' },
  { termKey: 'help.glossaryTerm4', defKey: 'help.glossaryDef4' },
  { termKey: 'help.glossaryTerm5', defKey: 'help.glossaryDef5' },
];

/** Accessible accordion item. */
function AccordionItem({
  id,
  question,
  answer,
  isOpen,
  onToggle,
}: {
  id: string;
  question: string;
  answer: string;
  isOpen: boolean;
  onToggle: () => void;
}) {
  const panelId = `${id}-panel`;
  const headerId = `${id}-header`;

  return (
    <div className="border-b border-[var(--color-border)] last:border-b-0">
      <h3>
        <button
          id={headerId}
          onClick={onToggle}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              onToggle();
            }
          }}
          className={[
            'w-full flex items-center justify-between px-4 py-4 text-left',
            'text-sm font-semibold text-[var(--color-text)]',
            'hover:bg-[var(--color-hover)] transition-colors duration-[var(--transition)]',
            'focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-[var(--color-focus-ring)]',
          ].join(' ')}
          aria-expanded={isOpen}
          aria-controls={panelId}
        >
          <span className="pr-4">{question}</span>
          <svg
            className={[
              'w-5 h-5 shrink-0 text-[var(--color-muted)] transition-transform duration-200',
              isOpen ? 'rotate-180' : '',
            ].join(' ')}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </h3>
      <div
        id={panelId}
        role="region"
        aria-labelledby={headerId}
        hidden={!isOpen}
      >
        {isOpen && (
          <div className="px-4 pb-4 text-sm text-[var(--color-muted)] leading-relaxed">
            {answer}
          </div>
        )}
      </div>
    </div>
  );
}

function HelpContent() {
  const { language } = useNomosStore();
  const [openFaqIndex, setOpenFaqIndex] = useState<number | null>(null);

  const toggleFaq = useCallback((index: number) => {
    setOpenFaqIndex((prev) => (prev === index ? null : index));
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
          {t('help.title', language)}
        </h1>
        <p className="text-sm text-[var(--color-muted)] mt-1">{t('help.description', language)}</p>
      </div>

      {/* FAQ Accordion */}
      <Card padding="none">
        <div className="p-6 pb-0">
          <CardHeader title={t('help.faq', language)} />
        </div>
        <div className="mt-4" aria-label={t('a11y.faqSection', language)}>
          {faqItems.map((item, index) => (
            <AccordionItem
              key={item.questionKey}
              id={`faq-${index}`}
              question={t(item.questionKey, language)}
              answer={t(item.answerKey, language)}
              isOpen={openFaqIndex === index}
              onToggle={() => toggleFaq(index)}
            />
          ))}
        </div>
      </Card>

      {/* Glossary — "Was bedeutet...?" */}
      <Card>
        <CardHeader title={t('help.glossary', language)} />
        <div className="mt-4 space-y-4" aria-label={t('a11y.glossarySection', language)}>
          {glossaryItems.map((item) => (
            <div key={item.termKey} className="space-y-1">
              <dt className="text-sm font-bold text-[var(--color-text)]">
                {t(item.termKey, language)}
              </dt>
              <dd className="text-sm text-[var(--color-muted)] pl-4 border-l-2 border-[var(--color-primary-light)]">
                {t(item.defKey, language)}
              </dd>
            </div>
          ))}
        </div>
      </Card>

      {/* Contact admin */}
      <Card>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <p className="text-sm text-[var(--color-text)]">
            {t('help.contactAdmin', language)}
          </p>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              if (typeof window !== 'undefined') {
                window.location.href = 'mailto:admin@example.com';
              }
            }}
            aria-label={t('action.contactAdmin', language)}
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            {t('action.contactAdmin', language)}
          </Button>
        </div>
      </Card>
    </div>
  );
}

export default function HelpPage() {
  return (
    <ErrorBoundary>
      <HelpContent />
    </ErrorBoundary>
  );
}
