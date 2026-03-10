---
phase: 14-apply-the-style-of-the-front-page-to-the-rest-of-the-ui-of-the-entire-app
plan: "04"
subsystem: ui

tags: [react, tailwind, glassmorphism, dark-theme, settings, billing, subscribe, avatar-setup, admin, landing]

requires:
  - phase: 14-01
    provides: AppNav, AuthenticatedLayout, GlassCard component foundation

provides:
  - SettingsPage restyled with bg-black, GlassCard sections, gradient active selectors, subscription section, sign out
  - BillingPage restyled with bg-black and Back to Settings link
  - SubscribePage restyled with bg-black, GlassCard, gradient subscribe button
  - AvatarSetupPage restyled with bg-black, GlassCard, dark inputs, gradient buttons, violet spinner
  - AdminPage restyled with bg-black (GlassCards already present)
  - LandingHero updated with chat bubbles + blurred locked photo mockup (removed audio visualizer)

affects: [phase 14 visual unification complete]

tech-stack:
  added: []
  patterns:
    - GlassCard wrapping all page content sections on dark black pages
    - Gradient active selectors (from-blue-600 to-violet-600) replacing solid gray active states
    - bg-white/5 border border-white/10 for dark input fields and feature list boxes
    - Subscription status + Manage Billing link pattern in SettingsPage (reads from useQuery subscription)
    - Sign out button pattern using handleSignOut with signOut() + clearAuth() + navigate('/login')

key-files:
  created: []
  modified:
    - frontend/src/pages/SettingsPage.tsx
    - frontend/src/pages/BillingPage.tsx
    - frontend/src/pages/SubscribePage.tsx
    - frontend/src/pages/AvatarSetupPage.tsx
    - frontend/src/pages/AdminPage.tsx
    - frontend/src/components/landing/LandingHero.tsx

key-decisions:
  - "Persona buttons in SettingsPage do not have active state comparison (updatePersona fires immediately per API design) — gradient selector pattern not applied to persona grid"
  - "AdminPage.test.tsx 'renders all 5 metric cards' test failure is pre-existing (confirmed by checking out prior commit) — not caused by bg-black change; deferred to out-of-scope log"

patterns-established:
  - "Dark page pattern: min-h-screen bg-black text-white as outer wrapper"
  - "GlassCard section pattern: <GlassCard className='p-5'> replaces <section className='bg-white rounded-2xl p-5 shadow-sm border border-gray-100'>"
  - "Gradient active selector: bg-gradient-to-r from-blue-600 to-violet-600 border-transparent text-white vs border-white/10 bg-white/5 text-slate-400 inactive"

requirements-completed: [UI-05, UI-06]

duration: 16min
completed: 2026-03-10
---

# Phase 14 Plan 04: Restyle Remaining Pages + LandingHero Mockup Summary

**bg-black + GlassCard unification across SettingsPage (with subscription + sign out), BillingPage (with back button), SubscribePage, AvatarSetupPage, AdminPage, and LandingHero chat bubbles mockup**

## Performance

- **Duration:** 16 min
- **Started:** 2026-03-10T14:00:18Z
- **Completed:** 2026-03-10T14:15:45Z
- **Tasks:** 2 auto tasks (Task 3 is a checkpoint)
- **Files modified:** 6

## Accomplishments

- SettingsPage fully restyled: bg-black, 5 GlassCard sections, gradient active selectors for platform and spiciness, new Subscription section showing plan/status with Manage Billing link, Sign out button at bottom
- BillingPage: bg-black (was bg-gray-950), Back to Settings link added, Manage billing button uses gradient
- SubscribePage: bg-black, GlassCard inner card, gradient subscribe button (was bg-purple-600)
- AvatarSetupPage: bg-black, GlassCard wrapping entire form, all inputs converted to bg-white/5 dark glass style, personality buttons use gradient active state, submit/regenerate/approve buttons use gradient, spinner uses border-violet-500
- AdminPage: bg-black (GlassCards already present from Phase 12)
- LandingHero: removed BAR_HEIGHTS constant and audio visualizer; replaced notification block + visualizer with chat bubbles ("Missing you already...", "Show me something", "Just for you...") and a blurred locked photo placeholder

## Task Commits

1. **Task 1: Restyle SettingsPage, BillingPage, SubscribePage, AvatarSetupPage** - `efc964d` (feat)
2. **Task 2: AdminPage bg-black + LandingHero mockup replacement** - `db4f024` (feat)

## Files Created/Modified

- `frontend/src/pages/SettingsPage.tsx` - Full dark glass restyle: bg-black, GlassCard sections, gradient selectors, subscription section, sign out button
- `frontend/src/pages/BillingPage.tsx` - bg-gray-950 -> bg-black, Back to Settings link, gradient Manage billing button
- `frontend/src/pages/SubscribePage.tsx` - bg-gray-950 -> bg-black, GlassCard inner card, gradient subscribe button
- `frontend/src/pages/AvatarSetupPage.tsx` - bg-gray-950 -> bg-black, GlassCard form wrapper, dark glass inputs, gradient buttons, violet spinner
- `frontend/src/pages/AdminPage.tsx` - bg-gray-950 -> bg-black only (GlassCards already present)
- `frontend/src/components/landing/LandingHero.tsx` - Removed BAR_HEIGHTS + audio visualizer, added chat bubbles + locked photo mockup

## Decisions Made

- Persona buttons in SettingsPage have no active state highlighting because `updatePersona` fires an immediate API call (no local state comparison available for which persona is currently active). The gradient active pattern was applied to platform buttons and spiciness buttons where local prefs state is available.
- AdminPage.test.tsx failure confirmed pre-existing (failing before my commits). Deferred.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed wrong state comparison in persona buttons**
- **Found during:** Task 1 (SettingsPage TypeScript build)
- **Issue:** Initial implementation compared `prefs.preferred_platform === opt.value` for persona buttons (wrong state field — caused TS2367 type error: platform type vs persona type)
- **Fix:** Removed conditional class logic from persona buttons since persona active state is not tracked in local `prefs` state (updatePersona fires immediately via API)
- **Files modified:** frontend/src/pages/SettingsPage.tsx
- **Verification:** TypeScript build passes cleanly
- **Committed in:** efc964d (part of Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in wrong state comparison)
**Impact on plan:** Necessary type fix. Plan specified gradient active selectors for persona — implemented as static glass style since no local active-tracking state exists for persona selector. Platform and spiciness selectors correctly use gradient active pattern.

## Issues Encountered

- AdminPage.test.tsx "renders all 5 metric card titles" test was already failing before this plan's changes (confirmed by checking out prior commit `5421e3a` and running the test). The test failure is unrelated to `bg-black` change. Deferred to out-of-scope items.

## Next Phase Readiness

- All 6 files complete. Phase 14 visual unification pass is fully implemented across all app pages.
- Task 3 is a `checkpoint:human-verify` — user must visually verify the complete dark glass redesign across all pages at http://localhost:5173 before the phase can be marked complete.
- 4 of 5 tests GREEN (LandingPage 8/8, AppNav 2/2, ChatBubble 4/4, LoginPage 2/2). AdminPage 1 test pre-existing failure.

---
*Phase: 14-apply-the-style-of-the-front-page-to-the-rest-of-the-ui-of-the-entire-app*
*Completed: 2026-03-10*
