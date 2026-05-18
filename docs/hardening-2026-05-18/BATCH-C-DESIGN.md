# Batch C — Context Pipeline + Vault + Monitoring: Implementation Design

> Produced by nomos-architect (read-only investigation), 2026-05-19.
> Verified root causes. Implementer follows the ordered action list verbatim.

## Spec decision
`docs/superpowers/specs/2026-04-13-context-management-design.md` describes APIs that
do not exist (MemoryManager.process_context, is_summary/token_count columns, plugin
hooks). DO NOT chase the spec. Implement minimal real wiring against the existing
code shape (`ContextPipeline.process_new_message`, `[SUMMARY]:` text marker, no new
columns / no migration / no plugin hooks — YAGNI). Add a `Status: Superseded by
Batch C` header to the spec.

## Root causes (verified)
- **Context tests (5):** `context_pipeline.py:16` imports `store_message, list_messages`
  by name → tests patching `memory.store_message` are ineffective → real DB funcs run
  against a MagicMock session. Fix: `from nomos_api.services import memory` + call via
  `memory.<fn>`.
- **test_empty_context_handling:** TEST wrong — not async, missing `await`/mark.
- **test_prune_old_context:** CODE wrong — `prune_old_context` counts but never deletes.
- **test_monitoring::test_alert_service_threshold_check:** CODE wrong — `Alert.id`
  is `String(128)` PK with no default; `AlertService.check_alerts` creates `Alert(...)`
  without `id` → IntegrityError on NULL PK. Fix: `id=str(uuid.uuid4())` in metrics.py:111.
- **test_vault_client_enhanced::test_get_secret_not_found:** CODE wrong —
  `vault_client.py:121` broad `except Exception` swallows `VaultSecretNotFoundError`.
  Fix: `if isinstance(exc, VaultError): raise` at top of the handler.

## Ordered action list (run pytest + ruff after EACH step — rule 04/05)
1. `vault_client.py:~121` — add `if isinstance(exc, VaultError): raise` at top of broad
   except. Run `pytest tests/test_vault_client_enhanced.py`.
2. `services/metrics.py` — `import uuid`; line 111 add `id=str(uuid.uuid4())`. Run
   `pytest tests/test_monitoring.py`.
3. `services/context_pipeline.py:16` — `from nomos_api.services import memory`; update
   calls (lines ~48,51,93,116,142,168) to `memory.<fn>`. Run context tests.
4. `services/memory.py` — add `async def prune_messages(db, agent_id, session_id,
   keep_recent) -> int`: delete oldest non-`[SUMMARY]` rows for the pair below the
   keep_recent-th-newest id; commit; return rowcount. Summaries always retained
   (DSGVO-safe: only oldest non-summary turns removed).
5. `context_pipeline.py:162-187` — `prune_old_context` delegates to
   `memory.prune_messages`; remove "would prune" placeholder + misleading comment 70-72.
6. `tests/test_context_pipeline.py` — fix `test_empty_context_handling` (async/await/
   `@pytest.mark.asyncio`/patch `memory.list_messages`); `test_prune_old_context`
   patch target → `memory.prune_messages`. Run full file.
7. `routers/proxy.py` — keep Batch B auth (`user`, `db`, `check_agent_access`). After
   `check_agent_access` and before the stateless `messages=[...]`: 
   `pipeline = ContextPipeline()`;
   `await pipeline.process_new_message(db, request.agent_id, session_id, "user", request.message)`;
   `messages = await pipeline.get_managed_context(db, request.agent_id, session_id)`
   (do NOT also append request.message). After a successful LLM/gateway response,
   before BOTH success returns: `await memory.store_message(db, request.agent_id,
   session_id, "assistant", response_text)`. NOT on 502/503 error branches.
8. Spec — add `Status: Superseded by Batch C` reconciliation header.
9. Follow-up flag: ARQ cron entry calling `prune_old_context` per (agent_id,
   session_id) with keep_recent=50. If out of Batch C scope, leave prune real-but-
   uncalled (now truthful) + note the cron hook.
10. Full `pytest` (expect ~388 passing) + `ruff check` + `docker compose up` browser
    two-turn verification (second response must show prior-turn context;
    `agent_memory` has 4 rows).

## Regression guards
- Golden path: first turn still yields exactly one user + one assistant message;
  `get_managed_context` returns the user turn on an empty session (stored before read).
- Do NOT re-append `request.message` (would double-store).
- The 5 mocked context tests never touch a real DB after step 3 — safe.
- isinstance-guard / uuid id are additive — no regression to the 379.
