---
phase: 07-avatar-system-production
plan: 10
subsystem: database
tags: [supabase, pgrst204, migration, fastapi, pydantic]

# Dependency graph
requires:
  - phase: 07-avatar-system-production
    provides: avatars table schema, AvatarResponse model, POST /avatars/me/reference-image endpoint
  - phase: 07-avatar-system-production plan 07-09
    provides: BackgroundTasks fire-and-forget pattern and pollForReferenceImage frontend polling loop
provides:
  - reference_image_url TEXT column in public.avatars (applied via Supabase Dashboard)
  - AvatarResponse.reference_image_url field (Optional[str] = None)
  - Idempotent ALTER TABLE in migration 004 (IF NOT EXISTS guard)
  - GAP-4 closed: PGRST204 crash on POST /avatars/me/reference-image eliminated
affects:
  - 07-VERIFICATION.md
  - Human verification of full avatar onboarding flow

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Idempotent migration pattern: ADD COLUMN IF NOT EXISTS for safe re-runs"
    - "Model field parity: AvatarResponse must mirror all columns written by background tasks"

key-files:
  created: []
  modified:
    - backend/migrations/004_phase7_avatar_fields.sql
    - backend/app/models/avatar.py
    - .planning/phases/07-avatar-system-production/07-VERIFICATION.md

key-decisions:
  - "reference_image_url TEXT column added to migration 004 with IF NOT EXISTS guard — idempotent, safe to re-run"
  - "AvatarResponse.reference_image_url placed between nationality and created_at to match DB column order and enable frontend polling detection"
  - "Supabase Dashboard SQL Editor used for live schema update — Claude cannot apply SQL to Supabase automatically"

patterns-established:
  - "Background task write-back fields must be in both the migration ALTER TABLE block AND the Pydantic response model — missing either causes PGRST204 or silent polling failure"

requirements-completed: [AVTR-05]

# Metrics
duration: 15min
completed: 2026-03-02
---

# Phase 7 Plan 10: GAP-4 Fix — reference_image_url Column Missing from Migration and AvatarResponse

**PGRST204 crash on POST /avatars/me/reference-image eliminated by adding reference_image_url TEXT to migration 004 ALTER TABLE block and to AvatarResponse model, then applying the column via Supabase Dashboard.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-02T12:00:00Z
- **Completed:** 2026-03-02T12:15:00Z
- **Tasks:** 4 (Tasks 1-3 completed in prior session; Task 4 completed in this session)
- **Files modified:** 3

## Accomplishments

- Identified two root causes of the PGRST204 crash: missing DB column in migration 004 and missing field in AvatarResponse
- Added `ADD COLUMN IF NOT EXISTS reference_image_url TEXT` to the ALTER TABLE block in `backend/migrations/004_phase7_avatar_fields.sql`
- Added `reference_image_url: Optional[str] = None` to `AvatarResponse` in `backend/app/models/avatar.py`
- Human applied the SQL via Supabase Dashboard SQL Editor — column confirmed present via information_schema query (one row returned: `reference_image_url | text | YES`)
- Updated VERIFICATION.md to record GAP-4 closed in both frontmatter `gaps_closed` list and Gaps Summary prose section

## Task Commits

Each task was committed atomically:

1. **Task 1: Audit the two applied fixes** - (no new commit — fixes already on disk, verified only)
2. **Task 2: Commit the two gap-4 fixes** - `8e8a524` (fix)
3. **Task 3: Apply migration SQL in Supabase Dashboard** - N/A (manual human step, no commit)
4. **Task 4: Update VERIFICATION.md to record GAP-4 closed** - `85c7fdb` (docs)

## Files Created/Modified

- `backend/migrations/004_phase7_avatar_fields.sql` - Added `ADD COLUMN IF NOT EXISTS reference_image_url TEXT` to Part 1 ALTER TABLE block
- `backend/app/models/avatar.py` - Added `reference_image_url: Optional[str] = None` to `AvatarResponse` between nationality and created_at
- `.planning/phases/07-avatar-system-production/07-VERIFICATION.md` - GAP-4 recorded in frontmatter gaps_closed list, Gaps Summary section, and closing line updated to reference plan 07-10

## Decisions Made

- The IF NOT EXISTS guard on the ADD COLUMN makes the migration idempotent — confirmed safe for future re-runs
- AvatarResponse field added between nationality and created_at to maintain logical column ordering
- Supabase SQL Editor was the only available path for live schema update (Claude cannot authenticate to Supabase dashboards)

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None. The human confirmed the Supabase SQL ran successfully and the column was verified via information_schema query before Task 4 proceeded.

## User Setup Required

The Supabase schema update (Task 3) was a one-time manual step. No further setup is required for GAP-4.

The Supabase Dashboard SQL Editor was used to run:
```sql
ALTER TABLE public.avatars
  ADD COLUMN IF NOT EXISTS reference_image_url TEXT;
```
Verified by: `SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'avatars' AND column_name = 'reference_image_url';` — returned one row.

## Next Phase Readiness

- All four code-level gaps (GAP-1 through GAP-4) are now closed
- POST /avatars/me/reference-image no longer crashes with PGRST204
- GET /avatars/me now returns reference_image_url (null while generating, non-null when ready)
- Frontend polling loop (pollForReferenceImage) can detect and display the generated image
- Phase 7 is complete at code level — human verification of the full live onboarding flow remains the final gate (see 07-VERIFICATION.md Human Verification Required section)
- Requirements AVTR-01 through AVTR-05, INTM-03, ARCH-03, BILL-01, BILL-02 can be marked complete after successful human verification

---
*Phase: 07-avatar-system-production*
*Completed: 2026-03-02*
