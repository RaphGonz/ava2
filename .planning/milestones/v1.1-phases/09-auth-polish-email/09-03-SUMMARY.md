---
phase: 09-auth-polish-email
plan: "03"
subsystem: auth
tags: [google-oauth, supabase, react, typescript, password-reset]

# Dependency graph
requires:
  - phase: 09-01
    provides: Backend auth endpoints (POST /auth/forgot-password, POST /auth/send-welcome, Supabase hook handler)
provides:
  - Supabase JS client singleton (implicit flow, detectSessionInUrl: true)
  - GoogleSignInButton component (Google branding, signInWithOAuth)
  - AuthBridge in App.tsx (SIGNED_IN -> Zustand setAuth + send-welcome for new Google signups)
  - LoginPage with Google button, "or" divider, isGoogleOnlyUser Forgot password hide
  - SignupPage with Google button and "or" divider
  - ForgotPasswordPage calling POST /auth/forgot-password with anti-enumeration success message
  - ResetPasswordPage calling supabase.auth.updateUser with expired-token error state
  - /forgot-password and /reset-password routes registered in App.tsx
affects:
  - 09-04
  - Phase 13 smoke test (Google OAuth user journey)

# Tech tracking
tech-stack:
  added:
    - "@supabase/supabase-js ^2.98.0"
  patterns:
    - "AuthBridge component rendered inside BrowserRouter but outside Routes — runs on every page with no visual output"
    - "Google-only user detection via identities array (not app_metadata.provider) to handle linked accounts correctly"
    - "isGoogleOnlyUser state checked on mount via supabase.auth.getSession() — hides Forgot password link conditionally"
    - "send-welcome fire-and-forget via fetch() in AuthBridge — non-blocking, errors are console.warn only"

key-files:
  created:
    - frontend/src/lib/supabaseClient.ts
    - frontend/src/components/GoogleSignInButton.tsx
    - frontend/src/pages/ForgotPasswordPage.tsx
    - frontend/src/pages/ResetPasswordPage.tsx
  modified:
    - frontend/src/App.tsx
    - frontend/src/pages/LoginPage.tsx
    - frontend/src/pages/SignupPage.tsx
    - frontend/package.json
    - frontend/package-lock.json

key-decisions:
  - "Google-only user detection uses identities array (not app_metadata.provider) — linked accounts have both providers, correctly showing Forgot password link"
  - "AuthBridge new-signup detection: provider=google AND created_at within 60s — fire-and-forget POST /auth/send-welcome"
  - "ForgotPasswordPage anti-enumeration: identical 200 success response regardless of whether email is registered"
  - "ResetPasswordPage expired-token state: dedicated 'Link expired' page with Request a new link button (not redirect to login)"

patterns-established:
  - "AuthBridge pattern: Supabase auth listener bridged to Zustand store via SIGNED_IN event — one-way bridge, no direct Supabase data queries from frontend"
  - "Google-only detection: check identities[] for provider='email' absence, not app_metadata.provider presence"

requirements-completed: [AUTH-01, AUTH-02]

# Metrics
duration: 15min
completed: 2026-03-05
---

# Phase 9 Plan 03: Google Sign-In + Password Reset Frontend Summary

**@supabase/supabase-js integrated for Google OAuth (implicit flow) and password reset, with AuthBridge bridging Supabase sessions to Zustand, Google-only user detection on LoginPage, and new ForgotPassword/ResetPassword pages**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-05T00:00:00Z
- **Completed:** 2026-03-05T00:15:00Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Installed @supabase/supabase-js and created supabaseClient.ts singleton (implicit flow, detectSessionInUrl: true) — sole exception to "no direct Supabase client" rule
- Added AuthBridge to App.tsx: listens for SIGNED_IN events, populates Zustand auth store, detects new Google signups (created_at < 60s) and fires POST /auth/send-welcome
- Added /forgot-password and /reset-password routes to App.tsx
- Updated LoginPage and SignupPage with GoogleSignInButton above email/password form with "or" divider
- LoginPage hides "Forgot password?" link for Google-only accounts (identities array check, not app_metadata)
- LoginPage shows specific error message when Google-only account tries email/password login
- Created ForgotPasswordPage: calls POST /auth/forgot-password, shows anti-enumeration success message
- Created ResetPasswordPage: calls supabase.auth.updateUser, dedicated "Link expired" state, 2s redirect to /login on success

## Task Commits

1. **Task 1: Supabase JS client + GoogleSignInButton + AuthBridge in App.tsx** - `71d2b97` (feat)
2. **Task 2: Update Login/Signup + create ForgotPassword/ResetPassword pages** - `9646fb1` (feat)

## Files Created/Modified
- `frontend/src/lib/supabaseClient.ts` - Supabase JS client singleton (implicit flow, detectSessionInUrl: true)
- `frontend/src/components/GoogleSignInButton.tsx` - Google G logo SVG + signInWithOAuth (Google branding guidelines)
- `frontend/src/App.tsx` - AuthBridge component + /forgot-password and /reset-password routes
- `frontend/src/pages/LoginPage.tsx` - GoogleSignInButton, "or" divider, isGoogleOnlyUser Forgot password conditional
- `frontend/src/pages/SignupPage.tsx` - GoogleSignInButton, "or" divider
- `frontend/src/pages/ForgotPasswordPage.tsx` - POST /auth/forgot-password + anti-enumeration success page
- `frontend/src/pages/ResetPasswordPage.tsx` - supabase.auth.updateUser + expired-token error state
- `frontend/package.json` - @supabase/supabase-js ^2.98.0 added
- `frontend/package-lock.json` - lockfile updated

## Decisions Made
- Google-only user detection uses identities array (not app_metadata.provider) — a linked account has both google and email identities, so the Forgot password link correctly appears for linked accounts
- AuthBridge new-signup detection: provider=google AND created_at within 60s — fire-and-forget POST /auth/send-welcome, errors logged as console.warn only (non-blocking)
- ForgotPasswordPage anti-enumeration: identical 200 success response regardless of whether email is registered
- ResetPasswordPage expired-token: dedicated "Link expired" page with "Request a new link" button (not redirect to /login)

## Deviations from Plan

None - plan executed exactly as written. TypeScript compilation passes with zero errors.

## Issues Encountered

None.

## User Setup Required

Before Google Sign-In works in production:
1. Add `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` to `frontend/.env` (and production environment)
2. In Supabase Dashboard > Auth > URL Configuration: add `https://avasecret.org/` to Allowed Redirect URLs
3. Google OAuth Client ID and Secret configured in Supabase Dashboard > Auth > Providers > Google (done in Phase 8)
4. For password reset: in Supabase Dashboard > Auth > Email Templates, set redirect URL to `https://avasecret.org/reset-password`

## Next Phase Readiness
- AUTH-01 and AUTH-02 complete
- Google OAuth frontend complete — clicking "Continue with Google" on Login/Signup will redirect to Google consent screen
- Password reset flow complete end-to-end (ForgotPassword → email → ResetPassword → supabase.auth.updateUser)
- Phase 9 Plan 04 can proceed (final polish / smoke test prep)

---
*Phase: 09-auth-polish-email*
*Completed: 2026-03-05*

## Self-Check: PASSED

- FOUND: frontend/src/lib/supabaseClient.ts
- FOUND: frontend/src/components/GoogleSignInButton.tsx
- FOUND: frontend/src/pages/ForgotPasswordPage.tsx
- FOUND: frontend/src/pages/ResetPasswordPage.tsx
- FOUND: .planning/phases/09-auth-polish-email/09-03-SUMMARY.md
- FOUND commit 71d2b97 (Task 1)
- FOUND commit 9646fb1 (Task 2)
