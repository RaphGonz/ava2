# Stack Research

**Domain:** v1.1 Launch Ready — new capability additions to existing Ava production stack
**Researched:** 2026-03-02
**Confidence:** HIGH

---

## Scope: Additions Only

This is a subsequent-milestone research file. It documents only the NEW packages and configuration
needed for v1.1 features. It does not re-research or replace anything already shipped.

### Existing Stack (Do Not Modify)

| Area | Technology | Version |
|------|-----------|---------|
| Backend framework | FastAPI + uvicorn/gunicorn | >=0.115.0 |
| Language | Python | 3.12 |
| Database | Supabase (PostgreSQL + RLS) | `supabase==2.25.1` |
| Auth | Supabase JWT (email/password) via Python SDK | same |
| Billing | Stripe | `stripe` (pinned in requirements.txt) |
| Queue | BullMQ + Redis | `bullmq==2.19.5` |
| Monitoring | Sentry | `sentry-sdk` |
| Frontend framework | React | 19.2.0 |
| Build tool | Vite | ^7.3.1 |
| CSS | Tailwind | v4.2.1 |
| State | Zustand | ^5.0.11 |
| Data fetching | TanStack Query | ^5.90.21 |
| Routing | React Router | ^7.13.1 |

### Critical Architectural Constraint

The frontend has NO direct Supabase JS client. Auth flows through a FastAPI proxy:

```
Frontend  →  FastAPI  →  Supabase Python SDK  →  Supabase Cloud
```

The frontend calls `/auth/*` REST endpoints and receives `{ access_token, user_id }`.
JWT is decoded manually in `auth.ts` using `atob()`. This pattern must be preserved
for all new auth features. Adding `@supabase/supabase-js` to the frontend would create
a split-auth architecture — do not do it.

---

## New Capabilities and Their Stack Additions

### 1. Transactional Email

**What:** Welcome on signup, receipt after subscribing, cancellation confirmation.

**Add: `resend` Python SDK**

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `resend` | `^2.23.0` | Send transactional emails from FastAPI | Simple HTTP API, first-class Python SDK, async-compatible with FastAPI BackgroundTasks, EU data center available (GDPR), domain verification required once. Latest release 2026-02-23 (actively maintained). |

**Integration pattern:**

```python
# Pattern: non-blocking email via FastAPI BackgroundTasks
import resend
from fastapi import BackgroundTasks

resend.api_key = settings.RESEND_API_KEY

def send_welcome_email(to_email: str):
    resend.Emails.send({
        "from": "Ava <hello@yourdomain.com>",
        "to": [to_email],
        "subject": "Welcome to Ava",
        "html": "<p>Your account is ready.</p>",
    })

@router.post("/signup")
async def signup(body: SignupRequest, background_tasks: BackgroundTasks):
    # ... create user ...
    background_tasks.add_task(send_welcome_email, body.email)
```

**Trigger points:**
- Welcome: fire from `/auth/signup` handler after successful Supabase user creation
- Receipt: fire from the Stripe webhook handler (`invoice.payment_succeeded`) — already in `webhook.py`
- Cancellation: fire from the Stripe webhook handler (`customer.subscription.deleted`)

**No frontend changes needed.** Emails are backend-triggered events.

**New env vars required:** `RESEND_API_KEY`, `RESEND_FROM_ADDRESS`

---

### 2. Google OAuth Sign-In / Sign-Up

**What:** "Sign in with Google" button on login and signup pages.

**Add: Nothing new — Supabase Python SDK already supports OAuth**

`supabase==2.25.1` (already in requirements.txt) provides `supabase.auth.sign_in_with_oauth()`.
No new Python package required.

**How the flow works with the existing proxy pattern:**

```
1. User clicks "Sign in with Google" on frontend
2. Frontend: GET /auth/google/signin  (new backend route)
3. Backend: supabase.auth.sign_in_with_oauth({"provider": "google", "options": {"redirect_to": callback_url}})
           → returns { url: "https://accounts.google.com/o/oauth2/..." }
4. Frontend: window.location.href = url  (redirect to Google)
5. Google authenticates → redirects to Supabase → Supabase redirects to /auth/google/signin-callback
6. Backend /auth/google/signin-callback: receives ?code= param, exchanges via Supabase, returns access_token + user_id
7. Frontend: stores access_token + user_id in Zustand (same as existing email/password flow)
```

**Two new FastAPI routes needed (no new packages):**

```python
# GET /auth/google/signin
# Returns JSON: { "oauth_url": "https://accounts.google.com/..." }
# Frontend redirects to this URL

# GET /auth/google/signin-callback?code=...&...
# Exchanges code via Supabase Python SDK
# Returns JSON: { "access_token": "...", "user_id": "..." }  — same TokenResponse model
```

**Note:** The existing `/auth/google/connect` and `/auth/google/callback` routes in `google_oauth.py`
are for Google CALENDAR connection (stores OAuth tokens for Calendar API calls). These are a different
OAuth flow — do not conflate them. The new sign-in routes should live in `auth.py`.

**Configuration required (no code changes, just dashboard setup):**
- Supabase Dashboard: Authentication > Providers > Enable Google, add Client ID + Secret
- Google Cloud Console: Add Supabase callback URL to Authorized Redirect URIs
  - Format: `https://<project-ref>.supabase.co/auth/v1/callback`
- Add `/auth/google/signin-callback` to Supabase's allowed redirect URLs

**Frontend change:** Add "Sign in with Google" button that calls `GET /auth/google/signin`
then redirects to the returned URL. Handle `/auth/google/signin-callback` as a public route
in React Router that reads the access_token from the response and stores it.

---

### 3. Password Reset via Email Link

**What:** "Forgot password?" link → email with reset link → new password form.

**Add: Nothing new — Supabase Python SDK handles this end-to-end**

`supabase.auth.reset_password_for_email()` sends the email automatically via Supabase's
built-in email infrastructure. No Resend call needed here — Supabase sends the reset email.

**Flow:**

```
1. User clicks "Forgot password?" on /login
2. Frontend: POST /auth/reset-password { email }
3. Backend: supabase.auth.reset_password_for_email(email, {"redirect_to": "https://yourdomain.com/update-password"})
           → Supabase sends email with link; no return value needed
4. Frontend: shows "Check your email" message
5. User clicks link → browser opens yourdomain.com/update-password?access_token=...
6. Frontend /update-password: reads access_token from URL, shows new-password form
7. Frontend: POST /auth/update-password { new_password, access_token }
8. Backend: uses provided access_token as Bearer JWT, calls supabase.auth.update_user({"password": new_password})
```

**Two new FastAPI routes needed (no new packages):**

```python
# POST /auth/reset-password { email: str }
# Calls supabase.auth.reset_password_for_email(email, redirect_to=...)
# Returns 200 always (don't reveal whether email exists)

# POST /auth/update-password { new_password: str }
# Authenticated endpoint — uses the reset-link access_token as Bearer
# Calls supabase.auth.update_user({"password": new_password})
```

**One new frontend page needed:** `/update-password` — a public route (not behind ProtectedRoute)
that parses the `access_token` from the URL hash (Supabase appends it as `#access_token=...`),
displays a new-password form, and POSTs to `/auth/update-password`.

**Configuration required:**
- Supabase Dashboard: Add `https://yourdomain.com/update-password` to
  Authentication > Redirect Configuration > Allowed Redirect URLs
- Supabase's default email template for password reset is used as-is; customization is optional

---

### 4. Admin Analytics Dashboard

**What:** `/admin` page showing active users, messages sent, photos generated, subscriptions,
revenue over time. Read-only. Visible only to admins.

**Add: `recharts` on frontend (one new package)**

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `recharts` | `^3.7.0` | Line/bar charts for the `/admin` dashboard page | React-native SVG library, composable components, works with React 19 (peer dep accepts `^18.0.0 \|\| ^19.0.0`), no separate D3 install, ~350kb unparsed (acceptable for admin-only page), latest stable as of 2026-02-xx. |

**Architecture (no external analytics SaaS):**

The data already lives in Supabase PostgreSQL. Build on what exists.

**Step 1 — Event tracking table (new Supabase migration):**

```sql
CREATE TABLE analytics_events (
  id          bigserial PRIMARY KEY,
  user_id     uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  event_type  text NOT NULL,  -- 'message_sent', 'photo_generated', 'subscription_created', etc.
  created_at  timestamptz DEFAULT now(),
  metadata    jsonb DEFAULT '{}'
);
-- No RLS — admin-only access via service role
CREATE INDEX idx_analytics_events_type_time ON analytics_events(event_type, created_at);
```

**Step 2 — Backend inserts events** via `supabase_admin` (already exists in `database.py`) at
existing code points: message handler, image pipeline completion, Stripe webhook handler.

**Step 3 — FastAPI analytics routes** under `GET /admin/analytics/*`, protected by admin check.
Routes return pre-aggregated JSON (daily counts, totals). No heavy SQL in the browser.

**Step 4 — Admin role gate** using Supabase `app_metadata`:

```python
# Set admin role server-side only (never from frontend)
# supabase_admin.auth.admin.update_user_by_id(user_id, {"app_metadata": {"role": "admin"}})

# FastAPI dependency
def require_admin(user_data = Depends(get_current_user)):
    role = (user_data.get("app_metadata") or {}).get("role")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user_data
```

`app_metadata` is set only by the service role key (cannot be self-elevated by users).
It is embedded in the Supabase JWT, so `get_current_user()` already decodes it — no extra
database call needed to check the role.

**Step 5 — Frontend `/admin` route**: New React page behind `ProtectedRoute` + admin flag check.
Calls `/admin/analytics/*` endpoints, renders summary cards + Recharts line/bar charts.

**What NOT to add for analytics:**
- PostHog / Mixpanel / Amplitude — external analytics SaaS adds vendor dependency and
  pricing risk; custom events table in existing Supabase is sufficient for a usage dashboard
- PostHog self-hosted — requires ClickHouse + Kafka, massive ops overhead for a usage dashboard
- Grafana — separate infra to run and maintain; overkill for 4-5 metrics

---

### 5. VPS Production Deployment

**What:** Deploy to Hetzner or DigitalOcean VPS with Docker Compose, custom domain, HTTPS.

**Add: `jonasal/nginx-certbot` Docker image (replaces bare `nginx` in docker-compose.yml)**

| Technology | Version/Spec | Purpose | Why |
|------------|-------------|---------|-----|
| Hetzner CX32 | 4 vCPU, 8 GB RAM, 80 GB SSD, ~€6.80/mo | VPS host | Best EUR/resource ratio for EU deployment; GDPR-friendly; 20 TB bandwidth included; CX32 gives headroom for all Docker services (FastAPI + Redis + nginx + BullMQ workers) without OOM risk. CX22 (4 GB) is too tight for concurrent image generation queue bursts. |
| `jonasal/nginx-certbot` | latest (v3.x) | nginx + auto-renewing Let's Encrypt SSL as a single Docker image | Eliminates the brittle Certbot-sidecar + shared-volume pattern. Handles initial certificate issuance, 12h renewal loop, and nginx reload on renewal — all internally. Drop-in replacement for the bare `nginx` image. |

**docker-compose.yml change (minimal):**

```yaml
# Replace:
#   image: nginx:latest
# With:
nginx:
  image: jonasal/nginx-certbot:latest
  environment:
    - CERTBOT_EMAIL=ops@yourdomain.com
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx/conf.d:/etc/nginx/user_conf.d:ro
    - nginx_secrets:/etc/letsencrypt
  restart: unless-stopped

volumes:
  nginx_secrets:
```

**nginx config change:** The `jonasal/nginx-certbot` image expects server config files in
`/etc/nginx/user_conf.d/` (not `/etc/nginx/conf.d/`). Rename the mount point in the volume
and update the nginx config to listen on 443 with `ssl_certificate` paths pointing to
`/etc/letsencrypt/live/yourdomain.com/fullchain.pem`.

**VPS setup checklist (ops, not code):**
1. Create CX32 on Hetzner, choose Ubuntu 24.04
2. `apt install docker.io docker-compose-plugin`
3. Point domain A record to VPS IP (must propagate before first deploy — Certbot needs HTTP-01)
4. Open firewall: ports 22 (SSH), 80 (HTTP/Certbot), 443 (HTTPS). Block 6379 (Redis — internal only).
5. `git clone` repo, create `.env` with all production secrets
6. `docker compose up -d` — jonasal/nginx-certbot issues certificate on first boot

**No new Python or npm packages required.**

**What NOT to use:**
- Hetzner CX22 (4 GB RAM) — too tight; risks OOM during image generation queue bursts
- Traefik as reverse proxy — adds complexity; existing nginx config is battle-tested
- Separate Certbot sidecar container — requires nginx-reload hooks and shared volumes;
  jonasal/nginx-certbot handles this internally
- DigitalOcean for EU users — more expensive per spec (~$24/mo for 4 GB vs €6.80 Hetzner CX32)

---

### 6. Landing Page

**What:** Public-facing marketing page at `/` — hero, features, pricing, Sign Up CTA.

**Add: Nothing new — use existing React/Vite/Tailwind stack**

The landing page is a new React route using components already available.

| Technology | Version | Why Sufficient |
|------------|---------|----------------|
| React Router `<Route path="/">` | already v7.13.1 | Add a public route; redirect authenticated users to `/chat` |
| Tailwind v4 | already v4.2.1 | Existing design system; all landing page UI buildable with utility classes |
| React 19 | already v19.2.0 | Component-based landing page sections |

**Pattern:**

```tsx
// App.tsx addition
<Route path="/" element={<LandingPage />} />

// LandingPage.tsx: if user is logged in, redirect to /chat
function LandingPage() {
  const token = useAuthStore(s => s.token)
  if (token) return <Navigate to="/chat" replace />
  return <main>...</main>
}
```

**Framer Motion: only add if Figma spec requires it.** Tailwind's `transition`, `duration-*`,
`animate-*` utilities cover standard landing page animations (fade-in, slide-in). Framer Motion
adds ~100kb gzipped — only justified if the Figma design requires complex scroll-triggered
or gesture-based animations that Tailwind cannot express. Decide at build time, not now.

**What NOT to add preemptively:**
- Framer Motion — add only if Figma design requires it
- Next.js — would require a full SPA-to-SSR migration; not worth it for v1.1; SEO is
  secondary for a gated adult product requiring age verification
- Separate static site (Astro, Eleventy) — unnecessary split; one repo, one deploy

---

## Installation Commands

```bash
# Backend: add to requirements.txt
# resend>=2.23.0

pip install "resend>=2.23.0"

# Frontend: admin analytics charts (only new npm package)
npm install recharts@^3.7.0
```

**All other v1.1 features (Google OAuth, password reset, landing page, VPS deployment) require
zero new packages.** They are solved by existing libraries + Supabase configuration changes.

---

## Alternatives Considered

| Feature | Recommended | Alternative | Why Not |
|---------|-------------|-------------|---------|
| Transactional email | Resend | SendGrid | Heavier SDK, more dashboard config, no meaningful deliverability advantage at this volume |
| Transactional email | Resend | fastapi-mail + SMTP | Adds SMTP server setup/config; API service is simpler and more reliable |
| Transactional email | Resend | Supabase built-in email | Supabase email has rate limits (3/hr on free plan); Resend bypasses this for transactional volume |
| Analytics | Custom events table | PostHog cloud | External vendor dependency; PostHog free tier is 1M events/mo but adds external data dependency |
| Analytics | Custom events table | PostHog self-hosted | Requires ClickHouse + Kafka — disproportionate ops for a usage dashboard |
| Analytics charts | Recharts | Chart.js (react-chartjs-2) | Chart.js is canvas-based; Recharts SVG integrates better with React 19 declarative patterns |
| Analytics charts | Recharts | Tremor (built on Recharts) | Tremor adds opinionated component wrappers; direct Recharts is simpler for a bespoke dashboard |
| VPS | Hetzner CX32 | DigitalOcean 4 GB ($24/mo) | Hetzner is ~3x cheaper per spec in EUR |
| SSL | jonasal/nginx-certbot | Certbot sidecar + hooks | Sidecar requires nginx reload hooks and shared volume management; jonasal handles internally |
| Landing page animations | Tailwind utilities | Framer Motion | ~100kb bundle cost; justify only if Figma design requires scroll-triggered animations |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `@supabase/supabase-js` (frontend) | Creates dual auth paths — frontend bypasses FastAPI proxy, breaks existing JWT flow | Keep existing proxy: frontend → FastAPI → Supabase Python SDK |
| `fastapi-mail` | SMTP config complexity for something Resend handles via HTTP API | `resend` Python SDK |
| `react-admin` framework | Designed for CRUD entity management, not read-only analytics; heavy dependency | Custom React page + Recharts |
| PostHog / Mixpanel / Amplitude | External analytics vendor for what is a simple 4-metric usage dashboard | `analytics_events` table in existing Supabase PostgreSQL |
| Traefik | Extra learning curve over existing nginx that is already battle-tested | Keep nginx, swap bare image for `jonasal/nginx-certbot` |
| Next.js | Full SPA migration for no meaningful SEO gain on a gated adult product | Existing Vite + React Router SPA |
| Framer Motion | 100kb+ for animations Tailwind utilities cover | Tailwind `transition`, `animate-*` (add Framer only if Figma requires it) |
| `python-social-auth` | Django-centric; overkill when Supabase handles provider integration | Supabase Python SDK `sign_in_with_oauth` |
| `google-auth-oauthlib` for sign-in | Already used for Calendar OAuth; conflating Calendar token storage with sign-in JWT is a bug waiting to happen | Supabase Python SDK `sign_in_with_oauth` (separate route from Calendar flow) |

---

## Version Compatibility

| Package | Version | Compatible With | Notes |
|---------|---------|-----------------|-------|
| `resend` | `^2.23.0` | Python >=3.7, FastAPI >=0.115 | Sync API; wrap in `asyncio.to_thread` or use BackgroundTasks for non-blocking calls |
| `recharts` | `^3.7.0` | React `^18.0.0 \|\| ^19.0.0` | React 19 peer dep confirmed; project uses React 19.2.0 — compatible |
| `jonasal/nginx-certbot` | latest (v3.x) | Docker Compose v2, nginx 1.25+ | Volume mount path is `/etc/nginx/user_conf.d/` (not `/etc/nginx/conf.d/`) |
| Supabase Python SDK | `2.25.1` (already installed) | Python 3.12 | `sign_in_with_oauth` and `reset_password_for_email` available — no upgrade needed |
| Stripe (already installed) | pinned | Python 3.12 | Customer portal session creation uses existing `stripe` lib — no new package |

---

## New Environment Variables Required

| Variable | Feature | Where Set |
|----------|---------|-----------|
| `RESEND_API_KEY` | Transactional email | `.env` + VPS secrets |
| `RESEND_FROM_ADDRESS` | Transactional email | `.env` + VPS secrets (e.g., `Ava <hello@yourdomain.com>`) |
| `GOOGLE_OAUTH_CLIENT_ID` | Google Sign-In (Supabase Dashboard) | Supabase Dashboard only — not in FastAPI env |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google Sign-In (Supabase Dashboard) | Supabase Dashboard only — not in FastAPI env |
| `CERTBOT_EMAIL` | SSL certificate renewal notifications | `docker-compose.yml` env block |

---

## Sources

- [Resend PyPI — v2.23.0, released 2026-02-23](https://pypi.org/project/resend/) — HIGH confidence
- [Resend FastAPI integration](https://resend.com/docs/send-with-fastapi) — BackgroundTasks pattern MEDIUM confidence
- [Supabase Google OAuth docs](https://supabase.com/docs/guides/auth/social-login/auth-google) — setup steps HIGH confidence
- [Supabase Python: signInWithOAuth](https://supabase.com/docs/reference/python/auth-signinwithoauth) — method available HIGH confidence
- [Supabase Python: resetPasswordForEmail](https://supabase.com/docs/reference/python/auth-resetpasswordforemail) — email sent by Supabase HIGH confidence
- [Supabase RBAC: app_metadata](https://supabase.com/docs/guides/database/postgres/custom-claims-and-role-based-access-control-rbac) — admin role via app_metadata HIGH confidence
- [Recharts npm — v3.7.0, React 18/19 peer dep](https://recharts.org) — version MEDIUM confidence (multiple WebSearch sources agree)
- [jonasal/nginx-certbot GitHub](https://github.com/JonasAlfredsson/docker-nginx-certbot) — auto-renewing SSL MEDIUM confidence
- [Hetzner CX32 specs](https://www.hetzner.com/cloud) — €6.80/mo, 4 vCPU, 8 GB RAM MEDIUM confidence (pricing subject to April 2026 adjustment)
- [Stripe Customer Portal](https://docs.stripe.com/customer-management/integrate-customer-portal) — no new packages, existing `stripe` lib sufficient HIGH confidence

---
*Stack research for: Ava v1.1 Launch Ready — new capability additions only*
*Researched: 2026-03-02*
