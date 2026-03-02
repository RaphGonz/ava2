# Ava — Dual-Mode AI Companion

## What This Is

A dual-mode AI companion delivered via WhatsApp and a React web app. Users get a professional secretary and an intimate partner in one bot, each with a customized avatar (gender, age 20+, nationality, appearance) and personality preset. The bot generates AI photos of the avatar during intimate conversations and handles secretary tasks (calendar, research) in professional mode.

## Core Value

A single AI companion that seamlessly switches between getting things done (secretary) and personal connection (intimate partner), all inside the messaging app or web app the user already uses.

## Requirements

### Validated

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

## Current Milestone: v1.1 — Launch Ready

**Goal:** Transform the v1.0 MVP into a production-deployable, professional product that can acquire and retain real paying users.

**Target features:**
- Landing page (Figma-based): hero, features, pricing, Sign Up CTA — the acquisition funnel
- Production deployment: VPS (Hetzner/DigitalOcean), Docker Compose, domain + SSL, all APIs wired
- Admin dashboard: `/admin` page with usage analytics (active users, messages, photos, subscriptions)
- Auth polish: Google Sign-In/Sign-Up + password reset via email
- Transactional emails: welcome on signup, receipt after subscribing, cancellation confirmation
- Subscription management: user-facing plan page (plan, billing date) + cancellation with exit survey

### Active

- [ ] Landing page that converts visitors to paying users (Figma design provided at build time)
- [ ] Production VPS deployment with domain, SSL, and all production API connections
- [ ] Admin analytics dashboard (/admin) for usage monitoring
- [ ] Google OAuth sign-in / sign-up
- [ ] Password reset via email link
- [ ] Transactional emails (welcome, receipt, cancellation)
- [ ] User-facing subscription management page (current plan, billing date, cancel)
- [ ] Cancellation churn flow: exit survey before confirming cancel
- [ ] SAFE-03: Operationalize TAKE IT DOWN Act 48-hour takedown process (policy exists, process not implemented)
- [ ] WhatsApp Business Account verification (submitted, awaiting Meta approval)

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

**Codebase:** ~6,579 LOC Python + TypeScript/TSX. FastAPI backend, React + Vite + Tailwind v4 frontend.

**Tech stack:**
- Backend: FastAPI, Python 3.12, Supabase (PostgreSQL + RLS), BullMQ (Redis), Sentry
- Frontend: React 18, Vite, Tailwind v4, Zustand
- AI: OpenAI GPT-4o (chat/intent), ComfyUI Cloud (image generation)
- Billing: Stripe (subscription + webhook)
- Messaging: WhatsApp Business API (Meta), Web adapter
- Deployment: Docker Compose, nginx, Supabase Cloud

**Key architectural patterns established:**
- Python Protocol for pluggable providers (LLMProvider, ImageProvider, PlatformAdapter, Skill)
- Two Supabase clients: `supabase_client` (anon+RLS, user-facing) + `supabase_admin` (service role, server ops)
- Separate per-mode session histories prevent cross-mode prompt injection
- Crisis gate runs in ALL modes; ContentGuard only in INTIMATE mode

**WhatsApp Business:** Verification pending (2–15 business days). ngrok webhook URL needs registration in Meta Developer Console when credentials arrive.

**Known tech debt:**
- SAFE-03 TAKE IT DOWN Act process not operationalized (policy doc exists)
- Photo escalation (mild → explicit) is static per spiciness_level setting, not conversation-driven
- Secretary reminder system (SKIL-02) not built — deferred

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

## Constraints

- **Age restriction**: Avatar age must be 20+ — hard enforced via DB CHECK + Pydantic, no exceptions
- **Modularity**: Every major component is a pluggable Protocol — non-negotiable
- **Platform**: WhatsApp Business API (requires Meta approval; web app is fully operational)
- **Hosting**: Docker Compose on cloud VPS — always-on for message handling
- **Content safety**: Age verification + ContentGuard + crisis detection are mandatory

---
*Last updated: 2026-03-02 — v1.1 milestone started*
