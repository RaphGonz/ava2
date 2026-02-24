# Phase 5: Intimate Mode Text Foundation - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Bot provides personalized, flirty text conversation with selectable personality personas, safety guardrails that block prohibited content categories, and crisis detection that identifies suicidal ideation and delivers resources. Delivered over WhatsApp (text-only). Image generation, web interface, and billing are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Conversation style
- Default tone: playfully flirty (teasing, light innuendo, fun banter)
- Tone escalates based on user signals within guardrails — if the user gets more explicit, Ava follows
- Engagement pattern: mix of questions and affirmations, varied rhythm (not every message ends in a question)
- Memory scope: recent sessions (short-term) — Ava remembers the last few conversations for tone continuity, but not full relationship history

### Persona design
- 3–4 preset personas ship in Phase 5 (example set: playful, dominant, shy, caring)
- Depth: tone and vocabulary only — each persona has a distinct voice and word choice, but underlying behavior patterns (question cadence, escalation logic) are shared
- Selection: one-time setup during onboarding or first intimate mode activation; stored on user profile; changeable in settings
- Scope: intimate mode only — regular (non-intimate) conversations are not affected by persona choice

### Safety guardrails
- Response style: hard explicit refusal — clear statement of what Ava won't do, no ambiguity
- Post-refusal: Ava redirects and continues — states the block, then pivots to what she can do
- Blocked content categories: non-consensual scenarios, minors in any sexual context, real people (non-consenting), illegal acts beyond sexual content (violence instructions, drug synthesis, etc.), bestiality, torture
- Logging: all guardrail triggers logged to audit system with timestamp, user ID, and category — consistent with Phase 1 compliance framework

### Crisis detection & response
- Detection method: keyword + context scoring — trigger on high-risk phrases combined with conversation context; when ambiguous, treat as genuine (safer default)
- Response: warm in-persona pivot — Ava stays in her persona but shifts tone meaningfully: "Hey... I'm worried about you right now. Please reach out to [988 / Suicide & Crisis Lifeline]."
- Post-crisis flow: conversation continues at user's direction — Ava sends resources then follows the user's lead; no forced pause on intimate mode
- Logging: crisis detections logged separately from guardrail violations — timestamp, user ID, triggering phrases — for pattern analysis and at-risk user identification

### Claude's Discretion
- Exact prompt engineering for persona tone differences
- Short-term memory implementation (session count, storage mechanism)
- Specific phrasing of guardrail refusal messages
- Keyword list and context-scoring weights for crisis detection
- Crisis log schema (separate from guardrail audit log)

</decisions>

<specifics>
## Specific Ideas

- No specific product references were cited — open to standard approaches for prompt design and safety classification
- Personas are tone/voice-only (not behavioral archetypes), which keeps the system simpler to maintain and test

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-intimate-mode-text-foundation*
*Context gathered: 2026-02-24*
