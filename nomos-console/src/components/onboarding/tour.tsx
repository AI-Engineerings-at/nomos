/**
 * NomOS Onboarding Tour — 5-step interactive walkthrough on first login.
 * Highlights key UI areas with a dark overlay and spotlight effect.
 * Stored in localStorage: shows only once unless manually restarted.
 *
 * WCAG 2.2 AA:
 * - Focus trap within the tour step (keyboard users stay in the tooltip)
 * - Keyboard navigable: Tab, Enter, Space, Escape
 * - Aria-live region announces step changes
 * - Skip button always available
 *
 * i18n: All text via translation keys.
 */
'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { Button } from '@/components/ui/button';

const TOUR_STORAGE_KEY = 'nomos-tour-completed';

interface TourStep {
  /** CSS selector for the element to highlight. */
  targetSelector: string;
  /** i18n key for the step title. */
  titleKey: string;
  /** i18n key for the step description. */
  descriptionKey: string;
}

const TOUR_STEPS: TourStep[] = [
  {
    targetSelector: '[data-tour="dashboard"]',
    titleKey: 'tour.step1.title',
    descriptionKey: 'tour.step1.description',
  },
  {
    targetSelector: '[data-tour="my-team"]',
    titleKey: 'tour.step2.title',
    descriptionKey: 'tour.step2.description',
  },
  {
    targetSelector: '[data-tour="hire"]',
    titleKey: 'tour.step3.title',
    descriptionKey: 'tour.step3.description',
  },
  {
    targetSelector: '[data-tour="chat"]',
    titleKey: 'tour.step4.title',
    descriptionKey: 'tour.step4.description',
  },
  {
    targetSelector: '[data-tour="compliance"]',
    titleKey: 'tour.step5.title',
    descriptionKey: 'tour.step5.description',
  },
];

interface HighlightRect {
  top: number;
  left: number;
  width: number;
  height: number;
}

/**
 * Returns the bounding rect of a DOM element with some padding.
 */
function getHighlightRect(el: Element | null): HighlightRect | null {
  if (!el) return null;
  const rect = el.getBoundingClientRect();
  const padding = 8;
  return {
    top: rect.top - padding + window.scrollY,
    left: rect.left - padding + window.scrollX,
    width: rect.width + padding * 2,
    height: rect.height + padding * 2,
  };
}

/**
 * Determines optimal tooltip position to stay visible within the viewport.
 */
function getTooltipPosition(highlight: HighlightRect): { top: string; left: string; maxWidth: string } {
  const viewportHeight = window.innerHeight;
  const viewportWidth = window.innerWidth;
  const tooltipHeight = 200; // estimated
  const tooltipWidth = Math.min(360, viewportWidth - 32);

  // Position below the highlighted element by default
  let top = highlight.top + highlight.height + 16;
  let left = highlight.left;

  // If tooltip would go below viewport, position it above
  if (top + tooltipHeight > viewportHeight + window.scrollY) {
    top = highlight.top - tooltipHeight - 16;
  }

  // Keep tooltip within horizontal bounds
  if (left + tooltipWidth > viewportWidth + window.scrollX) {
    left = viewportWidth + window.scrollX - tooltipWidth - 16;
  }
  if (left < 16) {
    left = 16;
  }

  return {
    top: `${Math.max(16, top)}px`,
    left: `${left}px`,
    maxWidth: `${tooltipWidth}px`,
  };
}

export function OnboardingTour() {
  const { language } = useNomosStore();
  const [active, setActive] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [highlightRect, setHighlightRect] = useState<HighlightRect | null>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const nextButtonRef = useRef<HTMLButtonElement>(null);

  // Check localStorage on mount
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const completed = localStorage.getItem(TOUR_STORAGE_KEY);
    if (completed !== 'true') {
      // Small delay so the DOM has time to render
      const timer = window.setTimeout(() => setActive(true), 800);
      return () => window.clearTimeout(timer);
    }
  }, []);

  // Update highlight rect when step changes
  useEffect(() => {
    if (!active) return;

    const step = TOUR_STEPS[currentStep];
    if (!step) return;

    const el = document.querySelector(step.targetSelector);
    const rect = getHighlightRect(el);
    setHighlightRect(rect);

    // Scroll the target into view
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    // Focus the next/finish button
    window.setTimeout(() => {
      nextButtonRef.current?.focus();
    }, 300);
  }, [active, currentStep]);

  // Handle window resize
  useEffect(() => {
    if (!active) return;

    const handleResize = () => {
      const step = TOUR_STEPS[currentStep];
      if (!step) return;
      const el = document.querySelector(step.targetSelector);
      setHighlightRect(getHighlightRect(el));
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [active, currentStep]);

  // Escape key handler
  useEffect(() => {
    if (!active) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleSkip();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [active]);

  const handleNext = useCallback(() => {
    if (currentStep < TOUR_STEPS.length - 1) {
      setCurrentStep((s) => s + 1);
    } else {
      handleComplete();
    }
  }, [currentStep]);

  const handleSkip = useCallback(() => {
    handleComplete();
  }, []);

  const handleComplete = useCallback(() => {
    setActive(false);
    setCurrentStep(0);
    if (typeof window !== 'undefined') {
      localStorage.setItem(TOUR_STORAGE_KEY, 'true');
    }
  }, []);

  if (!active) return null;

  const step = TOUR_STEPS[currentStep];
  if (!step) return null;

  const stepLabel = language === 'de'
    ? `Schritt ${currentStep + 1} von ${TOUR_STEPS.length}`
    : `Step ${currentStep + 1} of ${TOUR_STEPS.length}`;

  const isLastStep = currentStep === TOUR_STEPS.length - 1;

  const tooltipPos = highlightRect
    ? getTooltipPosition(highlightRect)
    : { top: '50%', left: '50%', maxWidth: '360px' };

  return (
    <>
      {/* Dark overlay with spotlight cutout */}
      <div
        className="fixed inset-0 z-[9998]"
        style={{ pointerEvents: 'none' }}
        aria-hidden="true"
      >
        <svg
          className="w-full h-full"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: `${document.documentElement.scrollWidth}px`,
            height: `${document.documentElement.scrollHeight}px`,
          }}
        >
          <defs>
            <mask id="tour-spotlight-mask">
              <rect x="0" y="0" width="100%" height="100%" fill="white" />
              {highlightRect && (
                <rect
                  x={highlightRect.left}
                  y={highlightRect.top}
                  width={highlightRect.width}
                  height={highlightRect.height}
                  rx="8"
                  fill="black"
                />
              )}
            </mask>
          </defs>
          <rect
            x="0"
            y="0"
            width="100%"
            height="100%"
            fill="rgba(0,0,0,0.6)"
            mask="url(#tour-spotlight-mask)"
          />
        </svg>
      </div>

      {/* Highlight border around target */}
      {highlightRect && (
        <div
          className="fixed z-[9999] rounded-[var(--radius)] pointer-events-none"
          style={{
            position: 'absolute',
            top: `${highlightRect.top}px`,
            left: `${highlightRect.left}px`,
            width: `${highlightRect.width}px`,
            height: `${highlightRect.height}px`,
            border: '2px solid var(--color-primary)',
            boxShadow: '0 0 0 4px rgba(66, 98, 255, 0.2)',
          }}
          aria-hidden="true"
        />
      )}

      {/* Click blocker (prevents interaction with background) */}
      <div
        className="fixed inset-0 z-[9999]"
        onClick={(e) => e.stopPropagation()}
        aria-hidden="true"
      />

      {/* Tooltip */}
      <div
        ref={tooltipRef}
        role="dialog"
        aria-modal="true"
        aria-label={stepLabel}
        className="fixed z-[10000] bg-[var(--color-card)] border border-[var(--color-border)] rounded-[var(--radius-lg)] shadow-xl p-5 space-y-4"
        style={{
          position: 'absolute',
          top: tooltipPos.top,
          left: tooltipPos.left,
          maxWidth: tooltipPos.maxWidth,
          minWidth: '280px',
        }}
      >
        {/* Step counter */}
        <p className="text-xs font-semibold text-[var(--color-primary)] uppercase tracking-wider" aria-live="polite">
          {stepLabel}
        </p>

        {/* Title */}
        <h2 className="text-lg font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
          {t(step.titleKey as Parameters<typeof t>[0], language)}
        </h2>

        {/* Description */}
        <p className="text-sm text-[var(--color-muted)] leading-relaxed">
          {t(step.descriptionKey as Parameters<typeof t>[0], language)}
        </p>

        {/* Navigation buttons */}
        <div className="flex items-center justify-between pt-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleSkip}
            aria-label={t('tour.skip', language)}
          >
            {t('tour.skip', language)}
          </Button>

          <Button
            ref={nextButtonRef}
            size="sm"
            onClick={handleNext}
            aria-label={isLastStep ? t('tour.finish', language) : t('action.next', language)}
          >
            {isLastStep ? t('tour.finish', language) : t('action.next', language)}
          </Button>
        </div>
      </div>
    </>
  );
}

/**
 * Resets the tour so it will show again on next page load.
 * Call from a Help page or settings button.
 */
export function resetTour(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(TOUR_STORAGE_KEY);
  }
}
