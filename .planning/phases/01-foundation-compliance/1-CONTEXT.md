# Phase 1: Foundation & Compliance - Context

**Gathered:** 2026-02-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish legal and architectural framework that enables NSFW features while complying with regulations and platform policies. Deliverables: ToS/legal framework, age verification strategy, architecture decision for text-only intimate on WhatsApp + images via web portal, compliance framework, and basic audit log database schema. No production code beyond the schema.

</domain>

<decisions>
## Implementation Decisions

### Age Verification
- One-time self-declaration checkbox at signup ("I am 18+")
- No stored proof of declaration for now (no timestamp/IP logging)
- Declining the declaration = no access to the app at all (not even secretary mode)
- Implicit secondary signals: phone account ownership, payment card on file
- No full ID verification unless regulations require it later
- Architecture must include a pluggable verification slot — new verification methods (ID check, biometric, etc.) can be added without rearchitecting

### Content Policy — Forbidden Categories
- Absolutely forbidden, enforced at system level:
  - Minors in any sexual context
  - Non-consensual scenarios (rape fantasy, coercion roleplay)
  - Incest scenarios
  - Violence combined with sexual content
  - Bestiality
  - Torture
- Refusal is a system-level message (red box), not in-character — breaks the persona to make the boundary clear
- No lockout or escalation on refusal — flat refusal each time
- User bears legal responsibility if they jailbreak past guardrails

### Content Escalation & Spice Control
- User-accessible "spice level" setting in settings (simple tiers: e.g., low/medium/high/max)
- Spice level is primarily inferred from conversation tone — the setting exists for users who want manual control
- The setting acts as both floor (accelerate if user can't flirt) and ceiling (cap if user wants to keep things mild)
- Bot proactively escalates — all personality presets initiate escalation on their own
- Escalation pace is driven by the personality preset: shy = slow, dominant = fast, but all move forward
- "Stop" safe word exits intimate mode and lowers spice one notch (does not reset to zero)
- Next intimate session resumes at the lowered spice level

### Secretary Mode Boundaries
- Secretary mode is strictly professional — hard wall, no exceptions
- If user tries to flirt in secretary mode: playful deflection ("shh not now") but refuses to engage further
- No romantic or sexual content leaks into secretary responses

### Compliance Framework
- General best-practice compliance for now — no specific framework (GDPR, CCPA) until commercializing in specific regions
- TAKE IT DOWN Act: not applicable — all images are AI-generated fictional characters, not real people
- Watermarking and C2PA credentials: documented as future requirement (implemented in Phase 7), not built in Phase 1
- Basic audit log database schema built in Phase 1 — logs conversation events and image generation requests
- Full self-service account deletion: user can wipe all data (account, conversations, generated images) — immediate and irreversible

### Claude's Discretion
- Specific audit log schema design (tables, columns, indexes)
- ToS document structure and legal language
- Exact wording of age declaration checkbox
- System refusal message design and copy
- How to structure the pluggable verification architecture documentation

</decisions>

<specifics>
## Specific Ideas

- Refusal UI: red box system message, clearly distinct from in-character chat — not a persona response
- Secretary deflection tone: light and playful ("shh not now"), not cold or robotic
- Spice setting should be simple tiers, not a granular slider — keep it approachable
- Account deletion must be truly complete: account data, all conversations, all generated images, everything gone

</specifics>

<deferred>
## Deferred Ideas

- Per-jurisdiction compliance (GDPR, CCPA) — defer until commercializing in specific regions
- ID-based age verification — defer until regulations require it
- Watermarking and C2PA implementation — Phase 7
- Image generation audit logging implementation — Phase 7 (schema designed in Phase 1)

</deferred>

---

*Phase: 01-foundation-compliance*
*Context gathered: 2026-02-23*
