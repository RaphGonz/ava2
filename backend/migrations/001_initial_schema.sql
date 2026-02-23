-- =============================================================================
-- Migration: 001_initial_schema
-- Date:      2026-02-23
-- Phase:     02-infrastructure-user-management
-- Description:
--   Complete initial schema for Ava — creates all enums, tables, RLS policies,
--   and performance indexes in a single atomic transaction.
--
-- Tables created:
--   - public.user_preferences  (WhatsApp phone linkage)
--   - public.avatars            (one per user, age >= 20 enforced)
--   - public.messages           (flat message log for app + WhatsApp)
--
-- How to apply:
--   Option 1 — Supabase Dashboard SQL Editor:
--     Copy and paste the entire contents of this file into the SQL Editor at
--     https://supabase.com/dashboard/project/<your-project>/sql
--     Click "Run".
--
--   Option 2 — psql:
--     psql "postgresql://postgres:<password>@db.<your-project>.supabase.co:5432/postgres" \
--       -f migrations/001_initial_schema.sql
--
-- IMPORTANT: After applying this migration, disable email confirmation:
--   Supabase Dashboard > Authentication > Providers > Email >
--   uncheck "Confirm email"
--   This is required for Phase 2's immediate-token signup flow (sign_up returns
--   session=None when email confirmation is enabled, breaking token issuance).
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------------

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------------------------
-- Enums
-- ---------------------------------------------------------------------------

-- Avatar personality type (Claude's discretion: reasonable Phase 2 defaults)
CREATE TYPE personality_type AS ENUM (
  'playful',
  'dominant',
  'shy',
  'caring',
  'intellectual',
  'adventurous'
);

-- Message delivery channel
CREATE TYPE message_channel AS ENUM ('app', 'whatsapp');

-- Message role in conversation
CREATE TYPE message_role AS ENUM ('user', 'assistant');

-- ---------------------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------------------

-- User preferences table (Phase 2 scope: WhatsApp phone linkage only)
-- Spice level, notification settings, UI preferences deferred to later phases
CREATE TABLE public.user_preferences (
  id           UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id      UUID        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  whatsapp_phone TEXT,                          -- E.164 format: +1234567890
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(user_id)                               -- One preferences row per user
);

-- Avatars table (one per user, enforced via UNIQUE on user_id)
-- Phase 1 compliance decision: avatar age floor is 20+ (not 18+)
CREATE TABLE public.avatars (
  id                   UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id              UUID        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name                 TEXT        NOT NULL,
  age                  INTEGER     NOT NULL CHECK (age >= 20),  -- Hard floor from Phase 1 compliance
  personality          personality_type NOT NULL,
  physical_description TEXT,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(user_id)                             -- Enforce one avatar per user in Phase 2
);

-- Messages table (flat log, no session grouping in Phase 2)
-- avatar_id uses SET NULL on delete so messages survive avatar deletion
CREATE TABLE public.messages (
  id         UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id    UUID            NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  avatar_id  UUID            REFERENCES public.avatars(id) ON DELETE SET NULL,
  channel    message_channel NOT NULL,
  role       message_role    NOT NULL,
  content    TEXT            NOT NULL,
  created_at TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------

ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.avatars ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- user_preferences policies
-- NOTE: (SELECT auth.uid()) wrapper — not bare auth.uid() — allows Postgres to
-- cache the result per statement (~95% RLS performance improvement on large tables)

CREATE POLICY "Users can read own preferences"
  ON public.user_preferences FOR SELECT
  TO authenticated
  USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can insert own preferences"
  ON public.user_preferences FOR INSERT
  TO authenticated
  WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update own preferences"
  ON public.user_preferences FOR UPDATE
  TO authenticated
  USING ((SELECT auth.uid()) = user_id)
  WITH CHECK ((SELECT auth.uid()) = user_id);

-- avatars policies

CREATE POLICY "Users can read own avatar"
  ON public.avatars FOR SELECT
  TO authenticated
  USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can create own avatar"
  ON public.avatars FOR INSERT
  TO authenticated
  WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update own avatar"
  ON public.avatars FOR UPDATE
  TO authenticated
  USING ((SELECT auth.uid()) = user_id)
  WITH CHECK ((SELECT auth.uid()) = user_id);

-- messages policies

CREATE POLICY "Users can read own messages"
  ON public.messages FOR SELECT
  TO authenticated
  USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can insert own messages"
  ON public.messages FOR INSERT
  TO authenticated
  WITH CHECK ((SELECT auth.uid()) = user_id);

-- ---------------------------------------------------------------------------
-- Performance Indexes
-- Required for RLS policy performance — missing indexes cause full table scans
-- on every authenticated query (100x+ performance degradation on large tables)
-- ---------------------------------------------------------------------------

CREATE INDEX idx_user_preferences_user_id ON public.user_preferences (user_id);
CREATE INDEX idx_avatars_user_id ON public.avatars (user_id);
CREATE INDEX idx_messages_user_id ON public.messages (user_id);
CREATE INDEX idx_messages_user_created ON public.messages (user_id, created_at DESC);

-- Partial index for WhatsApp phone lookup — only indexes non-null rows
-- Every WhatsApp message triggers a phone lookup; partial index keeps it fast
-- without wasting index space on users who haven't linked a phone
CREATE INDEX idx_user_preferences_phone ON public.user_preferences (whatsapp_phone)
  WHERE whatsapp_phone IS NOT NULL;

COMMIT;
