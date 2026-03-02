# Feature Research

**Domain:** Dual-Mode AI Companion — v1.1 Launch-Ready Features
**Researched:** 2026-03-02
**Confidence:** HIGH (v1.0 core); HIGH (v1.1 SaaS patterns, well-established)

---

## Scope Note

This document covers two scopes:

- **Part A** — v1.1 Launch-Ready Features (7 new features being researched now)
- **Part B** — v1.0 Core AI Companion Features (preserved from prior research, 2026-02-23)

Roadmap and requirements work for v1.1 should reference Part A primarily.

---

# Part A: v1.1 Launch-Ready Features

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Landing page with clear value prop** | Every SaaS has one; users expect to understand the product before signing up | LOW | Hero + features + pricing + CTA. Conversion-critical. Figma design will be provided. |
| **Sign in with Google** | Dominant auth pattern in 2026; "email+password is friction" | LOW | Supabase supports Google OAuth natively; PKCE handled by `@supabase/supabase-js` |
| **Password reset via email** | Industry standard; users expect it; OWASP requirement | LOW | Supabase has built-in password reset flow; just need UI + email routing |
| **View current plan and billing date** | Users paying monthly need to know what they're paying for | LOW | Stripe subscription object has `current_period_end`; display it |
| **Cancel subscription self-service** | Required by consumer protection law in most markets; users demand it | MEDIUM | Stripe handles actual cancellation; need UI flow + churn survey |
| **Welcome email on signup** | Users expect a confirmation + orientation email immediately | LOW | Highest open rate of any email type (4x normal); do not skip |
| **Payment receipt email** | Expected by every paying user; required for tax/accounting | LOW | Stripe webhook `invoice.paid` → send receipt |
| **Cancellation confirmation email** | Users need proof their account is cancelled; reduces chargebacks | LOW | Stripe webhook `customer.subscription.deleted` → send email |

### Differentiators (Competitive Advantage)

Features that go beyond table stakes and build trust, reduce churn, or improve conversion.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Exit survey before cancel** | Captures churn reasons; enables targeted saves (discount, pause) | MEDIUM | 25-30% of cancellations can be saved with right offer; data feeds product roadmap |
| **Targeted retention offer in churn flow** | "Here's 20% off" or "Pause instead of cancel" presented based on survey answer | MEDIUM | Tied to exit survey response; dynamic offer based on stated reason |
| **Admin analytics dashboard** | Operator visibility into active users, revenue, content metrics; enables data-driven decisions | MEDIUM | Build custom `/admin` page; Stripe + Supabase data; no third-party dashboard needed |
| **Pricing table on landing page** | Transparent pricing reduces decision anxiety; leads who see pricing convert higher | LOW | Single tier (v1.1); clear feature list per plan |
| **Social proof on landing page** | Trust signals near CTAs lift conversion; companion-app users respond to peer validation | LOW | User count, testimonials, or "X photos generated" style metrics |
| **Subscription pause option** | Alternative to full cancel; reduces hard churn; common in consumer subscriptions | MEDIUM | Stripe supports subscription pausing natively; UI integration needed |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Build custom billing portal** | "We need full control over the billing UI" | Significant dev time; Stripe Customer Portal handles 90% of use cases for free | Use Stripe Customer Portal for complex billing ops; build only the plan-view and cancel CTA in the app |
| **Multi-step complex onboarding wizard** | "Guide users through every feature" | Friction before value; users abandon before completing | Single welcome email with 3 key actions; keep signup → first chat path under 60 seconds |
| **Mandatory marketing email opt-in on signup** | "Build the email list" | Reduces signup conversion; GDPR requires separate consent from transactional emails | Send only transactional emails without consent; offer optional newsletter opt-in separately |
| **Full analytics platform (Mixpanel/Amplitude)** | "We need deep user analytics" | Overkill for a new product; adds cost and complexity | Simple admin dashboard with Supabase queries + Stripe webhooks covers all needs for launch |
| **Social login with multiple providers** | "Give users all options" | Each provider adds integration work; Google covers 70-80% of users | Google OAuth only for v1.1; add Apple/GitHub/Facebook based on user demand post-launch |
| **Complex multi-tier pricing on landing page** | "Show all options" | Analysis paralysis reduces conversion for new products | Single plan or two clear tiers max; pricing page can expand later |

---

## v1.1 Feature Deep-Dives

### 1. Landing Page

**What makes a good SaaS/companion landing page:**

The hero section is the most important element. Visitors decide within 5 seconds. Requirements:
- Headline: outcome-focused, under 8 words ("Your AI companion who gets things done")
- Subheadline: one sentence explaining the dual-mode differentiator
- Primary CTA: "Get Started" or "Start Free" — single button, above the fold
- No navigation clutter that competes with the CTA

**Structural formula** (validated for SaaS landing pages, 2026):
1. Hero — value prop + CTA
2. Social proof strip — user count or "X conversations today" (even if small, signals activity)
3. Features section — 3-4 key capabilities with icons/visuals
4. How it works — 3-step visual (sign up → build avatar → start chatting)
5. Pricing — transparent; single plan for v1.1
6. Second CTA — repeat the primary CTA
7. FAQ — address 3-4 common objections (privacy, content safety, cancellation)

**Companion-app specific considerations:**
- Adult content nature means Google/Facebook ads are restricted; landing page must convert organic + word-of-mouth traffic efficiently
- Social proof matters more when the product is intimate/personal; anonymized testimonials or user counts build trust
- Pricing must be visible; hiding it increases bounce rate for subscription products
- Privacy reassurance near the CTA ("Your chats stay private") reduces conversion friction specific to this domain

**Table stakes vs differentiators for the landing page:**
- Table stakes: hero, features, pricing, CTA, mobile responsive
- Differentiator: social proof, how-it-works visual, FAQ section, testimonials

**Complexity:** LOW — Figma design provided; implementation is React + Tailwind, no backend needed

---

### 2. Admin Analytics Dashboard

**What metrics matter most at launch (new SaaS):**

For a new product, vanity metrics waste attention. The metrics that matter are:

**Tier 1 — Health indicators (check daily):**
- Active users last 7 days (DAU/WAU) — leading indicator of engagement and churn risk
- Messages sent (total + per user average) — validates product is being used
- Photos generated — validates image feature adoption; tracks ComfyUI spend
- Subscriptions active — revenue health; compare to signups to see conversion rate
- New signups (last 7/30 days) — acquisition signal

**Tier 2 — Revenue health (check weekly):**
- MRR (Monthly Recurring Revenue) — core health metric
- Churn this month (count + %) — retention signal
- Subscription conversion rate (signups → paying) — funnel efficiency

**Tier 3 — Operational (check on alerts):**
- Failed image generation rate — ComfyUI reliability
- Error rate (5xx) — system health

**What to skip at launch:**
- LTV, CAC, NPS — too little data to be meaningful at launch
- Cohort analysis — add after 90 days of data
- Revenue expansion metrics — no upsells yet

**Implementation approach:**
- `/admin` page with route guard (admin role check)
- Supabase queries for user/message/photo counts
- Stripe API for subscription counts and MRR
- No third-party analytics tool needed; simple SQL aggregations

**Complexity:** MEDIUM — SQL queries straightforward; auth guard + dashboard UI takes time

---

### 3. Cancellation / Churn Flow

**Industry-validated flow structure:**

```
User clicks "Cancel subscription"
    → Step 1: Exit survey (1 primary question + optional follow-up)
    → Step 2: Retention offer (based on survey answer, presented before final confirm)
    → Step 3: Confirm cancellation (final action; no more friction after this point)
    → Immediate: Cancellation confirmation email
    → Access retained until end of billing period
```

**Exit survey — primary question:**

"Why are you cancelling today?" (multiple choice, pick one)

Recommended options (validated across SaaS industry):
1. Too expensive / can't afford it right now
2. Not using it enough to justify the cost
3. Missing a feature I need
4. Switching to a different service
5. Technical problems or poor quality
6. Just wanted to try it
7. Other (text field)

**Second question (optional, shown after primary):**
"Is there anything we could do to change your mind?" (open text, 2-3 sentence limit)

**Retention offers by reason:**

| Survey Answer | Offer to Show |
|---------------|---------------|
| Too expensive | 30% discount for 2 months |
| Not using it enough | Pause subscription for 30 days instead |
| Missing a feature | "We're working on X — here's our roadmap; stay another month free" |
| Switching to competitor | No offer; just confirm and exit gracefully |
| Technical problems | Connect to support immediately; offer service credit |
| Just wanted to try it | No offer; confirm and exit |

**Key rules:**
- Trigger exit survey AFTER user clicks cancel, not before (respect intent; increases honesty)
- Maximum 2 questions; survey response rate drops 17% per additional question above 5
- Do not show the retention offer before the survey answer — target it to the stated reason
- After final confirm, DO NOT show more popups or friction; it damages brand
- Churnkey.co data: targeted cancellation flows save 25-30% of at-risk subscribers
- Access should remain active until billing period ends (Stripe `cancel_at_period_end`)

**Complexity:** MEDIUM — UI/UX is straightforward; the offer logic adds branching complexity

---

### 4. User-Facing Subscription Management

**What users expect to see:**

| Element | Why Needed | Source |
|---------|-----------|--------|
| Current plan name and price | Users forget what they're paying | Basic expectation |
| Next billing date | "When will I be charged again?" is top support question | Basic expectation |
| Payment method (last 4 digits) | Confirm which card is on file | Basic expectation |
| Upgrade/downgrade options | Self-serve plan changes reduce support burden | Table stakes |
| Cancel button | Required by law in most markets; users demand it | Table stakes |
| Invoice/receipt history | Users need for tax/accounting | Table stakes |

**Implementation approach — two options:**

Option A: Stripe Customer Portal (recommended for v1.1)
- Redirect user to Stripe's hosted portal (`/api/billing/portal` → `POST /billing-portal/sessions`)
- Stripe handles plan changes, payment method updates, invoice history, cancellation
- Co-branded with your logo; no custom UI needed
- Con: less control over churn flow (can't intercept with exit survey before cancel)

Option B: Custom subscription page + Stripe API
- Build the plan/billing display in-app (React page with Stripe subscription data)
- Handle cancel via custom flow that includes the exit survey
- Con: more dev work; must handle Stripe data display manually

**Recommendation:** Hybrid approach
- Build a simple in-app "Billing" page showing plan name, next billing date, payment method
- "Cancel Subscription" button triggers the custom exit survey flow (so churn data is captured)
- "Manage Payment Method" and "View Invoices" redirect to Stripe Customer Portal

This gives the best of both worlds: churn flow control + Stripe's billing management robustness.

**Complexity:** MEDIUM — Stripe API queries for subscription data; portal redirect is simple; custom cancel flow adds complexity

---

### 5. Transactional Emails

**Email 1: Welcome Email (trigger: user signs up)**

Purpose: Orient user, reduce first-session abandonment, set expectations.

Content structure:
- Subject: "Welcome to Ava — here's how to get started" (personalized, not "Welcome!")
- Opening: "Hi [Name], your AI companion is ready."
- 3 bullet points: what Ava does (dual mode), how to start (go to web app or WhatsApp link), one key action (build your avatar)
- Single CTA button: "Start chatting with Ava"
- Tone: warm, direct; matches intimate/personal brand

Do NOT include: long feature lists, multiple CTAs, newsletter signup in first email.

Note: Welcome emails have 4x open rate and 5x click rate of standard emails — make the single CTA count.

**Email 2: Payment Receipt (trigger: Stripe `invoice.paid` webhook)**

Purpose: Confirm charge, provide tax record, build trust.

Content structure:
- Subject: "Your Ava receipt — [Amount] charged on [Date]"
- Clear amount, date, last 4 card digits, billing period covered
- Link to invoice PDF (Stripe provides hosted invoice URL)
- "Manage your subscription" link → billing page
- Sender: billing@[domain] (not noreply — reduces spam classification)

Do NOT include: upsells, feature announcements in the receipt email — users scrutinize receipts; off-topic content erodes trust.

**Email 3: Cancellation Confirmation (trigger: Stripe `customer.subscription.deleted` or `cancel_at_period_end` set)**

Purpose: Confirm cancellation, state access expiry date, leave door open to return.

Content structure:
- Subject: "Your Ava subscription has been cancelled"
- Confirm cancellation, state exact date access ends
- What happens to their data (important for GDPR/trust: "Your avatar and conversation history are saved for 30 days")
- Optional: single low-pressure re-subscribe CTA ("Changed your mind? Reactivate any time")
- No offer (the offer was in the churn flow; repeating it in the email feels manipulative)
- Sender: support@[domain] (human-feeling, not billing)

**Email delivery infrastructure (Supabase + SMTP):**

Supabase Auth handles welcome/password-reset emails natively via its SMTP integration. For receipt and cancellation emails triggered by Stripe webhooks, a transactional email provider is needed:
- Resend (recommended): modern API, generous free tier (3,000 emails/month), excellent deliverability, React Email template support
- Postmark: excellent deliverability, higher cost
- SendGrid: widely used but more complex setup

Supabase + Resend is the lowest-friction stack for this project's existing architecture.

**Complexity:** LOW for email content/templates; LOW-MEDIUM for webhook-triggered delivery setup

---

### 6. Google OAuth

**Standard flow for Supabase + React:**

Supabase provides native Google OAuth via `supabase.auth.signInWithOAuth({ provider: 'google' })`. This handles PKCE automatically for web clients. The implementation is:

1. Google Cloud Console: create OAuth 2.0 Web Client, add authorized redirect URIs (Supabase callback URL)
2. Supabase Dashboard: enable Google provider, paste Client ID + Secret
3. Frontend: call `signInWithOAuth` on button click; Supabase handles the redirect, code exchange, and session creation
4. Backend: Supabase JWT validates automatically via RLS; no backend changes needed

**Security best practices (from Google's official docs):**
- Never embed client secret in frontend code; Supabase backend holds it
- Use PKCE (enabled by default in `@supabase/supabase-js` v2+)
- Use incremental authorization — only request profile + email scopes at login; don't request Google Calendar scopes upfront
- Do not use embedded webviews for OAuth — Google blocks this (policy enforcement)
- Redirect URI must exactly match what's in Google Cloud Console

**UX considerations:**
- "Continue with Google" button must use Google's official branding guidelines (specific button style, "G" logo)
- Show the button prominently on both login and signup pages
- For existing email+password users, handle account linking edge case (same email registered via both methods)

**Account linking edge case:** When a user who signed up with email+password tries Google OAuth with the same email, Supabase will either link automatically (if configured) or throw an error. This must be handled gracefully with a clear message.

**Complexity:** LOW — Supabase abstracts nearly all OAuth complexity; main work is Google Cloud Console setup and button UI

---

### 7. Password Reset

**Standard OWASP-compliant flow:**

```
User enters email on "Forgot Password" page
    → Generic response shown: "If an account exists for that email, a reset link has been sent"
    → Supabase sends email with time-limited reset link (default: 1 hour)
    → User clicks link → Supabase validates token, redirects to /reset-password
    → User enters new password (with strength requirements shown inline)
    → Password updated → all existing sessions invalidated → redirect to login
```

**Security requirements (OWASP standard):**
- Always return the same response regardless of whether email exists (prevent email enumeration)
- Token expires after 15-60 minutes (Supabase default is 1 hour; acceptable)
- Token is single-use: invalidated immediately after successful reset
- All existing sessions invalidated after reset (security requirement)
- Store only token hash in DB, never plaintext

**UX best practices:**
- "Forgot password?" link must be near the password field (not buried in settings)
- After successful reset, show success message with clear next step ("Password updated — log in")
- Inline password strength indicator during new password entry (green checkmarks for requirements)
- On mobile: large buttons, sufficient tap target size

**Supabase implementation:** `supabase.auth.resetPasswordForEmail(email, { redirectTo: 'https://[domain]/reset-password' })` — one API call. The `/reset-password` page calls `supabase.auth.updateUser({ password: newPassword })` after the user lands with the session token in the URL.

**Note:** Supabase handles the token generation, email sending (via SMTP integration), and validation. The main implementation work is the UI for the two pages (request form + new password form).

**Complexity:** LOW — Supabase handles the hard parts; two simple UI pages needed

---

## Feature Dependencies (v1.1)

```
[Google OAuth]
    └──requires──> [Supabase Google Provider configuration]
    └──shares UI with──> [Password Reset] (both on login/signup pages)

[Password Reset]
    └──requires──> [Transactional Email delivery] (SMTP/Resend)
    └──built on──> [Supabase auth.resetPasswordForEmail]

[Landing Page]
    └──requires──> [Pricing information] (plan name, price)
    └──links to──> [Signup page] (primary CTA destination)

[Subscription Management Page]
    └──requires──> [Stripe API integration] (subscription data)
    └──links to──> [Cancellation Churn Flow]

[Cancellation Churn Flow]
    └──requires──> [Subscription Management Page] (entry point)
    └──requires──> [Stripe cancel_at_period_end API]
    └──triggers──> [Cancellation Confirmation Email]

[Admin Dashboard]
    └──requires──> [Admin role guard] (route protection)
    └──requires──> [Supabase aggregation queries]
    └──requires──> [Stripe API for MRR/subscription counts]

[Transactional Emails]
    └──welcome email triggered by──> [Supabase auth signup event]
    └──receipt email triggered by──> [Stripe invoice.paid webhook]
    └──cancellation email triggered by──> [Stripe subscription.deleted webhook]
    └──requires──> [Resend or SMTP provider configured]
```

### Dependency Notes

- **Google OAuth must not block password reset:** They are parallel auth features; both should ship together in the same auth-polish phase
- **Cancellation churn flow requires subscription management page:** The cancel button lives on the billing page; they ship together
- **Transactional emails require Resend/SMTP before Stripe webhooks can send receipts:** Email infrastructure must be set up before webhook handlers emit emails
- **Admin dashboard is standalone:** No user-facing dependencies; can ship in any order relative to other v1.1 features
- **Landing page is standalone:** No backend dependencies for display; links to existing signup flow

---

## MVP Definition (v1.1 Milestone)

### Must Ship for v1.1

All 7 features below are table stakes for a "launch ready" product. None are optional.

- [ ] **Landing page** — Without it, there is no acquisition funnel; the product cannot acquire organic users
- [ ] **Google OAuth** — Expected by modern users; email+password-only is friction that reduces conversion
- [ ] **Password reset** — Required by user expectation and security best practices; blocking issue for real users
- [ ] **User subscription management page** — Paying users need to see their plan; missing = trust failure
- [ ] **Cancellation churn flow with exit survey** — Required for retention data and legal compliance (self-serve cancel)
- [ ] **Transactional emails (welcome, receipt, cancellation)** — Professional product baseline; Stripe receipts especially are expected by every paying user
- [ ] **Admin analytics dashboard** — Operator cannot make product decisions without visibility into usage

### Recommended Phase Groupings

**Phase A: Auth Polish** (Google OAuth + Password Reset)
These belong together; both touch the login/signup UI and auth system.

**Phase B: Landing Page**
Independent; requires Figma design handoff before starting. Can run in parallel with Phase A.

**Phase C: Billing & Subscription Management** (Subscription page + Cancellation flow + Transactional emails)
These are tightly coupled: billing page hosts cancel button; cancel triggers email; emails need Stripe webhooks.

**Phase D: Admin Dashboard**
Standalone; can slot anywhere. Lower urgency relative to user-facing features.

### Add After v1.1

- [ ] **Subscription pause option** — Reduces hard churn; add after seeing exit survey data to validate demand
- [ ] **Reactivation flow** — "Welcome back" email to churned users; needs a base of churned users first
- [ ] **Newsletter / marketing email sequence** — Nurture leads who visited but didn't convert; add post-launch

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Landing page | HIGH | LOW | P1 |
| Google OAuth | HIGH | LOW | P1 |
| Password reset | HIGH | LOW | P1 |
| Welcome email | HIGH | LOW | P1 |
| Payment receipt email | HIGH | LOW | P1 |
| Cancellation confirmation email | HIGH | LOW | P1 |
| User subscription management page | HIGH | MEDIUM | P1 |
| Cancellation churn flow + exit survey | HIGH | MEDIUM | P1 |
| Admin analytics dashboard | MEDIUM | MEDIUM | P1 |
| Retention offer in churn flow | MEDIUM | MEDIUM | P2 |
| Subscription pause option | MEDIUM | MEDIUM | P2 |
| Apple / GitHub OAuth | LOW | MEDIUM | P3 |
| Multi-tier pricing on landing page | LOW | LOW | P3 |
| Reactivation email sequence | MEDIUM | LOW | P3 |

---

## Sources

### Landing Page Best Practices
- [20 Best SaaS Landing Pages + 2026 Best Practices — fibr.ai](https://fibr.ai/landing-page/saas-landing-pages)
- [18 B2B SaaS Landing Page Best Practices That Convert — SaaS Hero](https://www.saashero.net/design/saas-landing-page-best-practices/)
- [Best CTA Placement Strategies for 2026 — LandingPageFlow](https://www.landingpageflow.com/post/best-cta-placement-strategies-for-landing-pages)
- [15 SaaS Landing Page Best Practices — Userpilot](https://userpilot.com/blog/saas-landing-page-best-practices/)
- [The AI Companion Market in 2025 — Market Clarity](https://mktclarity.com/blogs/news/ai-companion-market)

### Admin Dashboard Metrics
- [SaaS Metrics Dashboard Template: Ultimate 2025 Guide — Flowjam](https://www.flowjam.com/blog/saas-metrics-dashboard-template-ultimate-2025-guide-free-files)
- [Ultimate Guide to SaaS Dashboard Metrics — Phoenix Strategy Group](https://www.phoenixstrategy.group/blog/ultimate-guide-to-saas-dashboard-metrics)
- [Top 12 Key SaaS Business Metrics — ZoomCharts](https://zoomcharts.com/en/microsoft-power-bi-custom-visuals/blog/top-12-key-saas-business-metrics-you-must-track-in-2025)

### Cancellation / Churn Flow
- [Cancellation Flow Examples from Famous SaaS — Userpilot](https://userpilot.com/blog/cancellation-flow-examples/)
- [How to Build Cancellation Surveys that Reduce Churn — Churnkey](https://churnkey.co/resources/customer-exit-survey/)
- [Exit Surveys: Examples & Questions for Churn Reduction — Usersnap](https://usersnap.com/blog/exit-surveys/)
- [How to Build Cancellation & Exit Surveys — Paddle](https://www.paddle.com/resources/customer-exit-survey)
- [12 Proven Ways to Reduce SaaS Churn Rate — Baremetrics](https://baremetrics.com/blog/proven-ways-reduce-saas-churn-rate)

### Subscription Management
- [Integrate the customer portal with the API — Stripe Docs](https://docs.stripe.com/customer-management/integrate-customer-portal)
- [Customer self-service with a customer portal — Stripe Docs](https://docs.stripe.com/customer-management)
- [How to Master SaaS Subscription Management — Ratio Blog](https://www.ratiotech.com/blog/saas-subscription-management)

### Transactional Emails
- [Transactional Email Best Practices — Postmark](https://postmarkapp.com/guides/transactional-email-best-practices)
- [10 Must-Have Transactional Email Templates for SaaS — Userpilot](https://userpilot.com/blog/transactional-email-templates/)
- [15+ Cancellation Email Examples for SaaS — Userlist](https://userlist.com/blog/saas-cancellation-emails/)
- [The Complete Guide to Non-Sucky SaaS Transactional Emails — Fix My Churn](https://fixmychurn.com/complete-guide-transactional-emails/)

### Google OAuth
- [Login with Google — Supabase Docs](https://supabase.com/docs/guides/auth/social-login/auth-google)
- [Best Practices for Implementing Sign in with Google — Google Developers](https://developers.google.com/identity/siwg/best-practices)
- [OAuth 2.0 Best Practices — Google Developers](https://developers.google.com/identity/protocols/oauth2/resources/best-practices)

### Password Reset
- [Forgot Password Cheat Sheet — OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html)
- [Password Reset Best Practices — Authgear](https://www.authgear.com/post/authentication-security-password-reset-best-practices-and-more)
- [Implementing a Forgot Password Flow — SuperTokens](https://supertokens.com/blog/implementing-a-forgot-password-flow)

---

# Part B: v1.0 Core Features (preserved from prior research, 2026-02-23)

> This section documents the v1.0 AI companion feature landscape. It is preserved for reference.
> All items marked [x] are already shipped. Do not re-research or re-plan these.

### v1.0 Table Stakes (All Shipped)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Text-based conversation** | Core interaction method | LOW | Shipped |
| **Context memory within session** | Users expect AI to remember conversation | LOW | Shipped |
| **Personality customization** | All companions offer this | MEDIUM | Shipped — 4 preset personas |
| **Avatar appearance customization** | Visual representation expected | MEDIUM | Shipped — gender, age, nationality, free text |
| **Basic image generation** | Companions generate photos | MEDIUM | Shipped — ComfyUI Cloud |
| **Mobile-first interface** | AI companions are mobile products | LOW | Shipped — WhatsApp IS the interface |
| **Privacy controls** | Data safety non-negotiable | MEDIUM | Shipped — RLS, Supabase |
| **Subscription billing** | Freemium standard | MEDIUM | Shipped — Stripe |
| **Age verification** | NSFW legal requirement | HIGH | Shipped — 20+ enforced |
| **Content safety guardrails** | Mandatory for NSFW | HIGH | Shipped — ContentGuard + crisis detection |

### v1.0 Differentiators (All Shipped)

| Feature | Value Proposition | Notes |
|---------|-------------------|-------|
| **Dual-mode switching** | Unique: one AI for work AND personal | Shipped — fuzzy intent detection |
| **WhatsApp-native experience** | Meets users where they are | Shipped — WhatsApp Business API |
| **Productivity integrations** | Calendar, research — no competitor does this | Shipped — Google Calendar + Tavily |
| **Modular skill system** | Future-proof plugin architecture | Shipped — Protocol pattern |
| **Platform-agnostic design** | Messaging adapter enables expansion | Shipped — WhatsApp + Web adapters |

### v1.0 Competitor Gap

No AI companion product combines productivity assistant + intimate companion in dual-mode design:
- Replika: wellness-only (pivoted away from intimate in 2026)
- Character.AI: fiction/RP only, no productivity
- Candy.AI / Crushon.AI: intimate only, no productivity
- ChatGPT: productivity only, no personalization

Ava's market position is this gap.

---

*Feature research for: Dual-Mode AI Companion — v1.1 Launch-Ready Features*
*Researched: 2026-03-02*
