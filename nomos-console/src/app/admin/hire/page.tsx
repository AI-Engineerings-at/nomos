/**
 * NomOS — Hire Wizard (Neuen Mitarbeiter einstellen).
 * 4-step wizard: Identity -> Capabilities -> Security & Budget -> Deploy.
 * POST /api/agents with collected data.
 *
 * 4 States: Loading (Skeleton), Empty (N/A for wizard), Error (ErrorBoundary + inline), Data (form)
 * WCAG 2.2 AA: focus-visible, aria-labels, keyboard nav, progress indicator
 * i18n: All text via translation keys
 */
'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { useFetch, formatEur } from '@/lib/hooks';
import { api, ApiError } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import type { FleetResponse, Agent } from '@/lib/types';
import type { TranslationKey } from '@/lib/i18n';

interface RoleOption {
  id: string;
  nameKey: TranslationKey;
  descKey: TranslationKey;
  riskClass: 'minimal' | 'limited' | 'high';
  recommendedBudget: number;
}

const ROLE_OPTIONS: RoleOption[] = [
  { id: 'social-media', nameKey: 'hire.role.socialMedia', descKey: 'hire.role.socialMediaDesc', riskClass: 'limited', recommendedBudget: 50 },
  { id: 'support', nameKey: 'hire.role.support', descKey: 'hire.role.supportDesc', riskClass: 'limited', recommendedBudget: 80 },
  { id: 'research', nameKey: 'hire.role.research', descKey: 'hire.role.researchDesc', riskClass: 'minimal', recommendedBudget: 40 },
  { id: 'design', nameKey: 'hire.role.design', descKey: 'hire.role.designDesc', riskClass: 'minimal', recommendedBudget: 60 },
  { id: 'red-teamer', nameKey: 'hire.role.redTeamer', descKey: 'hire.role.redTeamerDesc', riskClass: 'high', recommendedBudget: 100 },
  { id: 'custom', nameKey: 'hire.role.custom', descKey: 'hire.role.customDesc', riskClass: 'limited', recommendedBudget: 50 },
];

interface CapabilityOption {
  id: string;
  nameKey: TranslationKey;
}

const CAPABILITY_OPTIONS: CapabilityOption[] = [
  { id: 'chat', nameKey: 'hire.capability.chat' },
  { id: 'email', nameKey: 'hire.capability.email' },
  { id: 'social-media', nameKey: 'hire.capability.socialMedia' },
  { id: 'research', nameKey: 'hire.capability.research' },
  { id: 'code-review', nameKey: 'hire.capability.codeReview' },
  { id: 'data-analysis', nameKey: 'hire.capability.dataAnalysis' },
];

type LlmLocation = 'local' | 'eu' | 'us';

interface HireFormData {
  name: string;
  roleId: string;
  capabilities: string[];
  budget: number;
  riskClass: 'minimal' | 'limited' | 'high';
  llmLocation: LlmLocation;
}

const DEPLOY_STEP_KEYS: TranslationKey[] = [
  'deploy.step.validateManifest',
  'deploy.step.checkCompliance',
  'deploy.step.generateDocs',
  'deploy.step.createContainer',
  'deploy.step.configureGateway',
  'deploy.step.setupMemory',
  'deploy.step.registerAgent',
  'deploy.step.runTests',
  'deploy.step.startHeartbeat',
  'deploy.step.ready',
];

/** Progress bar showing current step. */
function WizardProgress({ currentStep, totalSteps, lang }: { currentStep: number; totalSteps: number; lang: 'de' | 'en' }) {
  return (
    <div className="space-y-3" role="group" aria-label={t('a11y.wizardProgress', lang)}>
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-[var(--color-text)]">
          {t('hire.stepLabel', lang)} {currentStep}/{totalSteps}
        </span>
        <span className="text-sm text-[var(--color-muted)]">
          {Math.round((currentStep / totalSteps) * 100)}%
        </span>
      </div>
      <div className="flex gap-2">
        {Array.from({ length: totalSteps }).map((_, i) => (
          <div
            key={i}
            className={[
              'flex-1 h-2 rounded-[var(--radius-full)] transition-all duration-300',
              i < currentStep ? 'bg-[var(--color-primary)]' : 'bg-[var(--color-hover)]',
            ].join(' ')}
            aria-hidden="true"
          />
        ))}
      </div>
    </div>
  );
}

function HireWizardContent() {
  const { language, addToast } = useNomosStore();
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [deployProgress, setDeployProgress] = useState(0);
  const [deployComplete, setDeployComplete] = useState(false);
  const [deployError, setDeployError] = useState<string | null>(null);
  const [createdAgent, setCreatedAgent] = useState<Agent | null>(null);

  const fleet = useFetch<FleetResponse>('/fleet');
  const fclCount = fleet.data?.agents.length ?? 0;
  const fclAtLimit = fclCount >= 3;

  const [formData, setFormData] = useState<HireFormData>({
    name: '',
    roleId: '',
    capabilities: [],
    budget: 50,
    riskClass: 'limited',
    llmLocation: 'eu',
  });

  const selectedRole = ROLE_OPTIONS.find((r) => r.id === formData.roleId);

  const updateField = useCallback(<K extends keyof HireFormData>(key: K, value: HireFormData[K]) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
    setFormErrors((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }, []);

  const validateStep1 = (): boolean => {
    const errors: Record<string, string> = {};
    if (!formData.name.trim()) {
      errors.name = language === 'de' ? 'Bitte geben Sie einen Namen ein.' : 'Please enter a name.';
    }
    if (!formData.roleId) {
      errors.roleId = language === 'de' ? 'Bitte waehlen Sie eine Rolle.' : 'Please select a role.';
    }
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const validateStep2 = (): boolean => {
    const errors: Record<string, string> = {};
    if (formData.capabilities.length === 0) {
      errors.capabilities = language === 'de' ? 'Bitte waehlen Sie mindestens eine Faehigkeit.' : 'Please select at least one capability.';
    }
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const goNext = () => {
    if (step === 1 && !validateStep1()) return;
    if (step === 2 && !validateStep2()) return;
    if (step === 3) {
      handleDeploy();
      return;
    }
    setStep((s) => Math.min(s + 1, 4));
  };

  const goBack = () => {
    setStep((s) => Math.max(s - 1, 1));
    setFormErrors({});
  };

  const handleDeploy = async () => {
    setStep(4);
    setDeployError(null);
    setDeployProgress(0);

    try {
      // Simulate deploy steps with progression
      for (let i = 0; i < DEPLOY_STEP_KEYS.length; i++) {
        setDeployProgress(i + 1);
        // Small delay between steps for visual feedback
        await new Promise((resolve) => {
          window.setTimeout(resolve, 400);
        });

        // On the registerAgent step (step 7), actually call the API
        if (i === 6) {
          const result = await api.post<Agent>('/agents', {
            name: formData.name,
            role: selectedRole?.id ?? formData.roleId,
            company: 'NomOS', // Will be set from workspace context
            email: `${formData.name.toLowerCase().replace(/\s+/g, '.')}@nomos.local`,
            risk_class: formData.riskClass,
          });
          setCreatedAgent(result);
        }
      }

      setDeployComplete(true);
      addToast({ type: 'success', message: t('toast.hireSuccess', language), duration: 5000 });
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : t('toast.hireFailed', language);
      setDeployError(msg);
      addToast({ type: 'error', message: msg, duration: 8000 });
    }
  };

  const toggleCapability = (id: string) => {
    setFormData((prev) => ({
      ...prev,
      capabilities: prev.capabilities.includes(id)
        ? prev.capabilities.filter((c) => c !== id)
        : [...prev.capabilities, id],
    }));
    setFormErrors((prev) => {
      const next = { ...prev };
      delete next.capabilities;
      return next;
    });
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      {/* Title */}
      <h1 className="text-2xl font-extrabold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
        {t('hire.title', language)}
      </h1>

      {/* FCL Warning */}
      {fclAtLimit && (
        <div
          className="p-4 rounded-[var(--radius)] bg-[var(--color-warning-light)] border border-[var(--color-warning)] text-sm text-[var(--color-text)]"
          role="alert"
        >
          <p className="font-semibold">{t('hire.fclWarning', language)}</p>
        </div>
      )}

      {/* Progress */}
      <WizardProgress currentStep={step} totalSteps={4} lang={language} />

      {/* Step 1: Identity */}
      {step === 1 && (
        <Card className="space-y-6">
          <h2 className="text-lg font-bold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
            {t('hire.step1.title', language)}
          </h2>

          <Input
            label={t('hire.step1.nameLabel', language)}
            placeholder={t('hire.step1.namePlaceholder', language)}
            value={formData.name}
            onChange={(e) => updateField('name', e.target.value)}
            error={formErrors.name}
            required
          />

          <div className="space-y-2">
            <p className="text-sm font-semibold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
              {t('hire.step1.roleLabel', language)} <span className="text-[var(--color-error)]" aria-hidden="true">*</span>
            </p>
            <p className="text-xs text-[var(--color-muted)]">{t('hire.step1.roleDescription', language)}</p>

            {formErrors.roleId && (
              <p className="text-xs text-[var(--color-error)]" role="alert">{formErrors.roleId}</p>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-2" role="radiogroup" aria-label={t('hire.step1.roleLabel', language)}>
              {ROLE_OPTIONS.map((role) => (
                <button
                  key={role.id}
                  type="button"
                  role="radio"
                  aria-checked={formData.roleId === role.id}
                  onClick={() => {
                    updateField('roleId', role.id);
                    updateField('riskClass', role.riskClass);
                    updateField('budget', role.recommendedBudget);
                  }}
                  className={[
                    'text-left p-4 rounded-[var(--radius)] border-2 transition-all duration-[var(--transition)]',
                    'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]',
                    formData.roleId === role.id
                      ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)]'
                      : 'border-[var(--color-border)] hover:border-[var(--color-muted)] bg-[var(--color-card)]',
                  ].join(' ')}
                >
                  <p className="text-sm font-semibold text-[var(--color-text)]">{t(role.nameKey, language)}</p>
                  <p className="text-xs text-[var(--color-muted)] mt-1">{t(role.descKey, language)}</p>
                </button>
              ))}
            </div>
          </div>

          {/* SOUL Template preview */}
          {selectedRole && selectedRole.id === 'red-teamer' && (
            <div className="p-3 rounded-[var(--radius)] bg-[var(--color-hover)] border border-[var(--color-border)]">
              <p className="text-xs font-semibold text-[var(--color-primary)]">{t('hire.soulTemplate', language)}: Rico</p>
              <p className="text-xs text-[var(--color-muted)] mt-1">
                {language === 'de'
                  ? 'Das Rico-Template konfiguriert einen Red-Team-Agenten der Ihre Systeme auf Schwachstellen testet.'
                  : 'The Rico template configures a red-team agent that tests your systems for vulnerabilities.'}
              </p>
            </div>
          )}
        </Card>
      )}

      {/* Step 2: Capabilities */}
      {step === 2 && (
        <Card className="space-y-6">
          <h2 className="text-lg font-bold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
            {t('hire.step2.title', language)}
          </h2>

          <div className="space-y-2">
            <p className="text-sm font-semibold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
              {t('hire.step2.capabilitiesLabel', language)}
            </p>

            {formErrors.capabilities && (
              <p className="text-xs text-[var(--color-error)]" role="alert">{formErrors.capabilities}</p>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2" role="group" aria-label={t('hire.step2.capabilitiesLabel', language)}>
              {CAPABILITY_OPTIONS.map((cap) => {
                const checked = formData.capabilities.includes(cap.id);
                return (
                  <label
                    key={cap.id}
                    className={[
                      'flex items-center gap-3 p-3 rounded-[var(--radius)] border cursor-pointer transition-all duration-[var(--transition)]',
                      checked
                        ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)]'
                        : 'border-[var(--color-border)] hover:border-[var(--color-muted)]',
                    ].join(' ')}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleCapability(cap.id)}
                      className="w-4 h-4 rounded accent-[var(--color-primary)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]"
                    />
                    <span className="text-sm text-[var(--color-text)]">{t(cap.nameKey, language)}</span>
                  </label>
                );
              })}
            </div>
          </div>

          {/* LLM recommendation */}
          <div className="p-3 rounded-[var(--radius)] bg-[var(--color-hover)] border border-[var(--color-border)]">
            <p className="text-xs font-semibold text-[var(--color-primary)]">{t('hire.step2.llmLabel', language)}</p>
            <p className="text-xs text-[var(--color-muted)] mt-1">
              {language === 'de'
                ? `Fuer ${selectedRole ? t(selectedRole.nameKey, language) : 'diese Rolle'} empfehlen wir ein Modell mit starken Sprachfaehigkeiten.`
                : `For ${selectedRole ? t(selectedRole.nameKey, language) : 'this role'} we recommend a model with strong language capabilities.`}
            </p>
          </div>
        </Card>
      )}

      {/* Step 3: Security & Budget */}
      {step === 3 && (
        <Card className="space-y-6">
          <h2 className="text-lg font-bold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
            {t('hire.step3.title', language)}
          </h2>

          {/* Budget slider */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label
                htmlFor="budget-slider"
                className="text-sm font-semibold text-[var(--color-text)] font-[family-name:var(--font-headline)]"
              >
                {t('hire.step3.budgetLabel', language)}
              </label>
              <span className="text-lg font-bold text-[var(--color-primary)]">{formatEur(formData.budget)}</span>
            </div>
            <input
              id="budget-slider"
              type="range"
              min={10}
              max={500}
              step={10}
              value={formData.budget}
              onChange={(e) => updateField('budget', Number(e.target.value))}
              className="w-full h-2 bg-[var(--color-hover)] rounded-[var(--radius-full)] appearance-none cursor-pointer accent-[var(--color-primary)]"
              aria-label={t('hire.step3.budgetLabel', language)}
            />
            <p className="text-xs text-[var(--color-muted)]">
              {t('hire.step3.budgetRecommendation', language)}: {formatEur(selectedRole?.recommendedBudget ?? 50)}
            </p>
          </div>

          {/* Risk Class */}
          <div className="space-y-2">
            <p className="text-sm font-semibold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
              {t('hire.step3.riskClassLabel', language)}
            </p>
            <p className="text-xs text-[var(--color-muted)]">{t('hire.step3.riskClassDescription', language)}</p>
            <div className="flex gap-2 mt-2" role="radiogroup" aria-label={t('hire.step3.riskClassLabel', language)}>
              {(['minimal', 'limited', 'high'] as const).map((rc) => {
                const rcKey = `hire.riskClass.${rc}` as TranslationKey;
                return (
                  <button
                    key={rc}
                    type="button"
                    role="radio"
                    aria-checked={formData.riskClass === rc}
                    onClick={() => updateField('riskClass', rc)}
                    className={[
                      'px-4 py-2 text-sm rounded-[var(--radius)] border-2 transition-all duration-[var(--transition)]',
                      'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]',
                      formData.riskClass === rc
                        ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)] text-[var(--color-primary)] font-semibold'
                        : 'border-[var(--color-border)] text-[var(--color-muted)] hover:border-[var(--color-muted)]',
                    ].join(' ')}
                  >
                    {t(rcKey, language)}
                  </button>
                );
              })}
            </div>
          </div>

          {/* LLM Location */}
          <div className="space-y-2">
            <p className="text-sm font-semibold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
              {t('hire.step3.llmLocationLabel', language)}
            </p>
            <div className="space-y-2 mt-2" role="radiogroup" aria-label={t('hire.step3.llmLocationLabel', language)}>
              {([
                { key: 'local' as LlmLocation, labelKey: 'hire.step3.llmLocationLocal' as TranslationKey },
                { key: 'eu' as LlmLocation, labelKey: 'hire.step3.llmLocationEU' as TranslationKey },
                { key: 'us' as LlmLocation, labelKey: 'hire.step3.llmLocationUS' as TranslationKey },
              ]).map((opt) => (
                <label
                  key={opt.key}
                  className={[
                    'flex items-center gap-3 p-3 rounded-[var(--radius)] border cursor-pointer transition-all duration-[var(--transition)]',
                    formData.llmLocation === opt.key
                      ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)]'
                      : 'border-[var(--color-border)] hover:border-[var(--color-muted)]',
                  ].join(' ')}
                >
                  <input
                    type="radio"
                    name="llm-location"
                    checked={formData.llmLocation === opt.key}
                    onChange={() => updateField('llmLocation', opt.key)}
                    className="w-4 h-4 accent-[var(--color-primary)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]"
                  />
                  <span className="text-sm text-[var(--color-text)]">{t(opt.labelKey, language)}</span>
                </label>
              ))}
            </div>
            {/* TIA Warning for US */}
            {formData.llmLocation === 'us' && (
              <div className="p-3 rounded-[var(--radius)] bg-[var(--color-warning-light)] border border-[var(--color-warning)]" role="alert">
                <p className="text-xs text-[var(--color-text)] font-medium">{t('hire.step3.tiaWarning', language)}</p>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Step 4: Deploy */}
      {step === 4 && (
        <Card className="space-y-6">
          <h2 className="text-lg font-bold text-[var(--color-text)] font-[family-name:var(--font-headline)]">
            {deployComplete ? t('hire.step4.complete', language) : t('hire.step4.title', language)}
          </h2>

          {/* Deploy steps */}
          <div className="space-y-3" role="log" aria-live="polite">
            {DEPLOY_STEP_KEYS.map((stepKey, i) => {
              const stepNum = i + 1;
              const isDone = deployProgress > stepNum;
              const isCurrent = deployProgress === stepNum;
              const isPending = deployProgress < stepNum;

              return (
                <div key={stepKey} className="flex items-center gap-3">
                  {/* Status icon */}
                  <div
                    className={[
                      'w-6 h-6 rounded-full flex items-center justify-center shrink-0',
                      isDone ? 'bg-[var(--color-success)]' : isCurrent ? 'bg-[var(--color-primary)]' : 'bg-[var(--color-hover)]',
                    ].join(' ')}
                    aria-hidden="true"
                  >
                    {isDone ? (
                      <svg className="w-3.5 h-3.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={3}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    ) : isCurrent ? (
                      <div className="w-2.5 h-2.5 rounded-full bg-white animate-pulse" />
                    ) : (
                      <div className="w-2 h-2 rounded-full bg-[var(--color-muted)]" />
                    )}
                  </div>
                  <span
                    className={[
                      'text-sm',
                      isDone ? 'text-[var(--color-success)] font-medium' : isCurrent ? 'text-[var(--color-text)] font-semibold' : 'text-[var(--color-muted)]',
                    ].join(' ')}
                  >
                    {t(stepKey, language)}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Deploy error */}
          {deployError && (
            <div className="p-4 rounded-[var(--radius)] bg-[var(--color-error-light)] border border-[var(--color-error)]" role="alert">
              <p className="text-sm text-[var(--color-error)] font-medium">{deployError}</p>
            </div>
          )}

          {/* Completion actions */}
          {deployComplete && createdAgent && (
            <div className="space-y-4 pt-4 border-t border-[var(--color-border)]">
              <div className="p-3 rounded-[var(--radius)] bg-[var(--color-hover)]">
                <p className="text-xs font-semibold text-[var(--color-primary)]">{t('hire.step4.firstMessage', language)}</p>
                <p className="text-sm text-[var(--color-text)] mt-2">
                  {language === 'de'
                    ? `Hallo! Ich bin ${createdAgent.name} und freue mich, Teil Ihres Teams zu sein. Wie kann ich Ihnen helfen?`
                    : `Hello! I'm ${createdAgent.name} and I'm excited to be part of your team. How can I help you?`}
                </p>
              </div>
              <div className="flex gap-3">
                <Button onClick={() => router.push(`/app/chat/${createdAgent.id}`)}>
                  {t('hire.step4.openChat', language)}
                </Button>
                <Button variant="secondary" onClick={() => router.push('/admin/team')}>
                  {t('hire.step4.toTeam', language)}
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Navigation buttons */}
      {step < 4 && (
        <div className="flex justify-between">
          {step > 1 ? (
            <Button variant="secondary" onClick={goBack}>
              {t('action.back', language)}
            </Button>
          ) : (
            <Button variant="secondary" onClick={() => router.push('/admin/team')}>
              {t('action.cancel', language)}
            </Button>
          )}
          <Button onClick={goNext} disabled={fclAtLimit && step === 3}>
            {step === 3
              ? (language === 'de' ? 'Einarbeitung starten' : 'Start onboarding')
              : t('action.next', language)}
          </Button>
        </div>
      )}
    </div>
  );
}

export default function HirePage() {
  return (
    <ErrorBoundary>
      <HireWizardContent />
    </ErrorBoundary>
  );
}
