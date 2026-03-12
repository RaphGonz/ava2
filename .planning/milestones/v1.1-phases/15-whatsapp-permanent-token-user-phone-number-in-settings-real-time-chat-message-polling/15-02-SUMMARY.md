---
phase: 15-whatsapp-permanent-token-user-phone-number-in-settings-real-time-chat-message-polling
plan: "02"
subsystem: infra
tags: [whatsapp, meta-api, preferences, polling, production, vps]

# Dependency graph
requires:
  - phase: 15-01
    provides: linkWhatsApp() in preferences.ts + conditional phone input with E.164 validation in SettingsPage

provides:
  - Permanent WhatsApp System User token deployed to VPS (non-expiring, replaces 60-day developer token)
  - WhatsApp PHONE_NUMBER_ID configured in production backend/.env
  - WhatsApp end-to-end verified: message from linked phone receives AI reply within 30 seconds
  - Settings phone input: appears on WhatsApp toggle, persists through page reload
  - Chat polling: GET /chat/history fires every ~3 seconds (confirmed in DevTools Network tab)
  - Bug fixes: preferences upsert 500, missing whatsapp_phone column, phone normalization (+prefix)

affects: [whatsapp, preferences, chat-polling, production]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "on_conflict='user_id' for preferences upsert — prevents 500 on existing users"
    - "Phone normalization: WhatsApp sends '33612...' format, store as '+33612...' (E.164)"
    - "Welcome template sent via WhatsApp API when phone is first linked"

key-files:
  created:
    - backend/app/migrations/007_whatsapp_phone.sql
  modified:
    - backend/app/routers/preferences.py
    - backend/app/routers/webhook.py

key-decisions:
  - "Permanent System User token (business.facebook.com → System Users → Generate New Token) replaces 60-day developer token — no rotation needed after 60 days"
  - "WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID stored in VPS backend/.env (not committed to repo)"
  - "on_conflict='user_id' added to all preferences upsert calls — was causing 500 on users with existing rows"
  - "WhatsApp phone prefix normalization: incoming webhook sender format '33612...' normalized to '+33612...' before DB storage"
  - "Welcome template sent on phone link to confirm messaging channel is active"

patterns-established:
  - "Preferences upsert always uses on_conflict='user_id' — idempotent for all user rows"
  - "Phone number normalization at write time (not read time) — '+' prefix added before storage"

requirements-completed: [WA-01, WA-02, WA-03]

# Metrics
duration: ~60min (includes human action for Meta Business Manager + human verification)
completed: 2026-03-11
---

# Phase 15 Plan 02: WhatsApp Permanent Token + Production Verification Summary

**Permanent WhatsApp System User token deployed to VPS; WhatsApp E2E messaging and 3-second chat polling both verified in production, with 3 auto-fixed bugs (preferences upsert 500, missing DB column, phone normalization)**

## Performance

- **Duration:** ~60 min (includes human steps for Meta Business Manager + production verification)
- **Started:** 2026-03-11
- **Completed:** 2026-03-11
- **Tasks:** 3 (1 auto, 1 human-action, 1 human-verify)
- **Files modified:** 3 (+ 1 migration file created)

## Accomplishments

- Permanent WhatsApp System User token created in Meta Business Manager and deployed to VPS — no more 60-day expiry
- WhatsApp end-to-end verified: message to Ava business number → AI reply within 30 seconds
- Settings phone input appears on WhatsApp platform toggle and persists through page reload
- Chat polling confirmed: GET /chat/history fires every ~3 seconds visible in DevTools Network tab
- Fixed 3 production bugs discovered during verification (see Deviations)

## Task Commits

Each task was committed atomically:

1. **Task 1: Deploy Plan 01 frontend changes to production** - `abd66fa` (docs — frontend already deployed from 15-01)
2. **Task 2: Create permanent WhatsApp System User token** - human-action (VPS .env only — no code commit)
3. **Task 3: Verify WhatsApp E2E and chat polling** - verified pass (A, B, C all confirmed by user)

**Bug fix commits (auto-fixed during verification):**
- `9d21a86` fix(15): add whatsapp_phone column migration — missing from user_preferences table
- `0fbf0dc` fix(15): add on_conflict='user_id' to preferences upserts — 500 on existing users
- `20efb78` fix(15): normalize WhatsApp phone +prefix, fix placeholder URL, add welcome template on link

## Files Created/Modified

- `backend/app/migrations/007_whatsapp_phone.sql` - Adds whatsapp_phone column to user_preferences table
- `backend/app/routers/preferences.py` - Added on_conflict='user_id' to upsert calls
- `backend/app/routers/webhook.py` - Phone normalization (+prefix), welcome template send on phone link

## Decisions Made

- Permanent System User token (not the 60-day developer token from Getting Started page) — resolves the credential rotation gap that would have broken WhatsApp after 60 days
- WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID stored in VPS backend/.env only — not committed to repo (secret values)
- Welcome WhatsApp template sent when user links their phone number to confirm the channel is active

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Missing whatsapp_phone column in user_preferences table**
- **Found during:** Task 3 (WhatsApp E2E verification — Verify A)
- **Issue:** The whatsapp_phone column did not exist in user_preferences; saving phone number caused a DB error
- **Fix:** Created migration 007_whatsapp_phone.sql and applied it via Supabase SQL Editor
- **Files modified:** `backend/app/migrations/007_whatsapp_phone.sql`
- **Verification:** Phone number saved and persisted through page reload (Verify A passed)
- **Committed in:** `9d21a86`

**2. [Rule 1 - Bug] preferences upsert returning 500 on existing users (missing on_conflict)**
- **Found during:** Task 3 (Verify A — phone save)
- **Issue:** Preferences upsert calls lacked on_conflict='user_id', causing PostgreSQL duplicate key error for users who already had a preferences row
- **Fix:** Added on_conflict='user_id' to all upsert calls in preferences.py
- **Files modified:** `backend/app/routers/preferences.py`
- **Verification:** Existing users can save preferences without 500 error
- **Committed in:** `0fbf0dc`

**3. [Rule 1 - Bug] WhatsApp phone prefix normalization + welcome template**
- **Found during:** Task 3 (Verify B — WhatsApp reply)
- **Issue:** WhatsApp webhook delivers sender phone as '33612345678' (no '+') but storage expected E.164 '+33612345678'; mismatch blocked user lookup; also placeholder URL in template was incorrect
- **Fix:** Added '+' prefix normalization before DB storage; fixed placeholder URL; added welcome template send when phone is first linked
- **Files modified:** `backend/app/routers/webhook.py`
- **Verification:** WhatsApp message to Ava number received AI reply within 30 seconds (Verify B passed)
- **Committed in:** `20efb78`

---

**Total deviations:** 3 auto-fixed (all Rule 1 - Bug)
**Impact on plan:** All three fixes were required for production correctness. The WhatsApp integration would have failed without them. No scope creep.

## Issues Encountered

- Supabase migration had to be applied manually via SQL Editor (no automated migration runner in production) — standard pattern for this project

## User Setup Required

The following was configured manually by the user during Task 2:

- **WHATSAPP_ACCESS_TOKEN** — Permanent System User token from business.facebook.com → Business Settings → System Users → Generate New Token (WhatsApp app, whatsapp_business_messaging + whatsapp_business_management permissions)
- **WHATSAPP_PHONE_NUMBER_ID** — Numeric phone ID from Meta Developer Console → WhatsApp app → Getting Started
- Both written to `/opt/ava2/backend/.env` on VPS; `docker compose restart backend` run to apply

## Next Phase Readiness

- Phase 15 complete: all three gaps closed (permanent token, phone collection in Settings, chat polling)
- WhatsApp integration is production-ready and will not expire after 60 days
- No blockers — Phase 15 milestone fully achieved

---
*Phase: 15-whatsapp-permanent-token-user-phone-number-in-settings-real-time-chat-message-polling*
*Completed: 2026-03-11*
