/**
 * NomOS — Chat panel. Embedded chat interface with Art. 50 AI disclosure.
 * User messages on right (blue), agent messages on left (gray).
 * PAUSE button: RED, top-right, ALWAYS visible (Art. 14).
 * Art. 50 Label on EVERY agent message: "Diese Antwort wurde von KI generiert".
 * Data from: POST /api/proxy/chat, GET /api/proxy/status
 *
 * 4 States: Loading (Skeleton), Empty (first message CTA), Error (ErrorBoundary), Data (chat)
 * WCAG 2.2 AA: focus-visible, aria-labels, keyboard nav, live region
 * i18n: All text via translation keys
 */
'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useNomosStore } from '@/lib/store';
import { t } from '@/lib/i18n';
import { useFetch, formatDate } from '@/lib/hooks';
import { api, ApiError } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { EmptyState } from '@/components/ui/empty-state';
import { Skeleton } from '@/components/ui/skeleton';
import type { Agent, ChatMessage, ProxyChatResponse, ProxyStatusResponse } from '@/lib/types';
import { agentStatusToBadge } from '@/lib/types';
import { Badge } from '@/components/ui/badge';

function ChatSkeleton() {
  return (
    <div className="flex flex-col h-[calc(100vh-var(--header-height)-3rem)]" role="status" aria-busy="true">
      <span className="sr-only">Wird geladen...</span>
      <div className="flex items-center justify-between p-4 border-b border-[var(--color-border)]">
        <div className="flex items-center gap-3">
          <Skeleton width="w-10" height="h-10" rounded />
          <div className="space-y-1.5">
            <Skeleton width="w-32" height="h-4" />
            <Skeleton width="w-20" height="h-3" />
          </div>
        </div>
      </div>
      <div className="flex-1 p-4 space-y-4">
        <Skeleton width="w-2/3" height="h-16" />
        <div className="flex justify-end"><Skeleton width="w-1/2" height="h-12" /></div>
        <Skeleton width="w-3/4" height="h-20" />
      </div>
    </div>
  );
}

/** Single chat message bubble. */
function MessageBubble({ message, lang }: { message: ChatMessage; lang: 'de' | 'en' }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={[
          'max-w-[75%] rounded-[var(--radius-lg)] px-4 py-3',
          isUser
            ? 'bg-[var(--color-primary)] text-white rounded-br-[var(--radius-sm)]'
            : 'bg-[var(--color-hover)] text-[var(--color-text)] border border-[var(--color-border)] rounded-bl-[var(--radius-sm)]',
        ].join(' ')}
      >
        <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
        <div className={`flex items-center gap-2 mt-2 ${isUser ? 'justify-end' : 'justify-between'}`}>
          <span className={`text-xs ${isUser ? 'text-white/70' : 'text-[var(--color-muted)]'}`}>
            {formatDate(message.timestamp, lang)}
          </span>
          {/* Speaker button placeholder for agent messages */}
          {!isUser && (
            <button
              className="p-1 rounded-[var(--radius-sm)] text-[var(--color-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-card)] transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]"
              aria-label={t('a11y.speakerPlaceholder', lang)}
              disabled
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              </svg>
            </button>
          )}
        </div>
        {/* Art. 50 AI disclosure on agent messages */}
        {!isUser && (
          <p className="text-[10px] text-[var(--color-muted)] mt-1.5 pt-1.5 border-t border-[var(--color-border)] italic">
            {t('chat.aiDisclosure', lang)}
          </p>
        )}
      </div>
    </div>
  );
}

function ChatContent() {
  const params = useParams();
  const agentId = params.id as string;
  const router = useRouter();
  const { language, addToast } = useNomosStore();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [sending, setSending] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [pauseLoading, setPauseLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const agentFetch = useFetch<Agent>(`/fleet/${agentId}`);
  const gatewayStatus = useFetch<ProxyStatusResponse>('/proxy/status');

  const isGatewayOnline = gatewayStatus.data?.status === 'online';
  const agent = agentFetch.data;

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = useCallback(async () => {
    const text = inputValue.trim();
    if (!text || sending) return;

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}-user`,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setSending(true);

    try {
      const response = await api.post<ProxyChatResponse>('/proxy/chat', {
        agent_id: agentId,
        message: text,
        session_id: sessionId,
      });

      setSessionId(response.session_id);

      const agentMessage: ChatMessage = {
        id: `msg-${Date.now()}-agent`,
        role: 'agent',
        content: response.response,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, agentMessage]);
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : t('error.serverError', language);
      addToast({ type: 'error', message: msg, duration: 6000 });
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  }, [inputValue, sending, agentId, sessionId, language, addToast]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handlePause = async () => {
    setPauseLoading(true);
    try {
      await api.patch(`/fleet/${agentId}`, { status: 'paused' });
      addToast({ type: 'success', message: t('toast.agentPaused', language), duration: 4000 });
      agentFetch.reload();
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : t('error.serverError', language);
      addToast({ type: 'error', message: msg, duration: 6000 });
    } finally {
      setPauseLoading(false);
    }
  };

  if (agentFetch.loading) {
    return <ChatSkeleton />;
  }

  if (!agent) {
    return (
      <EmptyState
        message={t('error.notFound', language)}
        ctaLabel={t('action.back', language)}
        onCtaClick={() => router.back()}
      />
    );
  }

  const badgeStatus = agentStatusToBadge(agent.status);
  const isOffline = agent.status !== 'running';

  return (
    <div className="flex flex-col h-[calc(100vh-var(--header-height)-3rem)] bg-[var(--color-card)] border border-[var(--color-border)] rounded-[var(--radius-lg)] overflow-hidden">
      {/* Chat Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--color-border)] bg-[var(--color-card)]">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="p-1 rounded-[var(--radius-sm)] text-[var(--color-muted)] hover:text-[var(--color-text)] transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]"
            aria-label={t('action.back', language)}
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-bold shrink-0"
            style={{ backgroundColor: 'var(--color-primary)' }}
            aria-hidden="true"
          >
            {agent.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <p className="text-sm font-semibold text-[var(--color-text)]">{agent.name}</p>
            <Badge status={badgeStatus} />
          </div>
        </div>

        {/* PAUSE button — Art. 14: ALWAYS visible, RED, prominent */}
        <Button
          variant="danger"
          size="sm"
          onClick={handlePause}
          loading={pauseLoading}
          disabled={agent.status === 'paused'}
          aria-label={t('chat.pauseButton', language)}
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
          </svg>
          {t('chat.pauseButton', language)}
        </Button>
      </div>

      {/* Gateway offline banner */}
      {!isGatewayOnline && !gatewayStatus.loading && (
        <div className="px-4 py-2 bg-[var(--color-warning-light)] border-b border-[var(--color-warning)]" role="alert">
          <p className="text-xs text-[var(--color-text)] font-medium">{t('chat.gatewayOffline', language)}</p>
        </div>
      )}

      {/* Agent offline banner */}
      {isOffline && (
        <div className="px-4 py-2 bg-[var(--color-error-light)] border-b border-[var(--color-error)]" role="alert">
          <p className="text-xs text-[var(--color-text)] font-medium">{t('chat.agentOffline', language)}</p>
        </div>
      )}

      {/* Messages area */}
      <div
        className="flex-1 overflow-y-auto p-4"
        role="log"
        aria-label={t('a11y.chatMessages', language)}
        aria-live="polite"
      >
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <EmptyState
              message={t('empty.chat', language)}
              description={t('empty.chatDescription', language)}
            />
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} lang={language} />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="px-4 py-3 border-t border-[var(--color-border)] bg-[var(--color-card)]">
        <div className="flex items-center gap-2">
          {/* Microphone placeholder */}
          <button
            className="p-2 rounded-[var(--radius)] text-[var(--color-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-hover)] transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus-ring)]"
            aria-label={t('a11y.microphonePlaceholder', language)}
            disabled
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          </button>

          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t('chat.inputPlaceholder', language)}
            disabled={sending || isOffline}
            className={[
              'flex-1 px-4 py-2.5 text-sm',
              'bg-[var(--color-bg)] text-[var(--color-text)]',
              'border border-[var(--color-border)] rounded-[var(--radius-full)]',
              'placeholder:text-[var(--color-muted)]',
              'focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-[var(--color-focus-ring)]',
              'focus-visible:border-[var(--color-primary)]',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'transition-all duration-[var(--transition)]',
            ].join(' ')}
            aria-label={t('a11y.chatInput', language)}
          />

          <Button
            onClick={handleSend}
            disabled={!inputValue.trim() || sending || isOffline}
            loading={sending}
            size="sm"
            aria-label={t('action.send', language)}
            className="rounded-full px-4"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
            </svg>
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <ErrorBoundary>
      <ChatContent />
    </ErrorBoundary>
  );
}
