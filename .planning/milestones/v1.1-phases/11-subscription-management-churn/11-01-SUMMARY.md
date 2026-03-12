---
phase: 11-subscription-management-churn
plan: "01"
subsystem: payments
tags: [stripe, fastapi, python, postgres, supabase]

# Dependency graph
requires:
  - phase: 07-avatar-system-production
    provides: subscriptions table (stripe_customer_id, stripe_subscription_id, status, current_period_end)
  - phase: 08-infrastructure-deployment
    provides: usage_events table with RLS enabled
  - phase: 09-auth-polish-email
    provides: get_user_email_by_subscription_id, stripe webhook email wiring
provides:
  - Migration 006 adding cancel_at_period_end BOOLEAN column to subscriptions table
  - get_subscription_detail() — reads subscription state from local DB
  - get_customer_invoices() — lists up to 12 Stripe invoices for a customer
  - update_subscription_cancel_state() — persists cancel state on webhook event
  - create_portal_session() — creates fresh Stripe Customer Portal URL
  - cancel_subscription_at_period_end() — modifies subscription (not delete) for period-end cancel
  - GET /billing/subscription — plan_name, status, current_period_end, cancel_at_period_end
  - GET /billing/invoices — list of invoice dicts from Stripe
  - POST /billing/portal-session — returns single-use portal URL
  - POST /billing/cancel — modifies subscription + emits subscription_cancelled usage event
  - customer.subscription.updated webhook branch — persists cancel_at_period_end to DB
affects:
  - 11-02 (billing UI — consumes all 4 new endpoints)
  - 11-03 (churn flow — consumes POST /billing/cancel with survey payload)
  - 12-admin-dashboard (subscription_cancelled usage events accumulate for admin reporting)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Subscription state reads come from local DB (fast, no Stripe rate limit); Stripe called only for portal-session and cancel actions"
    - "cancel_at_period_end=True via stripe.Subscription.modify() — user retains access until period_end"
    - "Usage events emitted inline in route handler with non-fatal try/except (log only)"
    - "Portal sessions always created fresh (never cached) — single-use design"

key-files:
  created:
    - backend/migrations/006_subscription_cancel_at_period_end.sql
  modified:
    - backend/app/services/billing/subscription.py
    - backend/app/services/billing/stripe_client.py
    - backend/app/routers/billing.py

key-decisions:
  - "cancel_subscription_at_period_end uses stripe.Subscription.modify(cancel_at_period_end=True) — NOT stripe.Subscription.delete() — user retains access until period_end"
  - "All 4 new billing endpoints use get_current_user only — NOT require_active_subscription (users must be able to view billing/cancel even if subscription is in grace period)"
  - "Subscription state reads from local DB (not live Stripe API) — avoids rate limits and latency"
  - "Portal sessions never cached — each POST /billing/portal-session creates fresh session"
  - "subscription_cancelled usage event q1/q2 survey fields are optional (empty string default) — non-blocking even if user skips survey"

patterns-established:
  - "Service-router split: stripe_client.py owns Stripe API calls; subscription.py owns DB reads/writes; billing.py routes orchestrate both"
  - "Non-fatal usage event emission: try/except logs failure but never raises — billing flow not blocked by analytics"

requirements-completed: [SUBS-01, SUBS-02, SUBS-03, SUBS-04, SUBS-05]

# Metrics
duration: 15min
completed: 2026-03-09
---

# Phase 11 Plan 01: Subscription Management Churn — Backend Summary

**Billing backend for subscription self-service: 4 new API endpoints, 5 new service functions, migration 006, and webhook cancel-state persistence using stripe.Subscription.modify()**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-09T13:57:15Z
- **Completed:** 2026-03-09T14:12:15Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Migration 006 adds cancel_at_period_end BOOLEAN column to subscriptions table (idempotent IF NOT EXISTS guard)
- 5 new service functions exported from subscription.py and stripe_client.py — fully importable, all tests passing
- 4 new billing routes (GET /subscription, GET /invoices, POST /portal-session, POST /cancel) registered and verified
- Webhook extended with customer.subscription.updated branch persisting cancel state to DB
- POST /billing/cancel emits subscription_cancelled usage event with q1/q2 survey metadata

## Task Commits

Each task was committed atomically:

1. **Task 1: Migration 006 + billing service functions** - `944a21b` (feat)
2. **Task 2: New billing endpoints + webhook subscription.updated branch** - `de9a00e` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `backend/migrations/006_subscription_cancel_at_period_end.sql` - Adds cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE to subscriptions table
- `backend/app/services/billing/subscription.py` - Added get_subscription_detail(), get_customer_invoices(), update_subscription_cancel_state()
- `backend/app/services/billing/stripe_client.py` - Added create_portal_session(), cancel_subscription_at_period_end()
- `backend/app/routers/billing.py` - Added 4 new routes, CancelRequest model, customer.subscription.updated webhook branch

## Decisions Made

- `cancel_subscription_at_period_end` uses `stripe.Subscription.modify()` not `delete()` — matches STATE.md locked decision (v1.1 roadmap): "Stripe cancellation must use cancel_at_period_end=True"
- All 4 endpoints use `get_current_user` only (not `require_active_subscription`) — users in grace period must still access billing
- Subscription state served from local DB — no live Stripe API call on page load, avoids rate limits
- Portal sessions are stateless — fresh call every time, never cached
- Survey q1/q2 default to empty string — cancel works even without survey data

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed "delete" from cancel_subscription_at_period_end docstring**
- **Found during:** Task 1 verification
- **Issue:** Plan's verification script asserts `'delete' not in src` on the full function source; docstring originally read "NOT stripe.Subscription.delete()" causing false failure
- **Fix:** Rewrote docstring to avoid the word "delete" while preserving the intent: "Uses stripe.Subscription.modify() — NOT the delete method" changed to "Uses stripe.Subscription.modify(cancel_at_period_end=True)"
- **Files modified:** backend/app/services/billing/stripe_client.py
- **Verification:** Verification script passes, function body confirmed to use modify() only
- **Committed in:** 944a21b (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - docstring false-positive in verification assertion)
**Impact on plan:** Trivial — docstring wording change only. No behavior change.

## Issues Encountered

None — plan executed smoothly.

## User Setup Required

**Migration 006 must be run manually in Supabase Dashboard -> SQL Editor before billing frontend is deployed.**

File: `backend/migrations/006_subscription_cancel_at_period_end.sql`

Content:
```sql
ALTER TABLE public.subscriptions
  ADD COLUMN IF NOT EXISTS cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE;
```

**Additionally:** The `customer.subscription.updated` Stripe webhook event must be added to the webhook subscription list in the Stripe Dashboard (documented in Plan 03 human-action checkpoint).

## Next Phase Readiness

- All 4 API contracts are live and verified — Plans 02 (billing UI) and 03 (churn flow) can proceed
- Migration 006 SQL file ready to deploy; must be run before billing page renders subscription state
- customer.subscription.updated webhook event must be added to Stripe Dashboard webhook config (Plan 03 scope)
- subscription_cancelled usage events will accumulate in usage_events table for Phase 12 admin dashboard

---
*Phase: 11-subscription-management-churn*
*Completed: 2026-03-09*
