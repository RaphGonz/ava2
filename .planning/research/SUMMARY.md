# Project Research Summary

**Project:** Ava v1.1 — Launch Ready
**Domain:** SaaS launch polish for existing Dual-Mode AI Companion (FastAPI + Supabase + React + Stripe)
**Researched:** 2026-03-02
**Confidence:** HIGH

## Executive Summary

Ava v1.1 is a production-launch milestone that transforms the existing v1.0 product (fully shipped) into a commercially viable SaaS offering. The seven features in scope — landing page, Google OAuth, password reset, user billing/subscription management, cancellation churn flow with exit survey, transactional emails, and admin analytics dashboard — are all table stakes for a "launch ready" product. None are optional. Research confirms this milestone is unusually low-risk from a technology standpoint: only two new packages are required across the entire feature set (`resend` for Python email sending, `recharts` for frontend analytics charts). Every other feature is solved by existing libraries and configuration changes to Supabase, Stripe, and the reverse proxy.

The recommended implementation approach is additive: extend the existing FastAPI routers, Supabase auth configuration, and React SPA without restructuring anything. The most significant infrastructure change is replacing the bare `nginx` image with Caddy for automatic HTTPS — the current `nginx.conf` listens only on port 80 with no SSL wired up despite the Certbot volume mount existing, which means the site would launch over plain HTTP if not corrected. Email delivery requires SPF/DKIM/DMARC DNS records to be configured in Resend's dashboard before any transactional email is sent; this is a blocking prerequisite for password reset, welcome emails, and receipts.

The dominant non-technical risk is Stripe account termination. Stripe's restricted businesses policy explicitly prohibits AI-generated adult content. The landing page copy and Stripe account business description must frame the product as an "AI companion/assistant" — not as an intimate AI or adult content platform — or the account will eventually be flagged. A separate compliance deadline also looms: SAFE-03 (TAKE IT DOWN Act) takes effect May 19, 2026, approximately 2.5 months from now. A takedown process and 48-hour response capability must be in place before that date regardless of where v1.1 is in development.

## Key Findings

### Recommended Stack

The v1.1 stack requires only two new packages added to the existing FastAPI + Supabase + React + Stripe + BullMQ architecture. The rest of the feature set is delivered via Supabase configuration, Stripe configuration, and the existing libraries. This is a significant finding: it means the development risk is concentrated in configuration and integration logic, not in learning new frameworks.

**New packages only:**
- `resend ^2.23.0` (Python backend) — transactional email via HTTP API; async-compatible with FastAPI `BackgroundTasks`; 3,000 emails/month free tier; first-class Supabase partnership. Released 2026-02-23, actively maintained.
- `recharts ^3.7.0` (React frontend) — SVG chart library for the `/admin` analytics page; React 19 compatible (`^18.0.0 || ^19.0.0`); ~350kb unparsed but admin-only so acceptable.

**Infrastructure change (not a package):**
- Caddy replaces `nginx` image in `docker-compose.yml` — automatic HTTPS, zero-touch Let's Encrypt certificate issuance and renewal via a single `Caddyfile`. The current nginx configuration does not serve HTTPS despite having a Certbot volume mount.

**Critical constraint to preserve:**
The frontend has no direct Supabase JS client. All auth flows through a FastAPI proxy pattern: `Frontend → FastAPI → Supabase Python SDK → Supabase Cloud`. The exception is Google OAuth and password reset, where the `@supabase/supabase-js` client is used directly on the frontend for the PKCE flow. This is a one-time exception and must not be generalized; adding the Supabase JS client to other flows would create split-auth architecture.

**New environment variables required:**
- `RESEND_API_KEY` — transactional email
- `RESEND_FROM_ADDRESS` — sender address (e.g., `Ava <hello@yourdomain.com>`)
- `VITE_SUPABASE_URL` — frontend build-time var for Google OAuth PKCE flow
- `VITE_SUPABASE_ANON_KEY` — frontend build-time var for Google OAuth PKCE flow
- Google OAuth Client ID + Secret go into the Supabase Dashboard only (not FastAPI `.env`)

### Expected Features

Research confirms all seven v1.1 features are table stakes — a product missing any of them will feel incomplete or untrustworthy to paying users.

**Must have (table stakes) — all 7 features for v1.1:**
- **Landing page** — no acquisition funnel without it; users expect to understand the product before signing up; hero + features + pricing + CTA; Figma design to be provided
- **Google OAuth** — dominant auth pattern in 2026; email+password only increases friction and reduces conversion; Supabase handles PKCE natively
- **Password reset** — OWASP requirement; blocking issue for any real user who loses their password; Supabase handles token generation and email sending
- **User subscription management page** — paying users need to see their plan, next billing date, and payment method; missing this is a trust failure; hybrid of in-app display + Stripe Customer Portal redirect
- **Cancellation churn flow with exit survey** — required by consumer protection law in most markets (California ARL, EU DSA); captures churn reason for product learning; 25-30% of cancellations can be saved with targeted retention offers
- **Transactional emails** (welcome on signup, receipt on payment, cancellation confirmation) — professional product baseline; welcome emails have 4x industry open rate; Stripe receipts are expected by every paying user for tax/accounting
- **Admin analytics dashboard** — operator cannot make product decisions without visibility; Tier 1 metrics: active users, messages sent, photos generated, active subscriptions, new signups; Tier 2: MRR, churn count, conversion rate

**Recommended for v1.1 (differentiators):**
- Exit survey data drives targeted retention offers (discount, pause) — improves save rate
- Pricing section on landing page — transparent pricing reduces decision anxiety and increases conversion
- Admin dashboard with line/bar charts (Recharts) rather than plain numbers

**Defer to v2+:**
- Subscription pause option — add after seeing exit survey data to validate demand
- Reactivation email sequence — needs a base of churned users to be meaningful
- Apple/GitHub OAuth — Google covers 70-80% of users; add based on post-launch demand
- Multi-tier pricing — single plan for v1.1; analysis paralysis reduces conversion for new products
- External analytics (PostHog, Mixpanel) — custom `usage_events` table in existing Supabase covers all v1.1 needs

### Architecture Approach

All nine v1.1 features integrate with the existing architecture without restructuring. The pattern is: extend existing FastAPI routers, add new frontend pages to the React SPA, configure Supabase Auth providers and URL allowlists, and handle Stripe webhook events already flowing through `billing.py`. No new backend service, no new database, no new infrastructure beyond Caddy replacing nginx.

**New components added by v1.1:**

1. **Email service module** (`backend/app/services/email/`) — Resend SDK wrapper + email template builders; called as `BackgroundTasks` from the `/auth/signup` handler and from Stripe webhook events in `billing.py`

2. **Admin router** (`backend/app/routers/admin.py`) — protected by `require_admin` FastAPI dependency that reads `app_metadata.role == "admin"` from the Supabase JWT; serves aggregated metrics from `usage_events` table and Stripe API; all queries must be single-statement aggregations with indexes

3. **Churn flow router additions** (`POST /billing/survey`, `POST /billing/cancel`) — save optional survey response, then call `stripe.Subscription.modify(cancel_at_period_end=True)`; the survey table stores anonymous responses with user consent

4. **Billing portal endpoint** (`POST /billing/portal`) — creates Stripe Customer Portal session and returns redirect URL; no new Stripe integration needed, uses existing `stripe` library

5. **Frontend pages** (all new React routes using existing React Router + Tailwind): `/` (landing), `/billing`, `/cancel`, `/forgot-password`, `/reset-password`, `/auth/callback` (OAuth callback), `/admin`

6. **Caddy reverse proxy** — replaces `nginx` image in `docker-compose.yml`; single `Caddyfile` handles HTTPS termination, SPA serving, and API proxying; TLS certificates auto-issued and auto-renewed

**Supabase database additions (new migrations):**
- `usage_events` table with indexes on `(created_at DESC)`, `(user_id)`, `(event_type)` — powers admin analytics without N+1 queries
- `churn_surveys` table — stores anonymous cancellation survey responses

**Key integration boundary:** Google OAuth for sign-in is handled entirely at the Supabase Auth layer (dashboard configuration + `@supabase/supabase-js` on the frontend). It is completely separate from the existing `google_oauth.py` router which handles Google Calendar OAuth for secretary mode. Do not conflate these two flows.

### Critical Pitfalls

Research identified 11 pitfalls for v1.1. The top 5 by severity:

1. **Stripe will terminate the account if business description references adult/intimate AI content** — Frame the product as "AI personal assistant and companionship app" in the Stripe account registration and on the landing page. Never use words like "intimate," "explicit," "NSFW," or "adult" in public-facing copy. Stripe proactively monitors. A chargeback rate above 1% triggers review regardless of description. Recovery from termination includes a 90-day fund hold and loss of all processed payments.

2. **nginx.conf has no HTTPS — SSL is not wired up despite the Certbot volume mount existing** — The site will deploy over plain HTTP to a VPS. Stripe webhooks require HTTPS. OAuth redirect tokens travel unencrypted. Fix by replacing `nginx` image with Caddy (automatic HTTPS) or by performing the two-phase certbot bootstrap if keeping nginx. Must be verified before any production feature is tested: `curl -I http://yourdomain.com` must return 301.

3. **Email DNS (SPF/DKIM/DMARC) must be configured before any email feature works** — Without SPF, DKIM, and DMARC records, Gmail/Yahoo/Outlook route emails to spam or drop them silently. Password reset emails in spam = users cannot recover accounts. Configure all three DNS records in Resend's dashboard and verify propagation (`dig TXT yourdomain.com`) before the first production signup. Verify deliverability at mail-tester.com (aim for 9/10 or higher). Domain reputation recovery after initial spam delivery takes weeks.

4. **Stripe cancellation must use `cancel_at_period_end=True`, not immediate cancel** — Using `stripe.Subscription.cancel()` (immediate) instead of `stripe.Subscription.modify(cancel_at_period_end=True)` causes the user to lose access while still on the cancellation confirmation screen, and triggers the `customer.subscription.deleted` webhook immediately, which the existing webhook handler uses to set status to `canceled` in the database. Users will see 402 errors on chat moments after cancelling.

5. **Google Sign-In email collision with existing email+password users** — Email confirmation is disabled in Supabase (confirmed in `auth.py` comments). This means all existing users have "unverified" email status from Supabase's perspective. When those users attempt Google OAuth with the same email, Supabase removes their unconfirmed identity before linking the Google identity, potentially invalidating existing sessions. Run a one-time migration to mark all existing password-signup users as email-verified before enabling Google Sign-In.

**Additional pitfalls to plan around:**
- Password reset endpoint must return identical responses for registered and unregistered emails (email enumeration attack is a GDPR/privacy violation on an adult-adjacent platform)
- Admin dashboard needs role-based access control added before any analytics data is exposed; `ProtectedRoute` (requires login) is not the same as admin-role check
- Cancellation churn flow must be legally compliant: survey is optional (skip-and-cancel must work), maximum 3 clicks from intent to confirmation, no more friction after confirmation (California ARL, EU DSA, FTC click-to-cancel enforcement)
- SAFE-03 (TAKE IT DOWN Act) takes effect May 19, 2026 — 48-hour takedown process must be operational before that date regardless of v1.1 milestone status

## Implications for Roadmap

Based on combined research from all four files, the recommended phase structure for v1.1 is:

### Phase 1: Infrastructure + Email Foundation
**Rationale:** This is the hard prerequisite for everything else. SSL must be verified before any production URL is tested. Email DNS must propagate (24-48 hours) before any feature that sends email can be validated. These are sequential blockers with long lead times.
**Delivers:** Caddy replacing nginx (automatic HTTPS verified on production domain), SPF/DKIM/DMARC DNS records configured and verified, Resend account + domain verified, `resend` Python SDK installed, `email/` service module created with welcome + receipt + cancellation templates, `usage_events` and `churn_surveys` Supabase migrations applied
**Avoids:** Pitfall #2 (nginx no HTTPS), Pitfall #3 (email deliverability / DNS), Pitfall #6 (email landing in spam)
**Research flag:** Standard patterns — no deeper research needed; follow Resend's domain verification guide and Caddy docs

### Phase 2: Auth Polish (Google OAuth + Password Reset)
**Rationale:** Both features touch the same UI surface (login/signup pages) and the same auth system. Shipping them together avoids touching those pages twice. Google OAuth requires the production domain to be configured (depends on Phase 1 HTTPS being live). Email confirmation migration must run before Google Sign-In is enabled for existing users.
**Delivers:** `@supabase/supabase-js` added to frontend for PKCE flow, "Continue with Google" button on login + signup pages, `/auth/callback` React route (reads session post-OAuth), `/forgot-password` page, `/reset-password` page, rate limiting on password reset endpoint, email enumeration prevention (identical response for all emails), one-time migration marking existing users as email-verified
**Avoids:** Pitfall #3 (Google OAuth redirect URI mismatch — requires HTTPS domain), Pitfall #4 (email collision with existing users), Pitfall #7 (password reset email enumeration)
**Research flag:** Standard patterns for Supabase OAuth — follow Supabase docs. The email collision migration is a one-time script; run it before enabling the Google Sign-In button.

### Phase 3: Landing Page
**Rationale:** The landing page is the highest-leverage acquisition asset and the most visible expression of the Stripe framing constraint. Copy decisions made here affect the Stripe account description, ad channel choices, and SEO. Ship after auth is proven (visitors landing on `/` must be able to log in) but before billing (so there is an acquisition funnel active when billing launches).
**Delivers:** `LandingPage.tsx` at `/` route (unauthenticated visitors only; authenticated users redirect to `/chat`), hero + features + pricing + second CTA + FAQ sections, `react-helmet-async` for meta tags/OG, landing page copy that frames product as "AI companion/assistant" (never intimate AI), Stripe account business description review
**Avoids:** Pitfall #1 (Stripe adult content termination — landing page copy is the primary trigger), Pitfall #9 (ad channel blocks — landing page framing affects Google Ads eligibility)
**Research flag:** No technical research needed; the framing decision (Pitfall #1) is a business/legal decision that must be made before writing a single word of copy.

### Phase 4: Billing + Churn Flow
**Rationale:** Billing management, cancellation, and transactional email receipts/confirmations are tightly coupled: the billing page hosts the cancel button, cancel triggers the confirmation email, and the receipt email is fired from Stripe webhook events already flowing through `billing.py`. They must ship as a unit. Depends on email infrastructure from Phase 1.
**Delivers:** `BillingPage.tsx` at `/billing` (shows plan name, next billing date, payment method, cancel button), `POST /billing/portal` endpoint (Stripe Customer Portal redirect), `GET /billing/subscription` endpoint, `CancelPage.tsx` multi-step churn flow with optional exit survey, `POST /billing/survey` + `POST /billing/cancel` endpoints, `stripe.Subscription.modify(cancel_at_period_end=True)` implementation, receipt email fired from `invoice.payment_succeeded` webhook, cancellation confirmation email fired from `customer.subscription.deleted` webhook, `customer.subscription.updated` webhook handler to store `cancel_at_period_end` flag
**Avoids:** Pitfall #5 (Stripe cancel race condition — use period-end not immediate cancel), Pitfall #10 (cancellation dark pattern — survey optional, ≤3 clicks), Pitfall #1 (Stripe framing — billing page copy must also avoid adult content language)
**Research flag:** No new research needed; Stripe Customer Portal and `cancel_at_period_end` are well-documented patterns.

### Phase 5: Admin Dashboard
**Rationale:** Admin dashboard is standalone — no user-facing dependencies. It is the lowest-urgency v1.1 feature (operator visibility is needed but is not blocking user acquisition or retention). Schedule it last so it does not delay user-facing features. However, event emission points must be added to the codebase during earlier phases when touching those code paths — accumulating events from Phase 1 onward means more data is available when the dashboard is built.
**Delivers:** `recharts ^3.7.0` npm package installed, `require_admin` FastAPI dependency (reads `app_metadata.role` from JWT), `admin.py` router with `GET /admin/stats/overview` and `GET /admin/stats/revenue` endpoints, `AdminPage.tsx` at `/admin` (role-gated, stat cards + Recharts line/bar charts), usage event emission in message handler + image pipeline + billing webhook, admin role set via one-time `supabase_admin` CLI call, Redis caching of admin queries (5-minute TTL), indexes on `usage_events` table verified
**Avoids:** Pitfall #8 (admin N+1 queries + no access control — add role check before exposing any data; use aggregating SQL with indexes not per-row queries)
**Research flag:** No deeper research needed; patterns are well-established (Recharts docs, Supabase app_metadata RBAC).

### Phase Ordering Rationale

- **Infrastructure first (Phase 1):** HTTPS and email DNS have the longest lead times (DNS propagation takes 24-48 hours; Caddy needs a live domain). Starting here unblocks everything else in parallel.
- **Auth second (Phase 2):** Google OAuth cannot be tested without HTTPS. Password reset cannot be tested without email delivery. Both depend on Phase 1.
- **Landing page third (Phase 3):** The framing decision (how to describe the product without triggering Stripe) must be locked in before billing launches. Landing page brings in the users who will hit the billing flows.
- **Billing + churn fourth (Phase 4):** The revenue-critical flows. Depends on email infrastructure (Phase 1) for receipt/cancellation emails. Depends on auth polish (Phase 2) for user to have a valid session on the billing page.
- **Admin last (Phase 5):** Standalone; event data accumulates during earlier phases; dashboard can ship after user-facing features are stable.

**Parallelizable work within phases:**
- Phase 1: Caddy migration and email DNS configuration can proceed simultaneously (different team members or days)
- Phase 2: Google OAuth frontend work and password reset UI can proceed simultaneously once Supabase providers are configured
- Phase 4: `BillingPage.tsx` frontend and `/billing/portal` backend can proceed in parallel

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (Landing Page):** No technical research needed but copy and imagery decisions require stakeholder sign-off on the Stripe framing constraint before writing begins. This is a business decision, not a technical one.
- **SAFE-03 compliance (cross-phase):** The TAKE IT DOWN Act (May 19, 2026 deadline, 2.5 months away) requires a 48-hour takedown response process. This is not a feature in any of the five phases above — it is a compliance deliverable that must be addressed outside the standard feature roadmap. Flag for immediate attention.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Infrastructure):** Caddy docs are excellent; Resend domain verification is a guided process; SPF/DKIM/DMARC records have standard formats.
- **Phase 2 (Auth):** Supabase Google OAuth is well-documented; password reset flow is a Supabase one-call operation.
- **Phase 4 (Billing):** Stripe Customer Portal and `cancel_at_period_end` are stable, well-documented Stripe APIs.
- **Phase 5 (Admin):** Recharts API is mature; Supabase app_metadata RBAC is a documented pattern.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Only 2 new packages; both confirmed against official release notes and peer dependency declarations. Caddy is production-proven. All existing stack versions confirmed compatible. |
| Features | HIGH | All 7 features are SaaS industry standard patterns with extensive documentation and prior art. No experimental or novel features in scope for v1.1. |
| Architecture | HIGH | Integration approach is additive to existing architecture; no novel patterns introduced. Caddy configuration is straightforward; all new FastAPI routes follow existing patterns in the codebase. |
| Pitfalls | HIGH | All critical pitfalls verified against official documentation: Stripe restricted businesses policy (official policy text), Supabase identity linking behavior (official docs), email authentication standards (Gmail/Yahoo 2024-2025 enforcement), FTC/California ARL enforcement history. |

**Overall confidence:** HIGH

### Gaps to Address

- **SAFE-03 / TAKE IT DOWN Act deadline (May 19, 2026):** This is a hard legal deadline 2.5 months away. The research identifies the risk but the compliance deliverables (48-hour takedown process, designated agent, operational response procedure) are not part of any v1.1 feature phase. This must be tracked separately. It does not require a code change — it requires a documented process and a contact mechanism. Do not let it fall through the cracks while the team is focused on feature development.

- **Stripe account business description review:** The current Stripe account may already have a description that references intimate AI or adult content if it was registered during v1.0 development. Before the landing page ships (Phase 3), verify the Stripe account business description against the framing constraint and update it if necessary.

- **Supabase Site URL configuration:** Supabase Dashboard → Authentication → URL Configuration → Site URL defaults to localhost in new projects. This must be updated to the production domain before Google OAuth goes live. It is an invisible configuration gap (not in code) that causes `redirect_uri_mismatch` errors on production.

- **Recharts version confirmation:** `recharts ^3.7.0` peer dependency for React 19 was confirmed by multiple sources but MEDIUM confidence (npm package peer dep declarations vs actual runtime compatibility). Verify with a quick `npm install recharts@^3.7.0` in the project and confirm no peer dep warnings before building the admin dashboard.

- **Hetzner CX32 vs CX22 decision:** Research recommends CX32 (4 vCPU, 8 GB RAM, ~€6.80/mo) over CX22 (4 GB RAM) for the VPS due to OOM risk during image generation queue bursts. If the VPS is already provisioned as CX22, this is a cost/risk trade-off to make consciously before production launch.

## Sources

### Primary (HIGH confidence)
- [Stripe Restricted Businesses Policy](https://stripe.com/legal/restricted-businesses) — AI-generated adult content prohibition (official policy text)
- [Supabase Identity Linking docs](https://supabase.com/docs/guides/auth/auth-identity-linking) — email collision behavior with unverified accounts
- [Supabase Google Auth guide](https://supabase.com/docs/guides/auth/social-login/auth-google) — provider configuration steps
- [Supabase RBAC / app_metadata guide](https://supabase.com/docs/guides/database/postgres/custom-claims-and-role-based-access-control-rbac) — admin role via JWT claims
- [Supabase resetPasswordForEmail](https://supabase.com/docs/reference/python/auth-resetpasswordforemail) — password reset API
- [Stripe Customer Portal integration](https://docs.stripe.com/customer-management/integrate-customer-portal) — portal session creation
- [Stripe webhook best practices](https://docs.stripe.com/billing/subscriptions/webhooks) — `cancel_at_period_end` behavior
- [OWASP Forgot Password Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html) — email enumeration prevention, rate limiting
- [Resend PyPI](https://pypi.org/project/resend/) — v2.23.0 release date and SDK stability
- [Google Ads Dating & Companionship Policy (Aug 2025)](https://support.google.com/adspolicy/answer/15328393) — chatbot disclosure requirements, certification

### Secondary (MEDIUM confidence)
- [Recharts npm](https://recharts.org) — v3.7.0 React 18/19 peer dependency (multiple sources agree)
- [jonasal/nginx-certbot GitHub](https://github.com/JonasAlfredsson/docker-nginx-certbot) — alternative SSL approach if keeping nginx
- [Hetzner Cloud pricing](https://www.hetzner.com/cloud) — CX32 specs and pricing (subject to change)
- [Certbot + nginx bootstrap pattern](https://dev.to/marrouchi/the-challenge-about-ssl-in-docker-containers-no-one-talks-about-32gh) — two-phase SSL setup
- [Churnkey cancellation flow data](https://churnkey.co/resources/customer-exit-survey/) — 25-30% save rate with targeted cancellation flows
- [FTC click-to-cancel enforcement](https://www.coulsonpc.com/coulson-pc-blog/dark-patterns-ftc-click-to-cancel-rule) — legal risk of dark patterns in cancellation
- [Amazon $2.5B FTC settlement 2025](https://lawandcrime.com/lawsuit/feds-accuse-amazon-of-using-dark-patterns-and-roach-motel-techniques-to-trick-customers-into-auto-renewing-prime-memberships/) — dark pattern enforcement precedent
- [Email deliverability SPF/DKIM/DMARC setup](https://www.mailgun.com/blog/dev-life/how-to-setup-email-authentication/) — DNS record configuration
- [Gmail/Yahoo 2024-2025 sender requirements](https://saleshive.com/blog/dkim-dmarc-spf-best-practices-email-security-deliverability/) — mandatory authentication enforcement

### Tertiary (LOW confidence, needs validation)
- Hetzner CX32 monthly pricing (~€6.80/mo) — subject to April 2026 adjustment per research notes

---
*Research completed: 2026-03-02*
*Ready for roadmap: yes*
