# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

---

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-02
**Phases:** 8 (7 planned + 1 inserted) | **Plans:** 38 | **Timeline:** 8 days (2026-02-23 → 2026-03-02)

### What Was Built

- Dual-mode AI companion with natural language mode switching (secretary ↔ intimate) — fuzzy intent detection, separate session histories, cross-mode prompt injection prevention
- WhatsApp Business API integration with RLS-isolated multi-tenant Supabase backend; web app with React/Tailwind v4 as second platform
- Secretary skill system: Google Calendar (add/view), Tavily research, OpenAI intent classification — full modular plugin architecture
- Intimate mode: 4 preset personas, ContentGuard dual-pass safety, crisis detection (988 routing), spiciness gate ordering
- Avatar builder with ComfyUI Cloud image generation, BullMQ async pipeline, watermarking, Stripe billing, Docker Compose production deployment
- Phase 07.1 (INSERTED): Replaced Replicate with ComfyUI Cloud — fixed critical `_poll_and_download` bug, implemented true 4-step API flow

### What Worked

- **Protocol-based modularity**: Python Protocols (structural typing) for LLMProvider, ImageProvider, PlatformAdapter, and Skill enabled ComfyUI to replace Replicate in Phase 07.1 with zero changes to callers — the architectural bet paid off immediately
- **Compliance-first ordering**: Starting with Phase 1 (legal framework, audit trail, age verification) before any code meant compliance decisions were baked in from the start, not retrofitted
- **Two Supabase client pattern**: Separating `supabase_client` (anon+RLS) from `supabase_admin` (service role) was established in Phase 2 and held perfectly through all 7 phases — never broke RLS isolation
- **Decimal phase insertion (07.1)**: When ComfyUI Cloud turned out to require a critical bug fix, inserting a decimal phase kept the main phase numbering stable and clearly signaled urgency
- **Gap-closure pattern in Phase 7**: When human verification found 4 gaps (GAP-1 through GAP-4), creating individual fix plans (07-07 through 07-10) kept work organized and traceable

### What Was Inefficient

- **REQUIREMENTS.md checkbox tracking**: SAFE-03 checkbox was never updated after the Phase 1 compliance work — the policy doc existed but the checkbox sat unchecked. Requirements need a dedicated update step per plan.
- **STATE.md performance metrics**: Got out of sync mid-project (Phase 4+). Only the first 11 plans have good timing data.
- **GAP discovery cycle**: 4 gaps in Phase 7 required 4 extra fix plans. Better pre-plan research for image generation APIs (ComfyUI's 4-step flow vs 2-step assumption) would have caught GAP-2 before Phase 7 started.
- **WhatsApp credential dependency**: The WhatsApp echo test was deferred in Phase 2 because credentials weren't available. The webhook flow is implemented but untested end-to-end on real infrastructure.

### Patterns Established

- **Structural typing over inheritance**: All pluggable components use `Protocol` with `runtime_checkable` — no ABC, no inheritance chains. Any class with the right methods satisfies the interface.
- **Deferred credential pattern**: All config fields default to empty string — missing credentials return graceful error messages (not startup crashes). OpenAI key, Stripe key, ComfyUI URL all follow this.
- **asyncio.to_thread wrapping**: All synchronous SDK calls (Google Auth, Tavily, etc.) inside async FastAPI handlers use `asyncio.to_thread()` — established in Phase 4, consistent thereafter.
- **Fire-and-forget + polling**: Phase 7 reference image generation uses FastAPI BackgroundTasks for async work + frontend polling loop — clean pattern for long-running operations in a synchronous-looking API.
- **Dev router guard**: `/dev/*` routes guarded by `app_env == 'development'` check — 404 in production without any feature flag system needed.

### Key Lessons

1. **Verify API contracts before assuming**: The ComfyUI `_poll_and_download` bug stemmed from assuming a 2-step flow (status → download) when the real flow was 4-step (queue → poll status → fetch history_v2 → download). Always verify actual API behavior in research phase, not just docs.
2. **Checkbox hygiene matters**: Requirement checkboxes should be updated at plan completion time, not left for milestone close. One unchecked box (SAFE-03) caused confusion at close.
3. **Human verification catches what automated tests miss**: The 4 gaps found in Phase 7 (GAP-1 through GAP-4) were composition/API issues that unit tests couldn't catch — full end-to-end human testing of the happy path is essential before milestone close.
4. **The modular bet pays off fast**: Phase 07.1 swapped the entire image generation backend in 2 plans. The Protocol abstraction established in Phase 3 (LLMProvider) and Phase 7 (ImageProvider) paid dividends immediately.

### Cost Observations

- Model mix: balanced profile (Sonnet 4.6 primary)
- Sessions: multiple across 8 days
- Notable: 157 commits across 8 days = ~19 commits/day average; consistently fast execution (~10 min/plan average)

---

## Milestone: v1.1 — Launch Ready

**Shipped:** 2026-03-12
**Phases:** 6 (8–13) | **Plans:** 20 | **Timeline:** 10 days (2026-03-03 → 2026-03-12)

### What Was Built

- Production VPS (Hetzner CX32) with Caddy HTTPS, UFW firewall, all API credentials verified; mail-tester 10/10
- Google Sign-In + password reset + 5 transactional emails (Resend SDK, non-blocking retry, enumeration-safe)
- Landing page: dark glassmorphism design (GlassCard, Framer Motion v12), hero/features/pricing, auth guard, Stripe-compliant copy
- Full subscription management: Stripe Customer Portal, cancellation with skippable exit survey, ≤3 clicks, cancel_at_period_end
- Admin dashboard: `/admin` metrics, usage_events table (4 event types), admin role-only access (403 for regular users)
- End-to-end smoke tests + 28-criteria production runbook; 2 bugs fixed (ChatBubble photo rendering + signed URL cache)

### What Worked

- **Phase 8 first**: Deploying infrastructure before any feature work meant every subsequent phase could be verified in production immediately. Phase 9's email features worked on first deploy because DNS was already propagated.
- **End-to-end smoke test as final phase (Phase 13)**: Having a dedicated validation phase with a written runbook caught 2 production bugs that would have been user-reported. Made milestone declaration concrete and credible.
- **Non-blocking email pattern**: `email never raises to callers — one retry after 3s then log and return False` meant Stripe webhooks could never be blocked by email failures. This pattern (established in Phase 9) held through all email touchpoints.
- **Deferred credential pattern from v1.0 continues to pay**: All new config fields (RESEND_API_KEY, SUPABASE_HOOK_SECRET) default to empty string — missing credentials return graceful errors at call time, not startup crashes.
- **Production URL override via FRONTEND_URL env var**: Single env var controls CORS in production; default to localhost for local dev. Zero config changes needed between environments.

### What Was Inefficient

- **Phase 10 (Landing Page) was the longest single plan**: 78 minutes for plan 04 (vs 10-16 min average) due to Vitest hoisting behavior and test fixture complexity. The Figma port was accurate but the test suite needed significant debugging.
- **Phase 9 human verification deferred to Phase 13**: Auth E2E (Google OAuth browser flow, email delivery) was correctly delegated to Phase 13 smoke test, but it meant Phase 9 "complete" required a caveat. This was the right call but worth noting.
- **STATE.md milestone field not updated**: STATE.md still showed `milestone: v1.0` throughout v1.1 work — tooling picked wrong phase count at milestone complete time.

### Patterns Established

- **Caddy named volumes must never be deleted**: `caddy_data` and `caddy_config` hold Let's Encrypt TLS certs. Added to known constraints permanently.
- **Email non-blocking contract**: All email calls wrapped in try/except — email failures are logged and return False but never raise. Stripe webhooks would retry endlessly if email caused non-200 response.
- **Google OAuth as frontend Supabase exception**: Only case where frontend directly calls Supabase JS SDK (PKCE flow) — explicitly labeled one-time exception, must not be generalized.
- **Smoke test runbook as milestone gate**: Phase 13's evidence table format (requirement ID + test type + result + evidence) gives a clear pass/fail record. Worth carrying forward to all future milestones.

### Key Lessons

1. **Infrastructure first pays compounding interest**: Each subsequent phase validated in real production immediately. By Phase 13, the environment was stable enough that smoke tests ran cleanly on first attempt.
2. **Exit survey skippability is a legal/UX requirement**: SUBS-05 (skip option) was not an afterthought — it's legally necessary in some jurisdictions and prevents the cancellation from being coercive. The "Skip survey and cancel" shortcut design (3-click path) is worth documenting as a reusable UX pattern.
3. **Dedicated smoke test phase eliminates milestone ambiguity**: "Is v1.1 done?" went from a judgment call to a 28-row evidence table. The 2 bugs caught (photo rendering, signed URL cache) justified the entire phase.
4. **asyncio.ensure_future over BackgroundTasks for long-running tasks**: CORSMiddleware cancels BackgroundTasks on connection close. This bit us in Phase 16 (post-v1.1) but the pattern was established in Phase 7. Every new background task should use ensure_future.

### Cost Observations

- Model mix: balanced profile (Sonnet 4.6 primary)
- Sessions: multiple across 10 days
- Notable: 168 commits since v1.0 in 10 days = ~17 commits/day; Phase 14-16 shipped as bonus work after milestone gates closed

---

## Cross-Milestone Trends

| Milestone | Phases | Plans | Days | Commits | Key Pattern |
|-----------|--------|-------|------|---------|-------------|
| v1.0 MVP | 8 | 38 | 8 | 157 | Protocol modularity paid off immediately |
| v1.1 Launch Ready | 6 | 20 | 10 | 168 | Infrastructure-first + smoke test gate = credible ship |
