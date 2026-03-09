---
phase: 10-landing-page
plan: 01
subsystem: ui
tags: [vitest, react, testing-library, motion, lucide-react, clsx, tailwind-merge, tdd]

# Dependency graph
requires: []
provides:
  - GlassCard shared primitive (base, active-warm, active-cool variants) for landing sections
  - vitest + jsdom test environment configured with @testing-library/react
  - LandingPage test scaffold in RED state covering LAND-01, LAND-02, LAND-03
  - motion, lucide-react, clsx, tailwind-merge installed as prod deps
affects:
  - 10-landing-page plans 02-04 (GlassCard imported by DualPromise, Trust, Pricing sections)
  - 10-landing-page plan 03+ (tests turn GREEN once components are implemented)

# Tech tracking
tech-stack:
  added:
    - motion@12.35.1 (Framer Motion v12, motion/react import)
    - lucide-react@0.577.0
    - clsx@2.1.1
    - tailwind-merge@3.5.0
    - vitest@4.0.18
    - "@testing-library/react@16.3.2"
    - "@testing-library/jest-dom@6.9.1"
    - "@testing-library/user-event@14.6.1"
    - jsdom@28.1.0
  patterns:
    - GlassCard uses cn() helper (clsx + tailwind-merge) defined locally in file, not exported
    - vitest globals: true enables describe/it/expect without imports in test files
    - vi.mock('../store/useAuthStore') pattern for mocking Zustand selectors in tests

key-files:
  created:
    - frontend/src/components/ui/GlassCard.tsx
    - frontend/vitest.config.ts
    - frontend/src/setupTests.ts
    - frontend/src/pages/LandingPage.test.tsx
  modified:
    - frontend/package.json (added test script + 8 new dependencies)

key-decisions:
  - "GlassCard uses motion/react (Framer Motion v12) NOT framer-motion — critical for correct import path"
  - "vitest globals: true set in config so test files don't need to import describe/it/expect"
  - "LandingPage tests intentionally in RED state at plan 01 completion — will turn GREEN after Plans 02-04"

patterns-established:
  - "GlassCard variant pattern: base/active-warm/active-cool — all landing section cards use this primitive"
  - "Test mocking pattern for useAuthStore: vi.mock selector pattern (selector: (s: { token: null }) => unknown)"

requirements-completed: [LAND-01, LAND-02, LAND-03]

# Metrics
duration: 14min
completed: 2026-03-09
---

# Phase 10 Plan 01: Landing Page Foundation Summary

**GlassCard glass-morphism component (3 variants) + vitest/jsdom configured + TDD scaffold in RED state covering LAND-01/02/03**

## Performance

- **Duration:** 14 min
- **Started:** 2026-03-09T10:02:47Z
- **Completed:** 2026-03-09T10:16:21Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- Installed all four required production deps (motion, lucide-react, clsx, tailwind-merge) in frontend
- Configured vitest with jsdom environment and @testing-library/react + jest-dom setup file
- Ported GlassCard component verbatim from Figma export with all three variants
- Created TDD test scaffold covering LAND-01/02/03 and auth redirect — confirmed RED (4 failing tests, expected)

## Task Commits

Each task was committed atomically:

1. **Task 1: Install dependencies and configure vitest** - `c988e72` (chore)
2. **Task 2: Port GlassCard component from Figma export** - `af630ac` (feat)
3. **Task 3: Create failing test scaffold for LandingPage requirements** - `87f66d2` (test)

## Files Created/Modified
- `frontend/src/components/ui/GlassCard.tsx` - Glass-morphism card primitive, 3 variants, exports GlassCard
- `frontend/vitest.config.ts` - Vitest config with jsdom, globals: true, setupFiles
- `frontend/src/setupTests.ts` - @testing-library/jest-dom global matchers
- `frontend/src/pages/LandingPage.test.tsx` - TDD scaffold covering LAND-01, LAND-02, LAND-03
- `frontend/package.json` - Added "test": "vitest" script + 8 new dependencies
- `frontend/package-lock.json` - Updated lockfile

## Decisions Made
- GlassCard imports from `"motion/react"` (Framer Motion v12) NOT `"framer-motion"` — per Figma source
- vitest `globals: true` — test files don't need to import describe/it/expect manually
- Tests are intentionally failing at this plan — they enforce LAND-01/02/03 correctness and will turn GREEN after Plans 02-04 implement the Figma design

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. All four packages resolved from npm immediately. Vitest configured and running on first attempt. Tests confirmed RED state (4 failing: LAND-01 x3, LAND-02 x1).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- GlassCard is importable by all landing section components (Plans 02-04)
- Test suite configured and failing as expected — ready for TDD GREEN phase
- Plans 02-04 need to implement: hero with "The AI that takes care of your day" headline, DualPromise (Assistant Mode / Companion Mode), Pricing section ("Choose your plan" / "Premium"), CTAs with "Create my Ava" linking to /signup

---
*Phase: 10-landing-page*
*Completed: 2026-03-09*

## Self-Check: PASSED

- FOUND: frontend/src/components/ui/GlassCard.tsx
- FOUND: frontend/vitest.config.ts
- FOUND: frontend/src/pages/LandingPage.test.tsx
- FOUND: .planning/phases/10-landing-page/10-01-SUMMARY.md
- FOUND commit: c988e72 (chore: install deps and configure vitest)
- FOUND commit: af630ac (feat: GlassCard component)
- FOUND commit: 87f66d2 (test: failing test scaffold)
