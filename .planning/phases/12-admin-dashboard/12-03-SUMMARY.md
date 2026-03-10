---
phase: 12-admin-dashboard
plan: "03"
subsystem: ui
tags: [react, jwt, vitest, tanstack-query, tailwind, admin]

# Dependency graph
requires:
  - phase: 12-01
    provides: "GET /admin/metrics endpoint with AdminMetrics response shape"
provides:
  - "AdminRoute guard — JWT-based is_admin check, silent redirect to /chat for non-admins"
  - "AdminPage — 5 stat cards (Active Users, Messages Sent, Photos Generated, Active Subscriptions, New Signups) each showing 7d/30d/all-time values"
  - "getAdminMetrics() API function in frontend/src/api/admin.ts"
  - "/admin route wired in App.tsx, URL-only access (no navigation link)"
  - "AdminPage.test.tsx — 4 Vitest tests covering access control and metric card rendering"
affects: [phase-13-smoke-test, phase-14-ui-style]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "AdminRoute uses same atob JWT decode pattern as Phase 6 user_id extraction to read user_metadata.is_admin"
    - "No auto-polling: staleTime=0 + refetchOnWindowFocus=false mirrors BillingPage pattern for one-shot load with manual refresh"
    - "URL-only admin access — no Link/href to /admin in any page component"

key-files:
  created:
    - frontend/src/api/admin.ts
    - frontend/src/pages/AdminPage.tsx
    - frontend/src/pages/AdminPage.test.tsx
  modified:
    - frontend/src/App.tsx

key-decisions:
  - "AdminRoute defined as named export in AdminPage.tsx (not App.tsx) — co-location with the page it guards, consistent with all other route guards being defined near their guarded component"
  - "AdminPage.tsx created in Task 1 alongside test file so tests could run GREEN in the same task — minor split from plan's task ordering but all done criteria met"
  - "No navigation link to /admin added anywhere — URL-only operator access per CONTEXT.md locked decision"

patterns-established:
  - "AdminRoute pattern: no token -> /login, token without is_admin -> /chat (silent), token with is_admin -> render children"
  - "StatCard sub-component: title + MetricWindow -> GlassCard with 7d/30d/all-time rows"

requirements-completed: [ADMN-01, ADMN-03]

# Metrics
duration: 10min
completed: 2026-03-10
---

# Phase 12 Plan 03: Admin Dashboard Frontend Summary

**React admin dashboard with JWT-based AdminRoute guard, 5 GlassCard metric stat cards (7d/30d/all-time), and 4 passing Vitest tests for access control and rendering**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-03-10T08:07:41Z
- **Completed:** 2026-03-10T08:17:29Z
- **Tasks:** 2 tasks completed
- **Files modified:** 4

## Accomplishments

- Created `frontend/src/api/admin.ts` with `AdminMetrics` type and `getAdminMetrics()` fetching `GET /admin/metrics` with Bearer auth
- Created `frontend/src/pages/AdminPage.tsx` with `AdminRoute` guard (JWT `user_metadata.is_admin` check), `AdminPage` default export showing 5 stat cards, and `StatCard` sub-component rendering 7d/30d/all-time values via `GlassCard`
- Wired `/admin` route in `App.tsx` wrapped in `AdminRoute` — no navigation link added to any other page (URL-only operator access)
- All 4 Vitest tests in `AdminPage.test.tsx` pass: unauthenticated → `/login`, non-admin → `/chat`, admin → renders children, metric cards render on data load
- TypeScript compilation clean (0 errors), full test suite 12/12 passing (LandingPage + AdminPage)

## Task Commits

1. **Task 1: Create admin.ts, AdminPage.tsx, and AdminPage.test.tsx** - `cc3e184` (feat)
2. **Task 2: Wire /admin route in App.tsx** - `041f4a5` (feat)

## Files Created/Modified

- `frontend/src/api/admin.ts` — `MetricWindow`, `AdminMetrics` types; `getAdminMetrics(token)` function
- `frontend/src/pages/AdminPage.tsx` — `AdminRoute` (named export), `StatCard`, `AdminPage` (default export)
- `frontend/src/pages/AdminPage.test.tsx` — 4 Vitest tests covering redirect behavior and metric card rendering
- `frontend/src/App.tsx` — Added `AdminPage`/`AdminRoute` imports and `/admin` route

## Decisions Made

- `AdminRoute` placed as a named export in `AdminPage.tsx` rather than `App.tsx` — co-location keeps the guard next to its guarded component; the test file imports from the same location cleanly.
- `AdminPage.tsx` was created in Task 1 (alongside the test file) so all 4 tests could run GREEN immediately — the plan's task split would have left tests non-runnable until Task 2, so both files were created together. Task 2 then wired `App.tsx` only. This fulfills all done criteria.
- No navigation link to `/admin` added to `SettingsPage`, `ChatPage`, or any other page — URL-only access per the locked CONTEXT.md decision.

## Deviations from Plan

**1. [Rule 3 - Blocking] AdminPage.tsx created in Task 1 alongside test file**
- **Found during:** Task 1 (test file creation)
- **Issue:** The test file imports `AdminRoute` and `AdminPage` from `AdminPage.tsx` — running tests without the file would cause import errors. The plan's Task 1 verify step requires "Tests pass (GREEN)" which is impossible without AdminPage.tsx.
- **Fix:** Created both `AdminPage.tsx` and `AdminPage.test.tsx` in Task 1. Task 2 then only wired `App.tsx`.
- **Files modified:** frontend/src/pages/AdminPage.tsx (created in Task 1 instead of Task 2)
- **Verification:** All 4 tests pass immediately after Task 1; Task 2 commit confirmed TypeScript clean + full suite GREEN
- **Committed in:** cc3e184 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 3 - blocking)
**Impact on plan:** Minimal — task boundary shifted to unblock tests. All outputs and done criteria delivered as specified.

## Issues Encountered

None — implementation matched plan specifications exactly. JWT `atob` decode for `user_metadata.is_admin` worked as expected per the Phase 6 pattern.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 12 complete: backend API (Plan 01), usage event wiring (Plan 02), and frontend dashboard (Plan 03) all delivered
- `/admin` URL accessible in production for operators with `is_admin: true` in their Supabase user_metadata
- Phase 13 (smoke test) can verify end-to-end: admin user visits /admin, non-admin user gets silent redirect
- Phase 14 (UI style unification) may want to apply consistent page chrome to AdminPage

---
*Phase: 12-admin-dashboard*
*Completed: 2026-03-10*
