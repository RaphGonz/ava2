# Roadmap: Ava — Dual-Mode AI Companion

## Milestones

- ✅ **v1.0 MVP** — Phases 1–7 + 07.1 (shipped 2026-03-02)
- 📋 **v1.1 Launch Ready** — Phases 8–13 (started 2026-03-02)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1–7 + 07.1) — SHIPPED 2026-03-02</summary>

- [x] Phase 1: Foundation & Compliance (2/2 plans) — completed 2026-02-23
- [x] Phase 2: Infrastructure & User Management (5/5 plans) — completed 2026-02-23
- [x] Phase 3: Core Intelligence & Mode Switching (4/4 plans) — completed 2026-02-23
- [x] Phase 4: Secretary Skills (5/5 plans) — completed 2026-02-24
- [x] Phase 5: Intimate Mode Text Foundation (4/4 plans) — completed 2026-02-24
- [x] Phase 6: Web App & Multi-Platform (6/6 plans) — completed 2026-02-24
- [x] Phase 7: Avatar System & Production (10/10 plans) — completed 2026-03-02
- [x] Phase 07.1: Switch Image Generation to ComfyUI Cloud (2/2 plans, INSERTED) — completed 2026-03-02

Full milestone archive: `.planning/milestones/v1.0-ROADMAP.md`

</details>

<details open>
<summary>📋 v1.1 Launch Ready (Phases 8–13) — IN PROGRESS</summary>

- [x] **Phase 8: Infrastructure & Deployment** — Production VPS live on HTTPS with all API credentials wired (completed 2026-03-05)
- [x] **Phase 9: Auth Polish & Email** — Google Sign-In works, password reset lands in inbox, welcome email received on signup (completed 2026-03-06)
- [x] **Phase 10: Landing Page** — Public acquisition page live at "/", CTA reaches signup, Stripe-safe copy (completed 2026-03-09)
- [x] **Phase 11: Subscription Management & Churn** — User can view plan, open Stripe portal, cancel in ≤3 clicks with optional survey (completed 2026-03-09)
- [x] **Phase 12: Admin Dashboard** — /admin shows key metrics, usage_events table accumulates events, regular users get 403 (completed 2026-03-10)
- [ ] **Phase 13: End-to-End Smoke Test & Milestone Validation** — Every core user journey verified in production before milestone is declared shipped

</details>

## Phase Details

### Phase 8: Infrastructure & Deployment
**Goal**: Production server is running, HTTPS-secured, firewall-hardened, and all external API credentials are verified and working
**Depends on**: Nothing (first phase of v1.1; v1.0 completed)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04, EMAI-01
**Success Criteria** (what must be TRUE):
  1. Visiting `https://yourdomain.com` serves the app — no certificate warnings, no HTTP fallback
  2. `curl -I http://yourdomain.com` returns 301 redirect to HTTPS (not a 200 over plain HTTP)
  3. A port scan shows only ports 80 and 443 reachable from the public internet; all other ports are blocked by the firewall
  4. All API health checks pass: WhatsApp webhook ping, ComfyUI image generation, Stripe checkout, OpenAI chat, Tavily search, and Supabase connection each return a success response
  5. Email DNS records (SPF, DKIM, DMARC) are configured on the sending domain and mail-tester.com scores 9/10 or higher — confirming emails will land in inbox, not spam
**Plans**: 4 plans

Plans:
- [x] 08-01-PLAN.md — Rewrite docker-compose.yml (nginx→Caddy), create Caddyfile + deploy.sh, add Resend config fields to config.py, create usage_events migration
- [x] 08-02-PLAN.md — Configure Resend sending domain DNS records (SPF/DKIM/DMARC) and update Supabase Site URL
- [x] 08-03-PLAN.md — Provision VPS, clone repo, create production .env, run deploy.sh, configure UFW firewall, verify HTTPS
- [x] 08-04-PLAN.md — Verify all API credentials functional + mail-tester.com score >= 9/10 (10/10 achieved)

### Phase 9: Auth Polish & Email
**Goal**: Users can sign in with Google, recover a forgotten password by email, and receive a welcome email after signing up
**Depends on**: Phase 8 (Google OAuth requires production HTTPS domain; password reset requires email DNS propagated; welcome email requires Resend domain verified)
**Requirements**: AUTH-01, AUTH-02, EMAI-02, EMAI-03, EMAI-04
**Success Criteria** (what must be TRUE):
  1. Clicking "Continue with Google" on the login page completes sign-in without any error and lands the user on /chat
  2. An existing email+password user can also sign in with Google using the same email address — no account collision or duplicate user created
  3. Requesting a password reset for a registered email delivers a working reset link to the inbox (not spam) within 2 minutes
  4. The password reset endpoint returns an identical response for both registered and unregistered emails (no email enumeration)
  5. A new user receives a welcome email within 60 seconds of completing signup; a subscriber receives a receipt email within 60 seconds of a successful Stripe payment; a cancelling user receives a confirmation email within 60 seconds of cancellation completing
**Plans**: 4 plans

Plans:
- [ ] 09-01-PLAN.md — Email service module (resend_client.py) + backend auth endpoints (forgot-password, send-email-hook, send-welcome)
- [ ] 09-02-PLAN.md — Wire receipt and cancellation emails into Stripe billing webhook handler
- [ ] 09-03-PLAN.md — Frontend: Supabase JS client, GoogleSignInButton, updated Login/Signup pages, ForgotPasswordPage, ResetPasswordPage
- [ ] 09-04-PLAN.md — Supabase Dashboard configuration + env vars + production deployment + end-to-end verification

### Phase 10: Landing Page
**Goal**: Visitors arriving at the root URL see a designed acquisition page that communicates the product's value and routes them to sign up
**Depends on**: Phase 9 (landing page CTA links to signup; auth must be functional before visitors are sent there)
**Requirements**: LAND-01, LAND-02, LAND-03
**Success Criteria** (what must be TRUE):
  1. An unauthenticated visitor navigating to "/" sees a designed page with at minimum: a hero section, a features section, and a pricing section
  2. Clicking any CTA button on the landing page navigates directly to the sign-up flow without intermediate pages
  3. An authenticated user navigating to "/" is redirected to /chat (landing page does not display to logged-in users)
  4. No word on the landing page uses terms like "intimate," "explicit," "NSFW," or "adult" — the product is framed as an AI companion/assistant throughout
**Plans**: 4 plans

Plans:
- [ ] 10-01-PLAN.md — Install deps (motion, lucide-react, clsx, tailwind-merge), port GlassCard from Figma, configure vitest, create failing test scaffold
- [ ] 10-02-PLAN.md — Port Hero and DualPromise sections (English copy, no Unsplash, pre-computed audio visualizer, CTA as Link)
- [ ] 10-03-PLAN.md — Port Trust and Pricing sections (light-bg GlassCard fix, pricing CTA routing to /signup)
- [ ] 10-04-PLAN.md — Port Footer (no 18+ block), assemble LandingPage with auth guard + sticky nav, all tests GREEN

### Phase 11: Subscription Management & Churn
**Goal**: Users can see their billing status, manage payment details via Stripe, and cancel with a friction-appropriate but legally compliant flow
**Depends on**: Phase 9 (user must be authenticated to access billing page; receipt and cancellation emails require email infrastructure from Phase 8)
**Requirements**: SUBS-01, SUBS-02, SUBS-03, SUBS-04, SUBS-05
**Success Criteria** (what must be TRUE):
  1. A subscribed user visiting the billing page sees their plan name, current status, and next billing date without any additional clicks
  2. Clicking "Manage billing" or "Update payment method" opens the Stripe Customer Portal in the same or new tab
  3. A user who initiates cancellation completes the full flow — survey (optional) through confirmation — in 3 clicks or fewer
  4. After cancellation, the user's subscription status shows `cancel_at_period_end=True` and they retain full access until the period end date displayed on the billing page
  5. The cancellation survey is skippable: a "Skip and cancel" option is present and functional — the user is never forced to complete the survey
**Plans**: TBD

### Phase 12: Admin Dashboard
**Goal**: The operator can view key product metrics from a protected /admin page, with usage events accumulating from earlier phases
**Depends on**: Phase 8 (production deployment must be live for real events to accumulate); Phase 9 (admin role assigned via Supabase; auth system must be operational)
**Requirements**: ADMN-01, ADMN-02, ADMN-03
**Success Criteria** (what must be TRUE):
  1. An operator with admin role visiting /admin sees at minimum: active users (7-day), messages sent, photos generated, active subscriptions, and new signups — all drawn from real data
  2. A regular (non-admin) user navigating to /admin receives a 403 response — no metrics are visible and no data is leaked
  3. The `usage_events` table in Supabase contains rows for at least four event types: `message_sent`, `photo_generated`, `mode_switch`, and `subscription_created` — confirming emission points are wired across the codebase
**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation & Compliance | v1.0 | 2/2 | Complete | 2026-02-23 |
| 2. Infrastructure & User Management | v1.0 | 5/5 | Complete | 2026-02-23 |
| 3. Core Intelligence & Mode Switching | v1.0 | 4/4 | Complete | 2026-02-23 |
| 4. Secretary Skills | v1.0 | 5/5 | Complete | 2026-02-24 |
| 5. Intimate Mode Text Foundation | v1.0 | 4/4 | Complete | 2026-02-24 |
| 6. Web App & Multi-Platform | v1.0 | 6/6 | Complete | 2026-02-24 |
| 7. Avatar System & Production | v1.0 | 10/10 | Complete | 2026-03-02 |
| 07.1. Switch Image Gen to ComfyUI Cloud | v1.0 | 2/2 | Complete (INSERTED) | 2026-03-02 |
| 8. Infrastructure & Deployment | v1.1 | 4/4 | Complete | 2026-03-05 |
| 9. Auth Polish & Email | 4/4 | Complete   | 2026-03-06 | - |
| 10. Landing Page | 4/4 | Complete    | 2026-03-09 | - |
| 11. Subscription Management & Churn | 3/3 | Complete    | 2026-03-09 | - |
| 12. Admin Dashboard | 3/3 | Complete   | 2026-03-10 | - |
| 13. End-to-End Smoke Test & Milestone Validation | v1.1 | 0/? | Not started | - |
| 14. UI Dark Theme Redesign | 4/4 | Complete    | 2026-03-10 | - |

### Phase 13: End-to-End Smoke Test & Milestone Validation
**Goal**: Every core user journey completes successfully in production — from signup through chat, mode switching, image generation, and subscription — before the milestone is declared shipped
**Depends on**: Phase 12 (all prior phases must be live and wired; smoke test runs against real production environment)
**Requirements**: All v1.1 requirements
**Success Criteria** (what must be TRUE):
  1. A new user can sign up, complete avatar setup, and see a reference image appear (non-null `reference_image_url` in Supabase) within 5 minutes — confirming ComfyUI pipeline works end-to-end
  2. A subscribed user can send a message in secretary mode and receive a coherent reply — confirming OpenAI + chat pipeline works
  3. The user can switch to intimate mode (via `/intimate` command) and back (`/secretary`) — confirming mode detection and session isolation work
  4. In intimate mode, asking for a photo results in a placeholder reply followed by an actual image appearing in the chat within 5 minutes — confirming the BullMQ job queue, ComfyUI image-to-image, watermarking, and frontend delivery all work
  5. An unsubscribed user hitting POST /chat receives a 402 — confirming the Stripe paywall is active in production (not bypassed by missing key)
  6. All secretary skills fire correctly: at minimum, one calendar event creation and one web search complete without error
**Plans**: TBD

### Phase 14: Apply the style of the front page to the rest of the UI of the entire app

**Goal:** Apply the landing page's dark glass visual language (bg-black, blue/violet/orange gradients, GlassCard glassmorphism, motion animations) to every authenticated page. Add persistent navigation (AppNav). Update LandingHero mockup. No new features — visual and navigation work only.
**Requirements**: UI-01, UI-02, UI-03, UI-04, UI-05, UI-06
**Depends on:** Phase 13
**Plans:** 4/4 plans complete

Plans:
- [ ] 14-01-PLAN.md — AppNav component (bottom/top nav) + App.tsx AuthenticatedLayout wrapper + Wave 0 test scaffolds
- [ ] 14-02-PLAN.md — Auth pages restyle (LoginPage, SignupPage, ForgotPasswordPage, ResetPasswordPage, GoogleSignInButton)
- [ ] 14-03-PLAN.md — Chat restyle (ChatPage dark header with avatar, ChatBubble gradient/glass, ChatInput dark)
- [ ] 14-04-PLAN.md — Remaining pages (SettingsPage GlassCard sections + subscription, BillingPage back button, SubscribePage, AvatarSetupPage, AdminPage bg-black, LandingHero chat bubbles mockup) + human visual verify
