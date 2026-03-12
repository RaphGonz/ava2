---
phase: 10
slug: landing-page
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-09
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest |
| **Config file** | `frontend/vitest.config.ts` — Wave 0 installs |
| **Quick run command** | `cd frontend && npm run test -- --run src/pages/LandingPage.test.tsx` |
| **Full suite command** | `cd frontend && npm run test -- --run` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm run test -- --run src/pages/LandingPage.test.tsx`
- **After every plan wave:** Run `cd frontend && npm run test -- --run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-T1 | 01 | 1 | LAND-01 | install verify | `cd frontend && node -e "require('./node_modules/motion/react')"` | ❌ W0 | ⬜ pending |
| 10-01-T2 | 01 | 1 | LAND-01 | import verify | `cd frontend && grep -c "motion/react" src/components/ui/GlassCard.tsx` | ❌ W0 | ⬜ pending |
| 10-01-T3 | 01 | 1 | LAND-01,02,03 | smoke (scaffold) | `cd frontend && npm run test -- --run src/pages/LandingPage.test.tsx` | ❌ W0 | ⬜ pending |
| 10-02-T1 | 02 | 2 | LAND-01 | content check | `grep -c "Create my Ava" frontend/src/components/landing/LandingHero.tsx` | ❌ W0 | ⬜ pending |
| 10-02-T2 | 02 | 2 | LAND-01 | content check | `grep -c "Assistant Mode" frontend/src/components/landing/LandingDualPromise.tsx` | ❌ W0 | ⬜ pending |
| 10-03-T1 | 03 | 2 | LAND-01 | content check | `grep -c "Trust & Security" frontend/src/components/landing/LandingTrust.tsx` | ❌ W0 | ⬜ pending |
| 10-03-T2 | 03 | 2 | LAND-01,02 | content check | `grep -c "Choose your plan" frontend/src/components/landing/LandingPricing.tsx` | ❌ W0 | ⬜ pending |
| 10-04-T1 | 04 | 3 | LAND-03 | compliance check | `grep "ShieldAlert" frontend/src/components/landing/LandingFooter.tsx \| wc -l \| grep "^0$"` | ❌ W0 | ⬜ pending |
| 10-04-T2 | 04 | 3 | LAND-01,02,03 | full test suite | `cd frontend && npm run test -- --run src/pages/LandingPage.test.tsx` | ❌ W0 | ⬜ pending |
| 10-04-T3 | 04 | 3 | LAND-01,02,03 | full suite gate | `cd frontend && npm run test -- --run` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/vitest.config.ts` — vitest config with jsdom environment
- [ ] `frontend/src/pages/LandingPage.test.tsx` — stubs for LAND-01, LAND-02, LAND-03
- [ ] Update `frontend/package.json` `"test"` script: `"test": "vitest"`
- [ ] Framework install: `cd frontend && npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual fidelity to Figma | LAND-01 | CSS/layout cannot be asserted in unit tests | Open `/` in browser, compare against Figma frames |
| Hero clip-path diagonal renders correctly | LAND-01 | CSS clip-path is a paint-time property | Open `/` in browser at desktop width, confirm diagonal split |
| Authenticated redirect in browser | LAND-02 | Zustand token persists in localStorage | Log in, navigate to `/`, confirm redirect to `/chat` |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-09
