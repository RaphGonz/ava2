# Phase 7: Avatar System & Production - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Users configure their avatar during signup, receive AI-generated photos during intimate conversations, and the system is billing-enabled with Stripe and production-hardened for beta launch. Covers avatar setup UX, LLM-driven image generation pipeline, monthly subscription billing, and deployment-ready infrastructure.

</domain>

<decisions>
## Implementation Decisions

### Avatar Setup Flow
- Avatar configuration form appears during signup, before anything else (before first chat)
- Form fields: gender, age (20+ enforced), nationality/race, free-text appearance description (all four AVTR-01 through AVTR-04)
- After form submission: generate a reference image immediately, show it to the user, offer to regenerate until satisfied
- Avatar editable at any time post-signup via web settings; editing triggers a new reference image generation

### Image Generation Pipeline
- Trigger: LLM decides when to send a photo — uses a `send_photo` tool call with scene/prompt description embedded in the call
- Image provider: Replicate API (FLUX or SDXL models), swappable via modular provider interface (ARCH-03)
- Pipeline: LLM tool call → backend enqueues BullMQ job → Replicate generates image → result delivered to user
- Delivery on web app: photo displayed inline in chat conversation
- Delivery on WhatsApp: secure authenticated link to web portal (per PLAT-03, no inline NSFW images on WhatsApp)

### Billing Model
- Monthly subscription, single tier at beta launch
- Architecture must support adding more tiers later without rework (configuration-driven, per BILL-02)
- Integration scope: Stripe Checkout for payment + webhooks to update subscription status in DB + backend enforces access behind active subscription
- No Stripe Billing Portal for beta (can add later)
- Immediate paywall: user must subscribe to start chatting, no free trial

### Production Readiness
- Monitoring: Sentry for error tracking + UptimeRobot for uptime alerts — no full observability stack needed for beta
- BullMQ failure strategy: retry 3× with exponential backoff → move to dead-letter queue → notify user that photo failed after all retries exhausted
- Compliance baseline: audit log every image generation request (user, prompt, timestamp, result URL) + visible watermark + C2PA metadata on all outputs
- Deployment: Docker Compose for fast, reproducible deployment on any server — speed to market is the priority
- Secrets: .env file on server, never committed to git; .env.example in repo documents required keys

### Claude's Discretion
- Reference image generation prompt construction from avatar fields
- Exact BullMQ queue configuration (concurrency, job TTL)
- Watermarking implementation details (library choice, watermark position/opacity)
- Sentry SDK integration specifics
- Docker Compose service layout (nginx, backend, worker, frontend)

</decisions>

<specifics>
## Specific Ideas

- "Generate a reference image immediately and offer to redo it until satisfied" — onboarding should feel like meeting your avatar for the first time, not filling out a form
- Speed to market is the top priority: the goal is to get real users fast, observe behavior, and iterate — production setup must enable this without friction
- Single Stripe tier for now, but billing layer must be config-driven so new tiers can be added without code changes

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-avatar-system-production*
*Context gathered: 2026-02-24*
