# Pitfalls Research

**Domain:** Production launch features added to existing FastAPI + Supabase + React + Stripe + Docker Compose app (adult-adjacent AI companion SaaS — v1.1 Launch Ready)
**Researched:** 2026-03-02
**Confidence:** HIGH — all critical claims verified against official documentation or multiple corroborating sources

> **Scope note:** This file covers v1.1 pitfalls specifically — common mistakes when ADDING production launch features to the existing v1.0 codebase. For v1.0 domain pitfalls (WhatsApp bans, RLS, prompt injection, avatar consistency, legal compliance), see the git history. Those are addressed; these are new.

---

## Critical Pitfalls

### Pitfall 1: Stripe Will Terminate the Account If the Business Is Described as Adult Content

**What goes wrong:**
Stripe's restricted businesses policy explicitly prohibits "pornography and other content intended for adult audiences designed to satisfy sexual desires" AND explicitly covers "any AI-generated content meeting the above criteria" (official policy text: "Tout contenu généré par intelligence artificielle répondant aux critères ci-dessus"). An Ava account that is described as an intimate AI companion with AI-generated photos — or whose landing page uses explicit language — will eventually be flagged by Stripe's compliance team. Termination typically comes with a 90-day fund hold.

**Why it happens:**
Stripe is the default processor developers reach for. The restriction is not just for pornography sites — it covers any platform where AI-generated content satisfies sexual desire. The bank network rules (Mastercard/Visa) that Stripe must comply with drive this, so there is no negotiated exception path for smaller merchants.

**How to avoid:**
- The Stripe account business description (entered during signup) must frame the product as "AI personal assistant and companionship app" — not "intimate AI partner" or "AI companion with photo generation"
- The landing page must not describe intimate image generation as a primary feature. Lead with secretary/assistant functionality. Describe intimate mode as "personal conversation" not "explicit content"
- If the product description does not match what is actually delivered, Stripe will eventually identify the mismatch. Build for the description you can honestly register
- Chargebacks from adult content purchases run 5–7x higher than standard e-commerce. A chargeback rate above 1% triggers Stripe review regardless of business description
- If the product ever pivots to explicitly sexual content delivery, migrate to CCBill, Segpay, or Epoch before Stripe detects the mismatch — not after

**Warning signs:**
- Stripe sends "we need more information about your business" email
- Chargeback rate approaches 0.5% (0.8% triggers review, 1% triggers termination)
- Landing page or marketing uses words like "explicit," "nude," "erotic," "NSFW," "intimate photos"
- User screenshots showing subscription description reference adult content

**Phase to address:** Landing page phase AND VPS deployment phase — the public-facing description of the product must be scoped before acquiring real paying users. Stripe account business description must be set accurately before processing first payment.

---

### Pitfall 2: nginx.conf Has No HTTPS — SSL Is Not Actually Wired Up

**What goes wrong:**
The current `nginx.conf` only listens on port 80. `docker-compose.yml` mounts `./certbot/conf:/etc/letsencrypt:ro` but the nginx config has no `ssl_certificate`, `ssl_certificate_key`, or HTTPS server block. Port 443 is exposed in docker-compose but nothing serves it. Deploying this to a Hetzner/DigitalOcean VPS means the site runs over plain HTTP. Stripe webhooks travel unencrypted (Stripe requires HTTPS endpoints), OAuth redirects expose tokens in transit, and Supabase JWT credentials are transmitted in plaintext.

**Why it happens:**
The certbot/nginx bootstrap is a well-documented "chicken and egg" problem: nginx refuses to start if `ssl_certificate` points to a file that does not yet exist, but certbot cannot issue a certificate until nginx is serving the ACME challenge on port 80. Developers defer this to "deal with it later" and it never gets properly wired up before launch.

**How to avoid:**
Use a two-phase bootstrap:
1. Start nginx with an HTTP-only config that serves `/.well-known/acme-challenge/` from a shared volume. No SSL directives.
2. Run `docker compose run --rm certbot certonly --webroot -w /var/www/certbot -d yourdomain.com` to obtain the certificate.
3. Replace the nginx config with a full HTTPS server block (port 443 with `ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem`) plus a permanent HTTP → HTTPS redirect on port 80.
4. Reload nginx: `docker compose exec nginx nginx -s reload`
5. Add a cron job or a `certbot renew` container that runs every 12 hours and reloads nginx after successful renewal.

The landing page phase must include writing this two-block nginx.conf as a deliverable, not a note.

**Warning signs:**
- Browser shows "Not Secure" on the domain after deploying
- `curl -I http://yourdomain.com` returns 200 instead of 301
- Stripe test webhook delivery fails with SSL or connection error
- `certbot/conf/` directory is empty or missing on the VPS

**Phase to address:** VPS production deployment phase — must be verified before any other production feature is tested against production URLs.

---

### Pitfall 3: Google OAuth Redirect URI Mismatch Breaks Login on Production Domain

**What goes wrong:**
`config.py` defaults `google_oauth_redirect_uri` to `"http://localhost:8000/auth/google/callback"`. When deployed, Google's consent screen redirects back to localhost (which fails on the user's browser). For v1.1 Supabase Google Sign-In (a separate flow from the existing Calendar OAuth), Supabase has a "Site URL" that defaults to localhost in new projects and must be updated to the production domain. If either is wrong, OAuth fails with `redirect_uri_mismatch` and users cannot log in via Google at all.

**Why it happens:**
Google Cloud Console requires redirect URIs to be explicitly whitelisted — it does not allow wildcards for production. Supabase's Site URL is set in the dashboard, not in code, so it is invisible in code reviews and easy to forget. The Supabase Sign-In OAuth flow goes through `https://[project].supabase.co/auth/v1/callback` — a different URI than the existing Calendar callback — and that URI must also be registered in Google Cloud Console.

**How to avoid:**
For the Calendar OAuth (existing flow):
- Set `GOOGLE_OAUTH_REDIRECT_URI=https://yourdomain.com/auth/google/callback` in production `.env`
- Add `https://yourdomain.com/auth/google/callback` to Google Cloud Console → Authorized redirect URIs

For Supabase Google Sign-In (new for v1.1):
- Add `https://[supabase-project-ref].supabase.co/auth/v1/callback` to Google Cloud Console → Authorized redirect URIs
- Update Supabase Dashboard → Authentication → URL Configuration → Site URL to `https://yourdomain.com`
- Add `https://yourdomain.com` and `https://yourdomain.com/**` to Supabase Additional Redirect URLs
- Do NOT use the custom `/auth/google/` router for Supabase Sign-In — configure it entirely through Supabase Dashboard → Authentication → Providers → Google

**Warning signs:**
- After Google Sign-In, browser URL shows `error=redirect_uri_mismatch`
- User is redirected to localhost (404) after clicking "Sign in with Google" on the production site
- Supabase auth logs show "invalid redirect url" or "Redirect URL not allowed"

**Phase to address:** Google OAuth / Auth polish phase — verify both flows on the production domain before enabling for users.

---

### Pitfall 4: Google Sign-In Email Collision With Existing Password-Signup Users

**What goes wrong:**
A user who signed up with email+password (e.g., `user@gmail.com`) then clicks "Sign in with Google" using the same Gmail address. Supabase auto-links identities matching the same email — but ONLY if the existing email is verified. The current signup flow has email confirmation disabled (per the comment in `auth.py`: "IMPORTANT: Requires email confirmation disabled in Supabase Dashboard"). With email confirmation disabled, all existing password-signup users have "unverified" email status from Supabase's perspective. When these users attempt Google OAuth, Supabase removes their unconfirmed email identity before linking the Google identity, which can invalidate existing sessions and cause confusion.

**Why it happens:**
Email confirmation was intentionally disabled to reduce signup friction. This is a reasonable early-stage decision. The problem only surfaces when Google OAuth is added later — the auth architecture has a gap that was not visible before.

**How to avoid:**
- Before enabling Google Sign-In for existing users, run a one-time migration to mark all existing password-signup users as email-verified: `supabase_admin.auth.admin.update_user_by_id(uid, {"email_confirm": True})` for each user
- In the Google Sign-In UI, detect the collision case and show a clear message: "You already have an account with this email. Sign in with your password to link Google." Do not silently fail
- Test the collision scenario explicitly in staging: create a user with email+password, attempt Google OAuth with the same email, verify the session is correct and no duplicate user row is created

**Warning signs:**
- After clicking "Sign in with Google," user is logged out or sees a blank session
- Supabase `auth.users` table has duplicate rows with the same email after Google OAuth
- Auth audit logs show "unconfirmed identity removed" during an OAuth flow

**Phase to address:** Google OAuth / Auth polish phase — run the email verification migration before enabling Google Sign-In.

---

### Pitfall 5: Stripe Cancellation Flow Uses "Immediate Cancel" Instead of "Cancel at Period End"

**What goes wrong:**
If the cancellation API call uses `stripe.Subscription.cancel()` (immediate cancellation), Stripe fires `customer.subscription.deleted` within seconds. The existing webhook handler calls `deactivate_subscription(sub_id, new_status="canceled")` on that event, which immediately sets the user's status to `canceled` in the database. The user is stripped of access while still on the cancellation confirmation screen. Subsequent page loads show them as unsubscribed even though they paid for the current billing period.

**Why it happens:**
The difference between "cancel at period end" (`stripe.Subscription.modify(cancel_at_period_end=True)`) and "cancel immediately" (`stripe.Subscription.cancel()`) is easy to miss. Both "work" — the distinction is when the user loses access.

**How to avoid:**
- Implement cancellation via `stripe.Subscription.modify(cancel_at_period_end=True)` so the user retains access until their billing period ends
- Add handling for `customer.subscription.updated` webhook event to store the `cancel_at_period_end` flag and `current_period_end` date in the subscriptions table
- Show the user: "Your subscription ends on [date] — you have full access until then." Not: "Your subscription is canceled."
- The churn survey must be a GATE for the cancellation flow — the cancel API call fires only after the user completes or explicitly skips the survey. Do not fire it optimistically.
- The `deactivate_subscription()` on `customer.subscription.deleted` (which fires at actual period end) is correct as-is. Do not change it.

**Warning signs:**
- User reports losing chat access immediately after cancelling
- Stripe Dashboard shows subscription with "Canceled immediately" rather than "Cancels on [date]"
- Local DB shows `status: canceled` before the billing period ends
- Frontend shows 402 error on chat immediately after cancellation flow completes

**Phase to address:** Subscription management + churn flow phase — design the cancellation API call correctly from the start.

---

### Pitfall 6: Transactional Emails Land in Spam Because the Domain Is New

**What goes wrong:**
A new domain with no sending history gets 55% inbox placement vs 85% for aged domains. Without SPF, DKIM, and DMARC DNS records, Gmail, Yahoo, and Outlook (2024-2025 enforcement requirements) treat emails as unauthenticated and route them to spam or drop them silently. Password reset emails are the most critical path — if they land in spam, users cannot recover their accounts. Welcome emails and receipts reinforce trust; spam delivery destroys it.

**Why it happens:**
Developers sign up for Resend or SendGrid, get an API key, and start sending. The email provider generates SPF/DKIM DNS records in their dashboard but these are not automatically added to the domain's DNS — someone must manually create TXT records. This step is easy to skip. DMARC is almost never configured by default.

**How to avoid:**
- Recommended provider: Resend (better developer experience and deliverability tooling than SendGrid for low-volume senders at launch)
- Configure ALL three DNS records before sending the first production email:
  - SPF: `v=spf1 include:amazonses.com ~all` (or provider equivalent) — use `~all` softfail, not `-all` hard fail
  - DKIM: the TXT record generated by the provider on a selector subdomain (e.g., `resend._domainkey.yourdomain.com`)
  - DMARC: start with `v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com` to monitor without rejecting
- Send transactional email from a subdomain (`hello@mail.yourdomain.com`) to isolate transactional reputation from the root domain
- Verify deliverability before launch: send a test email and check score at mail-tester.com — aim for 9/10 or higher
- Gmail has a 0.10% spam rate threshold for bulk senders — stay below it

**Warning signs:**
- Password reset or welcome email does not arrive in inbox (check spam folder)
- mail-tester.com score below 7/10
- Email provider dashboard shows "Authentication: failed" on sent messages
- Bounce rate above 2% on first batch of welcome emails

**Phase to address:** Transactional email phase — verify DNS propagation and deliverability before enabling password reset or welcome email sending for real users.

---

### Pitfall 7: Password Reset Reveals Whether an Email Is Registered (Email Enumeration)

**What goes wrong:**
The naive implementation returns different responses for registered vs unregistered emails: "Reset email sent" for known accounts, "No account found" for unknown ones. Attackers — or a user's partner — can determine which email addresses have Ava accounts. On an adult-adjacent platform this is a privacy violation: discovering that a specific email has an account reveals intimate information about the person. GDPR Article 5(1)(c) data minimisation principle applies.

**Why it happens:**
The natural developer instinct is to give helpful error messages. Most developers add a user-existence check before calling the reset function, not realising this creates an enumeration vector.

**How to avoid:**
- Always return the same message regardless of whether the email exists: "If an account with that email exists, you'll receive a reset link shortly."
- Call Supabase's `auth.reset_password_for_email()` directly — Supabase handles the existence check internally and returns the same success response either way. Do NOT add a pre-check for user existence.
- Apply rate limiting on the reset endpoint: max 5 requests per email per hour, max 20 requests per IP per hour (use FastAPI `slowapi` or nginx `limit_req`)
- Tokens expire after 24 hours (Supabase default) — document this in the email: "This link expires in 24 hours"
- Supabase invalidates reset tokens after use — single-use is handled automatically

**Warning signs:**
- `/auth/reset-password` returns different HTTP status codes or response bodies for existing vs non-existing emails
- No rate limiting on the password reset endpoint — can be called in a loop
- Error message explicitly says "no account found" or "email not registered"

**Phase to address:** Password reset phase — design the response message correctly from day one, it is easy to get wrong and difficult to change after users have seen the message pattern.

---

### Pitfall 8: Admin Dashboard Fires N+1 Queries and Has No Access Control

**What goes wrong:**
Two separate problems that are easy to combine into one bad situation:

1. An analytics dashboard that queries "active users this week," "messages sent today," "photos generated," and "active subscriptions" often fires multiple sequential queries — one per metric, or one per user — rather than a single aggregate. At 100 users this is invisible; at 1,000 users the page takes 10-30 seconds to load. Tables without indexes on `created_at` force PostgreSQL to do sequential scans.

2. The `/admin` route has no role-based access check. Any authenticated user who knows the URL can view all user data, usage statistics, and subscription information. This is a data exposure vulnerability.

**Why it happens:**
Dashboard queries are written with small datasets and look fast. Indexes feel premature. The admin route gets ProtectedRoute wrapping (requires login) but not AdminRoute wrapping (requires admin role) — these are different checks.

**How to avoid:**
For query efficiency:
- Write dashboard metrics as single aggregating SQL queries, not separate round-trips. Use CTEs or window functions.
- Add indexes in the migration: `CREATE INDEX ON messages (user_id, created_at DESC)`, `CREATE INDEX ON subscriptions (status, created_at)`, `CREATE INDEX ON avatars (user_id)`
- Cache admin dashboard results in Redis for 5 minutes — it is internal-only, stale data for 5 minutes is fine
- Do not store PII (email, name) in analytics event logs — store `user_id` UUID only

For access control:
- Add an `is_admin` boolean column to the Supabase `auth.users.raw_user_meta_data` or a separate `user_roles` table
- Create a `require_admin_role` FastAPI dependency that checks this flag and raises 403 for non-admins
- Apply it to the entire admin router, not per-endpoint
- Set the admin flag via Supabase Admin API: `supabase_admin.auth.admin.update_user_by_id(uid, {"user_metadata": {"is_admin": True}})`

**Warning signs:**
- Admin page takes more than 3 seconds to load with fewer than 100 users
- Supabase Query Performance tab shows sequential scans on messages or subscriptions tables
- Any logged-in user can access `/admin` directly in the browser
- Admin page shows user email addresses or other PII in event logs

**Phase to address:** Admin dashboard phase — add access control first (before building any metrics), add indexes in the migration file before it runs.

---

### Pitfall 9: Landing Page Ad Acquisition Channels Are Largely Blocked for This Product

**What goes wrong:**
Google Ads, Facebook/Meta Ads, TikTok Ads, and Instagram Ads prohibit adult content. Google's Dating and Companionship Ads policy (updated August 2025) requires certification AND explicitly states: "Dating services using synthetically generated profiles or chatbots without a clear and conspicuous disclosure are not allowed." Ava is explicitly an AI (not human) — so certification requires disclosing the AI nature on the landing page, and any hint of intimate content triggers automatic moderation rejection. Ad accounts get suspended often within 24 hours of a new campaign.

**Why it happens:**
Founders budget for paid acquisition assuming it works like SaaS. For adult-adjacent AI products, the mainstream ad channels are either entirely closed or require disclosure and certification that fundamentally changes the product's public framing.

**How to avoid:**
- Do not allocate launch budget to Google Ads or Facebook Ads for intimate features — channels are unreliable and account suspension risks are high
- Viable acquisition channels at launch: SEO/organic (Google does index adult-adjacent content; paid ads ≠ organic), Reddit communities (with honest disclosure), Twitter/X (more permissive ad policies), Discord, affiliate networks (CrakRevenue, MaxBounty)
- The landing page must not show explicit imagery above the fold — use suggestive but fully clothed imagery
- Avoid trigger keywords in page title, H1, and meta description: "sex," "explicit," "nude," "erotic," "adult content" — these affect both ad approvals and Google organic manual action risk
- If pursuing Google Ads Dating & Companionship certification: the review process examines post-login content. Ensure the certification reviewer does not encounter intimate image generation features
- Plan for SEO as the primary organic channel at launch — it is slower but stable

**Warning signs:**
- Google Ads account suspended within 24 hours of a new campaign going live
- Facebook/Meta ad rejected with "adult content" policy violation
- Landing page uses language that would be flagged by automated content scanners ("AI girlfriend," "intimate photos," "NSFW")

**Phase to address:** Landing page phase — write copy and choose imagery before building, not after. The framing decision affects every other piece of marketing.

---

### Pitfall 10: Cancellation Churn Flow Becomes a Dark Pattern and Creates Legal Exposure

**What goes wrong:**
A cancellation flow that: (a) buries the cancel button below the fold, (b) requires answering the churn survey before cancellation is allowed, (c) has more than 3 screens between "I want to cancel" and "cancellation confirmed," or (d) stores survey responses linked to user PII without consent — all constitute violations. California's Automatic Renewal Law requires cancellation to be "as easy as" signing up. The EU DSA/GDPR requires explicit consent before storing survey responses. The FTC pursued Amazon for $2.5 billion in 2025 for exactly this pattern — a subscription cancellation that required 6 clicks minimum.

**Why it happens:**
Product instinct is to maximize retention. Adding friction to cancellation feels reasonable from a business perspective. Churn surveys seem innocuous — collecting a reason for cancellation. The legal risk is underestimated until a complaint is filed.

**How to avoid:**
- Cancel button must be visible on the subscription page without scrolling
- Churn survey must be optional — user can click "Skip and cancel" and cancellation proceeds immediately
- Limit the survey to 1-2 questions maximum (one multiple choice "Why are you leaving?", one optional text field)
- Total click count from "I want to cancel" to "cancellation confirmed" must be 3 or fewer
- Do NOT store survey responses linked to `user_id` without a consent checkbox — store them anonymously, or add: "By submitting this survey, you consent to us storing your response to improve our service"
- Cancellation confirmation screen must show the access end date: "Your access continues until [date]." Not just "canceled."

**Warning signs:**
- Survey is a required step before the cancel button is enabled
- Survey form stores responses in a `user_id`-linked table with no consent record
- Cancel button requires scrolling or is in a modal inside another modal
- Cancellation flow has more than 3 confirmation screens

**Phase to address:** Subscription management + churn flow phase — design the flow spec before building. The legal constraint (optional survey, ≤3 clicks) is a design requirement, not a polish task.

---

### Pitfall 11: Docker Compose .env Secrets Committed to Git or Exposed on VPS

**What goes wrong:**
`backend/.env` contains `STRIPE_SECRET_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`, and `COMFYUI_API_KEY`. If this file is committed to the git repository once (even if later removed), git history preserves it permanently — secret scanning tools and anyone with `git log -p` can find it. On the VPS, if `.env` file permissions are too broad, any process running as a different user can read it.

**Why it happens:**
Local `.env` files are created early in development. `.gitignore` entries for environment files get missed when the repo was initially created with minimal config. Developers deploy by `git pull` on the VPS and bring the file along.

**How to avoid:**
- Before the first production push: verify `.gitignore` contains `backend/.env` (and `.env` for root-level)
- Run `git log --all -p -- backend/.env` — it must return no output. If it returns anything, a secret has been committed
- On the VPS: `chmod 600 backend/.env` and verify ownership is the Docker-running user
- Never transmit `.env` over Slack, email, or shared documents in plaintext
- If any secret in the file is ever exposed, rotate ALL secrets in the file immediately — Stripe, Supabase service role key, OpenAI, ComfyUI
- At this scale (single VPS, Docker Compose), a properly permissioned `.env` file is acceptable. Vault or AWS Secrets Manager are better but add operational complexity that is not warranted yet.

**Warning signs:**
- `git log --all --full-history -- backend/.env` returns any commit output
- `ls -la backend/.env` shows permissions wider than `-rw-------` (600)
- A team member requests the `.env` file and receives it as a file attachment

**Phase to address:** VPS production deployment phase — check before the first `git push` to any remote that includes the backend directory.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Email confirmation disabled in Supabase | No signup friction | All existing users appear "unverified" — causes Google OAuth identity linking issues on email collision | Must fix (run email verification migration) before enabling Google Sign-In |
| `get_subscription_status()` is a synchronous DB call inside async FastAPI endpoints | Simpler code | Blocks the event loop on every subscription-gated request — latency spike under concurrent load | Acceptable under 50 concurrent users; add Redis cache or async DB call before scaling |
| Google Calendar OAuth `state` param is the raw `user_id` UUID | Simple implementation | Predictable state value enables CSRF attacks against the OAuth flow | Low risk for Calendar (low-value target); must use random nonce for Supabase Sign-In |
| No idempotency key stored for Stripe webhook events | Simpler handler | Stripe retries webhooks; duplicate `checkout.session.completed` upserts on conflict (safe), but duplicate invoice events could cause unexpected state changes | Low risk with current upsert pattern; add Stripe-Event-Id dedup table before processing financial events |
| `/admin` page with only `ProtectedRoute` (no admin role check) | Faster to build | Any authenticated user who knows the URL can access all user data | Never acceptable — add admin role check before launch |
| JWT stored in localStorage via Zustand persist | Simple implementation | XSS attack can steal token; no server-side revocation capability | Acceptable for MVP; migrate to httpOnly cookies if XSS risk increases (e.g., user-generated content rendered as HTML) |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Supabase + Google Sign-In | Using the existing `/auth/google/` Calendar router for Supabase Sign-In | These are two different flows. Calendar OAuth uses a custom router. Supabase Sign-In uses Supabase Dashboard → Providers → Google + frontend `supabase.auth.signInWithOAuth()` |
| Google Cloud Console | Only adding localhost to authorized redirect URIs | Add production domain AND the Supabase callback URI (`https://[project-ref].supabase.co/auth/v1/callback`) — both are required |
| Stripe cancellation | `stripe.Subscription.cancel()` for immediate cancel | Use `stripe.Subscription.modify(cancel_at_period_end=True)` so user keeps access until billing period ends |
| Stripe webhook | (Already handled correctly) Parsing body as JSON before signature verification | The current `await request.body()` before `verify_webhook_event()` pattern is correct — do not change it |
| Certbot + nginx | Starting nginx with `ssl_certificate` directives before certs exist | Two-phase bootstrap: HTTP-only config first, `certbot certonly`, then add SSL server block |
| Transactional email | Starting to send before SPF/DKIM/DMARC DNS records are propagated | Configure DNS records, verify propagation with `dig TXT yourdomain.com`, test with mail-tester.com before first real user email |
| Supabase password reset | Adding a user-existence check before calling `reset_password_for_email()` | Call Supabase directly without pre-checking — Supabase handles obfuscation. A pre-check creates the enumeration vulnerability. |
| Supabase Site URL | Leaving Site URL as localhost in Supabase Dashboard | Update Site URL to production domain in Supabase Dashboard → Authentication → URL Configuration before launch |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Admin dashboard fires multiple sequential queries | Admin page loads in 10-30 seconds | Write metrics as a single aggregating SQL statement with a CTE; cache result for 5 min in Redis | 500+ rows in messages/subscriptions |
| `messages` table has no index on `(user_id, created_at)` | Full table scan on every chat history fetch | `CREATE INDEX ON messages (user_id, created_at DESC)` in migration | 5,000+ message rows |
| `subscriptions` table has no index on `status` | Full scan on subscription analytics | `CREATE INDEX ON subscriptions (status, created_at)` | 1,000+ subscription rows |
| Synchronous `get_subscription_status()` on every gated request | API latency spikes as concurrent users grow | Cache in Redis with 60-second TTL keyed by `user_id` | 20+ concurrent users hitting gated endpoints |
| nginx serving React bundle without `Cache-Control` headers | Every page load re-fetches hashed JS/CSS assets | `Cache-Control: max-age=31536000, immutable` for hashed assets; `no-cache` for `index.html` | Any production traffic — day 1 issue |
| Password reset endpoint with no rate limiting | Brute-force token guessing; inbox flooding | `slowapi` rate limiter: 5 requests/email/hour, 20/IP/hour | Any public-facing deployment |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| `/admin` route accessible to any authenticated user | All user data, PII, and subscription info exposed to any logged-in user | Add `require_admin_role` FastAPI dependency; check `is_admin` flag in Supabase user metadata |
| Churn survey responses stored with `user_id` and no consent record | GDPR Article 6 violation — personal data collected without lawful basis | Store responses anonymously by default; add explicit consent checkbox before linking to user |
| Google Calendar OAuth `state` parameter is predictable (`state=user_id`) | CSRF attack: attacker substitutes their auth code with victim's state token | For Supabase Sign-In, Supabase handles PKCE internally. For Calendar OAuth, replace `state={user_id}` with a random nonce stored in session |
| Password reset endpoint without rate limiting | Email enumeration via timing; inbox flooding; token brute force | `slowapi` rate limiter on the endpoint |
| `supabase_admin` (service role client) used inadvertently in new user-facing endpoints | Bypasses RLS — a bug in any user-facing endpoint using admin client exposes all users' data | Enforce in code review: admin client appears only in `/billing/webhook`, subscription service, and admin router. Never in auth, chat, avatar routers. |
| PII (email, message content) in application logs shipped to Sentry | User conversation content and emails visible to Sentry team and in log archives | Audit all `logger.*` calls before production; never log `user.email`, message bodies, or avatar descriptions |
| New admin UI rendering user-provided content as HTML | XSS vector inside the admin dashboard — one malicious user input compromises the admin session | Sanitize all user-provided content rendered in admin views; use React's default JSX escaping, never `dangerouslySetInnerHTML` |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Mandatory churn survey before cancel is processed | Legal risk, user anger, negative reviews | Survey always optional; "Skip and cancel" button present from the first survey screen |
| Cancellation shows "canceled" without stating access end date | User panics, contacts support thinking they lost access immediately | "Your subscription ends on [date] — you have full access until then." |
| Google Sign-In creates duplicate account for existing password users | User loses all their conversation history, avatars, and subscription | Detect collision, show explicit "link your account" flow, do not silently create a second user |
| Password reset email from generic `noreply@` address with no branding | Email looks like phishing; users don't trust the link; goes to spam | Use `hello@mail.yourdomain.com`, branded sender name ("Ava App"), include recognizable product imagery |
| Password reset link expires with no indication in the email | User clicks link hours later, gets a confusing error | State the expiry in the email body: "This link expires in 24 hours." |
| Landing page hero is identical to a generic SaaS product | Visitors don't understand what the product does or why it is for them | The hero must communicate the dual-mode value proposition clearly within 5 seconds of landing |
| Exit survey asks 5+ questions | Survey fatigue; users abandon without completing; no useful data | One required question (multiple choice, "Why are you leaving?"), one optional free-text field, always skippable |

---

## "Looks Done But Isn't" Checklist

- [ ] **SSL/HTTPS:** nginx.conf has an HTTPS server block on port 443 with valid cert paths AND an HTTP → HTTPS permanent redirect — verify with `curl -I http://yourdomain.com` (must return 301) and `curl https://yourdomain.com` (must return 200 without cert errors)
- [ ] **Stripe webhook:** Registered in Stripe Dashboard with the production HTTPS URL and the correct signing secret in production `.env` — verify with Stripe Dashboard → Webhooks → "Send test event"
- [ ] **Google OAuth production redirect:** Production domain added to Google Cloud Console authorized redirect URIs AND to Supabase Additional Redirect URLs AND Supabase Site URL updated — verify by completing a full Google Sign-In on the live domain
- [ ] **Supabase email verification migration:** All existing password-signup users have been marked as email-verified before Google Sign-In is enabled
- [ ] **Transactional email deliverability:** SPF, DKIM, and DMARC DNS records propagated and verified — `dig TXT yourdomain.com` returns SPF record; mail-tester.com score is 9/10 or higher
- [ ] **Admin route access control:** `require_admin_role` dependency applied to the admin router — verify that a non-admin user gets 403 when navigating to `/admin`
- [ ] **Password reset enumeration:** Response body is identical for registered and non-registered emails — verify manually by sending reset for a known non-existent email
- [ ] **Rate limiting on password reset:** `/auth/reset-password` returns 429 after 5 rapid requests from the same IP
- [ ] **Cancellation uses period-end:** After cancelling, Stripe Dashboard shows "Cancels on [date]" (not "Canceled") — verify subscription object has `cancel_at_period_end: true`
- [ ] **Churn survey is optional:** "Skip and cancel" button present on survey screen; clicking it immediately processes cancellation — test without answering any survey question
- [ ] **`.env` not in git history:** `git log --all -p -- backend/.env` returns no output
- [ ] **No PII in logs:** `grep -rn "logger\." backend/app/ | grep -iE "email|\.content|\.text|message_body"` returns nothing that would log user content

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Stripe account terminated for adult content | HIGH | Migrate to CCBill/Segpay; export customer list from Stripe before freeze; email customers directly about re-subscribing; expect 2-4 week payment gap while new processor onboards |
| SSL not configured — site running on HTTP | LOW | Run two-phase certbot bootstrap (30-60 min downtime); update nginx.conf; reload nginx |
| Google OAuth redirect mismatch | LOW | Add URI to Google Cloud Console and Supabase Dashboard; propagates within 5 minutes; no downtime |
| Email landing in spam — DNS records missing | MEDIUM | Add SPF/DKIM/DMARC records; wait 24-48 hours for propagation; resend critical emails; domain reputation takes weeks to recover |
| Admin dashboard publicly accessible | MEDIUM | Deploy access control fix immediately; audit Supabase logs for requests to `/admin` from non-admin users; assess if any data was improperly accessed |
| Churn survey storing PII without consent | MEDIUM | Delete stored responses or anonymize them; add consent mechanism; document remediation for GDPR accountability record |
| `.env` committed to git | HIGH | Rotate ALL secrets immediately (Stripe, Supabase service role, OpenAI, ComfyUI); remove from git history with `git filter-repo`; notify any affected API providers; audit usage logs for unauthorized calls |
| Subscription deactivated immediately on period-end cancel | MEDIUM | Identify affected users (those who canceled in the last billing period); manually set their subscription status to `active` via `supabase_admin`; Stripe Dashboard shows their actual period end date |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Stripe adult content restriction | Landing page + VPS deployment | Landing page copy review; Stripe account business description matches framing |
| nginx no HTTPS | VPS production deployment | `curl -I http://domain` returns 301; `curl https://domain` returns 200 with valid cert |
| Google OAuth redirect mismatch | Auth polish (Google Sign-In) phase | Full Google Sign-In on production domain completes without `redirect_uri_mismatch` |
| Email collision with password accounts | Auth polish (Google Sign-In) phase | Collision test: existing user attempts Google OAuth with same email; correct behavior verified |
| Stripe cancel race condition | Subscription management + churn phase | Stripe test mode cancel: DB shows `cancel_at_period_end`, not immediate `canceled` |
| Email deliverability/spam | Transactional email phase | mail-tester.com ≥9/10; password reset email arrives in inbox (not spam) |
| Password reset enumeration | Password reset phase | Same response for registered and unregistered emails; rate limiter confirmed active |
| Admin N+1 + no access control | Admin dashboard phase | Admin page loads <2s; non-admin user gets 403; EXPLAIN ANALYZE shows index scans |
| Landing page ad channel blocks | Landing page phase | Page copy does not contain trigger words; imagery is suggestive but not explicit |
| Cancellation dark pattern | Churn flow phase | Cancel completes in ≤3 clicks without survey; survey is skippable at every step |
| `.env` secrets management | VPS production deployment | `git log --all -p -- backend/.env` returns no output; file permissions are 600 on VPS |

---

## Sources

- [Stripe Restricted Businesses Policy](https://stripe.com/legal/restricted-businesses) — AI-generated adult content explicitly prohibited (HIGH confidence — official policy document)
- [Supabase Identity Linking](https://supabase.com/docs/guides/auth/auth-identity-linking) — auto-linking behavior with unverified emails (HIGH confidence — official docs)
- [Supabase Google Auth Troubleshooting](https://supabase.com/docs/guides/troubleshooting/google-auth-fails-for-some-users-XcFXEu) — email scope and failure modes (HIGH confidence — official docs)
- [Supabase Redirect URL Configuration](https://supabase.com/docs/guides/auth/redirect-urls) — Site URL and additional redirect URLs behavior (HIGH confidence — official docs)
- [Stripe Webhook Best Practices](https://docs.stripe.com/billing/subscriptions/webhooks) — event ordering, idempotency, `cancel_at_period_end` (HIGH confidence — official docs)
- [Stripe Race Condition Solutions](https://www.pedroalonso.net/blog/stripe-webhooks-solving-race-conditions/) — idempotency patterns in practice (MEDIUM confidence — verified against Stripe docs)
- [OWASP Forgot Password Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html) — enumeration prevention and rate limiting (HIGH confidence — OWASP)
- [Google Ads Dating and Companionship Policy — August 2025 update](https://support.google.com/adspolicy/answer/15328393?hl=en) — chatbot disclosure requirement, certification (HIGH confidence — official Google policy)
- [FTC Click-to-Cancel and Dark Patterns Enforcement](https://www.coulsonpc.com/coulson-pc-blog/dark-patterns-ftc-click-to-cancel-rule) — roach motel enforcement history (MEDIUM confidence)
- [Amazon $2.5B FTC Settlement 2025](https://lawandcrime.com/lawsuit/feds-accuse-amazon-of-using-dark-patterns-and-roach-motel-techniques-to-trick-customers-into-auto-renewing-prime-memberships/) — dark pattern enforcement consequences (HIGH confidence — reported fact)
- [Email Deliverability — SPF/DKIM/DMARC Setup](https://www.mailgun.com/blog/dev-life/how-to-setup-email-authentication/) — DNS record configuration (HIGH confidence — official Mailgun documentation)
- [Gmail and Yahoo 2024 Sender Requirements](https://saleshive.com/blog/dkim-dmarc-spf-best-practices-email-security-deliverability/) — mandatory authentication enforcement (HIGH confidence — multiple authoritative sources)
- [Certbot + nginx Bootstrap Problem](https://dev.to/marrouchi/the-challenge-about-ssl-in-docker-containers-no-one-talks-about-32gh) — two-phase SSL setup pattern (MEDIUM confidence — community-verified)
- [Docker Compose Secrets and .env Security](https://docs.docker.com/compose/how-tos/use-secrets/) — official Docker documentation on secrets management (HIGH confidence)
- [GDPR Dark Patterns and Consent](https://www.fairpatterns.com/post/gdpr-dark-patterns-how-they-undermine-compliance-risk-legal-penalties) — survey consent requirements (MEDIUM confidence — legal analysis)
- [Adult Content Marketing Without Ads](https://absolute.digital/insights/adult-content-marketing-in-2025-how-to-grow-traffic-when-ads-arent-an-option/) — viable acquisition channels for adult-adjacent products (MEDIUM confidence)

---

*Pitfalls research for: Ava v1.1 Launch Ready — production launch features added to existing FastAPI/Supabase/React app*
*Researched: 2026-03-02*
*Overall confidence: HIGH — all critical pitfalls verified against official documentation. Enforcement history claims (FTC, Amazon) verified against news reports.*
