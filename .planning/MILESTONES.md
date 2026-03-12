# Milestones

## v1.0 MVP (Shipped: 2026-03-02)

**Phases completed:** 8 phases (1–7 + 07.1 inserted), 38 plans
**Timeline:** 2026-02-23 → 2026-03-02 (8 days)
**Codebase:** ~6,579 LOC (Python + TypeScript/TSX), 398 files committed, 157 commits

**Key accomplishments:**
1. Full legal/compliance framework — content policy, ToS, age verification strategy, takedown process, and append-only audit trail (SAFE-01, SAFE-02, PLAT-03, ARCH-04)
2. Multi-tenant FastAPI backend with Supabase RLS isolation, WhatsApp Business API webhook integration, and secure JWT auth (USER-01–03, PLAT-01)
3. Dual-mode AI conversation orchestrator with fuzzy mode switching, separate per-mode session histories preventing cross-mode prompt injection, and LLM provider abstraction (CHAT-01–05, ARCH-02)
4. Modular secretary skill system — Google Calendar integration, Tavily research, and intent classification via OpenAI structured outputs (SECR-01–03, ARCH-01)
5. Intimate mode with preset personas (playful/dominant/shy/caring), ContentGuard dual-pass safety layer, crisis detection with 988 routing, and ordered ChatService safety gates (INTM-01–02, PERS-01)
6. React web app (Tailwind v4, Zustand) with platform adapter abstraction, secure signed-URL NSFW photo delivery, and WhatsApp/web dual-platform support (PLAT-02–05)
7. Avatar builder (gender/age 20+/nationality/free-text) with ComfyUI Cloud image generation, watermarking, BullMQ async pipeline, Stripe billing, and Docker Compose production deployment (AVTR-01–05, INTM-03, ARCH-03, BILL-01–02)
8. ComfyUI Cloud provider replacing Replicate — fixed critical `_poll_and_download` bug, implemented true 4-step API flow, seed randomization, and updated ImageProvider Protocol (Phase 07.1)

**Delivered:** A production-ready dual-mode AI companion — secretary + intimate — that switches modes via natural language, generates custom avatar photos via ComfyUI Cloud with watermarking, and is deployable via Docker Compose with Stripe billing and Sentry monitoring.

**Git range:** Initial commit → a61a8e2 (wip: phase 07 human verification complete)

### Known Gaps

- **SAFE-03** (TAKE IT DOWN Act — 48-hour takedown process): Phase 1 documented scope limitation (fictional AI characters are largely out of scope per the Act's intent), policy document created, but formal operational 48-hour process not implemented. Deferred to post-launch.

---

## v1.1 Launch Ready (Shipped: 2026-03-12)

**Phases completed:** 6 phases (8–13), 20 plans
**Timeline:** 2026-03-03 → 2026-03-12 (10 days)
**Codebase:** ~168 commits since v1.0, 353 files changed, +35,332 / -2,531 lines

**Key accomplishments:**
1. Production VPS deployed on HTTPS via Caddy with automatic TLS, UFW firewall, and all API credentials verified (mail-tester 10/10, ComfyUI, Stripe, WhatsApp, OpenAI, Supabase all confirmed)
2. Google Sign-In + password reset + 5 transactional emails (welcome, receipt, cancellation, forgot-password) via Resend — enumeration-safe, idempotent, non-blocking on failure
3. Landing page with dark glassmorphism design (GlassCard, Framer Motion v12), hero/features/pricing sections, auth guard, Stripe-compliant copy — no NSFW framing on public surfaces
4. Full subscription management — Stripe Customer Portal, cancellation flow with skippable exit survey in ≤3 clicks, `cancel_at_period_end=True` with access retained until period end
5. Admin dashboard with `/admin` metrics (active users, messages, photos, subscriptions), usage_events emission wired across codebase, admin role-only access (regular users get 403)
6. End-to-end smoke tests + 28-criteria production runbook — all core user journeys verified in production; 2 bugs fixed (ChatBubble photo rendering + signed URL cache)

**Delivered:** A publicly launchable product: HTTPS production deployment, Google OAuth, email infrastructure, landing page acquisition funnel, subscription management, and admin analytics — all verified end-to-end in production.

**Git range:** v1.0 tag → feat(13-01): add admin metrics smoke test

---

