# Roadmap: Ava — Dual-Mode AI Companion

## Overview

Ava is built in 7 phases that progress from legal foundation through infrastructure, core intelligence, productivity skills, intimate mode features, and finally production hardening. The roadmap addresses critical pitfalls early (WhatsApp NSFW ban, legal compliance, database security), validates the core differentiator (mode switching) before expanding scope, and completes text-based features before adding image generation complexity.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation & Compliance** - Legal framework and architectural decisions for WhatsApp NSFW constraints (completed 2026-02-23)
- [x] **Phase 2: Infrastructure & User Management** - Database, auth, WhatsApp integration with RLS security (completed 2026-02-23)
- [x] **Phase 3: Core Intelligence & Mode Switching** - LLM integration and dual-mode conversation orchestrator (completed 2026-02-23)
- [x] **Phase 4: Secretary Skills** - Productivity tools (calendar, reminders, research) (completed 2026-02-24)
- [x] **Phase 5: Intimate Mode Text Foundation** - Personality system, content escalation, safety guardrails (completed 2026-02-24)
- [ ] **Phase 6: Web App & Multi-Platform** - Web interface for photo delivery and platform abstraction
- [ ] **Phase 7: Avatar System & Production** - Image generation, billing, and production hardening

## Phase Details

### Phase 1: Foundation & Compliance
**Goal**: Establish legal and architectural framework that enables NSFW features while complying with regulations and platform policies
**Depends on**: Nothing (first phase)
**Requirements**: SAFE-01, SAFE-02, SAFE-03, PLAT-03, ARCH-04
**Success Criteria** (what must be TRUE):
  1. ToS and legal framework reviewed by attorney and covers AI-generated imagery liability
  2. 48-hour takedown process documented and ready to implement
  3. Age verification strategy defined (20+ floor enforcement)
  4. Architecture decision documented: text-only intimate mode on WhatsApp, images via web portal
  5. Compliance framework addresses TAKE IT DOWN Act requirements (watermarking, audit logs, consent)
**Plans**: 2 plans

Plans:
- [ ] 01-01-PLAN.md — Audit log database schema and takedown process documentation
- [ ] 01-02-PLAN.md — Policy documents (ToS, content policy, age verification) and architecture decision records

### Phase 2: Infrastructure & User Management
**Goal**: Secure, multi-tenant database and WhatsApp integration with production-grade message handling
**Depends on**: Phase 1
**Requirements**: USER-01, USER-02, USER-03, PLAT-01, ARCH-04
**Success Criteria** (what must be TRUE):
  1. User can create account with authentication
  2. User data is fully isolated (RLS enabled on all tables, tested with multiple accounts)
  3. User can send WhatsApp message and receive echo response (webhook integration working)
  4. WhatsApp Business Verification submitted and in progress
  5. Database schema supports avatar metadata, conversation history, user preferences
**Plans**: 5 plans

Plans:
- [ ] 02-01-PLAN.md — Backend project scaffold, Pydantic config, Supabase client singletons, database schema migration with RLS
- [ ] 02-02-PLAN.md — Auth API (signup/signin) and minimal barebones HTML test UI
- [ ] 02-03-PLAN.md — Avatar creation and WhatsApp phone linking endpoints with onboarding dev page
- [ ] 02-04-PLAN.md — WhatsApp webhook (echo handler), outbound message service, message history endpoint
- [ ] 02-05-PLAN.md — Human verification checkpoint: RLS isolation test, auth flow, WhatsApp echo

### Phase 3: Core Intelligence & Mode Switching
**Goal**: Users can have text conversations with the bot and switch between secretary and intimate modes
**Depends on**: Phase 2
**Requirements**: CHAT-01, CHAT-02, CHAT-03, CHAT-04, CHAT-05, ARCH-02
**Success Criteria** (what must be TRUE):
  1. User can have a basic text conversation with the bot in secretary mode
  2. Bot remembers context within the current conversation session
  3. User can switch to intimate mode using "I'm alone" or similar phrasing
  4. User can switch back to secretary mode using "stop" or similar
  5. Mode switching handles typos and variations gracefully with confirmation gates
  6. Separate model contexts prevent prompt injection across modes
**Plans**: 4 plans

Plans:
- [ ] 03-01-PLAN.md — LLM service abstraction layer (LLMProvider Protocol, OpenAI provider, system prompt templates, config + deps)
- [ ] 03-02-PLAN.md — TDD: session state + mode switch detection (SessionStore, ConversationMode, ModeSwitchDetector, test suite)
- [ ] 03-03-PLAN.md — Chat orchestration + webhook upgrade (ChatService, avatar fetch, replace echo with AI pipeline)
- [ ] 03-04-PLAN.md — End-to-end verification checkpoint (automated tests + human verify)

### Phase 4: Secretary Skills
**Goal**: Users can manage Google Calendar and ask research questions via WhatsApp chat using a modular skill system
**Depends on**: Phase 3
**Requirements**: SECR-01, SECR-02, SECR-03, ARCH-01
**Success Criteria** (what must be TRUE):
  1. User can add a meeting to Google Calendar via chat
  2. User can view upcoming schedule from Google Calendar via chat
  3. User can ask the bot to research a topic and receive a concise answer
  4. Skill registry demonstrates modular architecture (new skills can be added as plugins)
**Plans**: 5 plans

Plans:
- [ ] 04-01-PLAN.md — Skill registry (Skill Protocol + ParsedIntent), intent classifier (OpenAI structured outputs), config + deps
- [ ] 04-02-PLAN.md — Google OAuth infrastructure: DB migration, token store, /auth/google routes
- [ ] 04-03-PLAN.md — CalendarSkill: add meeting (SECR-01) and view schedule (SECR-02) with conflict detection and bilingual date parsing
- [ ] 04-04-PLAN.md — ResearchSkill: Tavily-powered factual Q&A with concise answer + source link (SECR-03)
- [ ] 04-05-PLAN.md — ChatService skill dispatch integration + automated tests for secretary routing

### Phase 5: Intimate Mode Text Foundation
**Goal**: Bot provides personalized, flirty conversation with safety guardrails and crisis detection
**Depends on**: Phase 4
**Requirements**: INTM-01, INTM-02, PERS-01
**Success Criteria** (what must be TRUE):
  1. Bot adopts chatty, flirty conversational style in intimate mode
  2. Bot asks user questions and encourages them during intimate conversations
  3. User can select from preset personality personas (e.g., playful, dominant, shy, caring)
  4. Content safety guardrails block non-consensual or illegal content requests
  5. Crisis detection identifies suicidal ideation and provides 988 resources
**Plans**: 4 plans

Plans:
- [ ] 05-01-PLAN.md — Per-persona intimate prompts, ContentGuard safety service, CrisisDetector service
- [ ] 05-02-PLAN.md — ChatService wiring: crisis gate (all modes) + content guard gate (intimate) + audit logging
- [ ] 05-03-PLAN.md — Persona change endpoint (PATCH /avatars/me/persona) + SessionStore cache invalidation
- [ ] 05-04-PLAN.md — TDD: intimate mode test suite (ContentGuard, CrisisDetector, persona prompts, gate ordering)

### Phase 6: Web App & Multi-Platform
**Goal**: Users can access Ava via web app with direct photo display and choose their preferred interface
**Depends on**: Phase 5
**Requirements**: PLAT-02, PLAT-03, PLAT-04, PLAT-05
**Success Criteria** (what must be TRUE):
  1. User can chat via web app with authentication
  2. NSFW photos are delivered via secure authenticated web links (not inline WhatsApp)
  3. User can choose whether to use WhatsApp or web app as primary interface
  4. Messaging layer abstracts platform differences (WhatsApp and web use same core logic)
  5. New messaging platforms can be added as adapters without touching core
**Plans**: 6 plans

Plans:
- [ ] 06-01-PLAN.md — Phase 6 DB migration (user_preferences new columns + message_channel 'web')
- [ ] 06-02-PLAN.md — React + Vite + Tailwind frontend scaffold, Zustand auth store, LoginPage
- [ ] 06-03-PLAN.md — PlatformAdapter Protocol, WhatsApp/Web adapters, platform_router, webhook refactor
- [ ] 06-04-PLAN.md — Web chat API (POST /chat, GET /chat/history), preferences PATCH, photo signed-URL, ChatService extensions
- [ ] 06-05-PLAN.md — Chat components (ChatBubble, MessageList, ChatInput), ChatPage, SettingsPage, PhotoPage
- [ ] 06-06-PLAN.md — Automated verification + human checkpoint for Phase 6 system

### Phase 7: Avatar System & Production
**Goal**: Users can customize avatars, receive AI-generated photos, and system is production-ready with billing
**Depends on**: Phase 6
**Requirements**: AVTR-01, AVTR-02, AVTR-03, AVTR-04, AVTR-05, INTM-03, ARCH-03, BILL-01, BILL-02
**Success Criteria** (what must be TRUE):
  1. User can configure avatar (gender, age 20+, nationality/race, appearance description) during onboarding
  2. Avatar definition generates canonical reference image for consistency
  3. User receives AI-generated photos during intimate conversations (via web portal)
  4. All generated images have visible watermarks and C2PA credentials
  5. Image generation audit logs capture all requests for compliance
  6. Billing infrastructure supports multiple pricing models (subscription, credits)
  7. BullMQ async processing handles webhooks reliably at scale
  8. System ready for beta launch (monitoring, logging, error handling production-grade)
**Plans**: TBD

Plans:
- (To be created during planning)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Compliance | 2/2 | Complete   | 2026-02-23 |
| 2. Infrastructure & User Management | 5/5 | Complete    | 2026-02-23 |
| 3. Core Intelligence & Mode Switching | 4/4 | Complete    | 2026-02-23 |
| 4. Secretary Skills | 5/5 | Complete   | 2026-02-24 |
| 5. Intimate Mode Text Foundation | 4/4 | Complete    | 2026-02-24 |
| 6. Web App & Multi-Platform | 2/6 | In Progress|  |
| 7. Avatar System & Production | 0/TBD | Not started | - |
