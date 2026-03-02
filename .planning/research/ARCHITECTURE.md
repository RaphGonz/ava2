# Architecture Research

**Domain:** Dual-Mode AI Companion — v1.1 Launch-Ready Feature Integration
**Researched:** 2026-03-02
**Confidence:** HIGH

---

## Scope

This document covers v1.1 architecture exclusively: how nine new features integrate with the
existing FastAPI + Supabase + React codebase. The v1.0 base architecture is treated as fixed
context, not re-researched. All component decisions assume the existing deployment model
(Docker Compose, nginx, Supabase Cloud, Stripe webhooks) is the stable platform to extend.

---

## Existing Architecture (Fixed Context)

```
┌─────────────────────────────────────────────────────────────────┐
│                         VPS — Docker Compose                     │
│                                                                   │
│  ┌────────────┐   ┌─────────────────────────────────────────┐   │
│  │   nginx    │   │              backend (FastAPI)           │   │
│  │  :80/:443  │──>│  /auth  /avatars  /messages  /chat      │   │
│  │  SPA serve │   │  /billing  /webhook  /photos  /health   │   │
│  │  API proxy │   └──────────────────┬──────────────────────┘   │
│  └────────────┘                      │                           │
│                             ┌────────┴────────┐                  │
│                             │  redis + worker  │                  │
│                             │  (BullMQ jobs)   │                  │
│                             └─────────────────┘                  │
└──────────────────────────────────────┬──────────────────────────┘
                                       │
              ┌────────────────────────┼─────────────────────┐
              │                        │                      │
   ┌──────────┴──────┐    ┌────────────┴───────┐   ┌────────┴──────┐
   │ Supabase Cloud  │    │    Stripe          │   │  ComfyUI /    │
   │ (PostgreSQL +   │    │  (subscriptions,   │   │  OpenAI /     │
   │  Auth + RLS +   │    │   webhooks)        │   │  external APIs│
   │  Storage)       │    └────────────────────┘   └───────────────┘
   └─────────────────┘
```

### Established Patterns to Preserve

| Pattern | What It Is | Why It Must Be Kept |
|---------|-----------|---------------------|
| Two Supabase clients | `supabase_client` (anon+RLS) + `supabase_admin` (service role) | Prevents JWT bleed in concurrent async requests; RLS isolation guarantee |
| `get_current_user` dependency | Validates Supabase JWT on every protected endpoint | Single auth validation point; all new protected routes must use this |
| `require_active_subscription` dependency | Chains from `get_current_user`; raises 402 if no active sub | Billing gate pattern; reuse on any new gated feature |
| Pydantic settings via `config.py` | All config comes from env; validated at startup | New services must add their keys here, never hard-code |
| BullMQ + Redis worker | Long-running async jobs (image generation) | Any new long-running task belongs here, not in a request handler |
| Sentry initialized in `main.py` | Exception tracking already active | No new monitoring infra needed; just ensure new routes are covered |

---

## v1.1 System Overview (After All Features Shipped)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           VPS — Docker Compose (v1.1)                     │
│                                                                            │
│  ┌─────────────┐   ┌──────────────────────────────────────────────────┐  │
│  │ Caddy       │   │                  backend (FastAPI)                │  │
│  │ :80/:443    │──>│                                                   │  │
│  │ Auto-HTTPS  │   │  EXISTING:  /auth  /avatars  /messages  /chat    │  │
│  │ SPA serve   │   │             /billing  /webhook  /photos  /health  │  │
│  │ API proxy   │   │                                                   │  │
│  └─────────────┘   │  NEW v1.1:  /billing/portal  (portal redirect)  │  │
│                    │             /billing/cancel   (cancel flow)       │  │
│                    │             /admin/*           (analytics)        │  │
│                    │             /auth/reset-password (pw reset stub)  │  │
│                    └──────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                     Frontend (React SPA — Vite)                     │  │
│  │                                                                     │  │
│  │  EXISTING:  /login  /signup  /chat  /settings  /photo  /subscribe  │  │
│  │  /avatar-setup                                                      │  │
│  │                                                                     │  │
│  │  NEW v1.1:  /           (landing page)                              │  │
│  │             /billing    (subscription management)                   │  │
│  │             /cancel     (churn flow — multi-step)                   │  │
│  │             /forgot-password                                        │  │
│  │             /reset-password  (deep-link target from email)          │  │
│  │             /admin           (analytics dashboard, role-gated)      │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌────────────────────┐   ┌───────────────────────────────────────────┐  │
│  │  redis + worker    │   │  NEW: email service (Resend SDK)          │  │
│  │  (BullMQ jobs)     │   │  Called from: billing webhook handler     │  │
│  └────────────────────┘   │  and auth signup hook                     │  │
│                            └───────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
              │
              ├── Supabase Cloud (PostgreSQL + Auth + RLS + Storage)
              ├── Stripe (subscriptions, Customer Portal, webhooks)
              ├── Resend (transactional email delivery)
              └── Google OAuth (via Supabase Auth provider config)
```

---

## Feature-by-Feature Integration Analysis

### 1. Transactional Emails

**Where email sending lives:** `backend/app/services/email/` — a new service module.

**Recommended library:** Resend Python SDK (`pip install resend`).
Resend is the current recommendation for new Python/FastAPI projects: clean API, generous free
tier (3,000 emails/month), excellent deliverability, and a first-class Supabase partnership.
Postmark is a viable alternative with higher cost; SendGrid is the legacy choice with more
configuration complexity.

**Trigger points and what changes:**

| Trigger | Where in Code | What Calls Email |
|---------|--------------|------------------|
| User signs up | `billing.py` webhook OR Supabase Auth Hook | `welcome_email(user_email)` |
| Payment succeeds | `billing.py` — `invoice.payment_succeeded` webhook event | `receipt_email(user_email, amount, invoice_url)` |
| Subscription cancelled | `billing.py` — `customer.subscription.deleted` event | `cancellation_email(user_email, period_end)` |

**The signup trigger has two options:**

Option A (simpler): Supabase custom Auth Hook — Supabase calls a webhook when a user is
created. The hook URL points to a new `POST /auth/hooks/signup` endpoint in the backend that
sends the welcome email via Resend. This keeps email logic server-side without touching the
`/auth/signup` router.

Option B (simpler still for now): Add `send_welcome_email(user.email)` as a `BackgroundTask`
directly in the existing `POST /auth/signup` handler. No Supabase hook setup needed. Acceptable
for v1.1 scale.

**Recommendation:** Option B for v1.1. Add `BackgroundTasks` to the signup endpoint and
call the email service there. Supabase Auth Hooks are the right long-term solution but add
external webhook complexity that is unnecessary at launch scale.

**New files:**
```
backend/app/services/email/
    __init__.py
    resend_client.py      # Resend SDK wrapper, reads RESEND_API_KEY from settings
    templates.py          # Email body builders (welcome, receipt, cancellation)
```

**Config change:** Add `resend_api_key: str = ""` to `Settings` in `config.py`.

**Data flow:**
```
POST /auth/signup → create user → BackgroundTask → resend_client.send(welcome)
Stripe webhook → invoice.payment_succeeded → subscription.py → email_service.receipt()
Stripe webhook → subscription.deleted → subscription.py → email_service.cancellation()
```

---

### 2. Google OAuth (Sign In / Sign Up)

**Key insight:** Google OAuth for login is entirely a Supabase Auth feature, not a custom
OAuth implementation. The existing `google_oauth.py` router handles Google Calendar OAuth
(a different flow: user-specific API access for secretary mode). The new Google Sign-In is
a separate concern at the Supabase Auth layer.

**What changes:**

| Layer | Change |
|-------|--------|
| Supabase Dashboard | Enable Google provider, paste Client ID + Secret |
| Google Cloud Console | Create new OAuth 2.0 Web Client; add `https://[project].supabase.co/auth/v1/callback` as authorized redirect URI |
| Frontend | Add "Continue with Google" button to `LoginPage.tsx` and `SignupPage.tsx` |
| Backend | No changes — Supabase JWT works the same regardless of auth method |

**Frontend implementation pattern:**

The frontend must use `@supabase/supabase-js` client directly (not via the backend) for this
flow. This is the only place where the frontend calls Supabase directly rather than routing
through the FastAPI backend. The Supabase JS client handles PKCE automatically.

```typescript
// frontend/src/api/auth.ts — add:
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
)

export async function signInWithGoogle() {
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo: `${window.location.origin}/auth/callback` }
  })
  if (error) throw error
}
```

**New frontend route required:** `/auth/callback` — a minimal page that calls
`supabase.auth.getSession()` after the OAuth redirect, extracts the JWT, stores it in
Zustand auth store, and redirects to `/chat`. The `@supabase/supabase-js` client handles the
PKCE code exchange automatically; the callback page just needs to read the established session.

**Zustand store change:** After OAuth callback, the token format is identical to
email/password login — both return a Supabase JWT. The `useAuthStore` `setAuth(token, userId)`
call is identical; no store changes needed.

**Account linking edge case:** If a user registered with email+password and then tries Google
OAuth with the same email, Supabase v2 with `mailer_autoconfirm` disabled will return an error
("User already registered"). The frontend must catch this and show: "An account with this
email already exists. Sign in with your password instead." This is handled in the
`/auth/callback` error path.

**New env vars required:**
```
VITE_SUPABASE_URL=https://[project].supabase.co
VITE_SUPABASE_ANON_KEY=[anon key]
```

---

### 3. Password Reset

**What Supabase provides:** Full token generation, email sending (via configured SMTP), and
token validation. The backend does not need a new endpoint for password reset.

**Flow:**

```
Frontend /forgot-password
    → supabase.auth.resetPasswordForEmail(email, { redirectTo: 'https://domain/reset-password' })
    → Supabase sends email with link → token embedded in URL as hash fragment
    → User clicks → browser lands on /reset-password?type=recovery&...
    → /reset-password page calls supabase.auth.updateUser({ password: newPassword })
    → Supabase validates token, updates password, invalidates all sessions
    → Frontend clears auth store, redirects to /login with success message
```

**Configuration requirement:** The `redirectTo` URL (`https://[domain]/reset-password`) must
be added to Supabase Dashboard → Authentication → URL Configuration → Redirect URLs. Without
this, Supabase rejects the redirectTo parameter.

**Supabase SMTP for password reset emails:** Supabase sends password reset emails using its
built-in SMTP (configurable in the dashboard). For v1.1, configure Resend as the SMTP provider
in Supabase Dashboard → Authentication → SMTP Settings. This makes password reset emails use
the same email infrastructure as transactional emails (consistent from-address and deliverability).

**New frontend pages:**
- `ForgotPasswordPage.tsx` — email input form; calls Supabase SDK directly
- `ResetPasswordPage.tsx` — new password form; calls `supabase.auth.updateUser` after OAuth
  callback establishes the recovery session

**Backend changes:** None. The Supabase Auth service handles the full flow.

**Nginx/Caddy change:** `/reset-password` must route to the SPA `index.html`. This is already
handled by the existing `try_files $uri $uri/ /index.html` fallback in nginx, so no routing
change is needed.

---

### 4. Admin Dashboard (`/admin`)

**Architecture decision: custom React page, not a third-party admin framework.**

Reason: the data lives across two systems (Supabase PostgreSQL + Stripe API). Third-party
admin tools (fastapi-admin, Streamlit, Metabase) would require either replicating data or
building adapters. A custom React page with a FastAPI `/admin` router is simpler and fits
the existing architecture.

**Route protection — admin role gate:**

The `admin` check uses a Supabase custom claim. Admin users get `app_metadata.role = "admin"`
set via `supabase_admin` (service role). The backend reads this claim from the JWT:

```python
# backend/app/dependencies.py — add:
async def require_admin(user=Depends(get_current_user)):
    role = (user.app_metadata or {}).get("role")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
```

Setting admin role (one-time CLI operation, not a UI feature for v1.1):
```python
supabase_admin.auth.admin.update_user_by_id(
    user_id, {"app_metadata": {"role": "admin"}}
)
```

**New backend router:** `backend/app/routers/admin.py`

```
GET /admin/stats/overview   → active users, messages, photos, subscriptions (last 7/30 days)
GET /admin/stats/revenue    → MRR, churn count, new subs (from Stripe API)
GET /admin/users            → paginated user list (id, email, sub status, created_at)
```

All admin endpoints use `Depends(require_admin)`.

**Data storage for usage events:** Use PostgreSQL for event storage. A simple `usage_events`
table in Supabase:

```sql
CREATE TABLE usage_events (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid REFERENCES auth.users(id),
    event_type  text NOT NULL,  -- 'message_sent', 'photo_generated', 'mode_switch', 'subscription_created'
    metadata    jsonb,           -- event-specific data (e.g., mode, photo quality)
    created_at  timestamptz DEFAULT now()
);

-- Index for time-range queries (most admin queries filter by created_at)
CREATE INDEX idx_usage_events_created_at ON usage_events(created_at DESC);
CREATE INDEX idx_usage_events_user_id ON usage_events(user_id);
CREATE INDEX idx_usage_events_type ON usage_events(event_type);
```

**Event emission points:**

| Event | Where Emitted |
|-------|--------------|
| `message_sent` | `web_chat.py` — after successful LLM response |
| `photo_generated` | Worker job — after ComfyUI completes |
| `mode_switch` | `web_chat.py` — when mode detection changes mode |
| `subscription_created` | `billing.py` — in `activate_subscription()` |
| `subscription_cancelled` | `billing.py` — in `deactivate_subscription()` with `canceled` status |

**Emission pattern:** Fire-and-forget insert using `supabase_admin` (bypasses RLS — admin
writes should not be blocked by user RLS policies). Use `asyncio.create_task()` or
`BackgroundTasks` to avoid blocking request handlers.

**Admin dashboard frontend page:** `frontend/src/pages/AdminPage.tsx`

- Route: `/admin` — guarded by checking `app_metadata.role` from JWT decode
- Data: fetched from `/admin/stats/*` endpoints
- Display: simple stat cards (no complex charting library needed for v1.1 — plain numbers
  with period-over-period delta are sufficient)
- No admin-specific frontend library required

**Frontend route guard:**
```typescript
function AdminRoute({ children }) {
  const token = useAuthStore(s => s.token)
  // decode JWT to read app_metadata.role
  const payload = token ? JSON.parse(atob(token.split('.')[1])) : null
  if (payload?.app_metadata?.role !== 'admin') return <Navigate to="/chat" />
  return <>{children}</>
}
```

---

### 5. Usage Event Tracking

Covered in section 4 above (the `usage_events` table and emission pattern). Additional notes:

**What NOT to track at v1.1:**
- Page views (no analytics SDK needed — server-side events are sufficient)
- Session duration (not meaningful for a conversational product)
- Button clicks (overkill for launch; add Posthog if product-market fit is confirmed)

**Admin query patterns for the stats endpoint:**

```sql
-- Active users (7-day)
SELECT COUNT(DISTINCT user_id) FROM usage_events
WHERE created_at > now() - interval '7 days';

-- Messages sent (30-day total + per-user average)
SELECT COUNT(*), COUNT(*)::float / NULLIF(COUNT(DISTINCT user_id), 0)
FROM usage_events
WHERE event_type = 'message_sent'
  AND created_at > now() - interval '30 days';

-- Photos generated (30-day)
SELECT COUNT(*) FROM usage_events
WHERE event_type = 'photo_generated'
  AND created_at > now() - interval '30 days';
```

MRR and subscription counts come from Stripe API (not the local DB), because Stripe is the
source of truth for billing state.

---

### 6. Landing Page

**Architecture decision: same React SPA, new `"/"` route, not a separate site.**

Rationale:
- The existing nginx/SPA setup already handles all routes via `try_files` fallback
- No new deployment unit needed
- Sharing Vite build means one deploy step
- The landing page has zero backend dependencies — all static React + Tailwind

**SEO consideration:** React SPAs have poor native SEO because crawlers see an empty `<div>`.
For a landing page at `"/"`, use `react-helmet-async` to inject proper `<title>`, meta
description, and Open Graph tags. Google's crawler now executes JavaScript (Googlebot renders
SPAs), so this is sufficient for v1.1 — a full SSR migration (Next.js) is not needed.

```typescript
// frontend/src/pages/LandingPage.tsx
import { Helmet } from 'react-helmet-async'

export default function LandingPage() {
  return (
    <>
      <Helmet>
        <title>Ava — Your AI Companion</title>
        <meta name="description" content="A dual-mode AI companion..." />
        <meta property="og:title" content="Ava — Your AI Companion" />
      </Helmet>
      {/* ... hero, features, pricing sections */}
    </>
  )
}
```

**New dependency:** `npm install react-helmet-async` + wrap `App` in `<HelmetProvider>`.

**Route change in `App.tsx`:** Add `<Route path="/" element={<LandingPage />} />` before the
catch-all `<Route path="*" element={<Navigate to="/chat" />} />`. The catch-all must move to
redirect authenticated users to `/chat` only if they hit unknown routes — the landing page at
`"/"` should be accessible to unauthenticated visitors.

**Auth logic change:** The existing catch-all `<Navigate to="/chat" replace />` must not apply
to `"/"`. The landing page is public. Only authenticated routes need protection.

**Nginx change:** No nginx change needed — `try_files $uri $uri/ /index.html` already handles
all SPA routes including `"/"`.

---

### 7. VPS Deployment

**Recommendation: Replace nginx with Caddy for SSL termination.**

Rationale: The current nginx configuration handles only HTTP (no SSL). Achieving HTTPS with
nginx requires Certbot integration, cron jobs for renewal, volume mounts for certificates,
and manual nginx reload after renewal. Caddy provides automatic HTTPS with zero-touch Let's
Encrypt certificate issuance and renewal — a single `Caddyfile` replaces all of this.

**Caddy Caddyfile (replaces nginx.conf):**

```
yourdomain.com {
    # Serve React SPA static files
    root * /srv/frontend

    # API proxy — route backend paths to FastAPI
    @api path /auth/* /chat/* /billing/* /avatars/* /preferences/* /photos/* /webhook/* /messages/* /dev/* /health/* /admin/*
    reverse_proxy @api backend:8000

    # SPA fallback — all other routes get index.html
    try_files {path} /index.html
    file_server

    # Compress responses
    encode gzip
}
```

**docker-compose.yml change:** Replace `nginx` service with `caddy`:

```yaml
caddy:
  image: caddy:2-alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./Caddyfile:/etc/caddy/Caddyfile:ro
    - ./frontend/dist:/srv/frontend:ro
    - caddy_data:/data           # persists TLS certificates
    - caddy_config:/config
  depends_on:
    - backend
  restart: unless-stopped
```

**Environment variable management on VPS:**

Store secrets in `backend/.env` (gitignored). On the VPS, copy `.env` manually or use a
secrets manager (Hetzner/DigitalOcean do not have a built-in secrets manager; `scp` the `.env`
file on first deploy, or use `docker secret` for Docker Swarm — overkill for single-node).

The `.env` pattern is correct for single-VPS deployments. What matters is:
- The `.env` file is never committed to git (already in `.gitignore`)
- Production `.env` contains real API keys, dev `.env` contains stubs
- Caddy manages TLS automatically; no SSL key material needed in `.env`

**Deployment checklist additions for v1.1:**
```
- RESEND_API_KEY=[key]              # transactional email
- VITE_SUPABASE_URL=[url]          # frontend .env (build-time)
- VITE_SUPABASE_ANON_KEY=[key]     # frontend .env (build-time)
- CADDY domain registration        # DNS A record → VPS IP
```

**Nginx vs Caddy decision confirmation:** Nginx is kept if the team wants zero change to the
reverse proxy layer and is willing to set up Certbot manually. Caddy is recommended because
the operational simplicity benefit is significant for a one-person/small-team product. The
configuration change is a 15-minute migration.

---

### 8. Subscription Management Page

**Architecture: hybrid — custom in-app page + Stripe Customer Portal redirect.**

The "Billing" page in the React app shows the user's current plan state and provides two
action paths:
1. Cancel → custom in-app churn flow (section 9 below)
2. Update payment method / view invoices → redirect to Stripe Customer Portal

**New backend endpoint:** `POST /billing/portal`

```python
@router.post("/portal")
async def create_portal_session(user=Depends(get_current_user)):
    """Create a Stripe Customer Portal session and return the redirect URL."""
    customer_id = get_stripe_customer_id(str(user.id))  # reads from subscriptions table
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{settings.frontend_url}/billing"
    )
    return {"portal_url": session.url}
```

**New frontend page:** `frontend/src/pages/BillingPage.tsx`

Data needed (from `GET /billing/subscription` — new endpoint that returns Stripe sub data):
```typescript
{
  plan_name: string         // e.g., "Ava Pro"
  status: string            // "active" | "canceled" | "past_due"
  current_period_end: string  // ISO date → "Next billing date: March 15, 2026"
  cancel_at_period_end: bool  // true if user already cancelled but access remains
}
```

**New backend endpoint:** `GET /billing/subscription`

```python
@router.get("/subscription")
async def get_subscription(user=Depends(get_current_user)):
    """Return current subscription details for the billing page."""
    # reads subscriptions table + fetches from Stripe for current_period_end
    ...
```

**Data flow:**

```
User visits /billing
    → GET /billing/subscription → shows plan, next billing date, status
    → "Manage Payment / View Invoices" click → POST /billing/portal → redirect to Stripe Portal
    → "Cancel Subscription" click → navigate to /cancel (churn flow)
```

**Stripe webhook additions needed:**

The existing billing webhook in `billing.py` handles `checkout.session.completed`,
`invoice.payment_failed`, and `customer.subscription.deleted`. For v1.1, add:
- `invoice.payment_succeeded` → trigger receipt email + update `current_period_end` in DB
- `customer.subscription.updated` → update `cancel_at_period_end` flag in DB (for cases where
  user cancels via Stripe Portal rather than in-app flow)

---

### 9. Cancellation Churn Flow + Exit Survey

**Where churn data lives:** A new `churn_surveys` table in Supabase.

```sql
CREATE TABLE churn_surveys (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        uuid REFERENCES auth.users(id),
    subscription_id text,             -- Stripe subscription ID for reference
    reason         text NOT NULL,      -- multiple-choice selection
    detail         text,               -- optional open-text follow-up
    retention_offer_shown text,        -- which offer was shown (if any)
    retention_offer_accepted bool DEFAULT false,
    created_at     timestamptz DEFAULT now()
);
```

**New backend endpoints (add to `billing.py` or new `churn.py` router):**

```
POST /billing/survey          → save churn survey response
POST /billing/cancel          → call Stripe cancel_at_period_end, trigger cancellation email
```

**Churn flow frontend route:** `frontend/src/pages/CancelPage.tsx`

Multi-step page (all client-side state, no route changes per step):

```
Step 1: Exit survey — "Why are you cancelling?"
        POST /billing/survey (saves reason before cancel; data captured even if user abandons)

Step 2: Retention offer — shown based on reason code
        "Too expensive" → show discount offer
        "Not using it" → show pause option
        "Other" → skip straight to Step 3

Step 3: Final confirmation
        "Confirm Cancellation" → POST /billing/cancel → Stripe cancel_at_period_end=true
        → navigate to /billing with success banner "Subscription cancelled. Access until [date]."
        → webhook fires → cancellation email sent
```

**Stripe cancel call pattern:**

```python
# POST /billing/cancel
stripe.Subscription.modify(
    subscription_id,
    cancel_at_period_end=True   # user retains access until period_end; does not immediately cancel
)
```

`cancel_at_period_end=True` is the correct approach — user keeps access until the billing
period ends. When the period ends, Stripe fires `customer.subscription.deleted`, which triggers
the existing `deactivate_subscription()` call and the cancellation confirmation email.

**Immediate cancel vs. period-end cancel:** Period-end cancel is required by consumer
protection expectations and reduces support requests ("you charged me after I cancelled").
Do not use `stripe.Subscription.cancel()` (immediate) unless the user explicitly requests a
refund.

---

## Component Boundaries — New vs Modified

### New Components (create from scratch)

| Component | Type | Location |
|-----------|------|----------|
| Email service | Backend service | `backend/app/services/email/` |
| Admin router | Backend router | `backend/app/routers/admin.py` |
| `require_admin` dependency | Backend dependency | `backend/app/dependencies.py` (add to existing) |
| Churn survey router | Backend router | `backend/app/routers/billing.py` (add endpoints) or new `churn.py` |
| `usage_events` table | Database | Supabase migration |
| `churn_surveys` table | Database | Supabase migration |
| LandingPage | Frontend page | `frontend/src/pages/LandingPage.tsx` |
| BillingPage | Frontend page | `frontend/src/pages/BillingPage.tsx` |
| CancelPage | Frontend page | `frontend/src/pages/CancelPage.tsx` |
| ForgotPasswordPage | Frontend page | `frontend/src/pages/ForgotPasswordPage.tsx` |
| ResetPasswordPage | Frontend page | `frontend/src/pages/ResetPasswordPage.tsx` |
| AuthCallbackPage | Frontend page | `frontend/src/pages/AuthCallbackPage.tsx` (OAuth callback) |
| AdminPage | Frontend page | `frontend/src/pages/AdminPage.tsx` |
| Supabase JS client (frontend) | Frontend lib | `frontend/src/lib/supabase.ts` (new singleton) |
| Caddyfile | Infrastructure | `Caddyfile` (replaces nginx.conf) |

### Modified Components (change existing)

| Component | What Changes |
|-----------|-------------|
| `backend/app/routers/billing.py` | Add `/portal`, `/subscription`, `/survey`, `/cancel` endpoints; add `invoice.payment_succeeded` and `customer.subscription.updated` webhook handlers |
| `backend/app/routers/auth.py` | Add `BackgroundTask` for welcome email on `POST /auth/signup` |
| `backend/app/config.py` | Add `resend_api_key`, `vite_supabase_url`, `vite_supabase_anon_key` (backend only needs `resend_api_key`; Vite env vars are frontend build-time) |
| `backend/app/services/billing/subscription.py` | Add `get_stripe_customer_id()`, `update_period_end()`, `set_cancel_at_period_end()` helpers |
| `backend/app/main.py` | Include `admin` router; no other changes |
| `frontend/src/App.tsx` | Add routes: `/`, `/billing`, `/cancel`, `/forgot-password`, `/reset-password`, `/auth/callback`, `/admin`; move catch-all logic to not redirect `"/"` |
| `frontend/src/store/useAuthStore.ts` | No changes to store shape; the token/userId fields work for OAuth sessions identically |
| `frontend/src/api/auth.ts` | Add `signInWithGoogle()`, `resetPasswordForEmail()`, `updatePassword()` using Supabase JS client |
| `docker-compose.yml` | Replace `nginx` service with `caddy`; add `caddy_data` and `caddy_config` volumes |
| `nginx.conf` | Remove (or keep for local dev without SSL); replaced by `Caddyfile` |

---

## Data Flow Changes

### New: Welcome Email on Signup

```
POST /auth/signup
    → supabase_client.auth.sign_up()
    → user created in Supabase Auth
    → BackgroundTask: email_service.send_welcome(user.email)
    → Resend API → email delivered
    → return TokenResponse (unchanged)
```

### New: Receipt Email on Payment

```
Stripe webhook → POST /billing/webhook → invoice.payment_succeeded event
    → get user_id from subscriptions table WHERE stripe_customer_id = customer
    → get user email from supabase_admin.auth.admin.get_user_by_id(user_id)
    → update current_period_end in subscriptions table
    → email_service.send_receipt(email, amount, invoice_url)
```

### New: Google OAuth Login

```
User clicks "Continue with Google" on /login or /signup
    → supabase.auth.signInWithOAuth({ provider: 'google' })  [frontend, Supabase JS]
    → redirect to Google consent screen
    → Google redirects to Supabase callback URL (https://[project].supabase.co/auth/v1/callback)
    → Supabase exchanges code, creates session, redirects to /auth/callback in the React app
    → /auth/callback page: supabase.auth.getSession() → extract token + user_id
    → useAuthStore.setAuth(token, userId)  [identical to email/password login]
    → navigate('/chat')
```

### New: Password Reset

```
User visits /forgot-password, enters email
    → supabase.auth.resetPasswordForEmail(email, { redirectTo: 'https://domain/reset-password' })
    → Supabase sends email via configured SMTP (Resend as SMTP)
    → User clicks link → browser loads /reset-password with token in URL hash
    → supabase.auth.updateUser({ password: newPassword })  [Supabase JS validates token]
    → clearAuth() in Zustand store → navigate('/login') with success message
```

### New: Admin Stats Query

```
GET /admin/stats/overview (requires admin JWT)
    → require_admin dependency validates app_metadata.role = "admin"
    → supabase_admin queries usage_events table (aggregations)
    → stripe.Subscription.list() for active count + MRR calculation
    → return combined stats JSON
    → AdminPage.tsx renders stat cards
```

---

## Recommended Project Structure After v1.1

```
backend/app/
├── routers/
│   ├── auth.py           [MODIFIED: add welcome email BackgroundTask]
│   ├── billing.py        [MODIFIED: add portal, subscription, survey, cancel endpoints]
│   ├── admin.py          [NEW: /admin/* endpoints]
│   └── ... (unchanged: avatars, messages, preferences, webhook, etc.)
│
├── services/
│   ├── billing/          [MODIFIED: add helpers to subscription.py]
│   ├── email/            [NEW]
│   │   ├── __init__.py
│   │   ├── resend_client.py
│   │   └── templates.py
│   └── ... (unchanged: chat, image, llm, etc.)
│
├── dependencies.py       [MODIFIED: add require_admin]
└── config.py             [MODIFIED: add resend_api_key]

frontend/src/
├── pages/
│   ├── LandingPage.tsx   [NEW]
│   ├── BillingPage.tsx   [NEW]
│   ├── CancelPage.tsx    [NEW]
│   ├── ForgotPasswordPage.tsx [NEW]
│   ├── ResetPasswordPage.tsx  [NEW]
│   ├── AuthCallbackPage.tsx   [NEW: OAuth redirect handler]
│   ├── AdminPage.tsx     [NEW]
│   └── ... (unchanged: ChatPage, SettingsPage, LoginPage, etc.)
│
├── api/
│   ├── auth.ts           [MODIFIED: add Google OAuth + password reset calls]
│   ├── billing.ts        [MODIFIED: add portal, subscription, survey, cancel API calls]
│   └── admin.ts          [NEW: admin stats API calls]
│
├── lib/
│   └── supabase.ts       [NEW: Supabase JS client singleton for OAuth + password reset]
│
└── App.tsx               [MODIFIED: add new routes, update catch-all logic]

infrastructure/
├── Caddyfile             [NEW: replaces nginx.conf for production]
├── nginx.conf            [KEPT for local dev reference; not used in prod]
└── docker-compose.yml    [MODIFIED: nginx → caddy service]
```

---

## Architectural Patterns

### Pattern 1: BackgroundTask for Side Effects

**What:** Attach email sends, event logging, and non-critical async operations as FastAPI
`BackgroundTasks`. The request returns immediately; the side effect runs after.

**When to use:** Any operation triggered by a request that does not affect the response
content: welcome emails, usage event inserts, webhook notifications.

**Trade-off:** If the server restarts between request handling and background task execution,
the task is lost. For v1.1 scale this is acceptable. For production-critical tasks (e.g.,
Stripe payment confirmation), use the BullMQ queue instead.

```python
from fastapi import BackgroundTasks

@router.post("/signup")
async def signup(body: SignupRequest, background_tasks: BackgroundTasks):
    response = supabase_client.auth.sign_up(...)
    background_tasks.add_task(email_service.send_welcome, response.user.email)
    return TokenResponse(...)
```

### Pattern 2: supabase_admin for Server-Side Writes

**What:** All server-initiated writes (email lookups, event inserts, admin queries) use the
`supabase_admin` (service role) client. User-initiated reads use `supabase_client` with RLS.

**When to use:** Any operation that must bypass RLS (webhook handlers, admin endpoints, usage
event inserts). Never use `supabase_admin` in user-facing read endpoints.

**Why critical for v1.1:** The `usage_events` inserts happen in server-side request handlers,
not user-initiated requests. Using `supabase_client` for these would fail RLS if the user's
JWT is not available (e.g., in webhook handlers). Use `supabase_admin`.

### Pattern 3: Stripe as Source of Truth for Billing State

**What:** The local `subscriptions` table is a cache of Stripe state. The `status`,
`current_period_end`, and `cancel_at_period_end` fields are authoritative only in Stripe.
Local table is updated via webhooks.

**When to use:** Always query Stripe directly for time-sensitive billing data (e.g., billing
page display). Use local table only for fast checks like `require_active_subscription`.

**Trade-off:** Webhook delays can cause the local table to be stale by seconds to minutes.
For `require_active_subscription`, this is fine (access control does not need real-time).
For the billing page display, prefer a Stripe API call for accuracy.

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0–1k users | Current Docker Compose single-VPS setup is correct. No changes needed. |
| 1k–10k users | Add read replica for Supabase (Supabase Pro supports this). Add connection pooling (PgBouncer). Consider moving usage_events to a separate analytics DB to prevent query contention. |
| 10k+ users | Separate the admin/analytics queries to a dedicated replica. Consider moving email sends to BullMQ queue to prevent transient Resend failures from affecting signups. |

**First bottleneck at current scale:** Supabase connection limits (default 60 connections on
free/Pro tier). The BullMQ worker + backend share connections. Monitor connection count in
Supabase dashboard.

---

## Anti-Patterns

### Anti-Pattern 1: Calling Supabase Admin Client from Frontend

**What people do:** Import `supabase_admin` equivalent (service role key) in the frontend for
admin operations.

**Why it's wrong:** Service role key is secret — embedding it in frontend JavaScript exposes
it to all users. Any user can then bypass RLS and access all data.

**Do this instead:** All admin operations go through authenticated FastAPI endpoints with the
`require_admin` dependency. The frontend sends a JWT; the backend validates it and uses the
service role client internally.

### Anti-Pattern 2: Using `stripe.Subscription.cancel()` for User Cancellations

**What people do:** Immediately cancel the Stripe subscription when a user clicks "Cancel".

**Why it's wrong:** User loses access immediately. Generates chargebacks and support requests.
Violates consumer expectations in most markets.

**Do this instead:** Use `stripe.Subscription.modify(id, cancel_at_period_end=True)`. User
retains access until the billing period ends. Access revokes automatically when Stripe fires
the `customer.subscription.deleted` webhook.

### Anti-Pattern 3: Sending Email Synchronously in Request Handlers

**What people do:** Call `resend.Emails.send(...)` directly in the request handler body, making
the response wait for email delivery.

**Why it's wrong:** Resend API latency (50-200ms) adds to every signup request. If Resend is
down, signups fail. Email delivery is never critical path for the user-facing response.

**Do this instead:** Use `BackgroundTasks` (for v1.1) or BullMQ queue (for production
resilience). The response returns immediately; email sends in the background.

### Anti-Pattern 4: Rebuilding What Supabase Auth Already Provides

**What people do:** Implement custom OAuth state management, PKCE code exchange, or token
refresh logic instead of using `@supabase/supabase-js`.

**Why it's wrong:** Supabase JS client handles PKCE, token refresh, session persistence, and
error cases. Custom implementations introduce security vulnerabilities and maintenance burden.

**Do this instead:** Use `supabase.auth.signInWithOAuth()` for Google OAuth, and
`supabase.auth.resetPasswordForEmail()` / `supabase.auth.updateUser()` for password reset.
The only custom logic needed is the callback page that reads the established session.

### Anti-Pattern 5: Storing Stripe Webhook Events Without Idempotency

**What people do:** Process Stripe webhook events without checking if they've been processed
before, causing duplicate emails or duplicate subscription activations.

**Why it's wrong:** Stripe retries webhook delivery on failure. The same event can arrive
2-5 times. Sending 3 welcome emails to a new user damages trust.

**Do this instead:** The existing `subscriptions.upsert(on_conflict="user_id")` pattern in
`activate_subscription()` is already idempotent. For emails, add a simple guard:
```python
# Before sending receipt email, check if this invoice_id was already processed
# Store processed_invoice_ids in a DB table or use Stripe's built-in idempotency key
```

---

## Integration Points

### External Services (v1.1 additions)

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **Resend** | Python SDK (`import resend`); API key in settings | Used for welcome, receipt, cancellation emails. 3k emails/month free tier. |
| **Supabase Auth (Google provider)** | Configure in Supabase dashboard; `@supabase/supabase-js` on frontend | No backend endpoint changes for OAuth sign-in; backend sees identical JWTs |
| **Supabase Auth (SMTP/Resend)** | Configure Resend SMTP credentials in Supabase dashboard | Supabase sends password reset emails via Resend as SMTP relay |
| **Stripe Customer Portal** | Backend creates portal session; frontend redirects to returned URL | Customer portal URL is ephemeral (single-use, expires in hours) |
| **Caddy** | Replace nginx container in docker-compose.yml | Automatic HTTPS; no Certbot, no cron jobs |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `billing.py` ↔ `email service` | Direct Python function call (via BackgroundTask) | Not async by default — call synchronously in background task or wrap with asyncio |
| `auth.py` ↔ `email service` | BackgroundTask on signup | Must not block the signup response |
| Admin router ↔ Stripe | Direct `stripe.*` API calls | No local caching for v1.1; Stripe responses are fast enough |
| Admin router ↔ `usage_events` | `supabase_admin` aggregate queries | supabase_admin bypasses RLS correctly for cross-user aggregations |
| Frontend ↔ Supabase Auth | `@supabase/supabase-js` client directly | Only exception to "all API calls go through FastAPI backend" rule |

---

## Build Order Recommendation

The dependency graph drives ordering. Features are grouped into phases based on what each
requires to be in place before it can be built.

```
Phase 1: Infrastructure & Delivery Foundation
    ├── VPS deployment (Caddy, SSL, domain)
    └── Email service (Resend SDK + welcome trigger)
        NOTE: Email must be working before billing events can send receipts

Phase 2: Auth Polish (parallel with Phase 1 frontend work)
    ├── Google OAuth (Supabase provider config + frontend button + /auth/callback page)
    └── Password Reset (ForgotPasswordPage + ResetPasswordPage + Supabase SMTP config)
        NOTE: Both features touch auth UI; ship together to minimize churn on login/signup pages

Phase 3: Landing Page
    └── LandingPage.tsx at "/" route + react-helmet-async SEO
        NOTE: No backend dependencies; can be built in parallel with Phase 2
        NOTE: Requires Figma design handoff before starting

Phase 4: Billing & Subscription Management
    ├── Subscription management page (GET /billing/subscription, BillingPage.tsx)
    ├── Stripe Customer Portal redirect (POST /billing/portal)
    ├── Cancellation churn flow (CancelPage.tsx, POST /billing/survey, POST /billing/cancel)
    ├── Receipt email (invoice.payment_succeeded webhook handler)
    └── Cancellation email (already has the webhook; add email trigger)
        NOTE: churn_surveys table migration must run before CancelPage can save data
        NOTE: Receipt email requires email service from Phase 1

Phase 5: Admin Dashboard
    ├── usage_events table migration
    ├── Event emission points (web_chat.py, billing.py, worker)
    ├── Admin router (/admin/stats/*)
    └── AdminPage.tsx + admin route guard
        NOTE: Admin is standalone; can slip to after launch if needed
        NOTE: No user-facing dependencies; ships whenever ready
```

**Critical path:** Phase 1 (email infra) → Phase 4 (billing emails). Phases 2 and 3 can run
in parallel with Phase 1. Phase 5 can run in parallel with any phase.

**If time is constrained:** Phase 5 (Admin Dashboard) can ship post-launch without blocking
the product going live. All other phases are required for launch.

---

## Sources

### Supabase Auth Integration
- [Login with Google — Supabase Docs](https://supabase.com/docs/guides/auth/social-login/auth-google) — HIGH confidence
- [Password Reset — Supabase Docs](https://supabase.com/docs/guides/auth/auth-password-reset) — HIGH confidence
- [JavaScript: Send a password reset request — Supabase Reference](https://supabase.com/docs/reference/javascript/auth-resetpasswordforemail) — HIGH confidence
- [Use Supabase Auth with React — Supabase Docs](https://supabase.com/docs/guides/auth/quickstarts/react) — HIGH confidence

### Stripe Integration
- [Integrate the customer portal with the API — Stripe Docs](https://docs.stripe.com/customer-management/integrate-customer-portal) — HIGH confidence
- [Cancel subscriptions — Stripe Docs](https://docs.stripe.com/billing/subscriptions/cancel) — HIGH confidence
- [Add a cancellation page to the customer portal — Stripe Docs](https://docs.stripe.com/customer-management/cancellation-page) — HIGH confidence

### Email Infrastructure
- [Send emails with FastAPI — Resend Docs](https://resend.com/docs/send-with-fastapi) — HIGH confidence
- [Send emails with Supabase — Resend](https://resend.com/supabase) — MEDIUM confidence

### Frontend SEO for SPAs
- [SEO Optimization for React + Vite Apps — DEV Community](https://dev.to/ali_dz/optimizing-seo-in-a-react-vite-project-the-ultimate-guide-3mbh) — MEDIUM confidence
- [react-helmet-async GitHub](https://github.com/staylor/react-helmet-async) — HIGH confidence

### Caddy vs Nginx
- [Why Caddy Is My Favorite Reverse Proxy in 2025 — DEV Community](https://dev.to/hugovalters/why-caddy-is-my-favorite-reverse-proxy-in-2025-42ed) — MEDIUM confidence
- [Caddy Reverse Proxy in 2025 — Virtualization Howto](https://www.virtualizationhowto.com/2025/09/caddy-reverse-proxy-in-2025-the-simplest-docker-setup-for-your-home-lab/) — MEDIUM confidence
- [Caddy Official Documentation](https://caddyserver.com/docs/) — HIGH confidence

---

*Architecture research for: Ava v1.1 Launch-Ready Feature Integration*
*Researched: 2026-03-02*
*Confidence: HIGH — all integration patterns verified against official Supabase, Stripe, and Resend documentation*
