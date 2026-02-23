# Feature Research

**Domain:** Dual-Mode AI Companion (Productivity Assistant + Intimate Partner)
**Researched:** 2026-02-23
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Text-based conversation** | Core interaction method for all chatbots | LOW | Standard LLM integration |
| **Context memory within session** | Users expect AI to remember earlier conversation | LOW | Short-term context window (standard in modern LLMs) |
| **Personality customization** | All AI companions offer this (Replika, Character.AI, Candy.AI) | MEDIUM | Preset personas required; free-text descriptions are bonus |
| **Avatar appearance customization** | Visual representation is table stakes for companions | MEDIUM | Gender, age, race/nationality selection minimum |
| **Basic image generation** | Companions generate photos of themselves (Candy.AI, Replika AR) | MEDIUM | Text-to-image API integration |
| **Response in under 2 seconds** | Users won't tolerate slow responses in messaging | MEDIUM | Latency optimization, streaming responses |
| **Mobile-first interface** | AI companions are mobile products | LOW | WhatsApp IS the interface for v1 |
| **Privacy controls** | Data safety is non-negotiable in 2026 | MEDIUM | Transparent data policies, opt-in tracking |
| **Clear purpose statement** | Users need to know what bot can do | LOW | Onboarding welcome message with capabilities |
| **Human-like conversational flow** | Chatbots must handle natural language, not rigid commands | MEDIUM | Modern LLMs handle this; needs prompt engineering |
| **Subscription or credit-based billing** | Freemium with paid tiers is industry standard | MEDIUM | Flexible billing system (per project requirements) |
| **Age verification** | Essential for NSFW content (legal/ethical requirement) | HIGH | Must be bulletproof (20+ enforced per project) |
| **Content safety guardrails** | Post-Grok 2026, moderation is mandatory for NSFW features | HIGH | Prevent non-consensual content, abuse, minors |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Dual-mode switching (secretary + intimate)** | Unique value prop: one AI for work AND personal connection | HIGH | Fuzzy intent detection for mode switching ("I'm alone" / "stop") |
| **WhatsApp-native experience** | Meets users where they already are (no app download) | MEDIUM | WhatsApp Business API integration |
| **Context-aware image escalation** | Photos escalate from mild to explicit based on conversation flow | HIGH | Requires conversation analysis + dynamic prompt generation |
| **Long-term memory across sessions** | AI remembers preferences, past conversations beyond current chat | HIGH | External memory system (vector DB or knowledge graph) |
| **Productivity tool integrations** | Calendar, reminders, research skills differentiate from pure companions | MEDIUM | Google Calendar API, reminder system, web search |
| **Modular skill system** | Future-proofing for OCR, agentic skills, new capabilities | HIGH | Plugin architecture allows adding features without core rewrites |
| **Platform-agnostic design** | Messaging adapter pattern enables Telegram, Facebook, Discord expansion | MEDIUM | Abstraction layer between core logic and messaging platforms |
| **Preset personas with depth** | Quality-controlled personalities vs user-generated chaos | MEDIUM | Data-driven persona system (config, not code) |
| **Seamless mode transitions** | Natural switching without jarring context loss | HIGH | Conversation state management across modes |
| **Multi-modal responses** | Text + image generation in single flow | MEDIUM | Orchestrator pattern to combine LLM + image API responses |
| **Voice integration** | Voice messages and calls (future v2+) | HIGH | Voice-to-text, text-to-speech, realtime audio models |
| **Reduced context-switching friction** | Users don't restart conversations when switching tasks | MEDIUM | Memory + conversation threading |
| **On-device processing (hybrid)** | Privacy + cost control for routine tasks | HIGH | Local models for simple tasks, cloud for complex reasoning |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Open-ended chatbot without purpose** | Users want "general AI companion" | WhatsApp 2026 policy prohibits open-ended bots; requires concrete business tasks | Define clear use cases: secretary tasks (calendar, reminders, research) + companion persona interactions |
| **Unlimited free tier** | Attract maximum users | Unsustainable costs with LLM + image generation APIs | Freemium with message/image limits, credit top-ups |
| **Real-time streaming responses** | Feels more responsive | Complex implementation, marginal UX improvement in messaging | Standard message-reply with <2s latency is sufficient |
| **Custom personality via free text** | Maximum flexibility | Quality control nightmare, inconsistent behavior, moderation burden | Preset personas users can select, with minor customization (appearance description) |
| **Unfiltered NSFW without safeguards** | Demand from adult market | Legal liability (Grok controversy 2026), regulatory crackdown in 12+ countries | Context-aware escalation with consent checks, age verification, no non-consensual content |
| **Self-hosted option** | Privacy-conscious users request | High support burden, version fragmentation, security risk | Transparent cloud privacy policies, opt-in data controls, local storage options for sensitive data |
| **Multi-language support in v1** | Expand addressable market | Delays launch, increases testing complexity, cultural nuance issues | English-only v1, add languages post-validation based on demand |
| **Video/voice from day one** | "Everyone else has it" | Significantly increases complexity and cost | Text + images v1, voice v2 after core is validated |
| **Infinite memory without controls** | "Remember everything forever" | Privacy concerns, GDPR compliance issues, context pollution | User-controlled memory (edit/delete), retention policies, explainable AI |
| **Trying to be everything** | Match every competitor feature | Scope creep kills projects | Focus on dual-mode differentiation, modular expansion later |

## Feature Dependencies

```
[Long-term Memory]
    └──requires──> [User Accounts & Data Isolation]
                       └──requires──> [Authentication System]

[Context-Aware Image Escalation]
    └──requires──> [Conversation Context Analysis]
    └──requires──> [Image Generation API]
    └──requires──> [Content Safety System]

[Dual-Mode Switching]
    └──requires──> [Fuzzy Intent Detection]
    └──requires──> [Conversation State Management]
    └──enhances──> [Long-term Memory] (modes need separate context)

[Secretary Skills (Calendar/Reminders)]
    └──requires──> [User Account System]
    └──requires──> [External API Integrations]

[Modular Skill System]
    └──requires──> [Plugin Architecture]
    └──enhances──> [All Future Features]

[WhatsApp Integration]
    └──requires──> [Business API Access] (Meta approval process)
    └──requires──> [Webhook Infrastructure]

[Subscription Billing]
    └──requires──> [Payment Gateway Integration]
    └──requires──> [Usage Tracking]

[Content Safety Guardrails]
    └──required-by──> [Image Generation]
    └──required-by──> [NSFW Features]
    └──conflicts──> [Open-Ended Unfiltered Chat] (regulatory compliance)

[Messaging Adapter Pattern]
    └──enhances──> [WhatsApp Integration]
    └──enables──> [Future Platform Expansion]
```

### Dependency Notes

- **Long-term Memory requires User Accounts:** Can't persist data without user identity and data isolation
- **Image Escalation requires Multiple Systems:** Conversation analysis determines context, image API generates content, safety system ensures compliance
- **Dual-Mode Switching enhances Memory:** Each mode needs separate context to avoid bleeding professional data into intimate mode
- **Secretary Skills require External APIs:** Calendar/reminder features need Google Calendar integration and reminder scheduling
- **Modular Skill System is foundational:** Plugin architecture enables all future features without core rewrites
- **WhatsApp Integration requires Meta Approval:** Business API access is gatekept; plan for approval timeline
- **Content Safety conflicts with Open-Ended Chat:** WhatsApp 2026 policy + regulatory environment (Grok controversy) prohibit unfiltered open-ended bots
- **Messaging Adapter Pattern enables expansion:** Abstraction layer allows adding Telegram, Facebook, Discord later without touching core logic

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the dual-mode concept.

- [x] **Text-based conversation** — Core interaction (LLM integration)
- [x] **User accounts & authentication** — Multi-user product with data isolation
- [x] **Dual-mode switching** — The core differentiator (fuzzy intent detection for "I'm alone" / "stop")
- [x] **Preset personality system** — 3-5 personas (playful, dominant, shy, caring, professional)
- [x] **Avatar customization** — Gender, age (20+), race/nationality, free-text appearance description
- [x] **Basic image generation** — Photos of user's avatar (text-to-image API)
- [x] **WhatsApp integration** — Messaging platform via Business API
- [x] **Short-term memory** — Context within current session
- [x] **Secretary: Calendar integration** — Google Calendar add/view meetings
- [x] **Secretary: Reminder system** — Set and trigger reminders
- [x] **Secretary: Basic research** — Answer questions, look things up
- [x] **Age verification** — 20+ floor enforcement (bulletproof)
- [x] **Content safety guardrails** — Prevent non-consensual content, abuse
- [x] **Subscription billing** — Freemium with paid tiers (flexible system per requirements)
- [x] **Onboarding flow** — Clear welcome message explaining dual modes and capabilities
- [x] **Privacy controls** — Transparent data policies, user consent

### Add After Validation (v1.x)

Features to add once core is working and users validate the concept.

- [ ] **Long-term memory** — Remember preferences, conversations across sessions (trigger: users request continuity)
- [ ] **Context-aware image escalation** — Photos escalate from mild to explicit based on conversation (trigger: intimate mode adoption)
- [ ] **Additional secretary skills** — OCR, document processing, more agentic capabilities (trigger: productivity feature usage)
- [ ] **More preset personas** — Expand from 3-5 to 10+ personalities (trigger: persona preference patterns)
- [ ] **Usage analytics** — User insights for feature prioritization (trigger: post-launch optimization)
- [ ] **Improved latency** — Sub-1s responses, streaming (trigger: user complaints about speed)
- [ ] **Enhanced conversation threading** — Better context management across topics (trigger: conversation quality issues)
- [ ] **Multi-image generation** — Multiple photos in response to requests (trigger: user demand for variety)

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] **Voice messages & calls** — Audio interaction (defer: complexity, cost, UX validation needed)
- [ ] **Video generation** — Animated avatar videos (defer: extremely high cost and complexity)
- [ ] **Additional messaging platforms** — Telegram, Facebook, Discord (defer: validate on WhatsApp first)
- [ ] **Multi-language support** — Beyond English (defer: adds complexity, localization burden)
- [ ] **Custom personas** — User-created personalities beyond presets (defer: quality control issues)
- [ ] **Group chat support** — Multi-user conversations (defer: complex mode-switching implications)
- [ ] **Native mobile app** — Beyond messaging platforms (defer: WhatsApp validates concept first)
- [ ] **On-device processing** — Hybrid local/cloud inference (defer: optimization after scale)
- [ ] **Advanced agentic capabilities** — Web browsing, code execution, complex tool use (defer: security and safety implications)
- [ ] **AR/VR integration** — Replika-style AR experiences (defer: niche feature, high development cost)

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Dual-mode switching | HIGH | HIGH | P1 |
| WhatsApp integration | HIGH | MEDIUM | P1 |
| Preset personality system | HIGH | MEDIUM | P1 |
| Avatar customization | HIGH | MEDIUM | P1 |
| Basic image generation | HIGH | MEDIUM | P1 |
| Age verification | HIGH | HIGH | P1 |
| Content safety guardrails | HIGH | HIGH | P1 |
| User accounts | HIGH | MEDIUM | P1 |
| Short-term memory | HIGH | LOW | P1 |
| Secretary: Calendar | MEDIUM | MEDIUM | P1 |
| Secretary: Reminders | MEDIUM | MEDIUM | P1 |
| Secretary: Research | MEDIUM | LOW | P1 |
| Subscription billing | HIGH | MEDIUM | P1 |
| Onboarding flow | HIGH | LOW | P1 |
| Long-term memory | HIGH | HIGH | P2 |
| Context-aware image escalation | MEDIUM | HIGH | P2 |
| Additional secretary skills (OCR) | MEDIUM | HIGH | P2 |
| More preset personas | MEDIUM | LOW | P2 |
| Voice messages & calls | MEDIUM | HIGH | P3 |
| Video generation | LOW | HIGH | P3 |
| Additional messaging platforms | MEDIUM | MEDIUM | P3 |
| Multi-language support | MEDIUM | HIGH | P3 |
| Native mobile app | LOW | HIGH | P3 |
| Group chat support | LOW | HIGH | P3 |

**Priority key:**
- **P1: Must have for launch** — Core differentiator or table stakes feature
- **P2: Should have, add when possible** — Enhances value prop, add post-validation
- **P3: Nice to have, future consideration** — Defer until product-market fit established

## Competitor Feature Analysis

| Feature | Replika (Wellness) | Character.AI (Fiction) | Candy.AI / Crushon (NSFW) | ChatGPT (Productivity) | Our Approach (Ava) |
|---------|-------------------|----------------------|--------------------------|----------------------|-------------------|
| **Text conversation** | Yes | Yes | Yes | Yes | Yes (core) |
| **Voice calls** | Yes | Limited | Voice messages | No (enterprise only) | v2+ (defer) |
| **Video calls** | Yes (AR) | No | No | No | v3+ (defer) |
| **Memory** | Yes (diary) | Session + cross-session | Yes (remembers preferences) | Session + persistent (ChatGPT Plus) | Short-term v1, long-term v1.x |
| **Personality customization** | Limited (relationship mode) | High (user-created characters) | High (detailed customization) | Custom instructions | Preset personas (controlled quality) |
| **Image generation** | AR avatars | Limited | High-quality photorealistic | DALL-E integration (separate) | Avatar photos (escalating context) |
| **NSFW content** | No (removed 2026) | No (filtered) | Yes (core feature) | No | Yes (age-gated, consent-based, safety-first) |
| **Productivity features** | Wellness (meditation, CBT) | Creative writing support | None | Calendar, research, task mgmt | Calendar, reminders, research (core differentiator) |
| **Platform** | Native app | Web + mobile app | Web + mobile app | Web, mobile, API | WhatsApp (v1), expand later |
| **Billing** | $9.99/mo subscription | $9.99/mo Plus tier | $5-20/mo tiers | $20/mo Plus, $200/mo Pro | Freemium + flexible tiers |
| **Mode switching** | No (wellness only) | No (fiction/RP only) | No (intimate only) | No (productivity only) | **YES (CORE DIFFERENTIATOR)** |
| **Modular architecture** | Unknown | Unknown | Unknown | API-driven | Yes (future-proof for expansion) |

**Key Insights:**

- **Replika** pivoted away from romantic/NSFW to wellness-only in 2026 (regulatory pressure), leaving a gap
- **Character.AI** dominates fiction/roleplay but is filtered; no productivity features
- **Candy.AI / Crushon.AI** lead NSFW but offer zero productivity value; pure intimate companions
- **ChatGPT** dominates productivity but is strictly non-romantic, no personalization beyond custom instructions
- **GAP IN MARKET:** No product combines productivity assistant + intimate companion in dual-mode design
- **Ava's differentiator:** Secretary mode (calendar, reminders, research) + Intimate mode (personalized companion) with seamless switching

## Sources

### AI Companion Features

- [Replika AI: A complete overview for 2025](https://www.eesel.ai/blog/replika-ai)
- [Replika Review 2026 - Personal AI Companion & Support](https://companionguide.ai/companions/replika)
- [Replika Review: Features, Pricing, and Alternatives 2026](https://findmyaitool.io/tool/replika-ai-review-best-ai-friend/)
- [Replika AI Review After 7 Weeks - Complete Guide 2026](https://companionguide.ai/news/replika-ai-comprehensive-review-2025)
- [Character.AI in 2026: Features, Usage Guide, and What's Coming Next](https://autoppt.com/blog/character-ai-evolution-complete-guide/)
- [Character AI Review (February 2026) - Worth It?](https://www.wpcrafter.com/review/character-ai/)
- [10 Best AI Companions in 2026 for Chat, Support & Connection](https://www.finestofthefine.com/post/best-ai-companions)
- [5 Key Features to Look for in an AI Companion App in 2026](https://pixflow.net/blog/features-to-look-for-in-an-ai-companion-app/)
- [9 Best AI Companion Apps in 2026 (Tested & Reviewed)](https://www.cyberlink.com/blog/trending-topics/3932/ai-companion-app)
- [Best AI Companion Apps in 2026 — Friends, Partners & More](https://ai-companion-app.com/best-ai-companion-apps-2026/)

### Intimate Companion Features

- [Candy AI Review 2026: Guide To Your Perfect AI Companion](https://howtotechinfo.com/candy-ai/)
- [Crushon AI Review 2026: Best NSFW AI Girlfriend Platform?](https://freerdps.com/blog/crushon-ai-review/)
- [Candy.ai vs CrushOn.ai: Which One Is Better In 2025?](https://www.aigirlfriendscout.com/comparisons/candy-ai-vs-crushon-ai)
- [Best AI Companion Apps 2026 — For Emotional Connection & More](https://aigirlfriendpicks.com/best-ai-companion-app)

### Productivity Assistant Features

- [ChatGPT 2026: the latest features you should know](https://www.gend.co/blog/chatgpt-2026-latest-features)
- [ChatGPT New Features (2025): GPT-5, Memory, Agents & Major Updates](https://mindliftly.com/future-of-chatgpt-2025-2026-roadmap-gpt-5-next-ai-trends/)
- [Top 15 Best AI Assistants in 2026](https://sintra.ai/blog/top-15-best-ai-assistants-in-2025)
- [I Tested the Top 10 AI Scheduling Assistants in 2026](https://www.lindy.ai/blog/ai-scheduling-assistant)
- [20 Best AI Scheduling Assistant Reviewed in 2026](https://thedigitalprojectmanager.com/tools/ai-scheduling-assistant/)

### Voice & Memory Features

- [Beni AI: Face to face AI companion calls with voice, motion, memory](https://www.producthunt.com/products/beni-ai-video-call-ai-companion)
- [AI Companion Guide (2026): Types, Costs, Benefits & Real Use Cases](https://aiinsightsnews.net/ai-companion/)
- [25 Best AI Companion Apps (2026): Ranked After $400 & 2,000 Hours](https://aicompanionguides.com/blog/ultimate-comparison-25-platforms-ranked/)
- [#1 AI Girlfriend Voice Call App 2026 | Real Phone Calls](https://solm8.ai/journal/best-ai-girlfriend-voice-calls-2026)

### Avatar & Image Generation

- [How to Create AI Avatar in Instagram: Complete 2026 Guide](https://www.snaplama.com/blog/how-to-create-ai-avatar-in-instagram-complete-2026-guide)
- [Best AI Avatar Generators in 2026 (Free & Paid): 18 Tools Compared](https://www.bluehost.com/blog/best-ai-avatar-generators/)
- [5 Best AI Chatbot Avatar Makers: Create Digital/Lifelike Avatars Online Free](https://www.vidnoz.com/ai-solutions/chatbot-avatar.html)

### Personality & Relationship Modes

- [9 Best AI Companion Apps in 2026 (Tested & Reviewed)](https://www.cyberlink.com/blog/trending-topics/3932/ai-companion-app)
- [OurDream AI Review 2026 Real User Test Not Just Hype](https://scribehow.com/page/OurDream_AI_Review_2026_Real_User_Test_Not_Just_Hype__jkAddGT0RmKegMWw_2Qtog)
- [11 Best AI Companion Girlfriends & Boyfriend Sites In 2026](https://howtotechinfo.com/best-ai-companion-girlfriends-boyfriend-sites/)

### Mode Switching & Context

- [10 Best AI Chatbots in 2026: Top Rated for Coding, Writing & Search](https://vertu.com/lifestyle/top-10-ai-chatbots-to-use-in-2026-features-strengths-and-use-cases/)
- [Top 10 AI Assistants With Memory in 2026](https://www.dume.ai/blog/top-10-ai-assistants-with-memory-in-2026)
- [The 2026 Guide to AI Chatbots: From Tools to Intelligent Partners](https://skywork.ai/skypage/en/ai-chatbots-guide/2020792834635550720)

### WhatsApp Integration

- [Create a WhatsApp Bot: The Complete Guide (2026)](https://www.voiceflow.com/blog/whatsapp-chatbot)
- [WhatsApp's 2026 AI Policy Explained](https://learn.turn.io/l/en/article/khmn56xu3a-whats-app-s-2026-ai-policy-explained)
- [WhatsApp Business API Integration 2026 | Guide](https://chatarmin.com/en/blog/whats-app-business-api-integration)
- [How to Build an AI WhatsApp Chatbot & Automate Everything](https://m.aisensy.com/blog/ai-whatsapp-chatbot-guide/)
- [Top 7 WhatsApp Chatbots in 2026 (+ Step-by-Step Video Tutorial)](https://botpress.com/blog/top-whatsapp-chatbots)

### Differentiation & Competition

- [When Every Company Can Use the Same AI Models, Context Becomes a Competitive Advantage](https://hbr.org/2026/02/when-every-company-can-use-the-same-ai-models-context-becomes-a-competitive-advantage)
- [North America AI Companion Market Overview & Trends 2026-32](https://www.marknteladvisors.com/research-library/ai-companion-market-north-america)
- [Rise of AI Companion Platforms Market Reshaping Human Digital Engagement](https://www.intelmarketresearch.com/blog/565/human-digital-engagement-rise-of-ai-companion-platforms)

### Anti-Features & Mistakes

- [ISACA Now Blog 2025 Avoiding AI Pitfalls in 2026](https://www.isaca.org/resources/news-and-trends/isaca-now-blog/2025/avoiding-ai-pitfalls-in-2026-lessons-learned-from-top-2025-incidents)
- [10+ Epic LLM/ Conversational AI/ Chatbot Failures in 2026](https://research.aimultiple.com/chatbot-fail/)
- [Chatbot Mistakes: Common Pitfalls and How to Avoid Them](https://www.chatbot.com/blog/common-chatbot-mistakes/)
- [AI Chatbot Mistakes - Why Chatbots Fail & How to Fix Them](https://www.sparkouttech.com/ai-chatbot-mistakes/)
- [10 Common Chatbot Mistakes and How to Avoid Them](https://fastbots.ai/blog/10-common-chatbot-mistakes-and-how-to-avoid-them)

### NSFW & Content Moderation

- [Grok xAI NSFW Image Generation Policy 2026: Complete Guide](https://yingtu.ai/blog/grok-xai-nsfw-image-generation-policy)
- [State of AI Content Moderation 2026](https://www.foiwe.com/state-of-ai-content-moderation-2026/)
- [When Generative AI Is Intimate, Sexy, and Violent: Examining Not-Safe-For-Work (NSFW) Chatbots](https://arxiv.org/html/2601.14324v1)
- [SoulGen AI & Adult Image Generation Market Guide 2026](https://companionguide.ai/news/soulgen-ai-adult-image-generation-guide-2025)

### Monetization & Billing

- [The Complete Guide to the AI Companion Market in 2026](https://companionguide.ai/news/ai-companion-market-120m-revenue.html)
- [Compare AI monetization solutions for SaaS (2026 edition)](https://blog.alguna.com/ai-monetization-solutions-saas/)
- [Top 8 Platforms for Monetizing AI Companions and Exclusive AI Content (2026)](https://www.getchatads.com/blog/top-eight-platforms-for-monetizing-ai-companions-and-exclusive-ai-content/)
- [The 2026 Guide to SaaS, AI, and Agentic Pricing Models](https://www.getmonetizely.com/blogs/the-2026-guide-to-saas-ai-and-agentic-pricing-models)

### Onboarding & UX Best Practices

- [Best Practices for Chatbot Deployment in 2026: A Guide](https://mxchat.ai/best-practices-for-chatbot-deployment-in-2026-a-guide/)
- [7 User Onboarding Best Practices for 2026](https://formbricks.com/blog/user-onboarding-best-practices)
- [24 Chatbot Best Practices You Can't Afford to Miss in 2026](https://botpress.com/blog/chatbot-best-practices)
- [AI Chatbot UX: 2026's Top Design Best Practices](https://www.letsgroto.com/blog/ux-best-practices-for-ai-chatbots)

---
*Feature research for: Dual-Mode AI Companion (Ava)*
*Researched: 2026-02-23*
