---
phase: 11-subscription-management-churn
plan: "02"
subsystem: payments
tags: [stripe, react, typescript, react-query, billing]

# Dependency graph
requires:
  - phase: 11-01
    provides: "Backend billing endpoints: /billing/subscription, /billing/invoices, /billing/portal-session, /billing/cancel"
provides:
  - "frontend/src/api/billing.ts — 4 new API functions: getSubscription, getInvoices, createPortalSession, cancelSubscription"
  - "frontend/src/pages/BillingPage.tsx — full billing UI with subscription status, invoice history, Manage billing, Upgrade modal"
  - "/billing route registered in App.tsx as ProtectedRoute-only"
affects: [11-03, 12-admin-dashboard, 13-smoke-test]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "useQuery staleTime: 60*1000 on subscription for Stripe Portal tab-return auto-refresh"
    - "cancel_at_period_end toggle pattern: Cancel link swaps to Resubscribe text + link"
    - "In-app upgrade modal before any Stripe redirect (prevents direct Stripe link bounce)"

key-files:
  created:
    - frontend/src/pages/BillingPage.tsx
  modified:
    - frontend/src/api/billing.ts
    - frontend/src/App.tsx

key-decisions:
  - "staleTime 60s on subscription query (not disabled refetchOnWindowFocus) — triggers refetch when user tabs back from Stripe Portal after >60s"
  - "cancelStep state wired at component level (idle/survey-q1/survey-q2/confirming/cancelled) — Plan 03 implements step logic without restructuring component"
  - "Upgrade modal is in-app (no direct Stripe redirect) — user sees plan info before checkout"
  - "Cancel link is de-emphasized text button (not a prominent action button) — low-regret tone per CONTEXT.md"
  - "All 4 billing API functions use token-only auth (no require_active_subscription) — billing accessible in all subscription states"

patterns-established:
  - "Portal session freshness: createPortalSession called fresh on every click (never cached)"
  - "Billing route: ProtectedRoute only, no OnboardingGate — subscription management accessible to all auth states"
  - "Invoice status badge colors: green-400 for paid, yellow-400 for open, gray-400 for others"

requirements-completed: [SUBS-01, SUBS-02]

# Metrics
duration: 10min
completed: 2026-03-09
---

# Phase 11 Plan 02: Billing UI Summary

**React billing page with Stripe Portal integration: subscription status display, invoice history with PDF links, Manage billing button, in-app Upgrade modal, and cancel/resubscribe toggle — all built on 4 new typed API client functions.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-03-09T15:47:01Z
- **Completed:** 2026-03-09T15:57:43Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Expanded billing.ts with SubscriptionData and Invoice types plus 4 API functions (getSubscription, getInvoices, createPortalSession, cancelSubscription)
- Created BillingPage.tsx with subscription info card (plan name, status, next billing date), action buttons, invoice history table, and Upgrade modal
- Wired /billing route in App.tsx as ProtectedRoute-only (no OnboardingGate) — billing accessible in all subscription states
- staleTime: 60*1000 on subscription query enables auto-refresh when user returns from Stripe Portal tab

## Task Commits

Each task was committed atomically:

1. **Task 1: Expand billing.ts API client** - `a3e27a4` (feat)
2. **Task 2: BillingPage component + route registration** - `5f81e06` (feat)

## Files Created/Modified
- `frontend/src/api/billing.ts` — Added SubscriptionData, Invoice types; getSubscription, getInvoices, createPortalSession, cancelSubscription functions
- `frontend/src/pages/BillingPage.tsx` — New billing page: subscription info (plan name, status, next billing date), Manage billing button (portal session), Upgrade modal (in-app before Stripe redirect), Cancel/Resubscribe link toggle, invoice history table with date/amount/status/PDF link
- `frontend/src/App.tsx` — Added BillingPage import and /billing ProtectedRoute registration

## Decisions Made
- staleTime: 60s on subscription query (refetchOnWindowFocus kept enabled by default) — user who spends >60s in Stripe Portal gets fresh data on tab return without any extra code
- cancelStep useState wired in BillingPage at component level now, so Plan 03 can implement the survey steps inline without restructuring
- In-app Upgrade modal (not direct checkout redirect) matches CONTEXT.md requirement: user sees plan options/pricing before any Stripe redirect
- Cancel link is a de-emphasized `<button className="text-sm text-gray-500...">` — not a prominent button — per CONTEXT.md low-regret tone decision

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- billing.ts API client fully typed and ready for Plan 03 cancel flow
- cancelStep state hook already in BillingPage — Plan 03 implements step logic
- /billing route live, accessible to all authenticated users
- SUBS-01 (view plan info) and SUBS-02 (invoice history + portal) requirements fulfilled

---
*Phase: 11-subscription-management-churn*
*Completed: 2026-03-09*
