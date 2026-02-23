---
phase: 03-core-intelligence-mode-switching
plan: 03
subsystem: api
tags: [openai, fastapi, webhook, chatservice, session, mode-detection, llm, whatsapp]

# Dependency graph
requires:
  - phase: 03-core-intelligence-mode-switching
    provides: "SessionStore, get_session_store(), ConversationMode enum, detect_mode_switch(), DetectionResult (03-02)"
  - phase: 03-core-intelligence-mode-switching
    provides: "OpenAIProvider, LLMProvider Protocol, secretary_prompt(), intimate_prompt() (03-01)"
  - phase: 02-infrastructure-user-management
    provides: "lookup_user_by_phone(), supabase_admin, send_whatsapp_message(), webhook.py scaffolding"

provides:
  - "get_avatar_for_user() in user_lookup.py — fetches avatar row from Supabase avatars table via supabase_admin"
  - "ChatService class with handle_message() — stateless orchestrator covering all 5 message flow branches"
  - "webhook.py upgraded: echo replaced by AI pipeline using ChatService singletons"
  - "Module-level _llm_provider (OpenAIProvider) and _chat_service (ChatService) singletons in webhook.py"
  - "Message persistence to Supabase with avatar_id populated from avatar row"

affects:
  - 03-core-intelligence-mode-switching
  - 04-api-conversation-endpoints (will import ChatService for REST chat endpoint)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Module-level singletons: OpenAIProvider and ChatService instantiated once at import time — shared across all requests"
    - "Avatar fetched per request but cached in SessionState._avatar_cache to avoid repeated DB calls"
    - "Reply sent BEFORE Supabase logging — DB failure cannot prevent message delivery"
    - "object.__setattr__ for dynamic attribute on regular dataclass instance"

key-files:
  created:
    - "backend/app/services/chat.py"
  modified:
    - "backend/app/services/user_lookup.py — added get_avatar_for_user()"
    - "backend/app/routers/webhook.py — replaced echo with AI pipeline, added ChatService singletons"

key-decisions:
  - "ChatService is a stateless orchestrator — all mutable state lives in SessionStore. Designed for module-level singleton use."
  - "Avatar fetched per-request in webhook.py and passed into handle_message() rather than fetched inside ChatService — keeps ChatService testable without DB"
  - "send_whatsapp_message() called BEFORE Supabase logging — ensures reply is never blocked by a DB failure"
  - "avatar_id now populated from avatar['id'] in Supabase message logging (was hardcoded None in Phase 2 echo)"

patterns-established:
  - "Pattern: ChatService.handle_message() branches on DetectionResult.confidence — exact/fuzzy act, ambiguous ask, pending resolve yes/no, none route to LLM"
  - "Pattern: Onboarding guard first — avatar None returns ONBOARDING_PROMPT immediately before any session/LLM logic"
  - "Pattern: LLM error caught inline — returns LLM_ERROR_MSG fallback string, never raises to webhook caller"

requirements-completed: [CHAT-01, CHAT-02, CHAT-03, CHAT-04, CHAT-05]

# Metrics
duration: 12min
completed: 2026-02-23
---

# Phase 03 Plan 03: ChatService Orchestrator and Webhook AI Pipeline Summary

**ChatService orchestrator with 5-branch message routing wired into webhook.py, replacing Phase 2 echo with a full AI pipeline (LLM + session + mode detection + Supabase persistence)**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-23T20:42:12Z
- **Completed:** 2026-02-23T20:54:32Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Created `backend/app/services/chat.py` with `ChatService.handle_message()` covering all 5 flow branches: no avatar (onboarding prompt), exact/fuzzy mode switch (immediate action), ambiguous match (clarification question), pending resolution (yes/no gate), normal message (LLM call with mode-isolated history)
- Extended `user_lookup.py` with `get_avatar_for_user()` — queries the `avatars` table via supabase_admin and returns dict or None
- Upgraded `webhook.py` from Phase 2 echo to full AI pipeline: OpenAIProvider + ChatService singletons at module level, avatar fetched per-request, reply sent before Supabase logging

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend user_lookup.py with get_avatar_for_user() and create ChatService** - `e9ec559` (feat)
2. **Task 2: Upgrade webhook.py to use ChatService (replace echo with AI pipeline)** - `da62877` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `backend/app/services/chat.py` — ChatService orchestrator: handle_message() with 5-branch routing (onboarding, exact switch, fuzzy switch, ambiguous, LLM), mode-isolated history snapshots, avatar caching in session
- `backend/app/services/user_lookup.py` — added get_avatar_for_user() fetching avatars table row via supabase_admin
- `backend/app/routers/webhook.py` — replaced echo with AI pipeline; module-level _llm_provider and _chat_service singletons; send_whatsapp_message() called before Supabase logging; avatar_id populated from avatar row

## Decisions Made

- ChatService designed as a stateless orchestrator (no instance state beyond injected LLM and SessionStore). This enables module-level singleton use in webhook.py without concurrency issues — all mutable state is in SessionStore behind asyncio.Lock.
- Avatar fetched in webhook.py and passed into handle_message() rather than fetched inside ChatService. This keeps ChatService testable without a real Supabase connection.
- Reply sent before Supabase message logging. DB write failure must never prevent message delivery — the user already received the reply, so a logging failure is non-critical.
- avatar_id now populated from avatar["id"] (was hardcoded None in Phase 2). Supabase message rows are now properly linked to the avatar.

## Deviations from Plan

None - plan executed exactly as written. The note in the plan about `object.__setattr__` treating SessionState "as if frozen" is technically imprecise (SessionState is a regular dataclass, not frozen), but the `object.__setattr__` call works correctly and was kept as specified for consistency with the plan's documented reasoning.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required. OpenAI API key must be set in `backend/.env` as `OPENAI_API_KEY` (documented in pending todos; was already a pending item from Phase 3 Plan 01).

## Next Phase Readiness

- Full WhatsApp AI pipeline is operational: incoming message -> user lookup -> avatar fetch -> ChatService (mode detection + session + LLM) -> send reply -> log to Supabase
- Phase 3 Plan 03 satisfies all 5 CHAT requirements (CHAT-01 through CHAT-05)
- Next: Phase 3 Plan 04 or 05 can add REST chat endpoint (import ChatService from app.services.chat) or end-to-end tests
- No blockers

## Self-Check: PASSED

- FOUND: backend/app/services/chat.py
- FOUND: backend/app/services/user_lookup.py (with get_avatar_for_user)
- FOUND: backend/app/routers/webhook.py (no echo, has handle_message)
- FOUND commit: e9ec559 (Task 1)
- FOUND commit: da62877 (Task 2)
- All 3 files pass py_compile
- grep Echo returns no results

---
*Phase: 03-core-intelligence-mode-switching*
*Completed: 2026-02-23*
