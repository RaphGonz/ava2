---
phase: 14-apply-the-style-of-the-front-page-to-the-rest-of-the-ui-of-the-entire-app
plan: "01"
subsystem: ui
tags: [react, tailwind, react-router, vitest, testing-library]

# Dependency graph
requires:
  - phase: 12-admin-dashboard
    provides: AdminRoute guard and AdminPage component used in App.tsx routing
  - phase: 10-landing-page
    provides: LandingPage nav style reference (bg-black/80 backdrop-blur-sm border-white/5 pattern)
provides:
  - AppNav persistent navigation component (mobile bottom tab bar + desktop sticky top bar)
  - AuthenticatedLayout wrapper component in App.tsx
  - Wave 0 test scaffolds for AppNav, ChatBubble, LoginPage
affects:
  - 14-02 (LoginPage dark theme — LoginPage.test.tsx stubs must turn GREEN)
  - 14-03 (ChatBubble dark theme — ChatBubble.test.tsx stubs must turn GREEN)
  - 14-04 (SettingsPage/BillingPage — AuthenticatedLayout already wired)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - AuthenticatedLayout pattern: wraps post-auth routes (chat, settings, billing, photo, admin) with AppNav as sibling to page children
    - Wave 0 scaffold pattern: test files created with some stubs that fail now and turn GREEN in later plans; importable from the start

key-files:
  created:
    - frontend/src/components/AppNav.tsx
    - frontend/src/components/AppNav.test.tsx
    - frontend/src/components/ChatBubble.test.tsx
    - frontend/src/pages/LoginPage.test.tsx
  modified:
    - frontend/src/App.tsx

key-decisions:
  - "AuthenticatedLayout nesting order: AuthenticatedLayout > ProtectedRoute > OnboardingGate > Page — layout renders unconditionally, auth/onboarding logic inside"
  - "Wave 0 scaffold tests: ChatBubble dark-theme and LoginPage bg-black tests intentionally RED — turn GREEN in Plans 02-03 when component classes are updated"
  - "AppNav excluded from /avatar-setup and /subscribe routes — pre-onboarding/subscription flows have their own layouts"

patterns-established:
  - "AuthenticatedLayout: all post-auth routes use this wrapper for consistent AppNav presence"
  - "Wave 0 scaffolding: stub tests created before implementation to define expected behavior"

requirements-completed:
  - UI-01
  - UI-02

# Metrics
duration: 12min
completed: 2026-03-10
---

# Phase 14 Plan 01: AppNav + AuthenticatedLayout + Wave 0 Test Scaffolds Summary

**AppNav persistent nav (mobile bottom tab bar + desktop sticky glass top bar) wired into App.tsx via AuthenticatedLayout, with Wave 0 test scaffolds for Plans 02-03**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-10T15:32:36Z
- **Completed:** 2026-03-10T15:44:18Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created AppNav.tsx with dual-layout nav: sticky top bar on desktop (matching landing page glass style) and fixed bottom tab bar on mobile (Chat/Photos/Settings)
- Wired AuthenticatedLayout into App.tsx wrapping /chat, /settings, /billing, /photo, /admin routes
- Changed OnboardingGate loading state from bg-gray-950 to bg-black for visual consistency
- Created 3 Wave 0 test scaffolds (AppNav.test.tsx GREEN, ChatBubble.test.tsx and LoginPage.test.tsx stubs that turn GREEN in Plans 02-03)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create AppNav component + Wave 0 test scaffolds** - `03d5d1e` (feat)
2. **Task 2: Wire AppNav into App.tsx via AuthenticatedLayout** - `ef42536` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified
- `frontend/src/components/AppNav.tsx` - New: bottom tab bar (mobile) + sticky top nav (desktop) with Chat/Photos/Settings links, gradient active state
- `frontend/src/components/AppNav.test.tsx` - New: 2 GREEN tests for nav link rendering and active route
- `frontend/src/components/ChatBubble.test.tsx` - New: Wave 0 scaffold — content tests GREEN now, dark-theme class tests turn GREEN in Plan 03
- `frontend/src/pages/LoginPage.test.tsx` - New: Wave 0 scaffold — input tests GREEN now, bg-black test turns GREEN in Plan 02
- `frontend/src/App.tsx` - Modified: added AppNav import, AuthenticatedLayout component, updated 5 routes to use AuthenticatedLayout, changed bg-gray-950 to bg-black in OnboardingGate

## Decisions Made
- **AuthenticatedLayout nesting order**: AuthenticatedLayout > ProtectedRoute > OnboardingGate > Page. The layout always renders (shows nav even during auth redirects before ProtectedRoute takes over), which is correct since AppNav needs the router context.
- **Wave 0 scaffold design**: ChatBubble and LoginPage stubs intentionally contain dark-theme assertions that fail now. This defines the target behavior before Plans 02-03 update the component classes. The failing tests are not regressions — they are forward-looking contracts.
- **/photo route protection**: The plan specified wrapping PhotoPage in AuthenticatedLayout without ProtectedRoute (mirroring the original App.tsx which also had no ProtectedRoute on /photo). Preserved as-is.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed unused `beforeEach` import in LoginPage.test.tsx**
- **Found during:** Task 2 (build verification)
- **Issue:** `beforeEach` was imported in LoginPage.test.tsx but never used — TypeScript strict mode (`TS6133`) blocked the build
- **Fix:** Removed `beforeEach` from the vitest import statement
- **Files modified:** `frontend/src/pages/LoginPage.test.tsx`
- **Verification:** `npm run build` passed cleanly after fix
- **Committed in:** `ef42536` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minor import cleanup, no scope change.

## Issues Encountered
- Pre-existing AdminPage test failure (`renders all 5 metric card titles when data is loaded`) confirmed pre-existing before this plan's changes — out of scope per deviation scope boundary rule. Logged to deferred items.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- AppNav is wired and GREEN — Plans 02 (LoginPage), 03 (ChatBubble/ChatPage), 04 (SettingsPage/BillingPage) can all run in Wave 2 in parallel
- Wave 0 scaffolds in place: ChatBubble.test.tsx and LoginPage.test.tsx define the dark-theme contracts Plans 02-03 must satisfy
- AuthenticatedLayout already wraps all authenticated routes — Plans 02-04 only need to restyle their page components

---
*Phase: 14-apply-the-style-of-the-front-page-to-the-rest-of-the-ui-of-the-entire-app*
*Completed: 2026-03-10*
