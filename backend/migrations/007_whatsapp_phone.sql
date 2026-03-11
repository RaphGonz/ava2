-- =============================================================================
-- Migration: 007_whatsapp_phone
-- Date:      2026-03-11
-- Phase:     15-whatsapp-permanent-token-user-phone-number-in-settings
-- Description:
--   Adds whatsapp_phone column to user_preferences table.
--   This column stores the user's WhatsApp phone number in E.164 format
--   (+1234567890) for routing outbound WhatsApp messages to the correct number.
--   The column is nullable — users without WhatsApp remain unaffected.
--
-- How to apply:
--   Supabase Dashboard → SQL Editor → paste → Run
--   OR: psql "postgresql://..." -f migrations/007_whatsapp_phone.sql
-- =============================================================================

ALTER TABLE public.user_preferences
  ADD COLUMN IF NOT EXISTS whatsapp_phone TEXT;
