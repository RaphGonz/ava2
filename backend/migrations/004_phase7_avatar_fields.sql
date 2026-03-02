-- =============================================================================
-- Migration: 004_phase7_avatar_fields
-- Date:      2026-02-25
-- Phase:     07-avatar-system-production
-- Description:
--   Extends the schema for Phase 7 (Avatar System & Production):
--
--   Part 1 — Avatar new fields (nullable to avoid breaking existing rows):
--     Adds gender and nationality TEXT columns to public.avatars.
--     Both nullable so existing rows are unaffected.
--
--   Part 2 — Subscriptions table (config-driven for BILL-02):
--     Creates public.subscriptions table to track Stripe subscription state.
--     stripe_price_id is stored but not hardcoded — amounts are config-driven.
--     RLS: user can read their own row; only service role writes (via webhook).
--
-- How to apply:
--   Supabase Dashboard SQL Editor:
--     Copy and paste the entire contents of this file into the SQL Editor at
--     https://supabase.com/dashboard/project/<your-project>/sql
--     Click "Run".
--
-- NOTE: Idempotent — safe to re-run. DO blocks catch duplicate errors.
-- =============================================================================


-- =============================================================================
-- Part 1: Avatar new fields
-- =============================================================================

ALTER TABLE public.avatars
  ADD COLUMN IF NOT EXISTS gender             TEXT,
  ADD COLUMN IF NOT EXISTS nationality        TEXT,
  ADD COLUMN IF NOT EXISTS reference_image_url TEXT;


-- =============================================================================
-- Part 2: Subscriptions table
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.subscriptions (
  id                     UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id                UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  stripe_customer_id     TEXT,
  stripe_subscription_id TEXT UNIQUE,
  stripe_price_id        TEXT,
  status                 TEXT NOT NULL DEFAULT 'inactive'
                           CHECK (status IN ('active', 'inactive', 'past_due', 'canceled')),
  current_period_end     TIMESTAMPTZ,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

DO $$ BEGIN
  ALTER TABLE public.subscriptions ADD CONSTRAINT subscriptions_user_id_unique UNIQUE (user_id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  CREATE POLICY "subscriptions_select_own"
    ON public.subscriptions FOR SELECT
    USING (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
