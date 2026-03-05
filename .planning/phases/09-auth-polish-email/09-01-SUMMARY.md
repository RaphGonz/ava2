---
phase: 09-auth-polish-email
plan: "01"
subsystem: auth
tags: [email, resend, standardwebhooks, transactional-email, password-reset, webhooks]

# Dependency graph
requires:
  - phase: 08-infrastructure-deployment
    provides: RESEND_API_KEY and RESEND_FROM_ADDRESS env vars live in backend/.env; mail-tester 10/10

provides:
  - Async Resend email wrapper (resend_client.py) with retry logic and 5 transactional email helpers
  - POST /auth/forgot-password — email enumeration-safe password reset trigger
  - POST /auth/send-email-hook — HMAC-verified Supabase auth hook routing recovery and signup emails
  - POST /auth/send-welcome — idempotent Google OAuth welcome email with welcome_sent flag
  - supabase_hook_secret config field for Supabase Dashboard hook secret

affects: [09-02, 09-03, 11-billing-stripe, stripe-webhook-handler]

# Tech tracking
tech-stack:
  added: [resend==2.23.0, standardwebhooks==1.0.1]
  patterns:
    - asyncio.to_thread() wrapping for synchronous Resend SDK (Phase 4 pattern extended)
    - Email never raises to callers — one retry after 3s then log and return False
    - supabase_hook_secret uses v1,whsec_ prefix stripping before Webhook() init

key-files:
  created:
    - backend/app/services/email/__init__.py
    - backend/app/services/email/resend_client.py
  modified:
    - backend/requirements.txt
    - backend/app/config.py
    - backend/app/routers/auth.py

key-decisions:
  - "resend and standardwebhooks added to requirements.txt; already installed on VPS Python env"
  - "Email send failure: one retry after 3s, then log and return False — never blocks auth/payment"
  - "supabase_hook_secret field added with empty-string default, format v1,whsec_<base64>"
  - "forgot-password always returns identical 200 message regardless of email existence (no enumeration)"
  - "send-email-hook strips v1,whsec_ prefix before passing to standardwebhooks.Webhook() per RESEARCH.md"
  - "send-welcome uses supabase_admin.auth.admin.update_user_by_id to set welcome_sent flag — idempotency guard"

patterns-established:
  - "Email service: all transactional email flows through resend_client.py single entry point"
  - "Hook signature: strip v1,whsec_ prefix before Webhook() init (standardwebhooks library requirement)"
  - "Idempotency via user_metadata.welcome_sent flag — avoids duplicate welcome emails on Google OAuth"

requirements-completed: [AUTH-02, EMAI-02]

# Metrics
duration: 16min
completed: 2026-03-05
---

# Phase 9 Plan 01: Email Service & Auth Endpoints Summary

**Resend transactional email wrapper with 5 helpers, three new auth endpoints (forgot-password with no-enumeration, HMAC-verified Supabase send-email-hook, idempotent Google OAuth send-welcome)**

## Performance

- **Duration:** 16 min
- **Started:** 2026-03-05T16:14:47Z
- **Completed:** 2026-03-05T16:30:46Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created `backend/app/services/email/resend_client.py` with async Resend wrapper, one-retry failure strategy, and 5 transactional helpers: send_email, send_welcome_email, send_password_reset_email, send_receipt_email, send_cancellation_email
- Added `POST /auth/forgot-password` with email enumeration protection (always returns same 200 message), `POST /auth/send-email-hook` with HMAC signature verification routing recovery and signup events, `POST /auth/send-welcome` with welcome_sent idempotency flag for Google OAuth path
- Added `resend==2.23.0` and `standardwebhooks==1.0.1` to requirements.txt; added `supabase_hook_secret` field to Settings

## Task Commits

Each task was committed atomically:

1. **Task 1: Email service module and config field** - `33e6b0b` (feat)
2. **Task 2: Backend auth endpoints** - `523bfef` (feat)

## Files Created/Modified
- `backend/app/services/email/__init__.py` - Empty package init (makes email a package)
- `backend/app/services/email/resend_client.py` - Async Resend wrapper with retry and 5 email helpers
- `backend/requirements.txt` - Added resend==2.23.0 and standardwebhooks==1.0.1
- `backend/app/config.py` - Added supabase_hook_secret field with empty-string default
- `backend/app/routers/auth.py` - Added forgot-password, send-email-hook, send-welcome endpoints

## Decisions Made
- Email failures use one-retry-then-log pattern (asyncio.sleep(3) then retry=False) — email never blocks auth or payment flows per CONTEXT.md decision
- `supabase_hook_secret` uses empty-string default consistent with all credential fields in Settings — missing key returns 401, not startup crash
- `standardwebhooks.Webhook()` requires the secret WITHOUT the `v1,whsec_` prefix — stripped before init per RESEARCH.md Pitfall 3
- `send-welcome` uses `supabase_admin.auth.admin.update_user_by_id` to write `welcome_sent: True` into user_metadata — best-effort, logged on failure, does not block response
- `forgot-password` uses Supabase `reset_password_for_email` with `redirect_to` pointing to `/reset-password` frontend route — Supabase handles the token generation and delivery (overridden by hook in production)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - both packages (resend, standardwebhooks) were already installed in the environment from prior setup.

## User Setup Required

The following external service configuration is required before these endpoints are functional in production:

1. **Supabase Dashboard — Enable Send Email Hook:**
   - Go to Authentication > Hooks > Send Email
   - Set endpoint: `https://avasecret.org/auth/send-email-hook`
   - Copy the generated secret (format: `v1,whsec_<base64>`)
   - Add to `backend/.env`: `SUPABASE_HOOK_SECRET=v1,whsec_<your-secret>`

2. **backend/.env** — Ensure these are set (from Phase 8):
   - `RESEND_API_KEY=re_...`
   - `RESEND_FROM_ADDRESS=Ava <ava@avasecret.org>`

3. **Redeploy backend** after adding `SUPABASE_HOOK_SECRET` to `.env`

## Next Phase Readiness
- Email infrastructure complete — send_receipt_email and send_cancellation_email ready for Phase 11 Stripe webhook handler
- Auth endpoints ready — forgot-password and send-email-hook can be wired in Supabase Dashboard immediately after env var is set
- Ready for Phase 9 Plan 02: Google Sign-In frontend integration

---
*Phase: 09-auth-polish-email*
*Completed: 2026-03-05*
