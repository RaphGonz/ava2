# Requirements: Ava — Dual-Mode AI Companion

**Defined:** 2026-02-23
**Core Value:** A single AI companion that seamlessly switches between getting things done (secretary) and personal connection (intimate partner), all inside the messaging app or web app the user already uses.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Core Chat

- [ ] **CHAT-01**: User can have text-based conversations with the AI in both secretary and intimate modes
- [ ] **CHAT-02**: Bot remembers context within the current conversation session
- [ ] **CHAT-03**: User can switch to intimate mode using a safe word ("I'm alone" or similar) with fuzzy intent detection
- [ ] **CHAT-04**: User can switch back to secretary mode using a trigger ("stop" or similar) with fuzzy intent detection
- [ ] **CHAT-05**: Mode switching handles typos and phrasing variations gracefully

### Secretary Skills

- [ ] **SECR-01**: User can add a meeting to their Google Calendar via chat
- [ ] **SECR-02**: User can view their upcoming schedule from Google Calendar via chat
- [ ] **SECR-03**: User can ask the bot to research a topic and receive a concise answer

### Intimate Mode

- [ ] **INTM-01**: Bot adopts a chatty, flirty conversational style in intimate mode
- [ ] **INTM-02**: Bot asks the user questions and encourages them in intimate mode
- [ ] **INTM-03**: Bot sends AI-generated photos of the user's avatar during intimate conversations

### Avatar & Personality

- [ ] **AVTR-01**: User can select avatar gender
- [ ] **AVTR-02**: User can select avatar age (20+ enforced, hard floor)
- [ ] **AVTR-03**: User can select avatar nationality/race
- [ ] **AVTR-04**: User can describe avatar appearance in free text for unlimited customization
- [ ] **AVTR-05**: Avatar definition feeds into image generation for consistent character photos
- [ ] **PERS-01**: User can choose from preset personality personas (e.g., playful, dominant, shy, caring)

### Platforms & Delivery

- [ ] **PLAT-01**: User can chat via WhatsApp (WhatsApp Business API integration)
- [ ] **PLAT-02**: User can chat via a web app with direct photo display
- [x] **PLAT-03**: NSFW photos on WhatsApp are delivered via secure authenticated web links (not inline)
- [ ] **PLAT-04**: User chooses whether to use WhatsApp or the web app as their primary interface
- [ ] **PLAT-05**: Messaging layer is modular — new platforms can be added as adapters without changing core logic

### User Management

- [x] **USER-01**: User can create an account
- [x] **USER-02**: User data is fully isolated from other users
- [ ] **USER-03**: User can configure their avatar and persona during onboarding

### Safety & Compliance

- [x] **SAFE-01**: Age verification enforces 20+ floor on avatar creation — no exceptions
- [x] **SAFE-02**: Content guardrails prevent generation of non-consensual or illegal content
- [ ] **SAFE-03**: System complies with TAKE IT DOWN Act requirements (48-hour takedown process)

### Billing

- [ ] **BILL-01**: Flexible billing infrastructure that supports multiple pricing models (subscription, credits, etc.)
- [ ] **BILL-02**: Billing model is customizable without code changes (configuration-driven)

### Architecture

- [ ] **ARCH-01**: Modular skill system — new capabilities (OCR, memory, agentic skills) can be added as plugins
- [ ] **ARCH-02**: Modular AI layer — LLM provider is swappable without changing business logic
- [ ] **ARCH-03**: Modular image generation — image API provider is swappable without changing photo flow
- [x] **ARCH-04**: Cloud-hosted on VPS/AWS, always-on for message handling

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Intimate Voice Calls

- **VOIC-01**: User can receive AI-generated voice calls in intimate mode
- **VOIC-02**: Voice matches the avatar's persona and personality
- **VOIC-03**: Voice calls support real-time conversation (not pre-recorded)

### Enhanced Memory

- **MEMR-01**: Bot remembers user preferences and past conversations across sessions
- **MEMR-02**: User can view and delete stored memories

### Expanded Skills

- **SKIL-01**: OCR — user can send images and bot extracts text
- **SKIL-02**: Reminder system — user can set time-based reminders
- **SKIL-03**: Additional agentic capabilities (web browsing, code execution, etc.)

### Content Escalation

- **ESCL-01**: Photos escalate from mild to explicit based on conversation context
- **ESCL-02**: Escalation is gradual and consent-aware

### Additional Platforms

- **MPLAT-01**: Telegram adapter
- **MPLAT-02**: Facebook Messenger adapter
- **MPLAT-03**: Discord adapter

### Preset Personas Expansion

- **PERS-02**: Expanded persona library (10+ personalities)
- **PERS-03**: User can fine-tune persona traits within a preset

## Out of Scope

| Feature | Reason |
|---------|--------|
| Multi-language support | English only for v1 — add based on demand post-launch |
| Native mobile app | WhatsApp + web app are the interfaces — no separate app needed |
| Self-hosted option | Cloud only — too much support burden for self-hosting |
| Video/voice in v1 | Text + images first — voice deferred to v2 (strong differentiator) |
| Real-time streaming responses | Standard message-reply with fast latency is sufficient |
| Custom personality via free text | Quality control nightmare — preset personas only |
| Unfiltered NSFW without safeguards | Legal liability — content guardrails are mandatory |
| Infinite memory without controls | Privacy/GDPR concerns — user-controlled memory in v2 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SAFE-01 | Phase 1 | Complete |
| SAFE-02 | Phase 1 | Complete |
| SAFE-03 | Phase 1 | Pending |
| PLAT-03 | Phase 1 | Complete |
| ARCH-04 | Phase 1 | Complete |
| USER-01 | Phase 2 | Complete |
| USER-02 | Phase 2 | Complete |
| USER-03 | Phase 2 | Pending |
| PLAT-01 | Phase 2 | Pending |
| CHAT-01 | Phase 3 | Pending |
| CHAT-02 | Phase 3 | Pending |
| CHAT-03 | Phase 3 | Pending |
| CHAT-04 | Phase 3 | Pending |
| CHAT-05 | Phase 3 | Pending |
| ARCH-02 | Phase 3 | Pending |
| SECR-01 | Phase 4 | Pending |
| SECR-02 | Phase 4 | Pending |
| SECR-03 | Phase 4 | Pending |
| ARCH-01 | Phase 4 | Pending |
| INTM-01 | Phase 5 | Pending |
| INTM-02 | Phase 5 | Pending |
| PERS-01 | Phase 5 | Pending |
| PLAT-02 | Phase 6 | Pending |
| PLAT-04 | Phase 6 | Pending |
| PLAT-05 | Phase 6 | Pending |
| AVTR-01 | Phase 7 | Pending |
| AVTR-02 | Phase 7 | Pending |
| AVTR-03 | Phase 7 | Pending |
| AVTR-04 | Phase 7 | Pending |
| AVTR-05 | Phase 7 | Pending |
| INTM-03 | Phase 7 | Pending |
| ARCH-03 | Phase 7 | Pending |
| BILL-01 | Phase 7 | Pending |
| BILL-02 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 28 total
- Mapped to phases: 28
- Unmapped: 0

---
*Requirements defined: 2026-02-23*
*Last updated: 2026-02-23 after roadmap creation*
