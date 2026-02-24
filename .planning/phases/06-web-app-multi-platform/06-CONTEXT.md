# Phase 6: Web App & Multi-Platform - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a web application (chat + photo viewer + settings) and refactor the messaging layer into a platform-agnostic adapter system. WhatsApp and web are the two adapters in this phase. The web app enables inline NSFW photo display and is the control hub for user settings. Adding future platforms requires only a new adapter — no core changes.

</domain>

<decisions>
## Implementation Decisions

### Web chat UI
- Visual style: minimal chat bubble layout (familiar messaging-app feel)
- Authentication: phone verification — user links their WhatsApp number to get web access (no separate credential system)
- Conversation history: web-only — web app tracks its own messages separately from WhatsApp history
- Feature scope: web app is the full settings hub, differentiating it from WhatsApp with:
  - **Persona selector** — visual UI to choose/change Ava's persona
  - **Spiciness ceiling** — content intensity slider (flirty → explicit); Ava will not escalate beyond the user's chosen level
  - **Mode-switch phrase** — user-configurable phrase that triggers switching between secretary and intimate mode (stored in profile, ChatService checks it during message dispatch)
  - **Notification preferences** — control WhatsApp notification behavior from the web
  - **Account & billing** — subscription status, credits, payment method management

### Photo delivery
- When a photo is ready, Ava sends a rich WhatsApp message in her persona: e.g., "here's what you asked for ❤" + a secure URL. Tone must be in-character, not system-generated.
- Link expiry: 24 hours
- Access model: token-based URL — no login required to view. The token itself is the auth. Anyone with the link can view for 24h.
- What the link opens: the photo embedded in the web app's chat view (not a standalone photo viewer; opens in full web app context)

### Platform switching & preference
- User declares their preferred platform (WhatsApp or web app) via a toggle in the settings panel
- Ava replies ONLY on the user's preferred platform — not on both simultaneously
- When a user messages from their non-preferred platform, Ava sends an in-character warm redirect that also mentions they can change their preference in settings. Example tone: "Hey 😊 I mostly hang out on [preferred platform] — come find me there! (You can change this in settings)"
- When a user switches preferred platform: full context carries over — current mode (secretary/intimate), persona, and recent message history are all available on the new platform

### Adapter contract & extensibility
- Adapter interface: inbound + outbound only. Core handles everything else.
  - `receive(message: NormalizedMessage) → None` — feeds into core pipeline
  - `send(user_id: str, text: str) → None` — delivers response to platform
- Abstraction mechanism: Python ABC (Abstract Base Class) or Protocol — type-checked, enforced at dev time
- Normalized message envelope: `user_id + text + platform + timestamp` (minimal; no platform-specific metadata)
- Phase 6 scope: WhatsApp adapter (refactor existing webhook handler) + Web adapter. No additional platforms.

### Claude's Discretion
- Exact web UI framework choice (React, Vue, HTMX, etc.)
- JWT vs. session cookie for web app auth
- Exact spiciness level names/thresholds (e.g., "Mild / Spicy / Hot" vs. a numeric scale)
- Platform preference enforcement implementation (middleware vs. adapter-level check)
- Photo token generation and storage mechanism

</decisions>

<specifics>
## Specific Ideas

- Photo delivery message should feel like Ava sent it, not a system notification. Example: "here's what you asked for ❤" — in-character, warm, personal.
- Mode-switch phrases are user-customizable (not fixed system commands) — stored in user profile, checked by ChatService during dispatch.

</specifics>

<deferred>
## Deferred Ideas

- Telegram adapter — natural third platform, but deferred to post-Phase 6
- Safe-word behavior (stop/de-escalate signal on special phrase) — distinct from mode-switch phrase, would require ChatService changes; note for backlog
- Per-user topic blocklist (things Ava never brings up) — personal guardrails on top of system guardrails; note for backlog
- Consent/age-verification records in settings panel — was discussed but not included in this phase's settings scope; note for backlog

</deferred>

---

*Phase: 06-web-app-multi-platform*
*Context gathered: 2026-02-24*
