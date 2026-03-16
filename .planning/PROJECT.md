# Ava — Dual-Mode AI Companion

## What This Is

A dual-mode AI companion delivered via WhatsApp and a React web app. Users get a professional secretary and an intimate partner in one bot, each with a customized avatar (gender, age 20+, nationality, appearance) and personality preset. The bot generates AI photos of the avatar during intimate conversations and handles secretary tasks (calendar, research) in professional mode.

## Core Value

A single AI companion that seamlessly switches between getting things done (secretary) and personal connection (intimate partner), all inside the messaging app or web app the user already uses.

## Requirements

### Validated

- ✓ Production VPS on HTTPS with Caddy, UFW, all API credentials verified — v1.1
- ✓ Email DNS (SPF/DKIM/DMARC) configured, mail-tester 10/10, Resend integration live — v1.1
- ✓ Google OAuth sign-in/sign-up + password reset via email link — v1.1
- ✓ Transactional emails (welcome, receipt, cancellation) — v1.1
- ✓ Landing page: hero, features, pricing, auth guard, Stripe-compliant copy — v1.1
- ✓ User-facing subscription management with Stripe Customer Portal — v1.1
- ✓ Cancellation flow: skippable exit survey, ≤3 clicks, cancel_at_period_end=True — v1.1
- ✓ Admin dashboard (/admin) with key metrics, usage_events table, admin role-only access — v1.1
- ✓ End-to-end smoke tests + production runbook — all 28 v1.1 criteria verified — v1.1
- ✓ Full app dark glass UI redesign (AppNav, GlassCard, motion animations on all authenticated pages) — v1.1 post-ship
- ✓ WhatsApp permanent System User token + user phone number in Settings — v1.1 post-ship
- ✓ Async chat architecture: immediate user bubble, background LLM reply — v1.1 post-ship
- ✓ Dual-mode chatbot: secretary mode (professional) and intimate mode (personal/flirty) — v1.0
- ✓ Safe word mode switching with fuzzy intent detection ("I'm alone" to enter, "stop" to exit) — v1.0
- ✓ WhatsApp integration as first messaging platform — v1.0 (pending WhatsApp Business verification)
- ✓ Modular messaging layer — pluggable adapters (WhatsApp + Web implemented) — v1.0
- ✓ Secretary: Google Calendar integration (add meetings, view schedule) — v1.0
- ✓ Secretary: Research capability via Tavily (Perplexity-style answers) — v1.0
- ✓ Intimate: Chatty, encouraging conversation from preset personas — v1.0
- ✓ Intimate: AI-generated avatar photos via ComfyUI Cloud with watermarking — v1.0
- ✓ Avatar builder: gender, age (20+ enforced), nationality/race, free-text appearance description — v1.0
- ✓ Preset personality system (playful, dominant, shy, caring) — v1.0
- ✓ Multi-user product with accounts and RLS data isolation — v1.0
- ✓ Cloud-hosted via Docker Compose — v1.0
- ✓ Modular skill system — new capabilities added as plugins — v1.0
- ✓ Modular AI layer — LLM and image generation backends are swappable — v1.0
- ✓ Flexible billing system — Stripe-backed, config-driven pricing — v1.0
- ✓ Content safety: age verification (20+ floor), ContentGuard, crisis detection (988) — v1.0
- ✓ NSFW delivery via secure web links (not inline WhatsApp) — v1.0

## Current Milestone: v1.2 — Cookie Banner

**Goal:** Add GDPR-compliant cookie consent to the landing page, gating Sentry and analytics behind user consent while keeping Stripe always loaded.

**Target features:**
- Cookie consent banner on landing page (pre-login visitors only)
- Sentry + analytics blocked until consent granted
- Consent persisted in localStorage
- Accept / Decline actions

### Active

- [ ] GDPR cookie consent banner on landing page
- [ ] Sentry and analytics scripts gated behind consent
- [ ] Consent stored in localStorage (persistent across sessions)

### Out of Scope

| Feature | Reason |
|---------|--------|
| Multi-language support | English only for v1 — add based on demand post-launch |
| Native mobile app | WhatsApp + web app are the interfaces |
| Self-hosted option | Cloud only — too much support burden |
| Video/voice in v1 | Text + images first — voice deferred to v2 |
| Real-time streaming responses | Standard message-reply with fast latency is sufficient |
| Unfiltered NSFW without safeguards | Legal liability — content guardrails are mandatory |
| Infinite memory without controls | Privacy/GDPR concerns — user-controlled memory in v2 |

## Context

**Shipped v1.0 (2026-03-02):** 8 phases (7 planned + 1 inserted), 38 plans, 8 days from start to ship.
**Shipped v1.1 (2026-03-12):** 6 phases (8–13), 20 plans, 10 days. Full production launch with acquisition funnel, auth, email, admin dashboard — all journeys verified.
**Post v1.1 shipped (2026-03-12):** Phases 14–16 completed — full dark glass UI, WhatsApp permanent token, async chat architecture.

**Codebase:** ~35,000+ lines changed since v1.0. FastAPI backend, React + Vite + Tailwind v4 frontend.
Stack: FastAPI, Python 3.12, Supabase (PostgreSQL + RLS), BullMQ (Redis), Sentry, Caddy, Docker Compose, Stripe, Resend, OpenAI GPT-4o, ComfyUI Cloud, WhatsApp Business API.

**Key architectural patterns established:**
- Python Protocol for pluggable providers (LLMProvider, ImageProvider, PlatformAdapter, Skill)
- Two Supabase clients: `supabase_client` (anon+RLS, user-facing) + `supabase_admin` (service role, server ops)
- Separate per-mode session histories prevent cross-mode prompt injection
- Crisis gate runs in ALL modes; ContentGuard only in INTIMATE mode
- asyncio.ensure_future (not BackgroundTasks) for LLM tasks — CORSMiddleware cancels BackgroundTasks on connection close
- Caddy named volumes (caddy_data, caddy_config) must never be deleted — hold TLS certs
- Google OAuth uses @supabase/supabase-js on frontend for PKCE flow (one-time exception to frontend no-direct-Supabase rule)

**WhatsApp Business:** Permanent System User token deployed. Verification still pending with Meta (submitted).

**Known tech debt:**
- SAFE-03 TAKE IT DOWN Act process not operationalized (policy doc exists) — May 19, 2026 deadline
- Photo escalation (mild → explicit) is static per spiciness_level, not conversation-driven
- Secretary reminder system (SKIL-02) not built — deferred
- No long-term memory across sessions (MEMR-01) — deferred

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| WhatsApp first | Largest user base, validates the concept where users already are | ✓ Good — platform adapter pattern worked well |
| Modular architecture (Protocol-based) | Future-proofing for OCR, memory, new skills, platforms | ✓ Good — ComfyUI swap validated the pattern (Phase 07.1) |
| Safe word mode switching | More natural than slash commands | ✓ Good — fuzzy matching with MAX_WORDS_FOR_FUZZY=10 guard |
| Preset personas (not custom text) | Simpler for users, easier quality control | ✓ Good — 4 personas shipped, extensible via config |
| Avatar: structured fields + free text | Balance guidance vs. customization freedom | ✓ Good — feeds directly into image prompt template |
| 20+ age floor on avatars | Legal/ethical safety requirement | ✓ Good — DB CHECK constraint + Pydantic ge=20 |
| NSFW delivery via web links | WhatsApp Business API prohibits NSFW inline | ✓ Good — signed-URL portal works; users in WhatsApp see link |
| ComfyUI Cloud over Replicate | Better output quality, more control over workflow | ✓ Good — 4-step flow working; Replicate kept as dead-code fallback |
| Two Supabase client pattern | JWT bleed prevention in concurrent async requests | ✓ Good — zero RLS isolation violations |
| BullMQ async for image pipeline | Webhook reliability at scale, decoupled from API layer | ✓ Good — fire-and-forget with polling on frontend |
| Stripe subscription gate | Prevents unauthorized access to image generation | ✓ Good — dev bypass works; 402 on expired subscription |
| nginx → Caddy for production | Automatic HTTPS without Certbot; simpler config | ✓ Good — TLS live day 1, deploy.sh validates Caddyfile before restart |
| Resend for transactional email | Good deliverability, simple SDK, non-blocking retry pattern | ✓ Good — mail-tester 10/10; email failures never block auth/payment |
| cancel_at_period_end=True for cancellation | User retains access until billing period ends; avoids 402 mid-flow | ✓ Good — legally compliant, no UX breakage during cancel |
| asyncio.ensure_future for LLM task | CORSMiddleware cancels BackgroundTasks on connection close | ✓ Good — immediate user bubble with background AI reply; no duplicate bubbles |
| onSuccess setQueryData (not onMutate) | Server returns real user row immediately; optimistic id causes duplicate bubble | ✓ Good — clean append without optimistic hacks |

## Constraints

- **Age restriction**: Avatar age must be 20+ — hard enforced via DB CHECK + Pydantic, no exceptions
- **Modularity**: Every major component is a pluggable Protocol — non-negotiable
- **Platform**: WhatsApp Business API (requires Meta approval; web app is fully operational)
- **Hosting**: Docker Compose on cloud VPS — always-on for message handling
- **Content safety**: Age verification + ContentGuard + crisis detection are mandatory

---
*Last updated: 2026-03-16 after v1.2 milestone start*
