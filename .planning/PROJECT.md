# Ava — Dual-Mode AI Companion

## What This Is

A dual-mode AI chatbot product delivered via WhatsApp (and later other messaging platforms). Users get a professional secretary and an intimate companion in one bot. Each user customizes their companion's appearance and personality through an avatar builder and preset personas.

## Core Value

A single AI companion that seamlessly switches between getting things done (secretary) and personal connection (intimate partner), all inside the messaging app the user already uses.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Dual-mode chatbot: secretary mode (professional) and intimate mode (personal/flirty)
- [ ] Safe word mode switching with fuzzy intent detection ("I'm alone" to enter intimate, "stop" to exit)
- [ ] WhatsApp integration as first messaging platform
- [ ] Modular messaging layer — pluggable adapters for Telegram, Facebook, etc.
- [ ] Secretary: Google Calendar integration (add meetings, view schedule)
- [ ] Secretary: Reminder system (set and trigger reminders)
- [ ] Secretary: Basic research capability (answer questions, look things up)
- [ ] Intimate: Chatty, encouraging conversation from preset personas
- [ ] Intimate: AI-generated photos of user's custom avatar, escalating from mild to explicit based on context
- [ ] Avatar builder: gender, age (20+ enforced), nationality/race selection + free text appearance description
- [ ] Preset personality system (playful, dominant, shy, caring, etc.)
- [ ] Multi-user product with accounts and data isolation
- [ ] Cloud-hosted (VPS/AWS)
- [ ] English only for v1
- [ ] Modular skill system — new capabilities (OCR, agentic skills, etc.) can be added as plugins
- [ ] Modular AI layer — LLM and image generation backends are swappable
- [ ] Flexible billing system (specifics TBD, must be customizable)

### Out of Scope

- Multi-language support — English only for v1, defer to later
- Mobile app — WhatsApp is the interface, no native app needed
- Self-hosted option — cloud only for now
- Video/voice — text and images only for v1
- Real-time streaming responses — standard message-reply pattern

## Context

**Product type:** Consumer SaaS delivered through messaging platforms. No custom frontend needed for v1 — WhatsApp IS the UI.

**Architecture philosophy:** Everything is modular. The system is designed as a core orchestrator with pluggable modules at every layer:
- **Messaging adapters:** WhatsApp first, but any platform can be added without touching core logic
- **LLM providers:** The conversation engine abstracts the LLM — swap GPT for Claude or an open-source model without changing business logic
- **Image generation:** The avatar photo system abstracts the image API — swap Stable Diffusion for DALL-E without changing the photo flow
- **Skills:** Secretary capabilities (calendar, reminders, research) are individual skill modules. Adding OCR, infinite memory, or new agentic skills means adding a new module, not modifying existing ones
- **Personality system:** Preset personas are data-driven, not hardcoded — adding a new persona is config, not code

**Mode switching:** The bot uses fuzzy intent detection to switch modes. "I'm alone" (or close variations like "I am alone", "im alone") triggers intimate mode. "Stop" (or similar) returns to secretary mode. The detection must be forgiving of typos and phrasing variations.

**Avatar & photo generation:** The avatar is defined by structured fields (gender, age 20+, nationality/race) plus a free-text appearance description. These feed into a prompt template for consistent character generation. Photos escalate in intensity based on conversation context — from clothed/flirty to explicit, driven by the conversation flow.

**Future expansion:** The modular architecture is designed to accommodate:
- Additional messaging platforms (Telegram, Facebook, Discord, etc.)
- OCR and document processing skills
- Infinite/long-term memory systems
- More agentic capabilities (web browsing, code execution, etc.)
- Additional external tool integrations (beyond Google Calendar)

## Constraints

- **Age restriction**: Avatar age must be 20+ — hard enforced, no exceptions
- **Modularity**: Every major component must be a pluggable module — this is non-negotiable
- **Platform**: WhatsApp Business API for messaging (requires Meta approval process)
- **Hosting**: Cloud VPS/AWS — must be always-on for message handling
- **Content safety**: Age verification on avatars must be bulletproof

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| WhatsApp first | Largest user base, validates the concept where users already are | — Pending |
| Modular architecture | Future-proofing for OCR, memory, new skills, new platforms | — Pending |
| Safe word mode switching | More natural than slash commands, feels like talking to a real person | — Pending |
| Preset personas (not custom text) | Simpler for users, easier to quality-control personality consistency | — Pending |
| Avatar: structured fields + free text | Balance between guidance and customization freedom | — Pending |
| 20+ age floor on avatars | Legal/ethical safety requirement | — Pending |

---
*Last updated: 2026-02-23 after initialization*
