---
phase: 04-secretary-skills
plan: "03"
subsystem: api
tags: [google-calendar, oauth2, asyncio, dateparser, session-state, skills]

# Dependency graph
requires:
  - phase: 04-secretary-skills/04-01
    provides: Skill Protocol, ParsedIntent dataclass, skill registry with register()/get()/list_skills()
  - phase: 04-secretary-skills/04-02
    provides: Google OAuth2 flow (get_credentials_for_user, get_auth_url), token storage (save/get/delete_calendar_tokens)
  - phase: 03-core-intelligence-mode-switching
    provides: SessionState in session/store.py, SessionStore with asyncio.Lock pattern

provides:
  - CalendarSkill class implementing SECR-01 (calendar_add) and SECR-02 (calendar_view)
  - PendingCalendarAdd dataclass for conflict confirmation state machine
  - execute_pending_add() helper for ChatService to call after user confirms conflict
  - SessionState.pending_calendar_add field for in-session conflict confirmation gate
  - Both intents registered in skill registry at module import time

affects:
  - 04-secretary-skills/04-04 (ChatService update — Plan 05 must wire confirmation gate and pass session to skill.handle())
  - 04-secretary-skills/04-05 (end-to-end verification of calendar flows)

# Tech tracking
tech-stack:
  added: [dateparser (FR+EN multilingual date parsing)]
  patterns:
    - asyncio.to_thread wrapping all synchronous Google API calls
    - Clarification gate pattern: pending field on SessionState, checked by ChatService before intent classification
    - Skill registration at module import time via register() call at module level
    - Any | None field type to avoid circular imports between store.py and calendar_skill.py

key-files:
  created:
    - backend/app/services/skills/calendar_skill.py
  modified:
    - backend/app/services/session/store.py

key-decisions:
  - "pending_calendar_add typed as Any | None in store.py to avoid circular import (store -> calendar_skill -> store)"
  - "CONFLICT_CONFIRM_KEYWORDS not defined in calendar_skill.py — belongs in chat.py (Plan 05) so confirmation check runs before intent classification"
  - "CalendarSkill.handle() accepts optional session kwarg to keep Skill Protocol stable while enabling conflict state storage"
  - "Default event duration is 1 hour — no explicit duration parsing needed for MVP"
  - "_check_conflicts returns empty list on error (non-fatal) — proceed to create rather than blocking the user"

patterns-established:
  - "Clarification gate pattern: store pending state on SessionState, ChatService intercepts next message before intent classification"
  - "asyncio.to_thread wrapping: all synchronous Google API calls (_query, _insert, build) run in thread pool"
  - "Graceful auth error handling: RefreshError deletes tokens + returns reconnect URL; None creds returns connect URL"

requirements-completed: [SECR-01, SECR-02]

# Metrics
duration: 8min
completed: 2026-02-24
---

# Phase 4 Plan 03: Calendar Skill Summary

**CalendarSkill with Google Calendar API v3 integration, multilingual date parsing (FR+EN), conflict detection with session-state confirmation loop, and asyncio.to_thread wrapping for all synchronous API calls**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-24T09:30:33Z
- **Completed:** 2026-02-24T09:38:33Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `pending_calendar_add: Any | None = None` field to SessionState using `Any` type to avoid circular imports, mirroring the existing `pending_switch_to` clarification gate pattern
- Created CalendarSkill implementing calendar_add (SECR-01) with missing-field prompting, dateparser-based FR+EN date parsing, conflict detection with PendingCalendarAdd session storage, and "Added: Title · Day · Time" confirmation format
- Created CalendarSkill implementing calendar_view (SECR-02) listing upcoming events in "bullet Day Time — Title" format
- All Google Calendar API calls (build, events.list, events.insert) wrapped in asyncio.to_thread — FastAPI event loop never blocked
- Both intents registered in skill registry at module import time; execute_pending_add() exported for ChatService (Plan 05) to call after user confirms conflict

## Task Commits

Each task was committed atomically:

1. **Task 1: Add pending_calendar_add field to SessionState** - `b663e96` (feat)
2. **Task 2: Implement CalendarSkill with conflict confirmation via session state** - `b968c7d` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `backend/app/services/session/store.py` - Added `from typing import Any` and `pending_calendar_add: Any | None = None` field to SessionState dataclass
- `backend/app/services/skills/calendar_skill.py` - New file: CalendarSkill class (handle/\_handle\_add/\_handle\_view), PendingCalendarAdd dataclass, execute\_pending\_add() helper, response templates, all helper functions (\_get\_service, \_check\_conflicts, \_create\_event, \_list\_events, \_parse\_user\_date, \_format\_event\_time), registry registration

## Decisions Made

- **Any | None for pending_calendar_add:** Avoided importing PendingCalendarAdd directly in store.py to prevent circular dependency. Type narrowing occurs in chat.py (Plan 05) where calendar_skill is already imported.
- **CONFLICT_CONFIRM_KEYWORDS excluded from calendar_skill.py:** The confirmation keyword check belongs in chat.py so it runs before intent classification — otherwise "yes" gets classified as "chat" intent, bypassing the confirmation handler entirely.
- **Optional session kwarg on handle():** CalendarSkill.handle() accepts `session=None` to keep the Skill Protocol interface stable. ChatService passes session explicitly for calendar_add; absence is logged as a warning with degraded behavior (no pending state stored).
- **Non-fatal conflict check failure:** If _check_conflicts raises, the exception is caught and logged, and event creation proceeds. Better UX than blocking the user on a transient API error.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. All verification commands passed on first run. 20 existing tests continue to pass.

## User Setup Required

None - no external service configuration required for this plan. Google Calendar OAuth credentials were handled in Plan 02.

## Next Phase Readiness

- CalendarSkill ready for Plan 05 (ChatService integration): ChatService must add the `pending_calendar_add` confirmation gate (check session field before intent classification, call `execute_pending_add()` on confirmation, pass `session` kwarg to `skill.handle()` for calendar_add intents)
- Import pattern for Plan 05: `from app.services.skills.calendar_skill import execute_pending_add, PendingCalendarAdd`
- No blockers.

## Self-Check: PASSED

- FOUND: backend/app/services/skills/calendar_skill.py
- FOUND: backend/app/services/session/store.py (with pending_calendar_add field)
- FOUND: .planning/phases/04-secretary-skills/04-03-SUMMARY.md
- FOUND commit: b663e96 (feat(04-03): add pending_calendar_add field to SessionState)
- FOUND commit: b968c7d (feat(04-03): implement CalendarSkill with conflict confirmation via session state)
- All 20 existing tests passing

---
*Phase: 04-secretary-skills*
*Completed: 2026-02-24*
