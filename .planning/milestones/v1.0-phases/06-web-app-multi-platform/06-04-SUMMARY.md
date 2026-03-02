---
phase: 06-web-app-multi-platform
plan: 04
subsystem: api
tags: [fastapi, supabase, chat, photo, preferences, spiciness, mode-switch]

# Dependency graph
requires:
  - phase: 06-03
    provides: WebAdapter, platform_router, NormalizedMessage, _chat_service singleton in webhook.py
  - phase: 06-01
    provides: DB schema with user_preferences table including mode_switch_phrase and spiciness_level
provides:
  - POST /chat — web chat endpoint (WebAdapter pipeline, channel='web' message logging)
  - GET /chat/history — filtered web-channel message history
  - PATCH /preferences/ — partial preference update (preferred_platform, spiciness_level, mode_switch_phrase, notif_prefs)
  - POST /photos/signed-url — 24h Supabase Storage signed URL for photo delivery
  - ChatService.handle_message() extended with custom mode-switch phrase (exact match before fuzzy) and spiciness ceiling
  - intimate_prompt() extended with spiciness_level parameter producing content ceiling instruction
affects:
  - 06-05 (frontend chat page consumes POST /chat + GET /chat/history)
  - 06-06 (frontend settings page consumes PATCH /preferences/ + GET /preferences/)
  - 07 (photo generation phase uses POST /photos/signed-url for delivery)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Single DB fetch per message for preferences (mode_switch_phrase + spiciness_level fetched once, reused for both checks)
    - Deferred import pattern (supabase_admin imported at module level in chat.py, consistent with existing guardrail helpers)
    - PATCH semantics via model_dump(exclude_none=True) — only provided fields written to DB

key-files:
  created:
    - backend/app/routers/web_chat.py
    - backend/app/routers/photo.py
  modified:
    - backend/app/routers/preferences.py
    - backend/app/models/preferences.py
    - backend/app/config.py
    - backend/app/main.py
    - backend/app/services/chat.py
    - backend/app/services/llm/prompts.py

key-decisions:
  - "web_chat.py imports _chat_service from webhook.py — shares same ChatService + SessionStore singleton, avoids second in-memory session store"
  - "Preferences fetched once per message in handle_message() — single DB call covers both mode_switch_phrase check and spiciness_level pass-through"
  - "spiciness_level variable initialized after prefs fetch (before mode switch detection) so it is always defined when reaching LLM call path"
  - "frontend_url defaults to http://localhost:3000 — production URL override via FRONTEND_URL env var"
  - "PreferencesPatchRequest uses model_dump(exclude_none=True) — strict PATCH semantics, no accidental field resets"

patterns-established:
  - "Reuse _chat_service singleton across routers via import — prevents multiple in-memory session stores"
  - "Fetch preferences once per message before gate checks — single DB call covers multiple behavioral extensions"

requirements-completed: [PLAT-02, PLAT-03, PLAT-04]

# Metrics
duration: 11min
completed: 2026-02-24
---

# Phase 6 Plan 04: Web Chat API, Photo Signed URL, Preferences PATCH, and ChatService Extensions Summary

**POST /chat + GET /chat/history (web channel), PATCH /preferences/ with spiciness/mode-phrase fields, POST /photos/signed-url (24h Supabase Storage), and ChatService custom phrase + spiciness ceiling wired through intimate_prompt()**

## Performance

- **Duration:** 11 min
- **Started:** 2026-02-24T17:01:45Z
- **Completed:** 2026-02-24T17:13:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- New web chat router (POST /chat, GET /chat/history) wired through WebAdapter -> platform_router -> ChatService; logs to messages table with channel='web'
- New photo router (POST /photos/signed-url) generating 24h Supabase Storage signed URLs for Phase 7 photo delivery
- Extended preferences router with PATCH /preferences/ accepting preferred_platform, spiciness_level, mode_switch_phrase, notif_prefs
- ChatService.handle_message() gains mode_switch_phrase exact-match check (case-insensitive) running BEFORE fuzzy detect_mode_switch()
- intimate_prompt() extended with spiciness_level parameter appending content ceiling instruction to all persona prompts

## Task Commits

Each task was committed atomically:

1. **Task 1: Web chat router, photo router, preferences extension, and main.py registration** - `96ee2a5` (feat)
2. **Task 2: ChatService — mode_switch_phrase and spiciness_level extensions** - `ef89e97` (feat)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified
- `backend/app/routers/web_chat.py` - POST /chat and GET /chat/history; imports _chat_service from webhook, wraps WebAdapter
- `backend/app/routers/photo.py` - POST /photos/signed-url; 24h signed URL from Supabase Storage 'photos' bucket
- `backend/app/routers/preferences.py` - Added PATCH /preferences/ with PreferencesPatchRequest; PATCH semantics via exclude_none
- `backend/app/models/preferences.py` - Added PreferencesPatchRequest model; extended PreferencesResponse with new Phase 6 fields
- `backend/app/config.py` - Added frontend_url setting (defaults to http://localhost:3000)
- `backend/app/main.py` - Registered web_chat and photo routers; updated CORS to include settings.frontend_url
- `backend/app/services/chat.py` - Added supabase_admin import; custom phrase check + spiciness_level fetch before mode detection; passes spiciness_level to intimate_prompt()
- `backend/app/services/llm/prompts.py` - intimate_prompt() accepts spiciness_level param; appends content ceiling instruction per level

## Decisions Made
- web_chat.py imports `_chat_service` from webhook.py to share the same ChatService + SessionStore singleton — prevents a second in-memory session store that would fragment conversation state
- Preferences (mode_switch_phrase + spiciness_level) fetched in a single DB call once per message; `spiciness_level` variable initialized after the fetch and before mode detection so it is always defined when the LLM code path is reached
- `PreferencesPatchRequest.model_dump(exclude_none=True)` enforces strict PATCH semantics — only fields explicitly sent in the request body are written to the DB
- `frontend_url` defaults to `http://localhost:3000` with production override via `FRONTEND_URL` environment variable

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None — all verifications passed on first run. 47 existing tests continued to pass after ChatService modifications.

## User Setup Required

None — no new external service configuration required. Photo signed-URL endpoint requires Supabase Storage 'photos' bucket to exist (Phase 7 setup concern, not Phase 6).

## Next Phase Readiness
- Frontend chat page (Phase 6 Plan 05) can now consume POST /chat and GET /chat/history
- Frontend settings page (Phase 6 Plan 06) can now consume GET /preferences/ and PATCH /preferences/
- Photo delivery infrastructure is ready for Phase 7 image generation to wire up

## Self-Check: PASSED

All created files exist on disk. Both task commits (96ee2a5, ef89e97) confirmed in git log. 47 tests pass.

---
*Phase: 06-web-app-multi-platform*
*Completed: 2026-02-24*
