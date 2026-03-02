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
