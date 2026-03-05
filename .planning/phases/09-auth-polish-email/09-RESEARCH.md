# Phase 9: Auth Polish & Email - Research

**Researched:** 2026-03-05
**Domain:** Supabase Google OAuth (PKCE/implicit), Supabase password reset, Resend transactional email, Supabase send-email auth hook
**Confidence:** HIGH (core stack verified against official Supabase and Resend docs)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Google Sign-In placement**
- Google button appears on BOTH the login page AND the signup page
- Button placed ABOVE the email/password form with an "or" divider below it
- After successful Google sign-in (new or returning), user lands on /chat

**Account collision (existing email+password user tries Google)**
- Auto-link accounts silently — Supabase merges the Google identity into the existing account
- User lands on /chat as normal — no prompt, no confirmation step, no duplicate user created

**Email format & tone**
- Simple HTML with brand colors — logo/wordmark, minimal layout, no heavy design system
- Tone: warm but concise — first-name greeting, short sentences, no corporate jargon
- Consistent template across all transactional emails (welcome, reset, receipt, cancellation)

**Welcome email**
- Content: warm welcome message + single "Start chatting" CTA button linking to /chat
- No feature dump — brief and inviting, not an onboarding guide
- Triggered for ALL new account creation regardless of auth method (email/password AND Google)

**Payment receipt email**
- Content: subscription confirmed + amount charged + next billing date + "Manage billing" link
- Clean, transactional, legally safe format

**Cancellation confirmation email**
- Content: subscription cancelled + access-until date + re-subscribe link
- Retention-friendly without being pushy

**Password reset**
- Unregistered email: returns identical success message as registered email — "If an account exists with this email, a reset link has been sent" — no email enumeration
- Expired/used reset link: dedicated error page with direct link back to the forgot-password form

**Auth error states**
- Google OAuth failure (popup blocked, cancelled, permissions denied): inline error below the Google button — "Google sign-in was cancelled. Try again or use email/password."
- Email/password login attempt on a Google-only account (no password set): specific error — "This account was created with Google. Please sign in with Google." — with Google button shown inline

**Google-only accounts (no password)**
- "Forgot password" link is hidden or disabled for users who signed up via Google
- Show "Sign in with Google" as their auth path instead

**Email send failure handling**
- One automatic retry after a short delay on any send failure
- If retry also fails: log the failure server-side, do NOT block the user action (auth/payment still succeeds)

### Claude's Discretion
- Exact retry delay duration
- Error logging format and destination
- Specific button/divider styling (match existing UI patterns)
- Password reset email copy
- Exact error message wording (within the intent above)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AUTH-01 | User can sign in and sign up with Google (one-click OAuth via Supabase) | Supabase `signInWithOAuth` with `provider: 'google'`, PKCE/implicit flow via `@supabase/supabase-js`; Supabase Dashboard Google provider config; auto-linking handles email collision |
| AUTH-02 | User can reset a forgotten password via an email link | Supabase `reset_password_for_email()` Python SDK (backend endpoint); `resetPasswordForEmail()` JS (if done frontend-only); send-email hook delivers the link via Resend; update-password page calls `updateUser({password})` |
| EMAI-02 | User receives a welcome email after signing up | Supabase send-email hook fires on `email_action_type: "signup"` — OR — dedicated backend endpoint called from `auth.py` signup handler after `supabase_client.auth.sign_up()` succeeds; Resend Python SDK sends the email |
| EMAI-03 | Subscriber receives a receipt email after a successful Stripe payment | `billing.py` webhook handler already fires on `checkout.session.completed` event; add Resend email call in `activate_subscription()` in `services/billing/subscription.py` |
| EMAI-04 | Cancelling user receives a confirmation email after cancellation | `billing.py` webhook fires on `customer.subscription.deleted`; add Resend email call in `deactivate_subscription()` when status becomes "canceled" |
</phase_requirements>

---

## Summary

This phase adds Google OAuth sign-in, password reset via email link, and three transactional emails (welcome, receipt, cancellation) to an existing FastAPI + React + Supabase + Resend stack that is fully deployed to production at avasecret.org.

The architecture is split across two layers. The **frontend** gains a `@supabase/supabase-js` client (this is the one-time exception documented in STATE.md) to drive the Google OAuth implicit flow: `signInWithOAuth({ provider: 'google' })` redirects to Google, then Supabase redirects back to the SPA where `detectSessionInUrl: true` (default) causes the JS library to auto-extract and store the session from the URL fragment. The backend gains a **Supabase send-email auth hook** — a new FastAPI endpoint that Supabase calls (via HTTPS webhook) whenever it would otherwise send an auth email (signup confirmation, password reset). That endpoint uses `standardwebhooks` (Python 1.0.1) for HMAC signature verification, then dispatches through the **Resend Python SDK v2.23.0** (`pip install resend`). Transactional billing emails (receipt, cancellation) are called directly inside the existing `billing.py` webhook handler, which already fires at the right moments.

The single most important decision to get right before writing any code: Supabase's **automatic identity linking** is ON by default. When a user who originally signed up with email+password tries Google with the same email, Supabase silently merges the identities — no extra code needed, but the email must already be marked as verified in Supabase. The STATE.md note "email_collision_migration must run before Google Sign-In button is enabled" is a pre-requisite task.

**Primary recommendation:** Install `@supabase/supabase-js` on the frontend (VITE_SUPABASE_URL + VITE_SUPABASE_ANON_KEY env vars already noted in STATE.md); add `resend` + `standardwebhooks` to backend/requirements.txt; wire the Supabase send-email hook to a new FastAPI endpoint; call Resend directly from the billing webhook handler for receipt/cancellation emails.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @supabase/supabase-js | ^2.x (latest) | Google OAuth on frontend; password reset redirect | Official Supabase JS client; only way to call `signInWithOAuth` from a browser SPA |
| resend (Python) | v2.23.0 (Feb 2026) | Send transactional emails from FastAPI | Already in production config (RESEND_API_KEY, RESEND_FROM_ADDRESS wired in Phase 8); Resend domain verified with 10/10 mail-tester score |
| standardwebhooks (Python) | 1.0.1 | Verify HMAC signature on Supabase auth hook calls | Official library referenced in Supabase docs for send-email hook verification; prevents unauthenticated calls to the hook endpoint |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-hmac (stdlib) | built-in | Fallback HMAC comparison if standardwebhooks not used | Only if standardwebhooks proves problematic; prefer standardwebhooks for replay-attack protection |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Supabase send-email hook for welcome email | Call Resend directly from `auth.py` signup handler | Direct call is simpler (no hook setup) but misses Google-signup welcome emails unless you also instrument that path; hook catches both |
| Supabase send-email hook for password reset | Supabase built-in SMTP (custom SMTP config) | Built-in SMTP config is simpler but gives less control over template; hook + Resend is what we already have for other emails |
| `resend` Python SDK | `httpx.AsyncClient` posting to Resend REST API | Raw httpx call is async-native but more code; `resend.Emails.send()` is synchronous but wrappable with `asyncio.to_thread` (established pattern in this codebase) |

**Installation:**

```bash
# Backend
pip install resend standardwebhooks

# Frontend (in frontend/ directory)
npm install @supabase/supabase-js
```

---

## Architecture Patterns

### Recommended Project Structure (additions only)

```
frontend/src/
├── lib/
│   └── supabaseClient.ts       # createClient(VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY)
├── components/
│   └── GoogleSignInButton.tsx  # Reusable Google button (used on Login + Signup pages)
├── pages/
│   ├── LoginPage.tsx           # + Google button above form, error states
│   ├── SignupPage.tsx          # + Google button above form
│   ├── ForgotPasswordPage.tsx  # New: email input -> calls POST /auth/forgot-password
│   └── ResetPasswordPage.tsx   # New: new-password form -> calls POST /auth/reset-password
backend/app/
├── routers/
│   └── auth.py                 # + POST /auth/forgot-password, POST /auth/reset-password
│                               # + POST /auth/send-email-hook (Supabase HTTPS hook endpoint)
├── services/
│   └── email/
│       ├── __init__.py
│       └── resend_client.py    # send_email(to, subject, html) wrapper with retry logic
```

### Pattern 1: Google OAuth Implicit Flow for SPA (No Callback Route Needed)

**What:** Browser calls `supabase.auth.signInWithOAuth({ provider: 'google' })`, Supabase redirects to Google, Google redirects back to `https://avasecret.org/` with tokens in the URL fragment. The `@supabase/supabase-js` client, initialized with `detectSessionInUrl: true` (the default), automatically reads the fragment and stores the session in localStorage.

**When to use:** Pure SPA with no server-side rendering. The existing architecture (React + Vite + no SSR) fits this exactly.

**Critical note:** This is the **implicit flow**, NOT PKCE. For a pure SPA where the callback is handled entirely client-side, implicit flow is simpler and appropriate. PKCE flow requires a server-side callback route to call `exchangeCodeForSession()`. Since there is no Next.js or server-side rendering, use implicit flow.

**Example:**

```typescript
// Source: https://supabase.com/docs/guides/auth/social-login/auth-google
// frontend/src/lib/supabaseClient.ts
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
  {
    auth: {
      detectSessionInUrl: true,   // default: true — auto-processes OAuth redirect fragments
      persistSession: true,        // stores tokens in localStorage
      autoRefreshToken: true,      // refreshes before expiry
    }
  }
)

// In GoogleSignInButton.tsx
async function handleGoogleSignIn() {
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: 'https://avasecret.org/',   // must be whitelisted in Supabase Dashboard
    }
  })
  if (error) setError('Google sign-in was cancelled. Try again or use email/password.')
}
```

**Post-OAuth session extraction:** After redirect, `supabase.auth.getSession()` returns the session. Extract the `access_token` and `user.id` from it and call `setAuth()` in the Zustand store — same store shape as the existing email/password flow.

### Pattern 2: Supabase Send-Email Auth Hook (FastAPI endpoint)

**What:** Supabase calls a registered HTTPS endpoint for every auth email event (signup confirmation = `email_action_type: "signup"`, password reset = `"recovery"`). The endpoint verifies the HMAC signature using `standardwebhooks`, then sends via Resend.

**When to use:** For all Supabase auth-triggered emails (password reset link, and optionally the signup welcome email via the "signup" action type).

**Example:**

```python
# Source: https://supabase.com/docs/guides/auth/auth-hooks/send-email-hook
# backend/app/routers/auth.py  (new endpoint added to existing auth router)

import hmac
import base64
from standardwebhooks.webhooks import Webhook
from fastapi import Request, HTTPException

@router.post("/send-email-hook")
async def supabase_send_email_hook(request: Request):
    """
    HTTPS hook called by Supabase whenever it needs to send an auth email.
    Verifies HMAC signature, then sends via Resend based on email_action_type.
    Must return 200 empty JSON on success; 401 on verification failure.
    """
    raw_body = await request.body()
    headers = dict(request.headers)

    # Verify HMAC (standardwebhooks uses webhook-id, webhook-timestamp, webhook-signature headers)
    hook_secret = settings.supabase_hook_secret.replace("v1,whsec_", "")
    wh = Webhook(hook_secret)
    try:
        payload = wh.verify(raw_body, headers)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    user = payload["user"]
    email_data = payload["email_data"]
    action_type = email_data.get("email_action_type")
    user_email = user["email"]
    token = email_data.get("token")
    redirect_to = email_data.get("redirect_to", settings.frontend_url)

    if action_type == "signup":
        # Welcome email — warm, single CTA
        await send_welcome_email(user_email, user.get("user_metadata", {}).get("full_name"))
    elif action_type == "recovery":
        # Password reset email — link includes token_hash
        reset_url = f"{redirect_to}?token={token}&type=recovery"
        await send_password_reset_email(user_email, reset_url)

    return {}
```

### Pattern 3: Resend Email Service Wrapper

**What:** A thin service module wrapping `resend.Emails.send()` (which is synchronous) in `asyncio.to_thread()` — the established pattern in this codebase for synchronous SDK calls inside async FastAPI handlers (see Phase 4 decision: "asyncio.to_thread() wraps synchronous Google Auth calls").

**Example:**

```python
# Source: https://resend.com/docs/send-with-python + codebase pattern (Phase 4 decision)
# backend/app/services/email/resend_client.py

import asyncio
import logging
import resend
from app.config import settings

logger = logging.getLogger(__name__)

resend.api_key = settings.resend_api_key


async def send_email(to: str, subject: str, html: str, retry: bool = True) -> bool:
    """
    Send a transactional email via Resend. Returns True on success.
    On failure: retries once (per CONTEXT.md decision), then logs and returns False.
    Non-blocking — caller must NOT raise on False (per CONTEXT.md: email failure
    must not block the user action).
    """
    params: resend.Emails.SendParams = {
        "from": settings.resend_from_address,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    try:
        await asyncio.to_thread(resend.Emails.send, params)
        return True
    except Exception as e:
        logger.error(f"Email send failed for {to}: {e}")
        if retry:
            # One automatic retry (CONTEXT.md: exact delay is Claude's discretion → 3s)
            await asyncio.sleep(3)
            return await send_email(to, subject, html, retry=False)
        return False
```

### Pattern 4: Password Reset Flow (Two-Stage)

**Stage 1 — Request reset (frontend calls backend):**

```python
# backend/app/routers/auth.py
@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    """
    Always returns 200 with identical message (no email enumeration).
    Supabase's reset_password_for_email() silently does nothing for unregistered emails.
    """
    try:
        supabase_client.auth.reset_password_for_email(
            body.email,
            options={"redirect_to": f"{settings.frontend_url}/reset-password"}
        )
    except Exception as e:
        logger.warning(f"Password reset error (suppressed): {e}")
    # Always return same response — prevents email enumeration (CONTEXT.md decision)
    return {"message": "If an account exists with this email, a reset link has been sent"}
```

**Stage 2 — Submit new password (frontend, on /reset-password page):**

```typescript
// frontend/src/pages/ResetPasswordPage.tsx
// After redirect with #access_token in fragment, supabase-js auto-detects the recovery session
// Then user submits new password:
const { error } = await supabase.auth.updateUser({ password: newPassword })
if (!error) navigate('/login')
```

### Pattern 5: Billing Email Triggers

**What:** Resend emails are called directly from the existing billing webhook handler, inside the events that already fire correctly.

```python
# backend/app/routers/billing.py — additions to existing stripe_webhook handler

if event_type == "checkout.session.completed":
    user_id = data.get("metadata", {}).get("user_id")
    if user_id:
        await activate_subscription(...)
        # EMAI-03: receipt email
        user_email = data.get("customer_details", {}).get("email")
        amount = data.get("amount_total", 0) / 100  # Stripe amounts are in cents
        if user_email:
            await send_receipt_email(user_email, amount, ...)

elif event_type == "customer.subscription.deleted":
    sub_id = data.get("id")
    period_end = data.get("current_period_end")  # Unix timestamp
    if sub_id:
        await deactivate_subscription(sub_id, new_status="canceled")
        # EMAI-04: cancellation confirmation email
        # Need to look up user email from subscriptions table via sub_id
        await send_cancellation_email(user_email, period_end)
```

**Note:** The billing webhook receives `customer_details.email` in `checkout.session.completed` events. For `customer.subscription.deleted`, the email must be fetched from the `subscriptions` table by `stripe_subscription_id` using `supabase_admin`.

### Anti-Patterns to Avoid

- **Do not use PKCE flow for this SPA:** PKCE requires a server-side callback route to exchange the code. This SPA has no SSR. Use implicit flow with `detectSessionInUrl: true`.
- **Do not block user actions on email failure:** CONTEXT.md is explicit — auth succeeds and billing succeeds regardless of email send outcome. The `send_email()` wrapper must never raise to callers.
- **Do not create a separate Supabase client in the backend for Google OAuth:** The frontend drives the OAuth flow entirely via `@supabase/supabase-js`. The backend never touches Google OAuth sign-in — it only handles its own auth endpoints.
- **Do not call `resend.Emails.send()` in an `async def` function without `asyncio.to_thread`:** The Resend Python SDK v2.23.0 is synchronous (no async support). Calling it directly blocks the FastAPI event loop. Use `asyncio.to_thread()` (established pattern in this codebase).
- **Do not mix the Google Calendar OAuth flow with Google Sign-In OAuth:** `google_oauth.py` is for Calendar credential storage (server-side). The new Google Sign-In uses `@supabase/supabase-js` client-side. These are completely separate flows.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HMAC webhook signature verification | Custom HMAC comparison code | `standardwebhooks` Python 1.0.1 | Handles replay-attack protection (timestamp check) beyond basic HMAC comparison; same library used in Supabase's official docs |
| OAuth token exchange | Custom Google OAuth2 code | `supabase.auth.signInWithOAuth({ provider: 'google' })` | Supabase manages PKCE code verifier, token storage, refresh — don't re-implement |
| Email delivery with retry | Custom SMTP client | Resend Python SDK | Resend domain already verified (10/10 mail-tester), API key already in production env |
| Google identity auto-linking | Custom user merge logic | Supabase handles automatically | Supabase Auth automatically links identities with same verified email — no application code needed |
| Password reset token generation | Custom token/link generation | `supabase_client.auth.reset_password_for_email()` | Supabase handles token generation, expiry (5-minute validity), one-time use enforcement |

**Key insight:** Supabase handles the hardest parts of auth (token security, identity linking, session management). The application's job is to wire the hooks and surface the right UI states.

---

## Common Pitfalls

### Pitfall 1: Email Enumeration in Password Reset

**What goes wrong:** Endpoint returns different responses for registered vs unregistered emails (e.g., "user not found" vs "email sent"), allowing attackers to enumerate valid accounts.

**Why it happens:** Developers check if the user exists before calling the reset function and return an error for unknown emails.

**How to avoid:** Always call `supabase_client.auth.reset_password_for_email()` and always return the same success message. Supabase silently does nothing for unregistered emails — that behavior is exactly what you want.

**Warning signs:** Any branch in the forgot-password endpoint that returns a different HTTP status or message based on email lookup result.

### Pitfall 2: Google-Only Account Tries to Reset Password

**What goes wrong:** A user who signed up with Google sees the "Forgot password" link, requests a reset, and gets confused because they never had a password.

**How to avoid:** The frontend must detect whether the current user is Google-only before showing the forgot-password link. Check `user.identities` — if it contains only `{ provider: 'google', ... }` and no `{ provider: 'email', ... }`, hide the link and show "Sign in with Google" instead. Detection happens client-side after `supabase.auth.getUser()`.

**Warning signs:** A Google-only user who successfully receives a reset link can set a password, but then their `user_metadata.provider` still shows `google` — this is acceptable behavior (Supabase allows multi-identity accounts).

### Pitfall 3: Supabase Hook Secret Format

**What goes wrong:** The `standardwebhooks` library fails to verify signatures because the secret includes the `v1,whsec_` prefix.

**How to avoid:** Strip the prefix before passing to `Webhook()`:
```python
hook_secret = settings.supabase_hook_secret.replace("v1,whsec_", "")
wh = Webhook(hook_secret)
```

**Warning signs:** `401 Invalid webhook signature` errors on the hook endpoint even with the correct secret configured.

### Pitfall 4: OAuth Redirect URL Not Whitelisted in Supabase

**What goes wrong:** Google redirects back to `https://avasecret.org/` but Supabase rejects the redirect with "Redirect URL not allowed."

**How to avoid:** In Supabase Dashboard → Authentication → URL Configuration:
- **Site URL**: `https://avasecret.org`
- **Redirect URLs**: Add `https://avasecret.org/**` (wildcard covers all paths)

Also add the same domain to Google Cloud Console → OAuth 2.0 Client → Authorized JavaScript Origins and Authorized Redirect URIs.

**Warning signs:** OAuth flow starts (Google consent screen appears) but fails on redirect back.

### Pitfall 5: Welcome Email Not Firing for Google Sign-Ups

**What goes wrong:** The Supabase send-email hook's `signup` action type fires for email/password signups but NOT for OAuth signups (Google OAuth users bypass the email confirmation step).

**Root cause:** The `signup` action type in the send-email hook fires when Supabase sends a confirmation email to the user's inbox. Google OAuth users are auto-confirmed — Supabase doesn't need to send a confirmation email for them.

**How to avoid:** For Google sign-ups, trigger the welcome email via `onAuthStateChange` on the frontend — detect a `SIGNED_IN` event with `session.user.app_metadata.provider === 'google'` AND `session.user.created_at` close to now (within 60 seconds). Alternatively, add a FastAPI endpoint `POST /auth/send-welcome` that the frontend calls immediately after any successful signup (both email and Google), with idempotency guarded by checking if the user already received one (store a `welcome_email_sent` flag in `user_metadata`).

**Warning signs:** Email/password users get welcome emails; Google users never do.

### Pitfall 6: Resend SDK Blocking the Event Loop

**What goes wrong:** `resend.Emails.send()` blocks FastAPI's async event loop, causing latency spikes or timeouts under concurrent requests.

**How to avoid:** Always wrap in `asyncio.to_thread()`:
```python
await asyncio.to_thread(resend.Emails.send, params)
```

**Warning signs:** FastAPI endpoint response times increase when email sending is slow; concurrent requests queue up.

### Pitfall 7: Stripe Webhook Missing Customer Email for Cancellation

**What goes wrong:** The `customer.subscription.deleted` Stripe event doesn't always include the customer's email directly in the payload — it has `customer` (ID) and `id` (subscription ID) but not always the email.

**How to avoid:** When handling `customer.subscription.deleted`, look up the email from the local `subscriptions` table using `stripe_subscription_id`:
```python
result = supabase_admin.from_("subscriptions").select("user_id").eq(
    "stripe_subscription_id", sub_id
).limit(1).execute()
# Then get email from Supabase auth.users via supabase_admin.auth.admin.get_user_by_id()
```

**Warning signs:** Cancellation emails fail silently because `user_email` is None.

### Pitfall 8: Token Storage Conflict Between Existing Auth and New Supabase Client

**What goes wrong:** The new `@supabase/supabase-js` frontend client stores its session in localStorage under Supabase's own key, while the existing app stores the JWT in Zustand's `ava-auth` key. These conflict — after Google OAuth, the Supabase session is in localStorage but `useAuthStore.token` is still null.

**How to avoid:** After a successful Google OAuth login (detected via `supabase.auth.getSession()` on page load or `onAuthStateChange`), extract the `access_token` and `user.id` from the Supabase session and call `setAuth(access_token, user.id)` to populate the Zustand store. The existing `get_current_user` FastAPI dependency validates JWTs via `supabase_client.auth.get_user(token)` — Supabase-issued Google OAuth JWTs will validate correctly since they come from the same Supabase project.

**Warning signs:** After Google OAuth redirect, user is on `/` (or `/chat`) but `useAuthStore.token` is null and they get redirected to `/login`.

---

## Code Examples

Verified patterns from official sources:

### Google Sign-In Button Component

```typescript
// Source: https://supabase.com/docs/guides/auth/social-login/auth-google
// frontend/src/components/GoogleSignInButton.tsx

import { supabase } from '../lib/supabaseClient'

interface Props {
  onError: (msg: string) => void
}

export function GoogleSignInButton({ onError }: Props) {
  async function handleClick() {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/`,
      }
    })
    if (error) {
      onError('Google sign-in was cancelled. Try again or use email/password.')
    }
  }

  return (
    <button
      onClick={handleClick}
      className="w-full flex items-center justify-center gap-2 border border-gray-200 rounded-lg py-2 text-sm font-medium hover:bg-gray-50 transition-colors"
    >
      {/* Google's official SVG icon */}
      <svg width="18" height="18" viewBox="0 0 18 18">
        {/* ...Google G logo paths... */}
      </svg>
      Continue with Google
    </button>
  )
}
```

### Session Extraction After OAuth Redirect

```typescript
// Source: https://supabase.com/docs/guides/auth/sessions/implicit-flow
// frontend/src/lib/supabaseClient.ts  OR  in App.tsx useEffect

// After OAuth redirect, supabase-js auto-processes the URL fragment.
// Listen for the SIGNED_IN event to update Zustand store:
supabase.auth.onAuthStateChange((event, session) => {
  if (event === 'SIGNED_IN' && session) {
    const { access_token } = session
    const user_id = session.user.id
    setAuth(access_token, user_id)
    // Detect new Google signup for welcome email trigger:
    const isGoogle = session.user.app_metadata?.provider === 'google'
    const createdAt = new Date(session.user.created_at)
    const isNewUser = (Date.now() - createdAt.getTime()) < 60_000
    if (isGoogle && isNewUser) {
      fetch('/auth/send-welcome', {
        method: 'POST',
        headers: { Authorization: `Bearer ${access_token}` }
      })
    }
  }
})
```

### Resend Email with Retry Wrapper

```python
# Source: https://resend.com/docs/send-with-python (adapted with asyncio.to_thread pattern)
# backend/app/services/email/resend_client.py

import asyncio
import logging
import resend
from app.config import settings

logger = logging.getLogger(__name__)


def _sync_send(params: dict) -> dict:
    resend.api_key = settings.resend_api_key
    return resend.Emails.send(params)


async def send_email(to: str, subject: str, html: str, retry: bool = True) -> bool:
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not configured — email not sent")
        return False
    params: resend.Emails.SendParams = {
        "from": settings.resend_from_address,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    try:
        await asyncio.to_thread(_sync_send, params)
        logger.info(f"Email sent to {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Email send failed for {to} ({subject}): {e}")
        if retry:
            await asyncio.sleep(3)  # Claude's discretion: 3s retry delay
            return await send_email(to, subject, html, retry=False)
        return False
```

### Supabase Send-Email Hook Verification

```python
# Source: https://supabase.com/docs/guides/auth/auth-hooks/send-email-hook
# backend/app/routers/auth.py — new endpoint

from standardwebhooks.webhooks import Webhook

@router.post("/send-email-hook")
async def supabase_send_email_hook(request: Request):
    """
    HTTPS hook for Supabase auth emails. Handles: signup (welcome), recovery (password reset).
    Must return 200 {} on success; 401 on bad signature.
    """
    raw_body = await request.body()   # CRITICAL: read raw body before anything else
    headers = dict(request.headers)

    hook_secret = settings.supabase_hook_secret.replace("v1,whsec_", "")
    wh = Webhook(hook_secret)
    try:
        payload = wh.verify(raw_body.decode(), headers)
    except Exception as exc:
        logger.warning(f"Hook signature verification failed: {exc}")
        raise HTTPException(status_code=401, detail="Invalid hook signature")

    user = payload.get("user", {})
    email_data = payload.get("email_data", {})
    action_type = email_data.get("email_action_type")
    user_email = user.get("email")

    if not user_email:
        return {}

    if action_type == "recovery":
        token = email_data.get("token_hash")
        site_url = email_data.get("site_url", settings.frontend_url)
        reset_url = f"{site_url}/reset-password?token={token}&type=recovery"
        await send_password_reset_email(user_email, reset_url)
    elif action_type == "signup":
        # email+password signup confirmation doubles as welcome trigger
        first_name = user.get("user_metadata", {}).get("full_name", "").split()[0] or "there"
        await send_welcome_email(user_email, first_name)

    return {}
```

### Supabase Dashboard Config (non-code)

Required configuration steps in Supabase Dashboard before any code ships:

1. **Authentication → Providers → Google**: Enable Google, paste Client ID + Client Secret from Google Cloud Console
2. **Authentication → URL Configuration → Site URL**: `https://avasecret.org`
3. **Authentication → URL Configuration → Redirect URLs**: Add `https://avasecret.org/**`
4. **Authentication → Hooks → Send Email**: Set to HTTPS endpoint, URL = `https://avasecret.org/auth/send-email-hook`, generate + copy hook secret
5. **Google Cloud Console → OAuth 2.0 Clients → Authorized redirect URIs**: Add the Supabase callback URL shown in the Supabase Google provider page (format: `https://<project-ref>.supabase.co/auth/v1/callback`)

### New env vars needed in backend/.env and frontend/.env

```bash
# backend/.env  (new)
SUPABASE_HOOK_SECRET=v1,whsec_<generated-in-supabase-dashboard>

# frontend/.env  (new — already noted in STATE.md v1.1 roadmap decisions)
VITE_SUPABASE_URL=https://<project-ref>.supabase.co
VITE_SUPABASE_ANON_KEY=<anon-key-from-supabase-dashboard>
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Implicit flow (tokens in URL fragment) as default | PKCE recommended for SSR/Next.js | Supabase 2.0+ | For this pure SPA, implicit flow remains correct; PKCE adds complexity without benefit |
| Custom SMTP for auth emails | Supabase send-email hook + Resend | 2024 (auth hooks GA) | Full control over templates and deliverability; Resend already wired in this project |
| Separate Google identity per email | Automatic identity linking | Supabase Auth v2 | Same email from Google + password = merged account, no duplicate user |

**Deprecated/outdated:**
- `supabase.auth.session()`: Replaced by `supabase.auth.getSession()` in supabase-js v2
- `signIn()` with provider: Replaced by `signInWithOAuth()` in supabase-js v2
- Supabase built-in email templates for password reset: Still works but less control; send-email hook is the modern approach

---

## Open Questions

1. **Welcome email for Google OAuth users via the hook**
   - What we know: The Supabase send-email hook fires `email_action_type: "signup"` only for email/password signups (confirmation email step). Google OAuth users are auto-confirmed and may not trigger this hook.
   - What's unclear: Whether Supabase fires the signup hook for OAuth users at all. Documentation is not explicit on this point.
   - Recommendation: Implement the welcome email via two paths: (a) the hook for email/password signups, AND (b) a `POST /auth/send-welcome` endpoint called from the frontend `onAuthStateChange` handler for Google signups. Use `user_metadata.welcome_sent = true` flag (set via `supabase_admin.auth.admin.update_user_by_id()`) to ensure idempotency.

2. **Stripe customer email availability in `customer.subscription.deleted` event**
   - What we know: The `checkout.session.completed` event contains `customer_details.email`. The `customer.subscription.deleted` event contains `customer` (ID) and `subscription ID` but the email field availability varies.
   - What's unclear: Whether the email is consistently present in the deletion event.
   - Recommendation: For the cancellation email, look up `user_id` from the local `subscriptions` table using `stripe_subscription_id`, then fetch the user's email from Supabase via `supabase_admin.auth.admin.get_user_by_id(user_id).user.email`.

3. **`email_collision_migration` pre-requisite**
   - What we know: STATE.md notes "email_collision_migration must run before Google Sign-In button is enabled — marks all existing password-signup users as email-verified in Supabase." This migration does not yet exist.
   - What's unclear: Whether all existing users created via the `POST /auth/signup` endpoint already have `email_confirmed_at` set (the current signup handler doesn't require email confirmation — this is disabled in Supabase per `auth.py` comment).
   - Recommendation: Check Supabase Dashboard → Authentication → Users for whether `email_confirmed_at` is populated for existing users. If email confirmation is disabled (as the code comment suggests), existing users may already have confirmed emails. The migration may be a no-op, but must be verified before enabling Google Sign-In.

---

## Sources

### Primary (HIGH confidence)
- https://supabase.com/docs/guides/auth/social-login/auth-google — Google OAuth setup, signInWithOAuth, redirect URL config
- https://supabase.com/docs/guides/auth/sessions/implicit-flow — Implicit flow mechanics for SPA, detectSessionInUrl behavior
- https://supabase.com/docs/guides/auth/auth-hooks/send-email-hook — Hook payload structure, email_action_type values, HMAC verification pattern
- https://supabase.com/docs/guides/auth/auth-identity-linking — Automatic identity linking behavior, account collision handling
- https://supabase.com/docs/reference/python/auth-resetpasswordforemail — Python SDK password reset method
- https://resend.com/docs/send-with-python — Resend Python SDK installation and send method
- https://pypi.org/project/standardwebhooks/ — standardwebhooks 1.0.1, Webhook.verify() usage
- https://github.com/resend/resend-python — Resend Python SDK v2.23.0 (Feb 2026), sync-only, asyncio.to_thread required

### Secondary (MEDIUM confidence)
- https://supabase.com/docs/guides/auth/redirect-urls — Redirect URL whitelist configuration (verified against official docs)
- https://supabase.com/docs/guides/auth/sessions/pkce-flow — PKCE vs implicit flow tradeoffs (confirmed implicit appropriate for this SPA)

### Tertiary (LOW confidence — needs validation)
- Claim that Supabase send-email hook does NOT fire for Google OAuth signups (only email/password). This was inferred from the hook being described as intercepting "Supabase's built-in email sending" — OAuth users bypass the email confirmation step entirely. Needs verification by testing against the live Supabase project.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Supabase JS/Python SDKs, Resend, standardwebhooks all verified against official docs
- Architecture: HIGH — patterns derived from official Supabase hook documentation and existing codebase conventions
- Pitfalls: MEDIUM-HIGH — most verified against official docs; Pitfall 5 (Google welcome email hook gap) is MEDIUM (inferred, needs live test)

**Research date:** 2026-03-05
**Valid until:** 2026-04-05 (Supabase auth SDK stable; Resend SDK fast-moving but current as of Feb 2026 release)
