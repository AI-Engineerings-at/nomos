# NomOS Production Polish — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 8 gaps to bring NomOS from 8/10 to 10/10. Customer does `docker compose up`, logs in, hires an agent, chats — zero friction.

**Architecture:** No structural changes. All fixes are in existing files. Biggest change: chat error handling in frontend, umlaut fix across i18n + templates.

**Tech Stack:** Next.js 15 (TypeScript), FastAPI (Python 3.12), Docker Compose, i18n (de.ts/en.ts)

**Spec:** `docs/superpowers/specs/2026-04-05-production-polish-design.md`

---

## File Structure

### Files to modify

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `docker-compose.yml` | G4: Console healthcheck + Caddy dependency |
| Modify | `nomos-console/src/app/app/chat/[id]/page.tsx` | G1: Error as chat message, G3: Provider banner |
| Modify | `nomos-console/src/lib/i18n/de.ts` | G2: Umlaute, G1+G3: Error keys, G5: missing keys |
| Modify | `nomos-console/src/lib/i18n/en.ts` | G1+G3: Error keys, G5: missing keys |
| Modify | `nomos-cli/nomos/core/gate.py` | G2: Umlaute in templates |
| Modify | `nomos-api/nomos_api/routers/proxy.py` | G2: Umlaute in error strings |
| Modify | `.env.example` | G6: Complete documentation |

### Files to create

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `docs/quickstart.md` | G8: English deployment guide |
| Create | `docs/de/schnellstart.md` | G8: German deployment guide |

---

## Task 1: Console Docker Healthcheck (G4)

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 1: Add healthcheck to nomos-console service**

In `docker-compose.yml`, find the `nomos-console:` service block. After the `depends_on` section, add:

```yaml
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 15s
```

- [ ] **Step 2: Change Caddy dependency from service_started to service_healthy**

In the `caddy:` service block, change:

```yaml
    depends_on:
      nomos-console:
        condition: service_started
```

to:

```yaml
    depends_on:
      nomos-console:
        condition: service_healthy
```

- [ ] **Step 3: Validate compose config**

Run: `cd /c/Users/Legion/Documents/nomos && docker compose config --services`
Expected: All 8 services listed without errors

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml
git commit -m "fix(docker): console healthcheck + caddy waits for healthy console"
```

---

## Task 2: Selina DB Status Fix (G7)

**Files:** None (API call only)

- [ ] **Step 1: Login and get auth cookie**

```bash
curl -sf http://localhost:8060/api/auth/login -X POST \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@nomos.local","password":"NomOS-Admin-2026!"}' \
  -c /tmp/nomos-cookie
```

- [ ] **Step 2: Re-run compliance gate for Selina**

```bash
curl -sf http://localhost:8060/api/agents/selina/gate -X POST \
  -b /tmp/nomos-cookie | python -m json.tool
```

Expected: `"status": "passed"`

- [ ] **Step 3: Verify in fleet**

```bash
curl -sf http://localhost:8060/api/fleet/selina -b /tmp/nomos-cookie | python -m json.tool
```

Expected: `"compliance_status": "passed"`

---

## Task 3: .env.example Complete (G6)

**Files:**
- Modify: `.env.example`

- [ ] **Step 1: Extract all ENV vars from docker-compose.yml**

Run: `grep -oP '\$\{[A-Z_]+' docker-compose.yml | sort -u | sed 's/\${//'`

- [ ] **Step 2: Update .env.example with all variables**

Replace the entire `.env.example` content. Every variable from docker-compose.yml must be documented. See the spec for grouping (Required, TLS, Ports, Optional, LLM Provider).

- [ ] **Step 3: Commit**

```bash
git add .env.example
git commit -m "docs: complete .env.example with all docker-compose variables"
```

---

## Task 4: Umlaut Fix (G2)

**Files:**
- Modify: `nomos-console/src/lib/i18n/de.ts`
- Modify: `nomos-cli/nomos/core/gate.py`
- Modify: `nomos-api/nomos_api/routers/proxy.py`

**CRITICAL:** Do NOT blind-replace. Only replace in German text strings, never in code identifiers, English strings, or i18n keys.

- [ ] **Step 1: Fix de.ts — Read the file first**

Read `nomos-console/src/lib/i18n/de.ts` completely. Identify every VALUE string (not key) that contains ae/oe/ue where ä/ö/ü should be.

Common patterns to fix:
- `fuer` → `für`
- `ueber` → `über`
- `Uebersicht` → `Übersicht`
- `zurueck` → `zurück`
- `pruefen` → `prüfen`
- `verfuegbar` → `verfügbar`
- `Bestaetigen` → `Bestätigen`
- `Loeschen` → `Löschen`
- `aendern` → `ändern`
- `Aenderungen` → `Änderungen`
- `Oeffentlich` → `Öffentlich`
- `Groesse` → `Größe`
- `moeglich` → `möglich`
- `Einfuehrung` → `Einführung`

Do NOT change: `true`, `blue`, `value`, `continue`, `queue`, `route`, `issue`, `minute`, `secure`, `feature`, `procedure`

Apply all fixes with Edit tool. Use replace_all where safe, otherwise targeted edits.

- [ ] **Step 2: Run console tests**

Run: `cd /c/Users/Legion/Documents/nomos/nomos-console && npx vitest run`
Expected: 85/85 passed (i18n keys unchanged, only values changed)

- [ ] **Step 3: Fix gate.py templates**

Read `nomos-cli/nomos/core/gate.py`. Find all German template strings (content variables, disclaimers, headings) and fix umlauts. Same rules as Step 1.

- [ ] **Step 4: Run CLI tests**

Run: `cd /c/Users/Legion/Documents/nomos/nomos-cli && python -m pytest tests/ -q`
Expected: All passed

- [ ] **Step 5: Fix proxy.py error strings**

Read `nomos-api/nomos_api/routers/proxy.py`. Fix German strings in HTTPException detail messages.

- [ ] **Step 6: Run API tests**

Run: `cd /c/Users/Legion/Documents/nomos/nomos-api && python -m pytest tests/ -q --ignore=tests/test_auth_router.py`
Expected: All passed (minus pre-existing rate limiter errors)

- [ ] **Step 7: Commit**

```bash
git add nomos-console/src/lib/i18n/de.ts nomos-cli/nomos/core/gate.py nomos-api/nomos_api/routers/proxy.py
git commit -m "fix(i18n): correct German umlauts — ue→ü, ae→ä, oe→ö across all packages"
```

---

## Task 5: Chat Error Handling (G1)

**Files:**
- Modify: `nomos-console/src/app/app/chat/[id]/page.tsx`
- Modify: `nomos-console/src/lib/i18n/de.ts`
- Modify: `nomos-console/src/lib/i18n/en.ts`

- [ ] **Step 1: Add i18n keys for chat errors**

In `de.ts`, add these keys:

```typescript
'chat.error.rateLimit': 'Anfrage-Limit erreicht. Bitte warten Sie einen Moment und versuchen Sie es erneut.',
'chat.error.gatewayOffline': 'Der Chat-Dienst ist nicht erreichbar. Bitte prüfen Sie die Einstellungen.',
'chat.error.noProvider': 'Kein LLM-Provider konfiguriert.',
'chat.error.noProviderCta': 'Einstellungen öffnen',
'chat.error.unknown': 'Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.',
'chat.error.retry': 'Erneut versuchen',
```

In `en.ts`, add matching keys:

```typescript
'chat.error.rateLimit': 'Rate limit reached. Please wait a moment and try again.',
'chat.error.gatewayOffline': 'Chat service is unreachable. Please check settings.',
'chat.error.noProvider': 'No LLM provider configured.',
'chat.error.noProviderCta': 'Open settings',
'chat.error.unknown': 'An error occurred. Please try again.',
'chat.error.retry': 'Try again',
```

- [ ] **Step 2: Modify handleSend to show errors as chat messages**

In `chat/[id]/page.tsx`, replace the catch block in `handleSend` (around line 145-148):

```typescript
// OLD:
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : t('error.serverError', language);
      addToast({ type: 'error', message: msg, duration: 6000 });
    }
```

With:

```typescript
    } catch (err) {
      let errorKey: string = 'chat.error.unknown';
      if (err instanceof ApiError) {
        if (err.status === 429) errorKey = 'chat.error.rateLimit';
        else if (err.status === 502) errorKey = 'chat.error.gatewayOffline';
        else if (err.status === 503) errorKey = 'chat.error.noProvider';
      }

      const errorMessage: ChatMessage = {
        id: `msg-${Date.now()}-error`,
        role: 'agent',
        content: t(errorKey as any, language),
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
```

- [ ] **Step 3: Run console tests**

Run: `cd /c/Users/Legion/Documents/nomos/nomos-console && npx vitest run`
Expected: 85/85 passed

- [ ] **Step 4: Commit**

```bash
git add nomos-console/src/app/app/chat/[id]/page.tsx nomos-console/src/lib/i18n/de.ts nomos-console/src/lib/i18n/en.ts
git commit -m "feat(chat): show LLM errors as chat messages instead of silent failure"
```

---

## Task 6: LLM Provider Status Check (G3)

**Files:**
- Modify: `nomos-console/src/app/app/chat/[id]/page.tsx`
- Modify: `nomos-console/src/lib/i18n/de.ts`
- Modify: `nomos-console/src/lib/i18n/en.ts`

- [ ] **Step 1: Add i18n keys for provider status**

In `de.ts`:

```typescript
'chat.noProvider.banner': 'Kein LLM-Provider konfiguriert. Ihr Agent kann noch nicht antworten.',
'chat.noProvider.cta': 'Provider in Einstellungen konfigurieren',
'chat.gatewayOffline.banner': 'Chat-Dienst nicht erreichbar.',
```

In `en.ts`:

```typescript
'chat.noProvider.banner': 'No LLM provider configured. Your agent cannot respond yet.',
'chat.noProvider.cta': 'Configure provider in settings',
'chat.gatewayOffline.banner': 'Chat service unreachable.',
```

- [ ] **Step 2: Add provider check to chat page**

In `chat/[id]/page.tsx`, after the existing `useFetch` calls, add a settings fetch:

```typescript
const settingsFetch = useFetch<SystemSettings>('/settings');
```

Add the import for `SystemSettings` from `@/lib/types`.

Then, before the chat input area, add a banner when no provider is configured:

```typescript
{settingsFetch.data && !settingsFetch.data.openai_api_key_set && !settingsFetch.data.anthropic_api_key_set && !settingsFetch.data.nvidia_api_key_set && (
  <div className="px-4 py-3 bg-[var(--color-warning-bg,#3d2e00)] border-b border-[var(--color-warning,#f59e0b)] text-sm">
    <div className="flex items-center gap-2">
      <svg className="w-5 h-5 text-[var(--color-warning,#f59e0b)] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.072 16.5c-.77.833.192 2.5 1.732 2.5z" />
      </svg>
      <span className="text-[var(--color-warning,#f59e0b)] font-medium">
        {t('chat.noProvider.banner' as any, language)}
      </span>
      <button
        onClick={() => router.push('/admin/settings')}
        className="ml-auto text-xs font-semibold text-[var(--color-primary)] hover:underline"
      >
        {t('chat.noProvider.cta' as any, language)}
      </button>
    </div>
  </div>
)}
```

Place this AFTER the compliance banner and BEFORE the chat messages area.

- [ ] **Step 3: Run console tests**

Run: `cd /c/Users/Legion/Documents/nomos/nomos-console && npx vitest run`
Expected: 85/85 passed

- [ ] **Step 4: Commit**

```bash
git add nomos-console/src/app/app/chat/[id]/page.tsx nomos-console/src/lib/i18n/de.ts nomos-console/src/lib/i18n/en.ts
git commit -m "feat(chat): provider status banner — warns when no LLM key configured"
```

---

## Task 7: i18n Completeness (G5)

**Files:**
- Modify: `nomos-console/src/lib/i18n/de.ts`
- Modify: `nomos-console/src/lib/i18n/en.ts`

- [ ] **Step 1: Find hardcoded German/English strings**

Run: `grep -rn "language === " nomos-console/src/app/ | head -30`

Identify all inline ternary translations and replace with i18n keys.

- [ ] **Step 2: Add missing keys**

For each hardcoded string found, add the corresponding key to both de.ts and en.ts.

- [ ] **Step 3: Replace hardcoded strings with t() calls**

In each file that uses `language === 'de' ? '...' : '...'`, replace with `t('key.name', language)`.

- [ ] **Step 4: Run console tests**

Run: `cd /c/Users/Legion/Documents/nomos/nomos-console && npx vitest run`
Expected: 85/85 passed

- [ ] **Step 5: Commit**

```bash
git add nomos-console/src/lib/i18n/de.ts nomos-console/src/lib/i18n/en.ts nomos-console/src/app/
git commit -m "fix(i18n): replace hardcoded strings with t() calls, add missing keys"
```

---

## Task 8: Deployment Guide (G8)

**Files:**
- Create: `docs/quickstart.md`
- Create: `docs/de/schnellstart.md`

- [ ] **Step 1: Create English quickstart**

Write `docs/quickstart.md` covering:
1. Prerequisites (Docker Desktop or Docker Engine, 4GB RAM, ports 80/443)
2. Clone and configure (git clone, cp .env.example .env, fill in secrets)
3. Start (`docker compose up -d`, wait for healthy)
4. Open browser (https://localhost or http://localhost:3040)
5. Bootstrap admin user (first-time setup page or curl command)
6. Configure LLM provider (Settings → API Key)
7. Hire first agent (Hire wizard walkthrough)
8. Chat with agent
9. Troubleshooting (common errors, how to check logs)

- [ ] **Step 2: Create German schnellstart**

Write `docs/de/schnellstart.md` — same content in German with correct umlauts.

- [ ] **Step 3: Ensure docs directory exists**

```bash
mkdir -p docs/de
```

- [ ] **Step 4: Commit**

```bash
git add docs/quickstart.md docs/de/schnellstart.md
git commit -m "docs: quickstart guide EN + DE — complete customer deployment walkthrough"
```

---

## Task 9: Integration Test

**Files:** None (verification only)

- [ ] **Step 1: Rebuild all images**

```bash
cd /c/Users/Legion/Documents/nomos
docker compose build nomos-api nomos-console nomos-worker
```

Expected: All 3 images built without errors.

- [ ] **Step 2: Start fresh stack**

```bash
docker compose down -v
docker compose up -d
```

Wait for all services to be healthy:

```bash
sleep 60 && docker ps --format "table {{.Names}}\t{{.Status}}"
```

Expected: 8/8 services healthy (including nomos-console with new healthcheck).

- [ ] **Step 3: API health check**

```bash
curl -sf http://localhost:8060/health | python -m json.tool
```

Expected: `{"status": "healthy", "service": "NomOS Fleet API", "version": "0.1.0", "vault": "not_configured"}`

- [ ] **Step 4: Bootstrap admin and login**

```bash
curl -sf http://localhost:8060/api/users/bootstrap -X POST \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@nomos.local","password":"NomOS-Admin-2026!"}' \
  -c /tmp/nomos-cookie | python -m json.tool
```

- [ ] **Step 5: Create agent via API**

```bash
curl -sf http://localhost:8060/api/agents -X POST \
  -H 'Content-Type: application/json' \
  -b /tmp/nomos-cookie \
  -d '{"name":"TestAgent","role":"research","company":"TestCo","email":"test@test.com","risk_class":"minimal"}' | python -m json.tool
```

Expected: `"compliance_status": "passed"`

- [ ] **Step 6: Test chat (expect error if no LLM key)**

```bash
curl -sf --max-time 15 http://localhost:8060/api/proxy/chat -X POST \
  -H 'Content-Type: application/json' \
  -b /tmp/nomos-cookie \
  -d '{"agent_id":"testagent","message":"Hello"}' 2>&1
```

Expected: Either a response (if NVIDIA key works) or HTTP 502/503 (expected without valid key — NOT a hang).

- [ ] **Step 7: Browser test**

Open http://localhost:3040 in browser:
1. Login page shows correct German umlauts
2. Login works
3. Dashboard shows TestAgent as "Compliant"
4. Click into agent → Compliance tab → all documents green
5. Click Chat → if no provider: yellow banner with settings link
6. Settings page → editable form, no "read-only" banner

- [ ] **Step 8: HTTPS test**

```bash
curl -sf -k https://localhost/api/health | python -m json.tool
curl -sf -k -I https://localhost/ | grep -E "Strict-Transport|X-Frame|Content-Security"
```

Expected: Health OK + all security headers present.

- [ ] **Step 9: Final commit**

```bash
git add -A
git commit -m "test: integration test passed — 8/8 services, hire-to-chat flow verified"
```

---

## Dependencies

```
Task 1 (G4 Healthcheck)  ──┐
Task 2 (G7 Selina)       ──┤── Parallel, independent
Task 3 (G6 .env)         ──┘

Task 4 (G2 Umlaute)      ──── Must be before Task 5 + Task 7

Task 5 (G1 Chat Errors)  ──┐
Task 6 (G3 Provider)     ──┘── Both modify chat page, do sequentially

Task 7 (G5 i18n)         ──── After Task 4 (umlaut fix first)

Task 8 (G8 Guide)        ──── After all code changes

Task 9 (Integration)     ──── LAST — verifies everything
```
