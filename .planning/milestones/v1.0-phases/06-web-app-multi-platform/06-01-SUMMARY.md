---
phase: 06-web-app-multi-platform
plan: 01
subsystem: database
tags: [postgres, supabase, migration, sql, enum, jsonb, check-constraint, index]

# Dependency graph
requires:
  - phase: 02-infrastructure-user-management
    provides: "user_preferences table and message_channel enum in 001_initial_schema.sql"
provides:
  - "003_phase6_preferences.sql: Phase 6 schema migration ready to apply to Supabase"
  - "preferred_platform column on user_preferences (TEXT, default 'whatsapp', CHECK IN ('whatsapp','web'))"
  - "spiciness_level column on user_preferences (TEXT, default 'mild', CHECK IN ('mild','spicy','explicit'))"
  - "mode_switch_phrase column on user_preferences (nullable TEXT)"
  - "notif_prefs column on user_preferences (JSONB, default '{}')"
  - "message_channel enum extended with 'web' value"
  - "idx_user_preferences_preferred_platform index on (user_id, preferred_platform)"
affects:
  - 06-web-app-multi-platform (all subsequent plans depend on these columns)
  - platform_router.py (reads preferred_platform for routing decisions)
  - web chat endpoints (write channel='web' to messages table)
  - preference endpoints (read/write new columns)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ALTER TYPE ADD VALUE placed outside BEGIN/COMMIT block — PostgreSQL restriction on enum mutations"
    - "DO $$ EXCEPTION WHEN duplicate_object THEN NULL guard — idempotent constraint additions safe for re-run"
    - "IF NOT EXISTS on ADD COLUMN — migration is safe to re-apply without errors"

key-files:
  created:
    - backend/migrations/003_phase6_preferences.sql
  modified: []

key-decisions:
  - "ALTER TYPE message_channel ADD VALUE IF NOT EXISTS 'web' placed before BEGIN block — PostgreSQL does not permit ADD VALUE inside a transaction"
  - "preferred_platform defaults to 'whatsapp' so all existing users retain current behaviour after migration"
  - "spiciness_level defaults to 'mild' (most conservative) — existing users unaffected"
  - "mode_switch_phrase is nullable TEXT with no default — NULL means use system phrase defaults, not an error"
  - "notif_prefs is JSONB NOT NULL DEFAULT '{}' — empty object means use system notification defaults"
  - "CHECK constraints wrapped in DO $$ EXCEPTION WHEN duplicate_object guard — migration is idempotent"
  - "Index covers (user_id, preferred_platform) to enable index-only scans for platform_router.py lookup"

patterns-established:
  - "Pattern: Migration idempotency — ADD COLUMN IF NOT EXISTS + DO $$ constraint guards allow safe re-runs"
  - "Pattern: Enum extension before transaction — always place ALTER TYPE ADD VALUE before BEGIN block"

requirements-completed: [PLAT-02, PLAT-04, PLAT-05]

# Metrics
duration: 5min
completed: 2026-02-24
---

# Phase 6 Plan 01: Phase 6 DB Migration Summary

**PostgreSQL migration adding preferred_platform, spiciness_level, mode_switch_phrase, and notif_prefs columns to user_preferences with CHECK constraints, plus message_channel enum extended to include 'web'**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-24T15:40:10Z
- **Completed:** 2026-02-24T15:45:00Z
- **Tasks:** 1 of 1
- **Files modified:** 1

## Accomplishments

- Created `backend/migrations/003_phase6_preferences.sql` — 111-line atomic migration ready to apply to Supabase
- Extended `message_channel` enum with 'web' value (ALTER TYPE outside transaction as required by PostgreSQL)
- Added four new columns to `public.user_preferences` with IF NOT EXISTS guards and appropriate defaults
- Added CHECK constraints on `preferred_platform` and `spiciness_level` with DO $$ duplicate-object guards
- Added performance index `idx_user_preferences_preferred_platform` on `(user_id, preferred_platform)` for platform_router.py

## Task Commits

Each task was committed atomically:

1. **Task 1: Write Phase 6 DB migration SQL** - `6aae159` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `backend/migrations/003_phase6_preferences.sql` — Phase 6 schema migration: enum extension + four new user_preferences columns + constraints + index

## Decisions Made

- ALTER TYPE ADD VALUE placed BEFORE the BEGIN block (PostgreSQL restriction — cannot run inside transaction)
- `preferred_platform` defaults to `'whatsapp'` and `spiciness_level` defaults to `'mild'` so all existing rows are valid after migration
- `mode_switch_phrase` is nullable with no default — NULL signals "use system default phrases"
- `notif_prefs` is JSONB NOT NULL DEFAULT `'{}'` — empty object means system defaults apply; explicit keys override
- CHECK constraints use `DO $$ EXCEPTION WHEN duplicate_object THEN NULL` guard for safe re-runs
- Index on `(user_id, preferred_platform)` chosen over `(user_id)` alone to allow index-only scans

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

**Apply migration to Supabase before proceeding to Phase 6 Plans 02+.**

Run the migration via either method documented in the file header:

- **Supabase Dashboard:** Copy `backend/migrations/003_phase6_preferences.sql` into the SQL Editor and click Run
- **psql:** `psql "postgresql://postgres:<password>@db.<your-project>.supabase.co:5432/postgres" -f migrations/003_phase6_preferences.sql`

No new environment variables required for this migration.

## Next Phase Readiness

- Schema foundation for all Phase 6 backend features is in place
- `preferred_platform` column enables platform_router.py to route replies to web vs WhatsApp
- `spiciness_level` column enables content ceiling enforcement in intimate mode for web chat
- `mode_switch_phrase` column enables user-configurable mode switching
- `notif_prefs` column enables granular notification control
- No blockers — proceed to Phase 6 Plan 02 after applying the migration

---
*Phase: 06-web-app-multi-platform*
*Completed: 2026-02-24*
