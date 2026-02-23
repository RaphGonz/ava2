# Project Research Summary

**Project:** Ava - Dual-Mode AI Companion
**Domain:** WhatsApp-based AI chatbot (productivity assistant + intimate companion)
**Researched:** 2026-02-23
**Confidence:** HIGH

## Executive Summary

Ava is a dual-mode AI companion delivered via WhatsApp that switches between secretary mode (calendar, reminders, research) and intimate mode (personalized companion with text-based interaction). This represents an unaddressed gap in the market: Replika pivoted away from romance in 2026, ChatGPT is strictly professional, and NSFW companions (Candy.AI, Crushon) offer zero productivity value. Expert builders in 2026 use tool-calling orchestration architectures with modular skill systems, multi-provider LLM abstraction, and event-driven webhook processing for scalability.

The recommended approach is a layered architecture: messaging adapter (WhatsApp normalization) → conversation orchestrator (mode detection and routing) → skill registry (pluggable tools) → provider abstractions (swappable LLMs and image APIs). Core stack is Node.js 20 + TypeScript 5 + Fastify 5 + PostgreSQL 16 with Drizzle ORM, LangChain.js 0.3 for LLM orchestration, OpenRouter for multi-model access, and BullMQ for async webhook processing. Start with WhatsApp Business API (requires Meta verification, 2-4 weeks) and build mode switching as the core differentiator from day one.

Critical risks include: WhatsApp instant ban for NSFW images (solution: text-only intimate mode on WhatsApp, images via separate portal), database RLS misconfiguration exposing all conversations (solution: enable Row-Level Security on every table before launch), prompt injection bypassing mode restrictions (solution: separate model contexts per mode + confirmation gates), and legal liability for AI-generated imagery (solution: implement TAKE IT DOWN Act 48-hour takedown process, age verification, watermarking before May 19, 2026 deadline). All four risks are preventable through architectural decisions made in Phases 0-2.

## Key Findings

### Recommended Stack

The 2026 standard for chatbot development is Node.js + TypeScript with Fastify (3-4x faster than Express), PostgreSQL with Drizzle ORM (better for 2026 than Prisma due to v6→7 migration churn), and LangChain.js for LLM orchestration. WhatsApp Business Cloud API is mandatory for production multi-user products—the unofficial whatsapp-web.js is only for MVP testing as Meta bans accounts. LLM abstraction via OpenRouter provides access to 500+ models with automatic failover and cost optimization. Image generation uses Replicate or Fal.ai APIs (not self-hosted Stable Diffusion due to operational complexity). BullMQ with Redis handles webhook processing asynchronously to meet WhatsApp's <20s acknowledgment requirement.

**Core technologies:**
- **Node.js 20 + TypeScript 5 + Fastify 5**: Runtime and HTTP framework — event-driven architecture ideal for real-time webhooks, Fastify offers 70K req/sec vs Express 20K req/sec
- **PostgreSQL 16 + Drizzle ORM**: Database layer — multi-tenancy via Row-Level Security, JSONB for flexible avatar data, Drizzle is 2026 recommended over Prisma
- **LangChain.js 0.3 + OpenRouter**: LLM orchestration — abstracts provider differences (OpenAI, Anthropic, etc.), tool calling for secretary skills, unified gateway for cost optimization
- **WhatsApp Business Cloud API**: Messaging platform — required for production (unofficial libraries lead to bans), webhooks-based, supports media uploads (though NSFW ban applies)
- **BullMQ 5 + Redis 7**: Job queue and cache — async webhook processing prevents timeouts, handles retries/deduplication/rate-limiting, critical for production reliability
- **Replicate/Fal.ai**: Image generation — API-based Stable Diffusion ($0.002-0.004/image), no GPU management, getimg.ai for consistent character system

### Expected Features

Users expect certain features from AI companions in 2026, competitive features differentiate, and some commonly requested features are problematic.

**Must have (table stakes):**
- Text conversation with <2s responses — standard LLM integration with latency optimization
- Dual-mode switching (secretary ↔ intimate) — THE core differentiator, requires fuzzy intent detection
- Personality customization with preset personas — 3-5 quality-controlled personalities vs user-generated chaos
- Avatar appearance customization — gender, age (20+), race/nationality, free-text description
- Short-term memory (session context) — conversation buffer in Redis
- User accounts with authentication — multi-tenant data isolation required
- Age verification (20+ enforced) — bulletproof, not self-reported
- Content safety guardrails — prevent non-consensual content, abuse, regulatory compliance
- Secretary skills: Calendar integration (Google Calendar), reminders, basic research — productivity differentiator

**Should have (competitive):**
- Long-term memory across sessions — vector DB for RAG retrieval of preferences and past conversations
- Context-aware image escalation — photos progress from mild to explicit based on conversation intensity
- Platform-agnostic design — messaging adapter pattern enables Telegram/Discord expansion
- Modular skill system — plugin architecture for future OCR, agentic capabilities without core rewrites
- WhatsApp-native experience — meets users where they are, no app download friction

**Defer (v2+):**
- Voice messages and calls — complexity and cost not justified until core is validated
- Video generation — extremely high cost and complexity ($$$), wait for market maturity
- Multi-language support — English-only v1, add languages post-validation based on demand
- Custom personas beyond presets — quality control nightmare, defer until v2+
- Native mobile app beyond messaging platforms — WhatsApp validates concept first, then consider dedicated app

### Architecture Approach

Modern AI chatbots use tool-calling orchestration architectures with modular, layered components. The dominant 2026 pattern separates messaging adapters (normalize platform events), conversation orchestrator (mode detection and routing), skill registry (MCP-style dynamic tool loading), and provider abstractions (unified LLM/image APIs). Event-driven webhook handling with message queues decouples receipt from processing, enabling horizontal scaling. Multi-tiered memory systems (short-term buffer, long-term vector DB, working cache) prevent context window exhaustion while maintaining personalization.

**Major components:**
1. **Messaging Adapter Layer** — Normalizes WhatsApp/Telegram/Discord events into unified schema, handles webhook verification, idempotency checking, platform-agnostic core logic
2. **Conversation Orchestrator** — Core engine managing conversation turns, mode detection and routing (secretary vs intimate), safety policy enforcement, tool coordination
3. **Skill Registry with Tool Calling** — MCP pattern where skills expose JSON schemas for LLM function calling, dynamic loading enables zero-downtime feature additions
4. **Provider Abstraction Layer** — Unified interface for LLMs (OpenAI, Anthropic via OpenRouter) and image generation (Replicate, Fal.ai), intelligent routing for cost optimization, automatic failover
5. **Multi-Tiered Memory System** — Short-term (conversation buffer in Redis), long-term (vector DB for RAG), working memory (inter-skill cache), context manager selectively loads relevant history
6. **Event-Driven Webhook Architecture** — Immediate acknowledgment (200 OK) → queue → async worker processing, prevents platform retries, enables horizontal scaling

### Critical Pitfalls

Research identified 8 critical pitfalls specific to this domain. The top 5 with highest impact:

1. **WhatsApp Business API Instant Ban for Adult Content** — WhatsApp has <5% approval rate for adult businesses and bans accounts sending NSFW images, even if user-requested. End-to-end encryption doesn't prevent detection (metadata, user reports). **Solution:** Text-only intimate mode on WhatsApp; deliver images via separate authenticated web portal, never inline media. This is a Phase 0 architectural constraint.

2. **Database Misconfiguration Exposing All User Conversations** — 83% of Supabase breaches involve RLS misconfigurations. 20+ AI chatbot apps exposed 400M+ messages in 2025-2026. RLS is disabled by default. **Solution:** Enable Row-Level Security on EVERY table using `auth.uid()` policies before production deployment, add indexes on user_id columns, test cross-user access with multiple accounts. Phase 1 database setup.

3. **Prompt Injection Bypassing Mode Restrictions** — LLMs cannot reliably separate system instructions from user input. Roleplay attacks achieve 76.2% bypass rates. **Solution:** Separate model contexts per mode, retokenization (98% attack prevention), confirmation gates for mode switches, input sanitization, output validation, rate limiting. Phase 2 mode switching.

4. **Avatar Consistency Drift Across Generated Images** — Character consistency is the primary technical challenge in AI image generation. Prompt variations cause different faces/bodies/ethnicities. **Solution:** Generate canonical reference image on avatar creation, use FLUX 2 Pro with up to 10 reference images, structured prompts repeated exactly, never allow synonym variation. Phase 3 avatar builder.

5. **Legal Liability for AI-Generated Intimate Imagery** — TAKE IT DOWN Act (effective May 19, 2026) creates federal crime for publishing AI-generated intimate imagery without consent. DEFIANCE Act allows $250K statutory damages. Section 230 doesn't apply when platform creates content. **Solution:** Implement 48-hour takedown process, age verification beyond checkboxes, visible watermarks + C2PA provenance, audit logging of all generations. Phase 0 legal/compliance before building image generation.

Additional critical pitfalls: false positive mode switching destroying trust (require confirmation, use conversation context), emotional dependency and mental health liability (crisis detection, 3-hour AI reminders, usage warnings), WhatsApp rate limiting killing UX (Business Verification for 100K limit, quality rating monitoring, message queueing).

## Implications for Roadmap

Based on research, the project should be divided into phases that address dependencies, mitigate critical pitfalls early, and validate core differentiators before expanding scope.

### Phase 0: Legal & Architectural Foundation
**Rationale:** Critical pitfalls must be addressed before building features. WhatsApp NSFW ban and TAKE IT DOWN Act liability are architectural constraints, not afterthoughts.
**Delivers:** Legal framework (attorney-reviewed ToS, 48-hour takedown process), messaging architecture decision (text-only intimate mode on WhatsApp, image portal separate), age verification strategy, compliance framework.
**Addresses:** Pitfalls #1 (WhatsApp ban), #5 (legal liability), #7 (emotional dependency framework).
**Timeline:** 1 week (parallel to Phase 1 setup).

### Phase 1: Database, User Management & WhatsApp Integration
**Rationale:** Data persistence and message flow must exist before conversational AI. RLS misconfiguration is the #1 breach vector—must be tested from day one. WhatsApp Business Verification takes 2-4 weeks, start immediately.
**Delivers:** PostgreSQL + Redis setup with RLS policies on all tables, user CRUD with authentication, WhatsApp Business API integration with webhook verification, basic message adapter (normalize WhatsApp events → echo back).
**Addresses:** Pitfall #2 (database breach via RLS), #8 (WhatsApp rate limits—complete Business Verification early).
**Uses:** PostgreSQL 16 + Drizzle ORM, Redis 7, WhatsApp Cloud API, Fastify 5 for webhooks.
**Avoids:** Client-side data filtering, missing RLS indexes, synchronous webhook processing.

### Phase 2: Core Intelligence & Mode Switching
**Rationale:** Mode switching is the core product differentiator—validate this early. Prompt injection defense must be architectural (separate contexts), not an add-on.
**Delivers:** LLM provider abstraction (OpenRouter integration), basic chat without tools, conversation buffer (short-term memory in Redis), agent router with fuzzy intent detection, confirmation gates for mode switches, separate model contexts per mode, input sanitization and output validation.
**Addresses:** Pitfall #3 (prompt injection), #6 (false positive mode switching).
**Uses:** LangChain.js 0.3, OpenRouter, Zod for validation, Redis for memory.
**Implements:** Conversation orchestrator, agent router, mode state management.

### Phase 3: Secretary Skills (Productivity Value)
**Rationale:** Secretary mode provides productivity utility and regulatory cover (WhatsApp requires concrete business use cases, not just open-ended chat). Skills validate tool-calling architecture before complex intimate mode features.
**Delivers:** Skill Registry with MCP pattern, Reminders skill (simpler—no OAuth), Calendar skill (Google Calendar API + OAuth), Research skill (web search or knowledge lookup).
**Addresses:** WhatsApp's 2026 policy requiring concrete business tasks (not just "companion chatbot").
**Uses:** Google Calendar API with OAuth 2.0, skill plugin architecture, LangChain tool definitions.
**Implements:** Tool Registry component, dynamic skill loading.

### Phase 4: Intimate Mode Foundation
**Rationale:** Personality system comes before image generation (simpler—just prompt engineering). Defer image generation until personality, safety, and legal framework are solid.
**Delivers:** Preset personality system (3-5 personas as system prompt templates), content escalation logic (conversation intensity analysis), safety policy engine (block non-consensual content), crisis detection (suicidal ideation → 988 resources), 3-hour AI reminder (California law), usage time warnings.
**Addresses:** Pitfall #7 (emotional dependency), content safety guardrails for NSFW.
**Uses:** Persona configs (data-driven, not hardcoded), safety pattern matching + LLM-based moderation.
**Implements:** Personality injection into system prompts, safety policy layer.

### Phase 5: Avatar System & Image Generation
**Rationale:** Image generation is most complex intimate mode feature—defer until core is validated. Avatar consistency requires reference image architecture from day one.
**Delivers:** Avatar customization UI (gender, age 20+, race/nationality, appearance description), canonical reference image generation and storage, image provider abstraction, Replicate/Fal.ai integration with reference image support, visible watermarks + C2PA credentials, generation audit logging.
**Addresses:** Pitfall #4 (avatar consistency drift—use reference images).
**Uses:** Replicate API with FLUX 2 Pro for character consistency, structured prompts, image storage with CDN caching.
**Implements:** Image Provider abstraction, avatar reference system, watermarking pipeline.

### Phase 6: Production Hardening
**Rationale:** Production concerns after features work. Message queue enables scaling, long-term memory is optimization (short-term works for MVP), multi-provider failover reduces risk.
**Delivers:** BullMQ integration for async webhook processing, idempotency tracking (prevent duplicate processing), long-term memory (vector DB for conversation history RAG), multi-provider LLM failover, structured logging and observability, billing/usage tracking.
**Addresses:** Scalability beyond initial users, cost optimization, operational resilience.
**Uses:** BullMQ + Redis for queue, Pinecone/Qdrant for vector DB, Pino for logging.
**Implements:** Event-driven architecture, RAG retrieval, LLM Router with failover.

### Phase Ordering Rationale

- **Phase 0 before all else**: Legal and architectural constraints are non-negotiable. WhatsApp NSFW ban and TAKE IT DOWN Act aren't feature decisions—they're compliance requirements that dictate architecture.
- **Phase 1 validates infrastructure**: Database + WhatsApp integration must work before building on top. RLS testing with multiple accounts prevents the #1 breach vector (misconfigured multi-tenancy).
- **Phase 2 validates core differentiator**: Mode switching is what makes Ava unique. If fuzzy intent detection doesn't work or prompt injection bypasses modes, the product concept fails. Validate early.
- **Phase 3 before Phase 4**: Secretary skills are simpler than intimate mode (no image generation, clearer safety boundaries, well-documented APIs). They validate tool-calling architecture and provide WhatsApp policy compliance (concrete business use case).
- **Phase 4 before Phase 5**: Personality system is low-risk prompt engineering. Image generation is high-risk (consistency, legal liability, cost). Get text-based intimate mode working first.
- **Phase 5 after legal foundation**: Avatar image generation requires Phase 0's legal framework (watermarking, audit logs, takedown process) to be compliant before generating first image.
- **Phase 6 is optimization**: Features work without async queues and long-term memory—these improve scalability and UX but aren't blocking for beta launch.

**Parallelizable work:**
- Phase 0 (legal) runs in parallel with Phase 1 (database/WhatsApp setup)
- Phase 3 skills (calendar, reminders, research) can be developed independently once Skill Registry exists
- Phase 6 observability can be added while Phase 5 image generation is being built

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (Calendar Skill):** Google Calendar OAuth flow has nuances (incremental scopes, refresh token rotation, consent screen setup). Research OAuth 2.0 best practices and Google Workspace API specifics.
- **Phase 5 (Image Generation):** Avatar consistency techniques evolving rapidly (FLUX 2 Pro was SOTA as of Feb 2026, but landscape changes fast). Research current best practices for character reference systems when starting this phase.
- **Phase 6 (Vector DB Selection):** Tradeoffs between Pinecone (managed, expensive), Qdrant (self-hosted or cloud), and Weaviate (open-source) depend on scale and budget. Research pricing and performance benchmarks.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Database + WhatsApp):** Well-documented. PostgreSQL RLS has standard patterns, WhatsApp Cloud API has official docs. Follow established guides.
- **Phase 2 (LLM Integration):** LangChain.js + OpenRouter patterns are mature. Use official documentation and examples.
- **Phase 4 (Personality System):** Prompt engineering is iterative but doesn't need deep research—use competitor analysis (Replika, Character.AI personas) as templates.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Core technologies (Node.js, TypeScript, Fastify, PostgreSQL, LangChain, WhatsApp API) are industry standard for 2026 chatbot development. Multiple official docs and recent articles confirm choices. Image generation APIs (Replicate, Fal.ai) are MEDIUM confidence due to rapid market evolution. |
| Features | HIGH | Extensive competitor analysis (Replika, Character.AI, Candy.AI, ChatGPT) reveals clear market gap for dual-mode product. Feature categorization (table stakes, differentiators, anti-features) based on 30+ sources from 2025-2026. MVP definition validated against WhatsApp 2026 policy requirements. |
| Architecture | HIGH | Tool-calling orchestration with modular skill systems is the 2026 standard pattern. Multiple sources confirm event-driven webhook architecture, multi-provider abstraction, and multi-tiered memory. Project structure recommendations based on feature-first TypeScript patterns for modern Node.js. |
| Pitfalls | HIGH | All 8 critical pitfalls verified with official sources: WhatsApp Business Policy for NSFW ban, Supabase RLS guides for database breach, OWASP LLM01:2025 for prompt injection, TAKE IT DOWN Act for legal liability, Nature journal for emotional dependency. Sources from Q4 2025 through Feb 2026 (recent and authoritative). |

**Overall confidence:** HIGH

Research is grounded in official documentation (WhatsApp Business API, Google Calendar API, Anthropic SDK, LangChain docs), regulatory sources (TAKE IT DOWN Act, GDPR compliance), academic papers (Nature on emotional dependency), and recent industry analysis (2026 chatbot benchmarks, AI companion market reports). The only MEDIUM confidence area is image generation APIs due to rapid innovation cycles, but multiple fallback providers (Replicate, Fal.ai, getimg.ai) mitigate risk.

### Gaps to Address

While research is comprehensive, several areas need validation during implementation:

- **Avatar consistency techniques:** Image generation is evolving rapidly. FLUX 2 Pro with reference images is current SOTA (Feb 2026), but better methods may emerge. Plan to re-research before Phase 5 starts (likely 6-8 weeks from now). Mitigation: Use provider abstraction so switching from Replicate to newer service is configuration change, not code rewrite.

- **WhatsApp NSFW policy enforcement strictness:** Research confirms NSFW images lead to bans, but unclear how aggressively WhatsApp monitors text content or external links to image portals. Conservative approach: text-only intimate mode, images via separate portal with authentication. Validation: Monitor quality rating closely during beta; if text-only intimate conversations trigger warnings, may need to soften language or add disclaimers.

- **Mode switching false positive rate:** Research shows intent classification achieves ~5% false positive rate with fine-tuning. Unknown if this is acceptable to users or if it breaks trust. Mitigation: Implement confirmation gates ("Switch to intimate mode?") and undo mechanism. Validation: Track mode switch satisfaction in beta user feedback.

- **Age verification effectiveness:** Research recommends beyond self-reported age (ID verification or payment method age check), but implementation details vary by jurisdiction. Gap: Best practice for 20+ verification in 2026 is unclear (vs. 18+ which has established patterns). Action: Consult legal counsel during Phase 0 to determine compliant age verification method (credit card, ID upload with liveness check, or third-party verification service).

- **Long-term memory retrieval strategy:** Vector similarity search is standard, but optimal retrieval heuristics (how many memories to load, similarity threshold, recency weighting) are product-specific. Gap: Won't know ideal settings until real conversations. Mitigation: Start with conservative defaults (top 5 memories, 0.7 similarity threshold), instrument with metrics, tune based on user feedback in Phase 6.

## Sources

### Primary (HIGH confidence)

**Official Documentation:**
- [WhatsApp Business Platform Node.js SDK](https://whatsapp.github.io/WhatsApp-Nodejs-SDK/) — Official SDK (archived 2023, confirms REST API is current approach)
- [WhatsApp Cloud API Documentation](https://developers.facebook.com/docs/whatsapp/cloud-api) — Current official integration
- [WhatsApp Business Policy](https://business.whatsapp.com/policy) — Content policies and prohibited categories
- [Google Calendar API Node.js Quickstart](https://developers.google.com/workspace/calendar/api/quickstart/nodejs) — OAuth flow and API usage
- [Anthropic SDK npm](https://www.npmjs.com/package/@anthropic-ai/sdk) — Version 0.78.0
- [BullMQ Official Documentation](https://docs.bullmq.io/) — Queue implementation guide
- [Drizzle ORM Documentation](https://orm.drizzle.team/) — ORM patterns and migration
- [OpenRouter API Documentation](https://openrouter.ai/docs) — Unified LLM gateway

**Regulatory & Legal:**
- [TAKE IT DOWN Act and DEFIANCE Act Analysis](https://www.crowell.com/en/insights/client-alerts/federal-and-state-regulators-target-ai-chatbots-and-intimate-imagery) — Federal law effective May 19, 2026
- [OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) — Security guidance
- [Emotional Risks of AI Companions (Nature)](https://www.nature.com/articles/s42256-025-01093-9) — Academic research on mental health

**Security & Data Breaches:**
- [Every AI App Data Breach 2025-2026](https://blog.barrack.ai/every-ai-app-data-breach-2025-2026/) — RLS misconfiguration case studies
- [Supabase Row Level Security Complete Guide 2026](https://designrevision.com/blog/supabase-row-level-security) — Implementation patterns

### Secondary (MEDIUM confidence)

**Technical Comparisons & Benchmarks:**
- [Drizzle vs Prisma 2026 Comparison](https://www.bytebase.com/blog/drizzle-vs-prisma/) — ORM evaluation
- [Express vs Fastify vs NestJS Performance](https://www.index.dev/skill-vs-skill/backend-nestjs-vs-expressjs-vs-fastify) — Framework benchmarks
- [LangChain vs LlamaIndex 2026](https://contabo.com/blog/llamaindex-vs-langchain-which-one-to-choose-in-2026/) — LLM framework comparison
- [AI Image Model Pricing Comparison 2026](https://pricepertoken.com/image) — Replicate vs Fal.ai costs

**Architecture Patterns:**
- [Designing a Chatbot System in 2026](https://bhavaniravi.com/blog/GenAI/designing-chatbot-system-in-2026/) — MCP integration, multi-layered memory
- [How to Build a Chatbot: Components & Architecture 2026](https://research.aimultiple.com/chatbot-architecture/) — Component breakdown
- [LLM Orchestration in 2026: Top 22 frameworks and gateways](https://research.aimultiple.com/llm-orchestration/) — Multi-provider abstraction

**Competitor Analysis:**
- [Replika AI Complete Overview 2025](https://www.eesel.ai/blog/replika-ai) — Feature set and pivot away from romance
- [Character.AI in 2026: Features & Usage Guide](https://autoppt.com/blog/character-ai-evolution-complete-guide/) — Fiction/roleplay focus
- [Candy AI Review 2026](https://howtotechinfo.com/candy-ai/) — NSFW companion features
- [ChatGPT New Features 2025](https://www.gend.co/blog/chatgpt-2026-latest-features) — Productivity assistant capabilities

**Domain-Specific Pitfalls:**
- [Noobs Guide to Character Consistency in Image Models](https://medium.com/@saquiboye/noobs-guide-to-character-consistency-in-image-models-882165438092) — Reference image techniques
- [Chatbot Intent Recognition 2026](https://research.aimultiple.com/chatbot-intent/) — False positive detection
- [WhatsApp API Rate Limits Guide](https://www.chatarchitect.com/news/whatsapp-api-rate-limits-what-you-need-to-know-before-you-scale) — Messaging limits and quality rating

### Tertiary (LOW confidence, needs validation)

- [Utilizing Flux in ComfyUI for Consistent Character Creation](https://learn.thinkdiffusion.com/consistent-character-creation-with-flux-comfyui/) — FLUX 2 Pro techniques (need to verify SOTA status before Phase 5)
- [Grok's Mass Digital Undressing Spree](https://www.techpolicy.press/the-policy-implications-of-groks-mass-digital-undressing-spree/) — Regulatory context (opinion piece, but cites real events)

---
*Research completed: 2026-02-23*
*Ready for roadmap: yes*
