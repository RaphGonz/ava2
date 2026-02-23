# Phase 3: Core Intelligence & Mode Switching - Context

**Gathered:** 2026-02-23
**Status:** Ready for planning

<domain>
## Phase Boundary

LLM integration and dual-mode conversation orchestrator. Users can have text conversations with the bot in secretary mode and switch to intimate mode. Phase delivers: working LLM service abstraction, mode switching logic, session context management, and basic secretary personality. Avatar personality depth (content escalation, safety guardrails) is Phase 5.

</domain>

<decisions>
## Implementation Decisions

### Mode switching detection
- Three parallel detection methods: safe words/phrases, slash commands, and buttons (in web app)
- Safe words/phrases: "I'm alone", "let's be alone", "stop", and similar natural language triggers
- Slash commands: `/intimate`, `/secretary`, `/stop` — reliable fallback that survives typos
- Buttons: visible in web app UI for discoverability and accessibility
- Only the authenticated user can trigger mode switches (architecture at Claude's discretion)

### Mode switching behavior
- Always confirm before switching: e.g., "Switching to private mode — just us now 💬" / "Back to work mode."
- Fuzzy match / typos / ambiguous phrasing: ask for clarification — "Did you mean to switch to private mode? Reply 'yes' or use /intimate."
- Already-in-mode attempt: acknowledge playfully — "We're already in private mode 😉" — no disruption

### Secretary personality
- Tone: warm and friendly professional — efficient and capable, with genuine warmth. Not robotic, not cold.
- Verbosity: concise by default; detailed on request (user can ask "explain more")
- Identity: uses the name defined at avatar creation (not hardcoded). The bot refers to itself by its avatar name.
- Language: detects and matches the user's language. If the user switches language, the bot follows.

### Session & memory
- Session scope: explicit reset only — no time-based expiry. Designed to be compatible with future long-context/memory solutions.
- Cross-session memory: none in Phase 3. Fresh context each session.
- Mode isolation: separate LLM context per mode — history does NOT cross the mode boundary (prevents prompt injection, per success criteria)
- Context window overflow: silently drop oldest messages. No user-facing notification.

### LLM service architecture
- Phase 3: single model for both modes, separated by system prompt (not separate models)
- Future-ready: architecture must support two models later — a standard model (secretary) and an uncensored model (intimate)
- Provider: abstracted behind a configurable LLM service interface so the provider can be swapped without rewriting call sites
- API failure: retry once silently, then return user-friendly message — "I'm having trouble thinking right now — try again in a moment."
- Unclear input: ask for clarification naturally — "I didn't quite catch that — could you rephrase?" Stays in character.

### Claude's Discretion
- Which LLM provider to use initially (abstracted, so the choice is low-stakes)
- How to architect the LLM service interface (adapters, DI, config-driven)
- Exact mode switch trigger phrase list (start with "I'm alone", "stop", "private", and expand)
- Session reset mechanism (command, endpoint, or automatic on first message detection)
- Retry logic details for API failures

</decisions>

<specifics>
## Specific Ideas

- Two future models are planned: one standard (secretary), one uncensored (intimate). Phase 3 lays the architectural groundwork so swapping models per mode is a config change, not a rewrite.
- Slash commands are the power-user / recovery path when safe words fail due to typos or uncertainty.
- "Explicit reset only" for sessions was chosen deliberately to avoid locking out long-context memory solutions (e.g., MemGPT-style systems) in a future phase.

</specifics>

<deferred>
## Deferred Ideas

- Persistent memory / never-forget context solution — future phase (user mentioned this explicitly as a planned addition)
- Per-mode LLM model selection (uncensored model for intimate mode) — Phase 5 or later
- Avatar personality depth, content escalation, safety guardrails — Phase 5
- Rate limiting and cost controls per user — future phase

</deferred>

---

*Phase: 03-core-intelligence-mode-switching*
*Context gathered: 2026-02-23*
