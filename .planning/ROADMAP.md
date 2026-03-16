# Roadmap: Ava -- Dual-Mode AI Companion

## Milestones

- ✅ **v1.0 MVP** -- Phases 1-7 + 07.1 (shipped 2026-03-02)
- ✅ **v1.1 Launch Ready** -- Phases 8-13 (shipped 2026-03-12)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-7 + 07.1) -- SHIPPED 2026-03-02</summary>

- [x] Phase 1: Foundation & Compliance (2/2 plans) -- completed 2026-02-23
- [x] Phase 2: Infrastructure & User Management (5/5 plans) -- completed 2026-02-23
- [x] Phase 3: Core Intelligence & Mode Switching (4/4 plans) -- completed 2026-02-23
- [x] Phase 4: Secretary Skills (5/5 plans) -- completed 2026-02-24
- [x] Phase 5: Intimate Mode Text Foundation (4/4 plans) -- completed 2026-02-24
- [x] Phase 6: Web App & Multi-Platform (6/6 plans) -- completed 2026-02-24
- [x] Phase 7: Avatar System & Production (10/10 plans) -- completed 2026-03-02
- [x] Phase 07.1: Switch Image Generation to ComfyUI Cloud (2/2 plans, INSERTED) -- completed 2026-03-02

Full milestone archive: `.planning/milestones/v1.0-ROADMAP.md`

</details>

<details>
<summary>✅ v1.1 Launch Ready (Phases 8-13) -- SHIPPED 2026-03-12</summary>

- [x] Phase 8: Infrastructure & Deployment (4/4 plans) -- completed 2026-03-05
- [x] Phase 9: Auth Polish & Email (4/4 plans) -- completed 2026-03-06
- [x] Phase 10: Landing Page (4/4 plans) -- completed 2026-03-09
- [x] Phase 11: Subscription Management & Churn (3/3 plans) -- completed 2026-03-09
- [x] Phase 12: Admin Dashboard (3/3 plans) -- completed 2026-03-10
- [x] Phase 13: End-to-End Smoke Test & Milestone Validation (2/2 plans) -- completed 2026-03-12

Full milestone archive: `.planning/milestones/v1.1-ROADMAP.md`

</details>

## Phase Details

### 🚧 v1.2 Cookie Banner (In Progress)

**Milestone Goal:** Add GDPR-compliant cookie consent to the landing page, gating Sentry and analytics behind user consent while keeping Stripe always loaded.

### Phase 14: Apply the style of the front page to the rest of the UI of the entire app

**Goal:** Apply the landing page's dark glass visual language (bg-black, blue/violet/orange gradients, GlassCard glassmorphism, motion animations) to every authenticated page. Add persistent navigation (AppNav). Update LandingHero mockup. No new features -- visual and navigation work only.
**Requirements**: UI-01, UI-02, UI-03, UI-04, UI-05, UI-06
**Depends on:** Phase 13
**Plans:** 4/4 plans complete

Plans:
- [x] 14-01-PLAN.md -- AppNav component (bottom/top nav) + App.tsx AuthenticatedLayout wrapper + Wave 0 test scaffolds
- [x] 14-02-PLAN.md -- Auth pages restyle (LoginPage, SignupPage, ForgotPasswordPage, ResetPasswordPage, GoogleSignInButton)
- [x] 14-03-PLAN.md -- Chat restyle (ChatPage dark header with avatar, ChatBubble gradient/glass, ChatInput dark)
- [x] 14-04-PLAN.md -- Remaining pages (SettingsPage GlassCard sections + subscription, BillingPage back button, SubscribePage, AvatarSetupPage, AdminPage bg-black, LandingHero chat bubbles mockup) + human visual verify

### Phase 15: WhatsApp permanent token + user phone number in settings + real-time chat message polling

**Goal:** Close three pre-milestone gaps: replace the expiring developer token with a permanent System User token, add a phone number input to the Settings WhatsApp toggle, and confirm real-time chat polling works in production.
**Requirements**: WA-01, WA-02, WA-03
**Depends on:** Phase 14
**Plans:** 2/2 plans complete

Plans:
- [x] 15-01-PLAN.md -- Add linkWhatsApp() to preferences.ts + conditional phone input in SettingsPage with E.164 validation
- [x] 15-02-PLAN.md -- Deploy frontend, create permanent Meta System User token on VPS, verify WhatsApp end-to-end and chat polling in production

### Phase 16: Async chat architecture -- immediate user bubble, background AI reply

**Goal:** Fix the web chat message flow so the user's message appears in the thread immediately upon send, and the AI reply appears independently when ready -- without optimistic hacks. POST /chat writes the user message to DB and returns it instantly; the LLM runs via asyncio.ensure_future; GET /chat/history polling picks up the AI reply when it lands.
**Requirements**: CHAT-01, CHAT-02, CHAT-03
**Depends on:** Phase 15
**Plans:** 1/1 plans complete

Plans:
- [x] 16-01-PLAN.md -- Refactor web_chat.py (synchronous user insert + asyncio.ensure_future LLM task) + chat.ts (remove onMutate, add onSuccess setQueryData)

### Phase 17: GDPR Cookie Consent Banner

**Goal:** Pre-login visitors control which scripts run on their device via a consent banner; that choice is persisted and respected on every subsequent visit.
**Depends on:** Phase 16
**Requirements**: COOK-01, COOK-02, COOK-03, COOK-04, COOK-05, COOK-06
**Success Criteria** (what must be TRUE):
  1. A visitor to the landing page sees a cookie consent banner before Sentry or analytics scripts initialise
  2. A visitor who clicks Accept sees Sentry and analytics load immediately and on all future visits without seeing the banner again
  3. A visitor who clicks Decline has Sentry and analytics blocked for the entire session and all future visits without seeing the banner again
  4. Stripe loads on the landing page regardless of whether the visitor has accepted or declined
  5. A returning visitor who already made a choice is not shown the banner
**Plans**: 2 plans

Plans:
- [ ] 17-01-PLAN.md -- Install @sentry/react + create consent.ts service module + useCookieConsent hook (deferred Sentry init, localStorage state)
- [ ] 17-02-PLAN.md -- Create CookieConsentBanner component + wire main.tsx + wire LandingPage.tsx + Vitest tests + human verify

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-7 + 07.1: MVP Phases | v1.0 | 38/38 | Complete | 2026-03-02 |
| 8. Infrastructure & Deployment | v1.1 | 4/4 | Complete | 2026-03-05 |
| 9. Auth Polish & Email | v1.1 | 4/4 | Complete | 2026-03-06 |
| 10. Landing Page | v1.1 | 4/4 | Complete | 2026-03-09 |
| 11. Subscription Management & Churn | v1.1 | 3/3 | Complete | 2026-03-09 |
| 12. Admin Dashboard | v1.1 | 3/3 | Complete | 2026-03-10 |
| 13. End-to-End Smoke Test | v1.1 | 2/2 | Complete | 2026-03-12 |
| 14. UI Dark Theme Redesign | v1.2 | 4/4 | Complete | 2026-03-10 |
| 15. WhatsApp permanent token + phone + polling | v1.2 | 2/2 | Complete | 2026-03-11 |
| 16. Async chat architecture | v1.2 | 1/1 | Complete | 2026-03-11 |
| 17. GDPR Cookie Consent Banner | v1.2 | 0/2 | Not started | - |
