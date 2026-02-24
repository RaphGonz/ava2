-- =============================================================================
-- Migration: 003_phase6_preferences
-- Date:      2026-02-24
-- Phase:     06-web-app-multi-platform
-- Description:
--   Extends the schema for Phase 6 (Web App / Multi-Platform support):
--
--   1. Extends the message_channel enum to add 'web' (alongside 'app' and
--      'whatsapp'), so web chat messages can be recorded in the messages table.
--
--   2. Adds four new columns to public.user_preferences:
--       - preferred_platform  : which platform Ava replies on (whatsapp | web)
--       - spiciness_level     : content ceiling Ava will not exceed (mild | spicy | explicit)
--       - mode_switch_phrase  : user-configurable phrase to trigger mode switch; NULL = system default
--       - notif_prefs         : JSONB map for notification preferences (WhatsApp on/off, frequency, etc.)
--
--   3. Adds CHECK constraints to enforce the allowed values for
--      preferred_platform and spiciness_level at the DB level.
--
--   4. Adds a performance index on (user_id, preferred_platform) to support
--      the platform_router.py lookup without full table scans.
--
-- How to apply:
--   Option 1 — Supabase Dashboard SQL Editor:
--     Copy and paste the entire contents of this file into the SQL Editor at
--     https://supabase.com/dashboard/project/<your-project>/sql
--     Click "Run".
--
--   Option 2 — psql:
--     psql "postgresql://postgres:<password>@db.<your-project>.supabase.co:5432/postgres" \
--       -f migrations/003_phase6_preferences.sql
--
-- NOTE: ALTER TYPE ... ADD VALUE cannot run inside a transaction block in
-- PostgreSQL (even on Postgres 15+). The ALTER TYPE statement below is placed
-- intentionally BEFORE the BEGIN block. The rest of the migration runs inside
-- an atomic transaction so column additions, constraints, and indexes are all
-- applied or rolled back together.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Step 1: Extend the message_channel enum
-- MUST be outside the transaction block — PostgreSQL restriction.
-- ---------------------------------------------------------------------------

ALTER TYPE message_channel ADD VALUE IF NOT EXISTS 'web';

-- ---------------------------------------------------------------------------
-- Step 2–4: Columns, constraints, and index — inside atomic transaction
-- ---------------------------------------------------------------------------

BEGIN;

-- ---------------------------------------------------------------------------
-- Step 2: Add new columns to user_preferences
-- ---------------------------------------------------------------------------

ALTER TABLE public.user_preferences
  -- preferred_platform: 'whatsapp' | 'web'
  --   Determines which channel Ava uses to reply to this user.
  --   Defaults to 'whatsapp' so existing users are unaffected by this migration.
  ADD COLUMN IF NOT EXISTS preferred_platform  TEXT NOT NULL DEFAULT 'whatsapp',

  -- spiciness_level: 'mild' | 'spicy' | 'explicit'
  --   Sets the content ceiling that Ava will never exceed in intimate mode.
  --   Defaults to 'mild' (most conservative) to preserve existing behaviour.
  ADD COLUMN IF NOT EXISTS spiciness_level     TEXT NOT NULL DEFAULT 'mild',

  -- mode_switch_phrase: nullable TEXT
  --   User-configurable trigger phrase to switch conversation modes.
  --   NULL means the system defaults ('/work', '/play', etc.) are used.
  ADD COLUMN IF NOT EXISTS mode_switch_phrase  TEXT,

  -- notif_prefs: JSONB
  --   Flexible map for notification preferences, e.g.:
  --   {"whatsapp_enabled": true, "frequency": "daily"}
  --   Empty object default means "use system defaults for everything".
  ADD COLUMN IF NOT EXISTS notif_prefs         JSONB NOT NULL DEFAULT '{}';

-- ---------------------------------------------------------------------------
-- Step 3: Add CHECK constraints
-- Wrapped in DO $$ BEGIN ... EXCEPTION WHEN duplicate_object THEN NULL; END $$
-- so re-running this migration (e.g. in CI) does not fail if constraints exist.
-- ---------------------------------------------------------------------------

DO $$ BEGIN
  ALTER TABLE public.user_preferences
    ADD CONSTRAINT chk_preferred_platform
    CHECK (preferred_platform IN ('whatsapp', 'web'));
EXCEPTION WHEN duplicate_object THEN
  NULL;  -- Constraint already exists; safe to continue
END $$;

DO $$ BEGIN
  ALTER TABLE public.user_preferences
    ADD CONSTRAINT chk_spiciness_level
    CHECK (spiciness_level IN ('mild', 'spicy', 'explicit'));
EXCEPTION WHEN duplicate_object THEN
  NULL;  -- Constraint already exists; safe to continue
END $$;

-- ---------------------------------------------------------------------------
-- Step 4: Performance index for platform_router.py lookup
-- Supports the query: SELECT preferred_platform FROM user_preferences
--                     WHERE user_id = $1
-- Including preferred_platform enables index-only scans (no heap fetch).
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_user_preferences_preferred_platform
  ON public.user_preferences (user_id, preferred_platform);

COMMIT;
