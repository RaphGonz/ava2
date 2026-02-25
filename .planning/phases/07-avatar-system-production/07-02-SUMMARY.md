---
phase: 07-avatar-system-production
plan: 02
subsystem: payments
tags: [stripe, fastapi, pydantic, supabase, billing, subscriptions]

# Dependency graph
requires:
  - phase: 07-01
    provides: subscriptions table (DB migration 004), avatar gender/nationality columns in schema

provides:
  - AvatarCreate and AvatarResponse with gender and nationality fields (AVTR-01, AVTR-03)
  - POST /avatars insert includes gender and nationality columns
  - POST /billing/checkout — creates Stripe Checkout Session, config-driven price ID (BILL-01, BILL-02)
  - POST /billing/webhook — verifies Stripe signature, handles checkout.session.completed/invoice.payment_failed/subscription.deleted
  - require_active_subscription FastAPI dependency — raises 402 for inactive subscriptions
  - POST /chat gated behind require_active_subscription
  - Config fields: stripe_secret_key, stripe_webhook_secret, stripe_price_id, sentry_dsn, replicate_api_token, redis_url
affects: [07-04, 07-05, frontend-onboarding, frontend-subscribe, chat-endpoints]

# Tech tracking
tech-stack:
  added: [stripe Python SDK]
  patterns:
    - Stripe price ID read from settings (never hardcoded) — config-driven billing per BILL-02
    - supabase_admin (service role) used exclusively for webhook subscription writes — no user JWT available in Stripe webhooks
    - await request.body() called before any JSON parsing in webhook handler — preserves raw bytes for signature verification
    - require_active_subscription as FastAPI Depends() dependency — composable 402 gate
    - Module-level stripe.api_key assignment (global pattern OK at this scale per RESEARCH.md)

key-files:
  created:
    - backend/app/services/billing/__init__.py
    - backend/app/services/billing/stripe_client.py
    - backend/app/services/billing/subscription.py
    - backend/app/routers/billing.py
  modified:
    - backend/app/models/avatar.py
    - backend/app/routers/avatars.py
    - backend/app/dependencies.py
    - backend/app/config.py
    - backend/app/main.py
    - backend/app/routers/web_chat.py
    - backend/requirements.txt

key-decisions:
  - "stripe_price_id stored in settings with empty-string default — no hardcoded price amounts; checkout raises 503 if unconfigured (BILL-02)"
  - "supabase_admin (service role) used for subscription persistence in webhook handler — Stripe webhook context has no user JWT"
  - "require_active_subscription FastAPI dependency raises 402 Payment Required when subscription status != active — composable gate"
  - "await request.body() before any parsing in webhook — preserves raw bytes required for Stripe HMAC signature verification"
  - "Avatar locked post-creation: no AvatarUpdate model and no PATCH /avatars/me full-update endpoint"

patterns-established:
  - "Billing gate pattern: require_active_subscription dependency composable on any protected endpoint"
  - "Stripe webhook pattern: raw_body first, verify signature, then dispatch on event_type"
  - "Config-driven pricing: all Stripe IDs/keys read from settings — no hardcoded values anywhere in billing layer"

requirements-completed: [AVTR-01, AVTR-02, AVTR-03, AVTR-04, BILL-01, BILL-02]

# Metrics
duration: 12min
completed: 2026-02-25
---

# Phase 7 Plan 02: Avatar Model Extension + Stripe Billing Backend Summary

**Avatar gender/nationality fields added to create path; full Stripe billing backend with checkout, webhook, subscription persistence, and 402 chat gate**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-25T09:31:24Z
- **Completed:** 2026-02-25T09:43:38Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments

- Extended AvatarCreate and AvatarResponse with optional gender (max 50) and nationality (max 100) fields; create_avatar DB insert now includes both columns (AVTR-01, AVTR-03)
- Built complete Stripe billing layer: stripe_client.py (checkout session + webhook signature verification), subscription.py (activate/deactivate/get_subscription_status using supabase_admin), billing router (POST /billing/checkout + POST /billing/webhook) (BILL-01, BILL-02)
- Added require_active_subscription FastAPI dependency and gated POST /chat behind it — returns 402 Payment Required for users without active subscription
- Added stripe_secret_key, stripe_webhook_secret, stripe_price_id, sentry_dsn, replicate_api_token config fields (all empty-string defaults); all 47 existing tests continue to pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Avatar model extension — gender/nationality fields on create path only** - `d208f59` (feat)
2. **Task 2: Stripe billing backend — router + subscription service + config + subscription gate** - `85d4af1` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `backend/app/models/avatar.py` - Added gender and nationality fields to AvatarCreate and AvatarResponse
- `backend/app/routers/avatars.py` - Updated create_avatar insert to include gender and nationality
- `backend/app/services/billing/__init__.py` - Empty package init
- `backend/app/services/billing/stripe_client.py` - Stripe checkout session creation and webhook signature verification
- `backend/app/services/billing/subscription.py` - activate_subscription(), deactivate_subscription(), get_subscription_status() using supabase_admin
- `backend/app/routers/billing.py` - POST /billing/checkout and POST /billing/webhook endpoints
- `backend/app/dependencies.py` - Added require_active_subscription dependency (raises 402 when status != active)
- `backend/app/config.py` - Added stripe_secret_key, stripe_webhook_secret, stripe_price_id, sentry_dsn, replicate_api_token fields
- `backend/app/main.py` - Registered billing router
- `backend/app/routers/web_chat.py` - POST /chat now uses require_active_subscription instead of get_current_user
- `backend/requirements.txt` - Added stripe

## Decisions Made

- stripe_price_id stored in Settings with empty-string default — billing router raises 503 (not 500) when price not configured, making misconfiguration obvious to operators
- supabase_admin (service role) used for all subscription DB writes in webhook handler — Stripe webhooks arrive without user JWT context
- require_active_subscription implemented as a pure async dependency that delegates to synchronous get_subscription_status() — keeps billing check sync-compatible without blocking event loop for simple SELECT
- Avatar locked post-creation: no AvatarUpdate model, no PATCH /avatars/me full-update endpoint — only existing PATCH /avatars/me/persona (personality change only) remains

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed missing stripe package**
- **Found during:** Task 2 verification
- **Issue:** `stripe` not yet installed in Python environment; `ModuleNotFoundError` on import
- **Fix:** Ran `pip install stripe -q` in the backend directory
- **Files modified:** None (requirements.txt already updated with stripe entry)
- **Verification:** All billing imports succeed; 47 tests pass
- **Committed in:** `85d4af1` (part of Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking — missing package)
**Impact on plan:** Fix necessary to complete verification. No scope creep.

## Issues Encountered

None beyond the missing stripe package (handled automatically via Rule 3).

## User Setup Required

To activate billing, add these to `backend/.env`:

```
STRIPE_SECRET_KEY=sk_live_...        # Stripe Dashboard → Developers → API keys
STRIPE_WEBHOOK_SECRET=whsec_...      # Stripe Dashboard → Webhooks → signing secret
STRIPE_PRICE_ID=price_...            # Stripe Dashboard → Products → price ID for monthly plan
```

Additionally, register `POST /billing/webhook` as a Stripe webhook endpoint in the Stripe Dashboard, selecting events: `checkout.session.completed`, `invoice.payment_failed`, `customer.subscription.deleted`.

## Next Phase Readiness

- Avatar model backend complete — ready for frontend onboarding form (Plan 04/05)
- Billing backend complete — ready for frontend subscribe flow (Plan 04/05)
- require_active_subscription gate operational — chat is paywall-protected when Stripe keys are configured
- All 47 existing tests pass — no regressions

## Self-Check: PASSED

- FOUND: backend/app/services/billing/__init__.py
- FOUND: backend/app/services/billing/stripe_client.py
- FOUND: backend/app/services/billing/subscription.py
- FOUND: backend/app/routers/billing.py
- FOUND: .planning/phases/07-avatar-system-production/07-02-SUMMARY.md
- FOUND: commit d208f59 (Task 1 — avatar model)
- FOUND: commit 85d4af1 (Task 2 — billing backend)

---
*Phase: 07-avatar-system-production*
*Completed: 2026-02-25*
