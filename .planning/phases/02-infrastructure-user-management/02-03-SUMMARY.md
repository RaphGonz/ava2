---
phase: 02-infrastructure-user-management
plan: 03
subsystem: api
tags: [fastapi, pydantic, supabase, avatars, preferences, e164, rls, html-template]

# Dependency graph
requires:
  - phase: 02-infrastructure-user-management
    plan: 01
    provides: FastAPI scaffold, Supabase clients, get_authed_supabase dependency, personality_type DB enum, avatars and user_preferences tables with RLS

provides:
  - POST /avatars endpoint with one-avatar-per-user enforcement and age >= 20 validation (Pydantic Field ge=20 + DB CHECK)
  - GET /avatars/me endpoint returning user's avatar or 404
  - PUT /preferences/whatsapp endpoint accepting PhoneLinkRequest body with E.164 field_validator
  - GET /preferences/ endpoint returning PreferencesResponse or 404
  - GET /dev/onboarding barebones HTML page for browser testing of avatar creation and phone linking
  - AvatarCreate, AvatarResponse, PersonalityType, PhoneLinkRequest, PreferencesResponse Pydantic models

affects: [02-04, 02-05, 03-core-intelligence, all-backend-phases]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Pydantic Field(ge=20) for numeric floor constraints (mirrors DB CHECK constraint for early HTTP 422 feedback)
    - Pydantic field_validator for format validation (E.164 phone numbers)
    - Request body (PhoneLinkRequest) instead of query param for phone input (proper REST semantics, enables Pydantic validation)
    - dev router pattern: pathlib.Path relative to __file__ for template resolution, 404 in non-development

key-files:
  created:
    - backend/app/models/preferences.py
    - backend/templates/onboarding.html
  modified:
    - backend/app/models/avatar.py
    - backend/app/routers/preferences.py
    - backend/app/routers/dev.py

key-decisions:
  - "Pydantic Field(ge=20) used on AvatarCreate.age in addition to field_validator — ge= on the Field produces Pydantic's GreaterThanEqual annotation which generates correct JSON Schema and matches plan spec exactly"
  - "PhoneLinkRequest body (not query param) for PUT /preferences/whatsapp — correct REST semantics and enables Pydantic validation before handler runs"
  - "GET /preferences/ returns 404 (not empty object) when no preferences row exists — matches plan spec; empty row would hide the distinction between 'never linked' and 'linked with no phone'"

patterns-established:
  - "Pattern: Dev router uses pathlib.Path(__file__).parent.parent.parent / 'templates' for template resolution — portable, not hardcoded"
  - "Pattern: All user-facing endpoints use get_authed_supabase (RLS enforced) — supabase_admin is only for webhook phone lookup"

requirements-completed: [USER-03]

# Metrics
duration: 15min
completed: 2026-02-23
---

# Phase 2 Plan 03: Avatar and Preferences API Summary

**Avatar creation and phone-linking API endpoints with Pydantic Field(ge=20) age enforcement, E.164 field_validator, and barebones onboarding dev page**

## Performance

- **Duration:** 15 min
- **Started:** 2026-02-23T13:40:24Z
- **Completed:** 2026-02-23T14:05:38Z
- **Tasks:** 2
- **Files modified:** 5 (3 modified, 2 created)

## Accomplishments

- Avatar Pydantic models updated: `AvatarCreate` uses `Field(ge=20)` for age (HTTP 422 on violation), full field constraints (min_length, max_length), `AvatarResponse` uses proper `PersonalityType` enum and `datetime` type
- Created `preferences.py` model with `PhoneLinkRequest` (E.164 field_validator) and `PreferencesResponse` — preferences router updated to use request body instead of query param
- Created `onboarding.html` barebones dev page with token input, avatar creation form (6 personality options, age min=20), phone-linking form, and get-avatar button — all fetch calls use `Authorization: Bearer` header

## Task Commits

Each task was committed atomically:

1. **Task 1: Avatar and preferences Pydantic models and API endpoints** - `c82dc53` (feat)
2. **Task 2: Barebones onboarding dev page for avatar creation and phone linking** - `a3a8b27` (feat)

**Plan metadata:** (docs commit — pending)

## Files Created/Modified

- `backend/app/models/avatar.py` - Updated: `Field(ge=20)` on age, `Field(min_length=1, max_length=100)` on name, `Field(None, max_length=2000)` on physical_description, `AvatarResponse` uses `PersonalityType` enum and `datetime`
- `backend/app/models/preferences.py` - Created: `PhoneLinkRequest` with `field_validator` for E.164, `PreferencesResponse` Pydantic model
- `backend/app/routers/preferences.py` - Updated: `PUT /preferences/whatsapp` accepts `PhoneLinkRequest` body, `GET /preferences/` returns `PreferencesResponse` or 404
- `backend/app/routers/dev.py` - Updated: Added `GET /dev/onboarding` route serving `onboarding.html` (development-only, 404 in production)
- `backend/templates/onboarding.html` - Created: Barebones HTML with token input, avatar form, phone form, no external dependencies

## Decisions Made

- **Field(ge=20) over field_validator only:** The plan spec shows `Field(..., ge=20)` — this produces Pydantic's `GreaterThanEqual` annotation (visible in `model_fields["age"].metadata = [Ge(ge=20)]`) and generates correct JSON Schema. The prior field_validator-only approach also rejected age<20, but didn't produce the proper Field constraint metadata the plan required.
- **Request body for phone linking:** Changed `PUT /preferences/whatsapp` from `phone: str` query param to `body: PhoneLinkRequest` request body. Enables Pydantic validation (422 on invalid E.164) before handler code runs. Correct REST semantics for a write operation.
- **GET /preferences/ returns 404:** Matches plan spec — if no preferences row exists, return 404. Returning an empty/null object would hide the distinction between "never configured" and "configured with no phone."

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] dev.py already existed with /dev/auth, no separate creation needed**
- **Found during:** Task 2 (dev router)
- **Issue:** Plan 02-02 had already created dev.py with the `/dev/auth` route. Plan 02-03 said "add the new route to the existing dev router" — this is exactly what was done.
- **Fix:** Added only `GET /dev/onboarding` to the existing dev.py. The `/dev/auth` route was not modified.
- **Files modified:** backend/app/routers/dev.py
- **Verification:** grep confirms both `/dev/auth` and `/dev/onboarding` present, existing auth route untouched
- **Committed in:** a3a8b27 (Task 2 commit)

---

**Total deviations:** 1 (non-breaking — additive only, no existing behavior changed)
**Impact on plan:** Dev router was pre-created by Plan 02-02. Added /dev/onboarding as specified without disrupting existing /dev/auth. No scope creep.

## Issues Encountered

- Python/pydantic not installed in the shell environment — used `py -3` Windows launcher with manual pip install of pydantic and fastapi for model verification. Full integration test requires real Supabase credentials (expected).

## User Setup Required

None — no new external service configuration required. All endpoints use existing Supabase configuration from Plan 01.

## Next Phase Readiness

- Avatar and preferences endpoints complete — Plan 02-04 (WhatsApp webhook) can use user_lookup and preferences data to route messages
- Onboarding dev page at `/dev/onboarding` ready for browser testing once backend is running with real Supabase credentials
- All user-facing endpoints correctly use `get_authed_supabase` (RLS enforced), consistent with architecture decision from Plan 01

---
*Phase: 02-infrastructure-user-management*
*Completed: 2026-02-23*
