-- Migration: 006_subscription_cancel_at_period_end.sql
-- Phase 11 — adds cancel_at_period_end to subscriptions table
-- Run in: Supabase Dashboard -> SQL Editor
-- Safe to re-run (IF NOT EXISTS guard)

ALTER TABLE public.subscriptions
  ADD COLUMN IF NOT EXISTS cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE;
