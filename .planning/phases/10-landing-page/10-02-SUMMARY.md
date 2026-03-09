---
phase: 10-landing-page
plan: 02
subsystem: ui
tags: [react, motion, lucide-react, tailwind, landing-page, figma-port]

# Dependency graph
requires:
  - phase: 10-01
    provides: GlassCard component (active-cool/active-warm variants) and vitest test infrastructure
provides:
  - LandingHero section component with split diagonal layout, English copy, BAR_HEIGHTS audio visualizer, Link to /signup
  - LandingDualPromise section component with GlassCard active-cool/active-warm cards in English
affects:
  - 10-landing-page plan 05+ (LandingPage assembly imports these components)
  - 10-landing-page tests (TDD scaffold will turn GREEN for LAND-01/LAND-02/LAND-03 once all sections assembled)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - motion.div wrapping Link pattern for animated CTA buttons (NOT motion.button with href)
    - BAR_HEIGHTS constant pattern for pre-computed visualizer heights (no Math.random in render)
    - clip-path diagonal split via inline style prop (NOT Tailwind class — Tailwind can't generate arbitrary clip-path)
    - hidden md:flex pattern to hide right-panel content on mobile for hero sections

key-files:
  created:
    - frontend/src/components/landing/LandingHero.tsx
    - frontend/src/components/landing/LandingDualPromise.tsx
  modified:
    - frontend/src/components/ui/GlassCard.tsx (type-only import fix)

key-decisions:
  - "TypingText helper removed from LandingHero — it was in the Figma source but unused in the actual output; removing avoids TS6133 unused variable error"
  - "GlassCard HTMLMotionProps changed to type-only import to satisfy verbatimModuleSyntax — pre-existing issue fixed as build blocker"
  - "Right companion panel hidden on mobile (hidden md:flex) — hero content readable on small screens via left panel + center CTAs"

patterns-established:
  - "CTA routing pattern: motion.div wrapping Link to='/signup' — never motion.button with href"
  - "Figma component ports: translate French copy verbatim to English intent, remove Unsplash img tags, keep gradient backgrounds"

requirements-completed: [LAND-01, LAND-02, LAND-03]

# Metrics
duration: 11min
completed: 2026-03-09
---

# Phase 10 Plan 02: Landing Page Hero + DualPromise Summary

**Full-screen split-diagonal hero and dual-mode GlassCard section ported from Figma with English copy, LAND-03 compliance, and pre-computed audio visualizer**

## Performance

- **Duration:** 11 min
- **Started:** 2026-03-09T10:27:36Z
- **Completed:** 2026-03-09T10:38:40Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Ported Hero section with split diagonal clip-path layout, Jarvis OS mockup, companion notification mockup, English copy throughout
- Replaced Math.random() audio visualizer with BAR_HEIGHTS constant (React strict mode safe)
- Replaced French motion.button CTA with motion.div wrapping Link to="/signup" and plain no-op button for Watch the demo
- Ported DualPromise section with two GlassCards in English (Assistant Mode / Companion Mode)
- Fixed pre-existing GlassCard TS1484 build blocker (type-only import)

## Task Commits

Each task was committed atomically:

1. **Task 1: Port Hero section** - `178f158` (feat)
2. **Task 2: Port DualPromise section** - `817e586` (feat)
3. **Auto-fix: TS errors** - `65bcdb6` (fix)

## Files Created/Modified
- `frontend/src/components/landing/LandingHero.tsx` - Full-screen hero with split diagonal, Jarvis mockup, English CTAs, exports LandingHero
- `frontend/src/components/landing/LandingDualPromise.tsx` - Two GlassCards (active-cool/active-warm) with English mode descriptions, exports LandingDualPromise
- `frontend/src/components/ui/GlassCard.tsx` - Fixed type-only import for HTMLMotionProps (TS1484)

## Decisions Made
- Removed `TypingText` helper from LandingHero — included in Figma source but never used in the rendered output; its presence caused TS6133 build error
- Right companion panel hidden on mobile with `hidden md:flex` — avoids broken overlapping layout on small screens while keeping the hero functional
- GlassCard `HTMLMotionProps` import changed to `type HTMLMotionProps` to satisfy `verbatimModuleSyntax` tsconfig requirement

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed unused TypingText component causing TS6133 error**
- **Found during:** Task 1 (Port Hero section) — build check after file creation
- **Issue:** TypingText helper included from Figma source but never called in LandingHero JSX; TypeScript strict mode emitted TS6133 "declared but value never read"
- **Fix:** Removed TypingText declaration and its associated useState/useEffect imports from LandingHero.tsx
- **Files modified:** `frontend/src/components/landing/LandingHero.tsx`
- **Verification:** `npm run build` succeeds with no TS errors
- **Committed in:** `65bcdb6`

**2. [Rule 1 - Bug] Fixed GlassCard HTMLMotionProps type-only import (pre-existing build blocker)**
- **Found during:** Overall verification build — pre-existing from Plan 01
- **Issue:** `import { motion, HTMLMotionProps } from "motion/react"` violated `verbatimModuleSyntax` tsconfig rule; TS1484 error blocked the entire build
- **Fix:** Changed to `import { motion, type HTMLMotionProps }` (type-only import syntax)
- **Files modified:** `frontend/src/components/ui/GlassCard.tsx`
- **Verification:** `npm run build` — `✓ built in 2.51s` with no errors
- **Committed in:** `65bcdb6`

---

**Total deviations:** 2 auto-fixed (Rule 1 - Bug x2)
**Impact on plan:** Both fixes required for TypeScript build success (success criteria). No scope creep.

## Issues Encountered

None beyond the auto-fixed TS errors above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- LandingHero and LandingDualPromise are importable by LandingPage assembly (Plan 05+)
- TypeScript build passes cleanly — no blocking errors
- TDD tests in LandingPage.test.tsx will progress toward GREEN once all sections (Trust, Pricing, Footer) are assembled and LandingPage imports them all

---
*Phase: 10-landing-page*
*Completed: 2026-03-09*

## Self-Check: PASSED

- FOUND: frontend/src/components/landing/LandingHero.tsx
- FOUND: frontend/src/components/landing/LandingDualPromise.tsx
- FOUND: .planning/phases/10-landing-page/10-02-SUMMARY.md
- FOUND commit: 178f158 (feat: Port Hero section)
- FOUND commit: 817e586 (feat: Port DualPromise section)
- FOUND commit: 65bcdb6 (fix: TS errors)
