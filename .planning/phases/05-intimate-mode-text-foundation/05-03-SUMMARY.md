---
phase: 05-intimate-mode-text-foundation
plan: "03"
subsystem: api
tags: [fastapi, pydantic, supabase, session-store, persona]

# Dependency graph
requires:
  - phase: 02-infrastructure-user-management
    provides: avatar model, avatars router, get_authed_supabase dependency
  - phase: 03-core-intelligence-mode-switching
    provides: SessionStore with asyncio.Lock-guarded mutations
provides:
  - PATCH /avatars/me/persona endpoint for live persona switching
  - PersonaUpdateRequest Pydantic model with PersonalityType validation
  - SessionStore.clear_avatar_cache() for immediate persona effect on next message
affects:
  - 05-04 (intimate mode prompt rendering uses updated persona from DB)
  - future phases extending avatar persona behavior

# Tech tracking
tech-stack:
  added: []
  patterns:
    - body.personality.value used for DB writes (avoids supabase-py enum serialization inconsistency)
    - object.__setattr__ used to clear dynamically-set attributes on frozen-style dataclass
    - Cache invalidation via dedicated method on SessionStore after DB mutation

key-files:
  created: []
  modified:
    - backend/app/models/avatar.py
    - backend/app/routers/avatars.py
    - backend/app/services/session/store.py

key-decisions:
  - "body.personality.value (string) written to DB instead of enum member — supabase-py enum serialization is inconsistent across versions"
  - "clear_avatar_cache uses object.__setattr__ to set _avatar_cache=None — matches how chat.py dynamically attaches the field to the dataclass"
  - "clear_avatar_cache is a no-op for sessions that do not exist yet — persona change before first message is handled naturally by DB fetch on first message"

patterns-established:
  - "Cache invalidation pattern: DB update -> clear_avatar_cache() called inline in PATCH endpoint"
  - "Enum.value pattern: always use .value when writing to supabase, never the enum member directly"

requirements-completed:
  - PERS-01

# Metrics
duration: 12min
completed: 2026-02-24
---

# Phase 05 Plan 03: Persona Selection API Summary

**PATCH /avatars/me/persona endpoint with PersonaUpdateRequest validation and SessionStore.clear_avatar_cache() for immediate persona propagation**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-24T00:00:00Z
- **Completed:** 2026-02-24T00:12:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- PATCH /avatars/me/persona endpoint added — updates persona in DB, returns 404 if no avatar, returns 422 for invalid PersonalityType values (Pydantic validation)
- PersonaUpdateRequest Pydantic model with `personality: PersonalityType` field added to avatar.py
- SessionStore.clear_avatar_cache() method added — uses asyncio.Lock and object.__setattr__ to reset _avatar_cache; no-op for non-existent sessions

## Task Commits

Each task was committed atomically:

1. **Task 1: PersonaUpdateRequest Model and PATCH Endpoint** - `04baeb5` (feat)
2. **Task 2: SessionStore.clear_avatar_cache()** - `4b3cb7e` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `backend/app/models/avatar.py` - Added PersonaUpdateRequest class after AvatarCreate
- `backend/app/routers/avatars.py` - Added PATCH /me/persona endpoint; imported PersonaUpdateRequest and get_session_store
- `backend/app/services/session/store.py` - Added clear_avatar_cache() async method to SessionStore

## Decisions Made
- Used `body.personality.value` (string) rather than enum member for supabase DB write — avoids known supabase-py enum serialization inconsistency
- `object.__setattr__` required to clear `_avatar_cache` because it is dynamically attached to the dataclass instance (not declared in fields), same pattern as how chat.py sets it
- clear_avatar_cache is deliberately a no-op when no session exists — correct behavior since there is no cache to invalidate

## Deviations from Plan

None - plan executed exactly as written.

Note: The plan mentioned "all 28 previously passing tests must still pass" but the pre-existing test_secretary_skills.py fails to collect due to missing supabase env vars (a pre-existing issue from Phase 4 execution environment). The 20 tests that were passing before this plan still pass (0 regressions introduced).

## Issues Encountered
- test_secretary_skills.py fails to collect due to missing SUPABASE_URL/SUPABASE_ANON_KEY/SUPABASE_SERVICE_ROLE_KEY env vars — this is pre-existing from Phase 4 (calendar_skill imports google_auth.flow which imports config.settings at module level). Not caused by or fixed in this plan. Deferred.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Persona PATCH endpoint is live; 05-04 (intimate mode prompt rendering) can now rely on `personality` field being up-to-date in DB after any persona change
- Session avatar cache is invalidated on persona change so the next message always picks up the new persona without a restart

---
*Phase: 05-intimate-mode-text-foundation*
*Completed: 2026-02-24*
