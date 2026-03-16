---
phase: 17-gdpr-cookie-consent-banner
plan: 01
subsystem: ui
tags: [sentry, plausible, gdpr, cookie-consent, react-hooks, localStorage]

# Dependency graph
requires: []
provides:
  - consent.ts service module with idempotent initSentry, injectAnalytics, initFromStoredConsent
  - useCookieConsent hook returning consent state, hasChosen, accept, decline
  - @sentry/react installed in frontend
  - VITE_SENTRY_DSN and VITE_PLAUSIBLE_DOMAIN env var placeholders
affects:
  - 17-gdpr-cookie-consent-banner (plans 02+: CookieBanner component, main.tsx wiring)

# Tech tracking
tech-stack:
  added: ["@sentry/react ^10.43.0"]
  patterns:
    - "Module-level boolean flags (sentryInitialized, analyticsInjected) for idempotent third-party init"
    - "Synchronous localStorage.getItem() in useState lazy initializer to prevent banner flash"
    - "Deferred SDK initialization gated behind explicit user consent"

key-files:
  created:
    - frontend/src/lib/consent.ts
    - frontend/src/hooks/useCookieConsent.ts
  modified:
    - frontend/package.json
    - frontend/.env (gitignored)

key-decisions:
  - "VITE_SENTRY_DSN left empty for local dev — Sentry.init() with undefined DSN is a no-op, not an error"
  - "useCookieConsent uses plain useState+localStorage (not zustand persist) to avoid async hydration banner flash"
  - "Module-level flags ensure initSentry/injectAnalytics are idempotent across multiple hook instances"

patterns-established:
  - "Consent pattern: all third-party SDKs must be initialized only after user consent, not at module import time"
  - "No instrument.ts or top-level Sentry.init() call — COOK-06 compliance"

requirements-completed: [COOK-04, COOK-06]

# Metrics
duration: 8min
completed: 2026-03-16
---

# Phase 17 Plan 01: GDPR Cookie Consent — Service Layer Summary

**@sentry/react installed and consent service layer built: idempotent initSentry/injectAnalytics in consent.ts, synchronous-localStorage useCookieConsent hook preventing banner flash on returning visitors**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-16T09:00:00Z
- **Completed:** 2026-03-16T09:08:00Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- Installed @sentry/react ^10.43.0 and added VITE_SENTRY_DSN/VITE_PLAUSIBLE_DOMAIN env var placeholders
- Created consent.ts with module-level idempotency flags preventing double-initialization of Sentry and Plausible
- Created useCookieConsent hook with synchronous localStorage read in useState lazy initializer (no banner flash)

## Task Commits

Each task was committed atomically:

1. **Task 1: Install @sentry/react and add env vars** - `7f299e6` (chore)
2. **Task 2: Create consent.ts service module** - `38bcf38` (feat)
3. **Task 3: Create useCookieConsent hook** - `98a6ab1` (feat)

## Files Created/Modified
- `frontend/src/lib/consent.ts` - Consent service: initSentry, injectAnalytics, initFromStoredConsent with idempotency guards
- `frontend/src/hooks/useCookieConsent.ts` - React hook returning { consent, hasChosen, accept, decline } with synchronous localStorage state
- `frontend/package.json` - Added @sentry/react ^10.43.0 dependency
- `frontend/.env` (gitignored) - Added VITE_SENTRY_DSN= and VITE_PLAUSIBLE_DOMAIN=avasecret.com

## Decisions Made
- VITE_SENTRY_DSN left empty for local dev (Sentry.init with undefined DSN is a no-op — no throws)
- useCookieConsent uses plain useState + localStorage.getItem() in lazy initializer rather than zustand persist, which hydrates async and would cause banner flash for returning visitors
- Module-level flags (sentryInitialized, analyticsInjected) are idempotent — safe to call accept() multiple times

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- frontend/.env is gitignored (correct behavior for security). The file was updated locally but not committed. This is expected and correct.

## User Setup Required
- Add production Sentry DSN to deployment environment secrets as `VITE_SENTRY_DSN`
- VITE_PLAUSIBLE_DOMAIN is pre-set to `avasecret.com` in .env — override in production if needed

## Next Phase Readiness
- consent.ts and useCookieConsent are ready for plan 17-02 (CookieBanner component)
- main.tsx wiring with initFromStoredConsent() will be done in plan 17-03
- TypeScript compilation passes with zero errors

---
*Phase: 17-gdpr-cookie-consent-banner*
*Completed: 2026-03-16*
