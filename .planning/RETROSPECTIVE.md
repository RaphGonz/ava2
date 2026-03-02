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

## Cross-Milestone Trends

| Milestone | Phases | Plans | Days | LOC | Key Pattern |
|-----------|--------|-------|------|-----|-------------|
| v1.0 MVP | 8 | 38 | 8 | ~6,579 | Protocol modularity paid off immediately |
