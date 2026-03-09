# Phase 11: Subscription Management & Churn - Research

**Researched:** 2026-03-09
**Domain:** Stripe Customer Portal, subscription lifecycle management, React billing UI
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Billing page layout**
- Dedicated `/billing` route — its own page, not a section within settings
- Required fields visible at top: plan name, current status, next billing date
- Invoice history section below: simple list with date, amount, status — each links to Stripe-hosted PDF in new tab
- Three actions present: **Manage billing** button (prominent), **Upgrade** button (prominent), **Cancel** link (small, less visually prominent — e.g., small text link below the action buttons)

**Cancellation flow**
- Flow: Cancel link → Survey Q1 → Survey Q2 → Final confirm button (survey-confirm-last pattern)
- Survey Q1: "What did you like most about Ava?" — free text, skippable
- Survey Q2: "Why are you leaving?" — free text, skippable
- Final step: "Yes, cancel my subscription" button to confirm cancellation
- After confirmation: stay on `/billing`, page shows updated state (Resubscribe option visible)
- Tone of confirmation message: warm, low-regret — e.g., "We're sad to see you go. You'll keep access until [date]."

**Post-cancellation state (cancel_at_period_end)**
- No prominent banner or alert showing cancellation status — intentionally low-key
- Only visible change: the Cancel link becomes a **Resubscribe** link/button
- Status field continues to show "Active" — no "Cancelling" badge
- Resubscribe click → opens Stripe Customer Portal (new tab)
- When subscription fully expires: redirect expired users to upgrade/paywall on app entry — not a custom expired billing page

**Upgrade flow**
- Upgrade button opens an **in-app upgrade modal** showing plan options/pricing before any Stripe redirect
- Modal handles the upgrade path; after user confirms, routes to Stripe checkout

**Stripe Portal navigation**
- "Manage billing" opens Stripe Customer Portal in a **new tab**
- Stripe `return_url` configured to `/billing`
- Billing page auto-refreshes subscription data when the user tabs back (window focus event triggers re-fetch)

### Claude's Discretion
- Exact visual design, spacing, and typography of the billing page
- Loading/skeleton states while fetching subscription data
- Error states (Stripe API unavailable, portal session creation failure)
- Exact survey skip mechanism (Skip button vs empty submit vs "Skip and cancel" link)

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SUBS-01 | User can view their current plan name, status, and next billing date | Backend: `GET /billing/subscription` endpoint reading from `subscriptions` table + Stripe API. Frontend: BillingPage component reads these three fields at load. |
| SUBS-02 | User can access invoice history and update payment method (redirects to Stripe Customer Portal) | Backend: `GET /billing/invoices` endpoint (stripe.Invoice.list) + `POST /billing/portal-session` (stripe.billing_portal.Session.create). Frontend: invoice list + "Manage billing" button opens portal URL in new tab. |
| SUBS-03 | User can cancel their subscription from the settings/billing page | Backend: `POST /billing/cancel` calls stripe.Subscription.modify(sub_id, cancel_at_period_end=True). Backend webhook handles `customer.subscription.updated` to persist `cancel_at_period_end=True` in subscriptions table. |
| SUBS-04 | Cancellation flow shows an exit survey before confirming (what they liked, what they'd add, why they're leaving) | Frontend: multi-step cancel flow (Survey Q1 → Survey Q2 → Confirm). Survey responses stored or logged server-side; user must reach confirm step. |
| SUBS-05 | Cancellation is non-coercive: survey is skippable, ≤ 3 clicks to complete, access retained until period end | Survey questions are free text with skip option. cancel_at_period_end=True ensures access retained. UI confirm reachable in 3 clicks: Cancel link → (skip or answer Q1) → (skip or answer Q2) → Confirm = maximum 3 active clicks. |
</phase_requirements>

---

## Summary

Phase 11 builds a dedicated `/billing` page backed by two new backend capabilities: a Stripe Customer Portal session creator and a subscription cancellation endpoint. The billing page is a read-dominant frontend — subscription data lives in the already-existing `subscriptions` table (created in Phase 7, migration 004), so most reads hit Supabase, not Stripe. Stripe is called only on explicit user actions (open portal, cancel).

The cancellation flow uses `stripe.Subscription.modify(cancel_at_period_end=True)` — NOT `stripe.Subscription.delete()` — per the locked decision from the v1.1 roadmap (STATE.md). This is a critical constraint: immediate cancel causes 402 errors while the user still holds an active session. The `customer.subscription.updated` webhook fires immediately when `cancel_at_period_end` is set, and `customer.subscription.deleted` fires at period end — the existing webhook handler only covers the `deleted` event, so a new handler branch is needed for `updated`.

The invoice history feature requires a new backend endpoint that calls `stripe.Invoice.list(customer=stripe_customer_id)` — the `stripe_customer_id` is already stored in the `subscriptions` table from Phase 7. No new schema migration is needed for the core billing page; however, a `cancel_at_period_end` column should be added to the `subscriptions` table so the frontend can determine UI state (show Cancel vs Resubscribe) without a Stripe API call on every page load.

**Primary recommendation:** Build the backend first (3 new endpoints + 1 new webhook branch + 1 migration), then the BillingPage component, then the cancellation flow as a self-contained multi-step modal or inline state machine.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| stripe (Python) | latest (pinned in requirements.txt as `stripe`) | Customer Portal session creation, subscription modify, invoice list | Already installed and configured; `stripe_secret_key` in Settings |
| React + TanStack Query | React 19, TanStack Query 5.x | Data fetching with focus-refetch for billing page | Already in use across the app; `useQuery` with `refetchOnWindowFocus` handles tab-back refresh |
| react-router-dom | 7.x | `/billing` route registration in App.tsx | Already in use |
| Tailwind CSS v4 | 4.x | Styling billing page consistent with rest of app | Already in use; CSS-first config established |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| motion (Framer Motion v12) | 12.x | Cancel flow step transitions | Already in use from Phase 10; import from `motion/react` |
| lucide-react | 0.577+ | Icons on billing page (credit card, calendar, etc.) | Already in use from Phase 10 |
| GlassCard | project component | Card container on billing page | Already built in Phase 10 at `frontend/src/components/ui/GlassCard.tsx` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Storing cancel_at_period_end in DB | Fetch from Stripe on every load | DB column is faster, cheaper, and doesn't expose Stripe rate limits to page load |
| Multi-step modal for cancellation | Separate route `/billing/cancel` | Inline state machine in BillingPage keeps routing simple; modal avoids browser back-button issues |
| stripe.Subscription.delete() | stripe.Subscription.modify(cancel_at_period_end=True) | delete() is immediate; modify() retains access — this is a LOCKED requirement per STATE.md |

**Installation:**
```bash
# All dependencies already installed — no new packages needed
# stripe, React Query, react-router-dom, motion, lucide-react, Tailwind all present
```

---

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── routers/billing.py              # Add 3 new endpoints to existing file
├── services/billing/
│   ├── stripe_client.py            # Add create_portal_session(), cancel_subscription()
│   └── subscription.py             # Add get_subscription_detail(), get_invoices(), update_cancel_at_period_end()
└── migrations/
    └── 006_subscription_cancel_at_period_end.sql   # ADD COLUMN cancel_at_period_end

frontend/src/
├── pages/BillingPage.tsx           # New — dedicated /billing route
├── api/billing.ts                  # Add getSubscription(), getInvoices(), createPortalSession(), cancelSubscription()
└── App.tsx                         # Add /billing ProtectedRoute
```

### Pattern 1: Backend — Subscription Detail Endpoint
**What:** `GET /billing/subscription` returns plan name, status, next billing date, and cancel_at_period_end from the local `subscriptions` table (not a live Stripe call). Fast, cheap, no rate limit exposure.
**When to use:** Page load, window focus refetch.
**Example:**
```python
# Source: Existing subscription.py pattern + subscriptions table schema (migration 004)
@router.get("/subscription")
async def get_subscription(user=Depends(get_current_user)):
    result = (
        supabase_admin.from_("subscriptions")
        .select("status, current_period_end, cancel_at_period_end, stripe_price_id, stripe_subscription_id")
        .eq("user_id", str(user.id))
        .limit(1)
        .execute()
    )
    if not result.data:
        return {"status": "none"}
    row = result.data[0]
    return {
        "plan_name": "Ava Monthly",   # Could be derived from stripe_price_id later
        "status": row["status"],
        "current_period_end": row["current_period_end"],
        "cancel_at_period_end": row.get("cancel_at_period_end", False),
    }
```

### Pattern 2: Backend — Create Portal Session
**What:** `POST /billing/portal-session` calls Stripe to create a short-lived portal URL and returns it. Frontend opens in new tab.
**When to use:** "Manage billing" and "Resubscribe" button clicks.
**Example:**
```python
# Source: https://docs.stripe.com/api/customer_portal/sessions/create
import stripe

def create_portal_session(stripe_customer_id: str, return_url: str) -> str:
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=return_url,
    )
    return session.url
```

### Pattern 3: Backend — Cancel Subscription (cancel_at_period_end)
**What:** `POST /billing/cancel` sets cancel_at_period_end=True on the Stripe subscription. Returns updated period end date. Does NOT immediately deactivate — user retains access.
**When to use:** User confirms cancellation in the survey flow.
**Example:**
```python
# Source: https://docs.stripe.com/api/subscriptions/update
import stripe

def cancel_subscription_at_period_end(stripe_subscription_id: str) -> dict:
    subscription = stripe.Subscription.modify(
        stripe_subscription_id,
        cancel_at_period_end=True,
    )
    return {
        "cancel_at_period_end": subscription.cancel_at_period_end,
        "current_period_end": subscription.current_period_end,
    }
```

### Pattern 4: Backend — Webhook — customer.subscription.updated
**What:** New branch in existing `/billing/webhook` handler. When `customer.subscription.updated` fires, persist `cancel_at_period_end` value to `subscriptions` table.
**Why needed:** Setting cancel_at_period_end via the API fires this event immediately. The billing page reads from the DB, not Stripe live — without this handler, the UI never sees the updated state.
**Example:**
```python
# Source: docs.stripe.com/billing/subscriptions/cancel + existing billing.py pattern
elif event_type == "customer.subscription.updated":
    sub_id = data.get("id")
    if sub_id:
        cancel_at_period_end = data.get("cancel_at_period_end", False)
        current_period_end_ts = data.get("current_period_end")
        await update_subscription_cancel_state(
            subscription_id=sub_id,
            cancel_at_period_end=cancel_at_period_end,
            current_period_end_ts=current_period_end_ts,
        )
```

### Pattern 5: Backend — Invoice List
**What:** `GET /billing/invoices` calls `stripe.Invoice.list(customer=stripe_customer_id, limit=12)` and returns date, amount, status, and PDF URL.
**Example:**
```python
# Source: https://docs.stripe.com/api/invoices/list
def get_customer_invoices(stripe_customer_id: str) -> list[dict]:
    invoices = stripe.Invoice.list(customer=stripe_customer_id, limit=12)
    return [
        {
            "date": inv.created,          # Unix timestamp
            "amount_paid": inv.amount_paid,  # cents
            "status": inv.status,
            "invoice_pdf": inv.invoice_pdf,  # Direct PDF download URL
        }
        for inv in invoices.data
    ]
```

### Pattern 6: Frontend — Window Focus Refetch
**What:** TanStack Query's `refetchOnWindowFocus: true` (default) triggers a re-fetch when user tabs back from Stripe Portal. No extra code needed — just don't disable it.
**Example:**
```typescript
// Source: TanStack Query defaults — refetchOnWindowFocus is true by default
const { data: subscription, isLoading } = useQuery({
  queryKey: ['subscription'],
  queryFn: () => getSubscription(token!),
  staleTime: 30 * 1000,   // 30s — short enough to catch portal changes on tab return
  // refetchOnWindowFocus: true  <-- default, no need to set explicitly
})
```

### Pattern 7: Frontend — Cancellation Flow State Machine
**What:** Inline state machine in BillingPage using a `step` enum: `'idle' | 'survey-q1' | 'survey-q2' | 'confirming' | 'cancelled'`. No separate route or component needed.
**When to use:** User clicks Cancel link.
**Example:**
```typescript
type CancelStep = 'idle' | 'survey-q1' | 'survey-q2' | 'confirming' | 'cancelled'

const [cancelStep, setCancelStep] = useState<CancelStep>('idle')
const [surveyQ1, setSurveyQ1] = useState('')
const [surveyQ2, setSurveyQ2] = useState('')

// Cancel link click → 'survey-q1'
// Next/Skip from Q1 → 'survey-q2'
// Next/Skip from Q2 → 'confirming'
// Confirm → API call → 'cancelled'
```

### Pattern 8: Frontend — Usage Event Emission (subscription_cancelled)
**What:** Per STATE.md (`usage_events emission points wired in Phase 8–11`), the cancel endpoint should emit a `subscription_cancelled` usage event after successfully setting cancel_at_period_end=True.
**When to use:** Inside `POST /billing/cancel` handler after Stripe call succeeds.

### Anti-Patterns to Avoid
- **Calling `stripe.Subscription.delete()`:** Immediately terminates subscription — user loses access and hits 402 on /chat. Use `stripe.Subscription.modify(cancel_at_period_end=True)` instead.
- **Reading subscription state from Stripe on page load:** Adds ~200-500ms latency, consumes rate limit quota. Read from local `subscriptions` table; Stripe is ground truth only for cancel/portal actions.
- **Hiding the "Skip" option behind conditional logic:** SUBS-05 requires skip is always present. Never make it conditional on survey answers.
- **Handling portal session creation in the frontend:** Portal session creation requires the Stripe secret key — must be server-side only.
- **Not handling `customer.subscription.updated` in webhook:** The billing page reads `cancel_at_period_end` from DB. Without this handler, the Cancel link never becomes Resubscribe after cancellation.
- **Registering `customer.subscription.updated` in Stripe Dashboard webhook:** This event must be explicitly added to the Stripe Dashboard webhook subscription list — it is NOT included by default with the current webhook.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Payment method management | Custom card update form | Stripe Customer Portal | PCI compliance nightmare; Portal handles card updates, invoice download, and plan changes natively |
| Invoice PDF generation | Server-side PDF render | `invoice.invoice_pdf` URL from Stripe | Stripe already generates and hosts these; link opens in new tab |
| Subscription state machine | Custom subscription status tracking | Stripe webhooks → local DB | Stripe is the source of truth; local DB is just a cache for fast reads |
| Portal authentication | Custom auth for billing section | Stripe billing_portal.Session (time-limited URL) | Portal sessions are short-lived, customer-scoped, Stripe-managed |

**Key insight:** Stripe Customer Portal exists precisely so developers don't build billing management UIs. Use it for payment method updates and invoice access. Only build custom UI for the cancellation survey (because Portal cancellation doesn't support custom survey questions).

---

## Common Pitfalls

### Pitfall 1: Wrong Cancellation Method
**What goes wrong:** Calling `stripe.Subscription.delete(sub_id)` instead of `stripe.Subscription.modify(sub_id, cancel_at_period_end=True)`.
**Why it happens:** The Stripe docs show delete() prominently; cancel_at_period_end is an update parameter.
**How to avoid:** Always use `stripe.Subscription.modify()`. This is locked in STATE.md: "Stripe cancellation must use cancel_at_period_end=True (not stripe.Subscription.cancel())".
**Warning signs:** User gets 402 on /chat immediately after cancelling.

### Pitfall 2: Missing `customer.subscription.updated` Webhook Handler
**What goes wrong:** Cancel API call succeeds, but billing page still shows Cancel link (not Resubscribe) because DB was never updated.
**Why it happens:** The existing webhook handler only covers `checkout.session.completed`, `invoice.payment_failed`, and `customer.subscription.deleted`. The `updated` event fires when `cancel_at_period_end` is toggled.
**How to avoid:** Add `customer.subscription.updated` handler branch AND register this event type in the Stripe Dashboard webhook settings.
**Warning signs:** cancel_at_period_end stays False in DB after cancellation.

### Pitfall 3: Missing `cancel_at_period_end` Column in subscriptions Table
**What goes wrong:** Webhook handler has nowhere to persist `cancel_at_period_end`; subscription.py SELECT query returns no such column.
**Why it happens:** Migration 004 created the subscriptions table without this column (Phase 7 only needed active/inactive).
**How to avoid:** Create migration 006 adding `cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE` before implementing anything else.
**Warning signs:** PostgreSQL column-not-found errors in logs.

### Pitfall 4: Portal Session URL is Single-Use and Short-Lived
**What goes wrong:** Caching the portal URL and reusing it — user gets "invalid session" error.
**Why it happens:** Stripe portal sessions expire quickly and are single-use.
**How to avoid:** `POST /billing/portal-session` must be called fresh on each button click. Never cache the URL client-side beyond a single navigation.
**Warning signs:** "The link is invalid" error in Stripe portal.

### Pitfall 5: stripe_customer_id May Be Missing
**What goes wrong:** `GET /billing/invoices` or `POST /billing/portal-session` receives empty stripe_customer_id because user signed up but never completed checkout.
**Why it happens:** subscriptions table row only exists after `checkout.session.completed` — users who signed up but never subscribed have no row.
**How to avoid:** Both endpoints must check for `None` stripe_customer_id and return a clean 404/400 response. Frontend must handle this state (show empty invoice section, not an error).
**Warning signs:** stripe.error.InvalidRequestError with "No such customer" message.

### Pitfall 6: Cancellation Survey Responses Not Stored
**What goes wrong:** Survey answers collected in frontend state but never sent to backend — operator has no data to read.
**Why it happens:** Easy to forget to wire survey payload into the cancel API call.
**How to avoid:** `POST /billing/cancel` request body should accept optional `{ q1: string, q2: string }`. Store as JSONB in `usage_events` table (event_type: `subscription_cancelled`, metadata: `{ q1, q2 }`). This satisfies both SUBS-04 (survey captured) and the usage_events emission requirement from STATE.md.
**Warning signs:** No `subscription_cancelled` rows in usage_events after real cancellations.

### Pitfall 7: Require Active Subscription Check Blocks /billing Route
**What goes wrong:** If `/billing` is wrapped in `require_active_subscription`, users with past_due or cancel_at_period_end subscriptions can't access billing.
**Why it happens:** Developers habitually protect all post-login routes.
**How to avoid:** `/billing` only needs `get_current_user` (auth check), not `require_active_subscription`. Users need billing access precisely when their subscription is in a problematic state.
**Warning signs:** 402 errors when accessing /billing.

### Pitfall 8: Window Focus Refetch Fires Too Aggressively
**What goes wrong:** Every time the user alt-tabs (e.g., to check email), the billing page re-fetches.
**Why it happens:** TanStack Query's `refetchOnWindowFocus: true` is the default.
**How to avoid:** Set `staleTime: 60 * 1000` (60 seconds) on the subscription query. A stale check prevents the refetch if data was fetched recently, but still triggers it when user returns from Stripe Portal (which takes > 60s to navigate).
**Warning signs:** Excessive network requests visible in browser devtools.

---

## Code Examples

Verified patterns from official sources:

### Create Portal Session (Python)
```python
# Source: https://docs.stripe.com/api/customer_portal/sessions/create
import stripe

session = stripe.billing_portal.Session.create(
    customer="cus_NciAYcXfLnqBoz",
    return_url="https://avasecret.org/billing",
)
portal_url = session.url  # Open this in a new tab
```

### Cancel Subscription at Period End (Python)
```python
# Source: https://docs.stripe.com/api/subscriptions/update
subscription = stripe.Subscription.modify(
    "sub_1MowQVLkdIwHu7ixeRlqHVzs",
    cancel_at_period_end=True,
)
# subscription.cancel_at_period_end == True
# subscription.current_period_end == Unix timestamp of access end date
```

### List Invoices (Python)
```python
# Source: https://docs.stripe.com/api/invoices/list
invoices = stripe.Invoice.list(customer="cus_NeZwdNtLEOXuvB", limit=12)
for inv in invoices.data:
    print(inv.created)          # Unix timestamp
    print(inv.amount_paid)      # Cents (divide by 100 for dollars)
    print(inv.status)           # 'paid', 'open', 'void', etc.
    print(inv.invoice_pdf)      # Direct PDF URL for new tab link
```

### Frontend — Subscription Data Fetch with Focus Refetch
```typescript
// Source: TanStack Query v5 docs — refetchOnWindowFocus default behavior
const { data: subscription } = useQuery({
  queryKey: ['subscription'],
  queryFn: () => getSubscription(token!),
  staleTime: 60 * 1000,
})
```

### Migration 006 — Add cancel_at_period_end Column
```sql
-- 006_subscription_cancel_at_period_end.sql
ALTER TABLE public.subscriptions
  ADD COLUMN IF NOT EXISTS cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE;
```

### API Cancel Request (TypeScript)
```typescript
// POST /billing/cancel — sends survey responses with cancellation
export async function cancelSubscription(
  token: string,
  survey: { q1: string; q2: string }
): Promise<void> {
  const res = await fetch('/billing/cancel', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(survey),
  })
  if (!res.ok) throw new Error('Cancellation failed')
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Immediate subscription cancellation (`stripe.Subscription.cancel()`) | `cancel_at_period_end=True` via `stripe.Subscription.modify()` | Stripe API v2 era | Users retain access until billing period ends; no surprise lockouts |
| Building custom billing management UI | Stripe Customer Portal | ~2020 | Payment method updates, invoice download, plan changes all handled by Stripe-hosted UI |
| Polling for subscription state | Webhook-driven DB updates + focus refetch | React Query era | Near-real-time UI without polling overhead |

**Deprecated/outdated:**
- `stripe.Subscription.cancel()` with no arguments: This immediately cancels. Only use when operator-initiated (not user-initiated cancellation in this project).
- Stripe Checkout `allowPromotionCodes` without explicit configuration: Not needed for this phase.

---

## Existing Code Inventory (Critical for Planning)

The following is already built and must be integrated with, not replaced:

| Asset | Location | Relevance |
|-------|----------|-----------|
| `billing.py` router | `backend/app/routers/billing.py` | Add 3 endpoints to existing file; existing `/billing/checkout` and `/billing/webhook` stay unchanged |
| `stripe_client.py` | `backend/app/services/billing/stripe_client.py` | Add `create_portal_session()` and `cancel_subscription_at_period_end()` |
| `subscription.py` | `backend/app/services/billing/subscription.py` | Add `get_subscription_detail()`, `get_invoices()`, `update_subscription_cancel_state()` |
| `subscriptions` table | Migration 004 | Has: `status`, `current_period_end`, `stripe_customer_id`, `stripe_subscription_id`. Missing: `cancel_at_period_end` (needs migration 006) |
| `require_active_subscription` dependency | `backend/app/dependencies.py` | Must NOT be applied to `/billing` endpoints — only `get_current_user` |
| `useAuthStore` | `frontend/src/store/useAuthStore.ts` | JWT token for all API calls |
| React Query `queryClient` | `frontend/src/App.tsx` | Already configured; `['subscription']` queryKey available |
| `App.tsx` routing | `frontend/src/App.tsx` | Add `/billing` ProtectedRoute (no OnboardingGate needed) |
| `GlassCard` component | `frontend/src/components/ui/GlassCard.tsx` | Can be used for billing sections |
| `usage_events` table | Migration 005 | Emit `subscription_cancelled` event with survey payload as metadata |
| Stripe production price ID | STATE.md | `price_1T7Y6yGzFiJv4RfGhYAwGZM7` — for display/reference |

---

## Open Questions

1. **Plan name display**
   - What we know: `stripe_price_id` is stored (`price_1T7Y6yGzFiJv4RfGhYAwGZM7`). Plan name is not stored locally.
   - What's unclear: Should we hard-code "Ava Monthly" or fetch from Stripe Products API?
   - Recommendation: Hard-code "Ava Monthly" for now — single-product MVP. Fetching from Stripe adds complexity and a live API call for no user benefit.

2. **Upgrade modal content**
   - What we know: Upgrade button opens in-app modal showing plan options before Stripe redirect.
   - What's unclear: Is there a second plan/tier to show in the modal, or is it purely a upsell to the existing single plan?
   - Recommendation: For MVP, Upgrade modal can simply be a confirmation UI that redirects to the existing `/subscribe` → Stripe Checkout flow. If multi-tier pricing is added later, the modal is the right hook.

3. **`customer.subscription.updated` webhook registration**
   - What we know: This event must be added to the Stripe Dashboard webhook subscription list.
   - What's unclear: Whether the existing Stripe webhook is currently registered for this event type.
   - Recommendation: Plan must include a human-action step to add `customer.subscription.updated` to the Stripe Dashboard webhook events list. This cannot be done in code.

4. **Cancellation email timing**
   - What we know: `send_cancellation_email` is called on `customer.subscription.deleted` (Phase 9). This fires at period END (not when user cancels).
   - What's unclear: Should the user also get an immediate "cancellation scheduled" email when they hit Confirm?
   - Recommendation: The existing behavior (email at period end via `customer.subscription.deleted`) aligns with the EMAI-04 requirement. No additional email needed. The confirmation screen itself provides immediate feedback.

---

## Sources

### Primary (HIGH confidence)
- `https://docs.stripe.com/api/customer_portal/sessions/create` — Python code for `stripe.billing_portal.Session.create()` confirmed
- `https://docs.stripe.com/api/subscriptions/update` — `stripe.Subscription.modify(cancel_at_period_end=True)` confirmed
- `https://docs.stripe.com/api/invoices/list` — Invoice list fields confirmed (invoice_pdf, amount_paid, status, created)
- `https://docs.stripe.com/api/subscriptions/retrieve` — Subscription object fields confirmed (current_period_end, cancel_at_period_end, status)
- `https://docs.stripe.com/billing/subscriptions/cancel` — `customer.subscription.updated` fires on cancel_at_period_end change; `customer.subscription.deleted` fires at period end
- Project codebase — billing.py, stripe_client.py, subscription.py, migration 004, App.tsx all read directly

### Secondary (MEDIUM confidence)
- TanStack Query v5 default behavior (`refetchOnWindowFocus: true`, `staleTime` semantics) — verified via project usage in existing queries

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in use; Stripe API calls verified against official docs
- Architecture: HIGH — existing code patterns directly observed; new patterns follow established conventions
- Pitfalls: HIGH — cancellation method constraint is in STATE.md; missing webhook handler confirmed by grepping codebase (no `subscription.updated` handler exists); DB schema gaps verified from migration files

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (Stripe API is stable; 30-day window reasonable)
