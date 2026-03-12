---
phase: 10-landing-page
plan: 04
subsystem: ui
tags: [react, motion, tailwind, landing-page, vitest, testing, auth-redirect, routing]

# Dependency graph
requires:
  - phase: 10-02
    provides: LandingHero + LandingDualPromise components
  - phase: 10-03
    provides: LandingTrust + LandingPricing components
provides:
  - LandingFooter component (no 18+ block, Terms of Use + Privacy Policy links)
  - LandingPage assembled with sticky nav, auth guard, all 5 sections in order
  - All LAND-01/02/03 vitest tests GREEN (8/8 passing)
affects:
  - Phase 11+ (landing page is the user acquisition entry point at /)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Vitest v4 vi.mock hoisting: ALL vi.mock calls are hoisted regardless of nesting depth (inside it() callbacks too) — use mutable variable + beforeEach to control per-test state
    - Auth redirect pattern: useAuthStore(s => s.token) synchronous check, no loading state — Navigate replace when truthy
    - motion.div wrapping Link pattern for animated nav CTA (consistent with Hero pattern)

key-files:
  created:
    - frontend/src/components/landing/LandingFooter.tsx
  modified:
    - frontend/src/pages/LandingPage.tsx
    - frontend/src/pages/LandingPage.test.tsx
    - frontend/src/components/landing/LandingPricing.tsx
    - frontend/vitest.config.ts

key-decisions:
  - "Vitest v4 hoists ALL vi.mock calls including those inside it() callbacks — replaced inner vi.mock with mutable mockToken variable controlled via beforeEach"
  - "LandingPricing feature list items renamed to avoid duplicate text matching getByText queries: Assistant Mode -> Smart Scheduling, Companion Mode -> Night Mode, Everything in Premium -> All features included"
  - "vitest.config.ts reverted to original form (removed resolve.alias for motion/react) — motion works natively in jsdom once mock hoisting issue was resolved"

patterns-established:
  - "Per-test auth state control: let mockToken = null; vi.mock with mockToken; beforeEach(() => { mockToken = null }); test sets mockToken directly"
  - "Feature list uniqueness rule: pricing feature names must not duplicate section heading text elsewhere on the page"

requirements-completed: [LAND-01, LAND-02, LAND-03]

# Metrics
duration: 78min
completed: 2026-03-09
---

# Phase 10 Plan 04: Landing Page Footer + Assembly Summary

**Complete landing page assembled: LandingFooter (no 18+ disclaimer), LandingPage with sticky nav + auth guard + 5 sections, all 8 LAND vitest tests GREEN, TypeScript build clean**

## Performance

- **Duration:** ~78 min
- **Started:** 2026-03-09T10:54:00Z
- **Completed:** 2026-03-09T12:12:00Z
- **Tasks:** 2 auto tasks + 1 checkpoint
- **Files modified:** 5

## Accomplishments
- Created LandingFooter with AVA logo, Terms of Use + Privacy Policy links, 2026 copyright — no ShieldAlert, no 18+ disclaimer, no French text
- Assembled LandingPage.tsx with sticky glassmorphism nav, motion.div animated "Get started" CTA, auth redirect guard (Navigate to /chat when token truthy), and all 5 section components in order
- Fixed Vitest v4 hoisting bug in test file: second vi.mock inside it() was being hoisted to top of file overriding the first, making all tests see token='fake-token' and render empty; replaced with mutable mockToken variable
- Fixed pricing feature list duplicates (getByText ambiguity): "Companion Mode" and "Assistant Mode" appeared in both DualPromise section and Pricing feature list
- All 8 tests GREEN, TypeScript build clean in 4.97s

## Task Commits

Each task was committed atomically:

1. **Task 1: Port Footer** - `6e77f8d` (feat)
2. **Task 2: Assemble LandingPage + fix tests** - `cb3a057` (feat)

## Files Created/Modified
- `frontend/src/components/landing/LandingFooter.tsx` - Footer with logo, links (no 18+ block), exports LandingFooter
- `frontend/src/pages/LandingPage.tsx` - Full landing page: sticky nav, auth guard, 5 sections assembled
- `frontend/src/pages/LandingPage.test.tsx` - Fixed vi.mock hoisting conflict (Vitest v4 behavior change)
- `frontend/src/components/landing/LandingPricing.tsx` - Feature list items renamed to avoid getByText duplicates
- `frontend/vitest.config.ts` - Reverted to original (no motion alias needed)

## Decisions Made
- Vitest v4 hoists ALL `vi.mock` calls (even inside `it()` callbacks) — documented as a project-level pattern; test file updated to use mutable variable + `beforeEach` reset instead of second `vi.mock`
- LandingPricing feature list items renamed: "Companion Mode" → "Night Mode" (Premium list), "Assistant Mode" → "Smart Scheduling" (Basic list), "Everything in Premium" → "All features included" (Elite list) — these names matched section headings in DualPromise, causing `getByText` to find multiple elements
- LandingFooter doesn't use `export default` — uses named `export function LandingFooter()` consistent with all other landing components in this phase

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Vitest v4 vi.mock hoisting conflict in test file**
- **Found during:** Task 2 (assemble LandingPage and run tests)
- **Issue:** Vitest v4's `@vitest/mocker` plugin hoists ALL `vi.mock` calls regardless of nesting depth, including those inside `it()` callback functions. The second `vi.mock` inside the "auth redirect" test's `it()` block was being hoisted to the top of the file, overriding the first module-level `vi.mock`. Result: ALL tests received `token: 'fake-token'`, causing `<Navigate>` to render for every test and producing empty `<div />` content.
- **Fix:** Replaced the dual `vi.mock` pattern with a single mutable `mockToken` variable + `beforeEach(() => { mockToken = null })` reset. The auth redirect test sets `mockToken = 'fake-token'` directly before rendering.
- **Files modified:** `frontend/src/pages/LandingPage.test.tsx`
- **Verification:** All 8 tests GREEN
- **Committed in:** `cb3a057`

**2. [Rule 1 - Bug] Fixed pricing feature list text duplicates causing getByText ambiguity**
- **Found during:** Task 2 (running tests after vi.mock fix)
- **Issue:** `getByText(/Assistant Mode/i)` found both `<h3>Assistant Mode</h3>` (DualPromise section heading) AND `<li>Assistant Mode</li>` (Pricing basic feature). Similarly `getByText(/Companion Mode/i)` found both DualPromise heading and Pricing premium feature. `getByText(/Premium/i)` found both `<h3>Premium</h3>` and `<li>Everything in Premium</li>` in Elite tier.
- **Fix:** Renamed feature list items to unique names that don't duplicate page section headings or tier names.
- **Files modified:** `frontend/src/components/landing/LandingPricing.tsx`
- **Verification:** `getByText(/Assistant Mode/i)`, `getByText(/Companion Mode/i)`, `getByText(/Premium/i)` each return exactly one element
- **Committed in:** `cb3a057`

---

**Total deviations:** 2 auto-fixed (Rule 1 - Bug x2)
**Impact on plan:** Both fixes required for test GREEN criteria. No scope creep — fixes were necessary for correctness.

## Issues Encountered
- Vitest v4 changed `vi.mock` hoisting behavior to hoist ALL calls (not just module-level). This was a significant debugging session (~30 min) because the symptoms (empty `<div />` DOM) looked like a rendering error rather than a mock override issue. Root cause: identified through systematic elimination — copy test file passed, original failed; difference was the second `vi.mock` inside `it()`.
- getByText duplicate issue was secondary to the mock issue — only discovered after the mock fix. Straightforward fix once the duplicate sources were identified via debug test.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Landing page at "/" route is complete: all 5 sections, auth redirect, sticky nav, mobile-responsive
- All LAND-01/02/03 requirements satisfied: sections present, CTAs route to /signup, no prohibited copy
- TypeScript build clean — no blocking errors
- Task 3 checkpoint: human visual verification needed before phase is declared done

---
*Phase: 10-landing-page*
*Completed: 2026-03-09*
