---
phase: 17-gdpr-cookie-consent-banner
plan: 02
subsystem: ui
tags: [react, gdpr, cookie-consent, sentry, motion, vitest]

# Dependency graph
requires:
  - phase: 17-01
    provides: consent.ts service (initSentry, injectAnalytics, initFromStoredConsent) and useCookieConsent hook (synchronous localStorage state)
provides:
  - CookieConsentBanner component (GlassCard-styled, AnimatePresence slide animation, Accept/Decline buttons)
  - main.tsx wired with initFromStoredConsent() before createRoot and Sentry.reactErrorHandler on all error handlers
  - LandingPage.tsx renders CookieConsentBanner as first child (landing-page-only banner placement)
  - 5 Vitest unit tests covering show/hide, localStorage writes, and returning visitor suppression
affects: [landing-page, sentry-integration, analytics-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Landing-page-only banner: CookieConsentBanner added only to LandingPage.tsx, never App.tsx or global layout"
    - "AnimatePresence exit animation: banner exits with y:80/opacity:0 slide-down on hasChosen becoming true"
    - "Sentry.reactErrorHandler: passed to all three createRoot error handlers (onUncaughtError, onCaughtError, onRecoverableError) unconditionally — no-op when uninitialized"
    - "Pre-createRoot consent init: initFromStoredConsent() called before createRoot so Sentry is active before first React render for returning visitors"

key-files:
  created:
    - frontend/src/components/CookieConsentBanner.tsx
    - frontend/src/components/CookieConsentBanner.test.tsx
  modified:
    - frontend/src/main.tsx
    - frontend/src/pages/LandingPage.tsx

key-decisions:
  - "Banner placed only in LandingPage.tsx, not App.tsx — authenticated users accepted via ToS, no banner on auth routes"
  - "Sentry.reactErrorHandler() passed unconditionally to createRoot — returns no-op function when Sentry not initialized, no conditional logic needed"

patterns-established:
  - "Cookie banner placement: always inside the page component that needs it, never in global layout"
  - "Consent test isolation: vi.mock('../lib/consent') stubs initSentry/injectAnalytics/initFromStoredConsent to prevent real Sentry/DOM side effects in tests"

requirements-completed: [COOK-01, COOK-02, COOK-03, COOK-05]

# Metrics
duration: 19min
completed: 2026-03-16
---

# Phase 17 Plan 02: CookieConsentBanner Component and Integration Summary

**GlassCard GDPR consent banner wired into LandingPage with AnimatePresence animation, localStorage persistence, and Sentry.reactErrorHandler in createRoot**

## Performance

- **Duration:** 19 min
- **Started:** 2026-03-16T15:21:27Z
- **Completed:** 2026-03-16T15:40:30Z
- **Tasks:** 3 (2 auto + 1 human-verify)
- **Files modified:** 4

## Accomplishments

- CookieConsentBanner component with GlassCard styling, Accept/Decline buttons, and AnimatePresence slide-in/slide-out animation
- main.tsx updated to call initFromStoredConsent() before createRoot and pass Sentry.reactErrorHandler to all three createRoot error handlers
- LandingPage.tsx wired to render CookieConsentBanner as first child; banner confirmed absent on /login and authenticated routes
- 5 Vitest unit tests all passing; TypeScript zero errors; production build succeeds

## Task Commits

Each task was committed atomically:

1. **Task 1: Create CookieConsentBanner component and tests** - `5100aaa` (feat)
2. **Task 2: Wire main.tsx and LandingPage.tsx** - `b19d5ea` (feat)
3. **Task 3: Human verification** - approved by user, no code commit required

## Files Created/Modified

- `frontend/src/components/CookieConsentBanner.tsx` - Fixed-position bottom banner with GlassCard, AnimatePresence, Accept/Decline
- `frontend/src/components/CookieConsentBanner.test.tsx` - 5 Vitest tests: show for new visitor, hide for returning, localStorage writes on click
- `frontend/src/main.tsx` - Pre-createRoot initFromStoredConsent(), Sentry.reactErrorHandler on all error hooks
- `frontend/src/pages/LandingPage.tsx` - Import and render of CookieConsentBanner as first child inside root div

## Decisions Made

- Sentry.reactErrorHandler() passed unconditionally to createRoot — it returns a no-op when Sentry is uninitialized, so no conditional logic needed and no risk when DSN is empty in local dev.
- Banner placed only in LandingPage.tsx, not in App.tsx or any layout component, consistent with the v1.2 decision that authenticated users accepted via ToS.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Pre-existing failing test in AdminPage.test.tsx (admin metric cards) — unrelated to this plan, not touched by any of our commits. Out of scope per deviation rules, logged here for awareness.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Complete GDPR cookie consent flow is now live for the landing page (phases 17-01 + 17-02 together deliver the full feature)
- Sentry and analytics are gated behind consent; Stripe loads regardless
- No blockers for v1.2 launch from this phase

---
*Phase: 17-gdpr-cookie-consent-banner*
*Completed: 2026-03-16*

## Self-Check: PASSED

- FOUND: frontend/src/components/CookieConsentBanner.tsx
- FOUND: frontend/src/components/CookieConsentBanner.test.tsx
- FOUND: .planning/phases/17-gdpr-cookie-consent-banner/17-02-SUMMARY.md
- FOUND: commit 5100aaa (feat: CookieConsentBanner component and tests)
- FOUND: commit b19d5ea (feat: wire main.tsx and LandingPage)
