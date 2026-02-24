-- Migration 002: Google Calendar OAuth token storage
-- Per-user token table. Stores access_token, refresh_token, expiry, and scopes.
-- RLS: each user can only read/write their own row.

CREATE TABLE IF NOT EXISTS google_calendar_tokens (
    user_id       UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    access_token  TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    token_expiry  TIMESTAMPTZ,
    scopes        TEXT[],
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE google_calendar_tokens ENABLE ROW LEVEL SECURITY;

CREATE POLICY "user owns google token" ON google_calendar_tokens
    FOR ALL USING (auth.uid() = user_id);
