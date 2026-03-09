---
phase: 11-subscription-management-churn
verified: 2026-03-09T00:00:00Z
status: human_needed
score: 14/14 automated must-haves verified
re_verification: false
human_verification:
  - test: "Apply Migration 006 to Supabase production"
    expected: "cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE column present on subscriptions table"
    why_human: "Supabase Dashboard SQL Editor action — cannot be executed or confirmed from code"
  - test: "Add customer.subscription.updated to Stripe Dashboard webhook event list"
    expected: "Webhook fires on subscription updates; backend persists cancel_at_period_end to local DB after cancel"
    why_human: "Stripe Dashboard configuration — cannot be verified programmatically"
  - test: "Navigate to /billing as a subscribed user and verify plan name, status, and next billing date display"
    expected: "Shows 'Ava Monthly', status 'Active', and a human-readable next billing date"
    why_human: "Visual rendering and real data from Stripe/Supabase required (SUBS-01)"
  - test: "Click 'Manage billing' button on /billing"
    expected: "Stripe Customer Portal opens in a new tab; returning to the tab after >60s refreshes subscription data"
    why_human: "Real Stripe portal session creation and window.open behavior; tab-return refresh requires real elapsed time (SUBS-02)"
  - test: "Verify invoice history section on /billing for a user with at least one Stripe invoice"
    expected: "Invoice rows display date, dollar amount, 'paid' status in green, and an ExternalLink icon to the PDF"
    why_human: "Requires real Stripe invoice data; PDF URL only valid for actual invoices (SUBS-02)"
  - test: "Complete the full cancel flow: Cancel link -> Skip -> Skip -> Confirm"
    expected: "Warm post-cancel message appears; Cancel link replaced by Resubscribe; status still shows 'Active'"
    why_human: "End-to-end flow calls real Stripe API; post-cancel DB state depends on webhook firing (SUBS-03, SUBS-04, SUBS-05)"
  - test: "Verify 3-click minimum cancel path: Cancel link -> 'Skip survey and cancel' -> 'Yes, cancel my subscription'"
    expected: "Exactly 3 clicks reach the final confirmed cancellation"
    why_human: "User interaction count must be verified by a human performing the clicks (SUBS-05)"
---

# Phase 11: Subscription Management & Churn — Verification Report

**Phase Goal:** Users can see their billing status, manage payment details via Stripe, and cancel with a friction-appropriate but legally compliant flow
**Verified:** 2026-03-09
**Status:** human_needed — all automated checks pass; 7 items require human/production verification
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | GET /billing/subscription returns plan_name, status, current_period_end, cancel_at_period_end for an authenticated subscribed user | VERIFIED | `billing.py` line 50-59: route calls `get_subscription_detail()`, returns full dict including all 4 fields |
| 2 | GET /billing/invoices returns a list of invoices (date, amount_paid, status, invoice_pdf) for the authenticated user's Stripe customer | VERIFIED | `billing.py` line 62-77: calls `get_customer_invoices()` with stripe_customer_id; `subscription.py` line 109-121: builds correct 4-field dicts |
| 3 | POST /billing/portal-session returns a Stripe portal URL; portal session created fresh on every call (never cached) | VERIFIED | `billing.py` line 80-99: calls `create_portal_session()` fresh each time; `stripe_client.py` line 65-75: direct `stripe.billing_portal.Session.create()` with no caching |
| 4 | POST /billing/cancel calls stripe.Subscription.modify(cancel_at_period_end=True) — NOT stripe.Subscription.delete() | VERIFIED | `stripe_client.py` line 85-88: `stripe.Subscription.modify(stripe_subscription_id, cancel_at_period_end=True)`; no `delete()` call exists in the file |
| 5 | customer.subscription.updated webhook branch persists cancel_at_period_end and current_period_end to subscriptions table | VERIFIED | `billing.py` line 212-224: `elif event_type == "customer.subscription.updated"` branch calls `update_subscription_cancel_state()`; `subscription.py` line 124-156: function updates both columns |
| 6 | POST /billing/cancel emits subscription_cancelled usage event with q1/q2 survey payload as metadata | VERIFIED | `billing.py` line 118-126: `supabase_admin.from_("usage_events").insert({"event_type": "subscription_cancelled", "metadata": {"q1": body.q1, "q2": body.q2}})` |
| 7 | cancel_at_period_end column exists in subscriptions table (migration 006) | VERIFIED (file) | `backend/migrations/006_subscription_cancel_at_period_end.sql` line 7: `ADD COLUMN IF NOT EXISTS cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE` — SQL file exists and is correct; **production application requires human action** |
| 8 | Authenticated user visiting /billing sees plan name, status, and next billing date | VERIFIED (code) | `BillingPage.tsx` line 334-368: renders `subscription.plan_name`, `formatStatus(subscription.status)`, `formatDate(subscription.current_period_end)` — **requires human to confirm visual rendering** |
| 9 | Invoice history list renders date, amount, status badge, and PDF link | VERIFIED (code) | `BillingPage.tsx` line 448-487: maps invoices with date (line 456), `$${(inv.amount_paid/100).toFixed(2)}` (line 460), status badge with color coding (line 463-474), ExternalLink to `inv.invoice_pdf` (line 476-484) |
| 10 | Clicking 'Manage billing' opens the Stripe Customer Portal in a new tab | VERIFIED (code) | `BillingPage.tsx` line 79-90: `handleManageBilling()` calls `createPortalSession(token)` then `window.open(url, '_blank')` |
| 11 | /billing route is ProtectedRoute only — no OnboardingGate | VERIFIED | `App.tsx` line 154-155: `<Route path="/billing" element={<ProtectedRoute><BillingPage /></ProtectedRoute>}` — OnboardingGate wraps only /chat and /settings (line 137-149) |
| 12 | Clicking the Cancel link opens Survey Q1 with text field and Skip/Next options | VERIFIED (code) | `BillingPage.tsx` line 161-203: survey-q1 step renders Q1 question, textarea, unconditional Skip button (line 175), Next button (line 181) |
| 13 | Cancellation is reachable in 3 clicks via 'Skip survey and cancel' shortcut | VERIFIED (code) | `BillingPage.tsx` line 188-196: "Skip survey and cancel" button in Q1 step calls `setCancelStep('confirming')` directly — path: Cancel link (click 1) → Skip survey and cancel (click 2) → Yes cancel (click 3) |
| 14 | After confirmation, warm post-cancel message shown; Cancel link becomes Resubscribe | VERIFIED (code) | `BillingPage.tsx` line 276-299: cancelled step renders "We're sad to see you go. You'll keep access until [date]"; line 411-428: Cancel link shown only when `isActive && !isCancellingAtPeriodEnd`; Resubscribe shown when `isCancellingAtPeriodEnd` |

**Score:** 14/14 truths verified (7 fully automated, 7 code-verified pending human confirmation)

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/migrations/006_subscription_cancel_at_period_end.sql` | cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE | VERIFIED | Exists, correct SQL with IF NOT EXISTS guard |
| `backend/app/services/billing/subscription.py` | get_subscription_detail(), get_customer_invoices(), update_subscription_cancel_state() | VERIFIED | All 3 functions present, lines 72-157; substantive implementations with DB queries |
| `backend/app/services/billing/stripe_client.py` | create_portal_session(), cancel_subscription_at_period_end() | VERIFIED | Lines 65-94; create_portal_session creates fresh session, cancel uses modify() not delete() |
| `backend/app/routers/billing.py` | GET /billing/subscription, GET /billing/invoices, POST /billing/portal-session, POST /billing/cancel + customer.subscription.updated webhook branch | VERIFIED | 4 routes at lines 50, 62, 80, 102; webhook branch at line 212 |
| `frontend/src/api/billing.ts` | getSubscription(), getInvoices(), createPortalSession(), cancelSubscription() | VERIFIED | All 4 functions exported, lines 40-81; typed with SubscriptionData and Invoice types |
| `frontend/src/pages/BillingPage.tsx` | Full BillingPage with subscription info, invoices, cancel flow | VERIFIED | 562-line substantive component; full CancelStep state machine implemented |
| `frontend/src/App.tsx` | /billing ProtectedRoute registered | VERIFIED | Line 154-155; ProtectedRoute only, no OnboardingGate |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `billing.py GET /billing/subscription` | `subscription.py get_subscription_detail()` | direct call | WIRED | Line 56: `detail = await get_subscription_detail(str(user.id))` |
| `billing.py POST /billing/cancel` | `stripe_client.py cancel_subscription_at_period_end()` | direct call | WIRED | Line 113: `result = cancel_subscription_at_period_end(detail["stripe_subscription_id"])` |
| `billing.py webhook customer.subscription.updated` | `subscription.py update_subscription_cancel_state()` | await call | WIRED | Lines 218-223: `await update_subscription_cancel_state(subscription_id=sub_id, ...)` |
| `billing.py POST /billing/cancel` | usage_events table | supabase_admin insert | WIRED | Lines 119-124: `supabase_admin.from_("usage_events").insert({"event_type": "subscription_cancelled", ...})` |
| `BillingPage.tsx` | `billing.ts getSubscription()` | useQuery | WIRED | Line 62: `queryFn: () => getSubscription(token)` with `queryKey: ['subscription']` |
| `BillingPage.tsx` | `billing.ts getInvoices()` | useQuery | WIRED | Line 73: `queryFn: () => getInvoices(token)` with `queryKey: ['invoices']` |
| `BillingPage.tsx Manage billing button` | `billing.ts createPortalSession()` | onClick handler | WIRED | Line 83: `const url = await createPortalSession(token)` then `window.open(url, '_blank')` |
| `BillingPage.tsx confirming step Confirm button` | `billing.ts cancelSubscription()` | async onClick | WIRED | Lines 119-120: `await cancelSubscription(token, {q1: surveyQ1, q2: surveyQ2})`; `queryClient.invalidateQueries({queryKey: ['subscription']})` |
| `cancelSubscription API call` | `POST /billing/cancel` | fetch with auth | WIRED | `billing.ts` line 71-80: `fetch('/billing/cancel', {method: 'POST', headers: {Authorization: ...}, body: JSON.stringify(survey)})` |
| `BillingPage.tsx Cancel link onClick` | `setCancelStep('survey-q1')` | useState state machine | WIRED | Line 133: `setCancelStep('survey-q1')` inside `handleCancelClick()` |

---

## Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| SUBS-01 | 11-01, 11-02 | User can view their current plan name, status, and next billing date | VERIFIED (code) | Backend: `get_subscription_detail()` returns plan_name/status/current_period_end; Frontend: BillingPage renders all three fields |
| SUBS-02 | 11-01, 11-02 | User can access invoice history and update payment method via Stripe Portal | VERIFIED (code) | Backend: GET /billing/invoices + POST /billing/portal-session; Frontend: invoice history table + Manage billing button wired to createPortalSession |
| SUBS-03 | 11-01, 11-03 | User can cancel their subscription from the billing page | VERIFIED (code) | Cancel link present when `isActive && !isCancellingAtPeriodEnd`; flow reaches POST /billing/cancel which calls stripe.Subscription.modify() |
| SUBS-04 | 11-01, 11-03 | Cancellation flow shows exit survey before confirming | VERIFIED (code) | Q1 "What did you like most about Ava?" and Q2 "Why are you leaving?" both render before confirming step; {q1, q2} payload sent to backend and stored in usage_events |
| SUBS-05 | 11-03 | Cancellation is non-coercive: skippable, <= 3 clicks, access retained until period end | VERIFIED (code) | Skip buttons unconditional on Q1 and Q2; "Skip survey and cancel" shortcut on Q1 enables 3-click path; stripe.Subscription.modify(cancel_at_period_end=True) used (not delete) |

No orphaned SUBS-* requirements found — all 5 mapped and implemented.

---

## Anti-Patterns Found

No blockers found. Full scan of all phase 11 files:

| File | Pattern | Severity | Notes |
|------|---------|----------|-------|
| `BillingPage.tsx` | No TODO/FIXME/placeholder comments found | — | All cancel steps fully implemented |
| `billing.py` | No empty implementations | — | All 4 routes return substantive responses |
| `stripe_client.py` | No `return {}` / `return []` stubs | — | Both new functions implemented |
| `subscription.py` | No console.log-only implementations | — | All 3 new functions interact with DB or Stripe |

---

## Human Verification Required

### 1. Apply Migration 006

**Test:** In Supabase Dashboard SQL Editor, run the contents of `backend/migrations/006_subscription_cancel_at_period_end.sql`
**Expected:** Query completes without error; `cancel_at_period_end` column exists on `subscriptions` table
**Why human:** Supabase Dashboard action — cannot be run or confirmed from the codebase

### 2. Add customer.subscription.updated to Stripe Webhook

**Test:** Stripe Dashboard -> Developers -> Webhooks -> [your endpoint] -> Add event -> `customer.subscription.updated`
**Expected:** Event appears in the webhook's event list
**Why human:** Stripe Dashboard configuration — cannot be set via code

### 3. View billing page as a subscribed user (SUBS-01)

**Test:** Log in as a subscribed user, navigate to `https://avasecret.org/billing`
**Expected:** Page loads without error; shows "Ava Monthly", status "Active", and a human-readable next billing date (e.g. "March 9, 2026")
**Why human:** Visual rendering and live Supabase/Stripe data required

### 4. Manage billing button opens Stripe Portal (SUBS-02)

**Test:** On /billing, click "Manage billing"
**Expected:** Stripe Customer Portal opens in a new browser tab; closing and returning to the /billing tab after >60 seconds triggers a fresh subscription data fetch
**Why human:** window.open behavior and tab-focus auto-refresh require real browser interaction and elapsed time

### 5. Invoice history renders with real data (SUBS-02)

**Test:** On /billing for a user with at least one Stripe invoice, check the Invoice history section
**Expected:** Each invoice row shows formatted date, dollar amount, "paid" status in green, and a clickable ExternalLink icon to the PDF
**Why human:** Invoice data only present for users who have paid; PDF URLs are Stripe-generated

### 6. Complete cancellation flow end-to-end (SUBS-03, SUBS-04)

**Test:** Cancel link -> answer or skip Q1 -> answer or skip Q2 -> "Yes, cancel my subscription"
**Expected:** Warm message "We're sad to see you go. You'll keep access until [date]." appears; clicking Done returns to normal billing view showing Resubscribe in place of Cancel; status still shows "Active"; Supabase subscriptions table has cancel_at_period_end = TRUE
**Why human:** Calls real Stripe API; DB state sync depends on customer.subscription.updated webhook firing; requires Stripe test credentials

### 7. Verify 3-click minimum cancel path (SUBS-05)

**Test:** Click "Cancel subscription" (click 1) -> click "Skip survey and cancel" (click 2) -> click "Yes, cancel my subscription" (click 3)
**Expected:** Confirmation step is reached and cancellation completes — exactly 3 active user clicks
**Why human:** Click-count compliance must be confirmed by a human performing the interaction

---

## Gaps Summary

No gaps. All automated must-haves are satisfied:

- Migration 006 SQL file exists and is correct
- All 5 service functions (`get_subscription_detail`, `get_customer_invoices`, `update_subscription_cancel_state`, `create_portal_session`, `cancel_subscription_at_period_end`) are implemented and wired
- `cancel_subscription_at_period_end` uses `stripe.Subscription.modify()` — not `delete()`
- All 4 backend routes registered and wired to service functions
- `customer.subscription.updated` webhook branch present and calls `update_subscription_cancel_state()`
- `POST /billing/cancel` emits `subscription_cancelled` usage event with `{q1, q2}` metadata
- All 4 billing API client functions exported from `billing.ts`
- BillingPage renders subscription info, invoices, Manage billing, Upgrade modal, and full cancel flow state machine
- `/billing` route registered as ProtectedRoute-only (no OnboardingGate)
- `staleTime: 60 * 1000` on subscription query with `refetchOnWindowFocus` enabled
- "Skip survey and cancel" shortcut enables 3-click cancellation (SUBS-05 compliance)
- Cancel link only shows when `isActive && !cancel_at_period_end`; Resubscribe link shown when `cancel_at_period_end === true`
- All 5 SUBS requirements (SUBS-01 through SUBS-05) have complete code implementations

The remaining 7 human verification items are operational and visual checks that cannot be confirmed programmatically. No code gaps or stubs were found.

---

_Verified: 2026-03-09_
_Verifier: Claude (gsd-verifier)_
