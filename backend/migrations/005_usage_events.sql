-- Migration: 005_usage_events.sql
-- Phase 8 — creates event log table for admin dashboard (ADMN-02)
-- Run in: Supabase Dashboard -> SQL Editor
-- Safe to re-run (IF NOT EXISTS guards throughout)

CREATE TABLE IF NOT EXISTS public.usage_events (
  id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id     UUID        REFERENCES auth.users(id) ON DELETE SET NULL,
  event_type  TEXT        NOT NULL,
  -- Expected values: 'message_sent' | 'photo_generated' | 'mode_switch' | 'subscription_created'
  metadata    JSONB,                   -- arbitrary event payload, shape defined per event_type
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for admin dashboard queries (event_type filter + time range)
CREATE INDEX IF NOT EXISTS usage_events_event_type_idx
  ON public.usage_events (event_type, created_at DESC);

CREATE INDEX IF NOT EXISTS usage_events_user_id_idx
  ON public.usage_events (user_id, created_at DESC);

-- RLS: enabled. No SELECT policy for regular users — admin reads via service role key only.
ALTER TABLE public.usage_events ENABLE ROW LEVEL SECURITY;

-- Emission helper (add to backend/app/services/usage.py in a future plan if needed):
-- async def emit_usage_event(user_id, event_type, metadata=None): ...
-- See STATE.md Phase 8 decisions for deferred import pattern.
