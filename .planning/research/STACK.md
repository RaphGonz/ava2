# Technology Stack

**Project:** Ava - Dual-Mode AI Companion
**Researched:** 2026-02-23
**Confidence:** MEDIUM-HIGH

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Node.js** | 20.x LTS | Runtime environment | Event-driven, non-blocking I/O ideal for real-time messaging webhooks. Industry standard for chatbot backends in 2025-2026. |
| **TypeScript** | 5.x | Type-safe JavaScript | Mandatory for modular architecture. Strict mode catches errors at compile time, makes refactoring safer, and enables IDE autocomplete. ESM-native in 2025. |
| **Fastify** | 5.x | HTTP framework | 3-4x faster than Express (70K vs 20K req/sec), first-class TypeScript support, schema validation built-in. Better for webhook handling at scale. |
| **PostgreSQL** | 16.x | Primary database | Best multi-tenant support via Row-Level Security + schemas. JSONB for flexible avatar/persona data. Battle-tested for SaaS at scale. |

**Confidence:** HIGH - These choices are industry standard for 2025-2026 Node.js chatbot development.

### LLM & AI Integration

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **LangChain.js** | 0.3.x | LLM orchestration | Best-in-class for agent workflows, tool calling, and conversation memory. Abstracts provider differences (OpenAI, Anthropic, etc.). Proven for production chatbots. |
| **OpenRouter** | API v1 | Unified LLM gateway | Access 500+ models (OpenAI, Anthropic, Claude, etc.) through one API. Automatic failover, cost optimization, and BYOK support. Perfect for swappable LLM backends. |
| **@anthropic-ai/sdk** | 0.78.x | Direct Anthropic access | For when you need Claude-specific features (long context, function calling). Used alongside OpenRouter for flexibility. |
| **Zod** | 3.x | Schema validation | LangChain tool definitions, environment variable validation, API request/response schemas. TypeScript-first runtime validation. |

**Confidence:** HIGH - LangChain + OpenRouter is the 2025 standard for modular LLM applications. Direct SDKs provide fallback options.

**Rationale:** LangChain focuses on orchestration and agents (perfect for secretary mode skills), while OpenRouter provides the swappable backend requirement. This combination delivers the modular AI layer specified in PROJECT.md.

### Image Generation

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Replicate API** | v1 | Image generation gateway | Access to Stable Diffusion, Flux, and consistent character models. Pay-per-use ($0.002-0.004/image). API-based, no infrastructure needed. |
| **Fal.ai** | v1 | Alternative/fallback | Faster inference (2-4s vs 5-10s), similar pricing. Use for production if Replicate has latency issues. |
| **getimg.ai** | API v2 | Consistent character system | Character reference feature (@ElementName reuse). Specifically designed for maintaining character consistency across generations. |

**Confidence:** MEDIUM - Image generation APIs are rapidly evolving. Multiple providers recommended as landscape shifts frequently.

**Rationale:**
- **Replicate** is the standard for API-based Stable Diffusion in 2025-2026 (no self-hosting needed)
- **getimg.ai** solves the "consistent character" requirement through their @ElementName system
- **Fal.ai** as backup ensures no single point of failure
- All three have per-image pricing (no monthly minimums), critical for early-stage SaaS

**What NOT to use:** Self-hosted Stable Diffusion (operational complexity, GPU costs, maintenance burden). OpenAI DALL-E (limited character consistency, higher cost per image).

### Messaging Integration

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **WhatsApp Business API** | Cloud API v21+ | Official WhatsApp integration | Required for production multi-user product. Webhooks-based, hosted by Meta, supports media uploads. |
| **whatsapp-web.js** | 1.34.x | Development/MVP alternative | Unofficial library using Puppeteer. ONLY for MVP testing - Meta can ban accounts. DO NOT use for production SaaS. |

**Confidence:** HIGH - Official WhatsApp Business API is mandatory for production. No viable alternatives for multi-user SaaS.

**Critical Note:** The official WhatsApp Node.js SDK (github.com/WhatsApp/WhatsApp-Nodejs-SDK) was **archived in June 2023**. Use direct REST API calls or community maintained SDKs like `@whiskeysockets/baileys` (unofficial) for development. For production, integrate directly with WhatsApp Cloud API webhooks.

**Migration path:**
1. **MVP/Development:** whatsapp-web.js (fast iteration, no approval needed)
2. **Production:** WhatsApp Business API (requires Meta verification, takes 2-4 weeks)

### Database & ORM

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Drizzle ORM** | 0.36.x | Database toolkit | SQL-first TypeScript ORM. 7.4kb bundle, serverless-optimized, faster than Prisma. Edge-ready for modern hosting. Migration story clearer than Prisma 7 changes. |
| **PostgreSQL** | 16.x | Relational database | Multi-tenancy via Row-Level Security. JSONB for avatar configs. pgvector for future semantic search (memory system). |
| **Redis** | 7.x | Cache & job queue | Session storage, LLM response caching, BullMQ job queue backend. Essential for webhook deduplication. |

**Confidence:** HIGH - Drizzle is the 2025-2026 recommended ORM for new TypeScript projects. PostgreSQL is industry standard for multi-tenant SaaS.

**Why Drizzle over Prisma:**
- Prisma 6→7 migration churn (Rust engine removed, schema changes)
- Drizzle has SQL-like API (easier for debugging, closer to the database)
- Smaller bundle size critical for serverless deployments
- TypeScript-first, better IDE experience

### Background Jobs & Queue

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **BullMQ** | 5.x | Job queue | Redis-backed queue for webhook processing, scheduled reminders, image generation jobs. Built for "exactly once" semantics. Best Node.js queue in 2025. |
| **Redis** | 7.x | Queue backend | BullMQ storage, rate limiting, caching. Single instance serves multiple purposes. |

**Confidence:** HIGH - BullMQ is the industry standard for Node.js background jobs since Bull deprecation.

**Why BullMQ:** WhatsApp webhooks can arrive out-of-order or duplicate. BullMQ handles retries, deduplication, rate limiting (critical for LLM API quotas), and parallel processing. Essential for production chatbot reliability.

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **Zod** | 3.x | Runtime validation | Environment variables, API schemas, LLM tool definitions. Replaces Joi/Yup. TypeScript-first. |
| **googleapis** | 140.x | Google Calendar API | Official Node.js client for Calendar integration (secretary mode). OAuth2 flow built-in. |
| **tsx** | 4.x | TypeScript runner | Development execution (replaces ts-node). Faster, ESM-native, works with Node 20+ watch mode. |
| **vitest** | 2.x | Testing framework | Replaces Jest. 10-20x faster in watch mode, native ESM, better TypeScript support. Vite-ecosystem standard. |
| **pino** | 9.x | Logging | Fast JSON logger. Cloudflare/Vercel compatible. Structured logging for debugging LLM conversations. |
| **dotenv** | 16.x | Environment variables | Load .env files. Pair with Zod for validation. Standard for local development. |
| **Awilix** | 10.x | Dependency injection | Container for plugin/skill system. Constructor injection for testability. TypeScript-compatible. |

**Confidence:** HIGH - These are current best-practice libraries for TypeScript Node.js in 2025-2026.

### External Services

| Service | Purpose | Why Recommended |
|---------|---------|-----------------|
| **OpenRouter** | LLM aggregator | Unified API for OpenAI, Anthropic, Claude, Gemini, etc. Automatic failover, cost tracking, BYOK support. |
| **Replicate** | Image generation | Stable Diffusion models as API. Pay-per-use, no GPU management. |
| **WhatsApp Business API** | Messaging platform | Official API required for production. Webhook-based architecture. |
| **Google Calendar API** | Calendar integration | Official API for secretary mode. OAuth2 flow for user auth. |
| **Railway / Render** | Hosting | Managed PostgreSQL + Redis + Node.js. Simpler than AWS for early-stage SaaS. Auto-scaling webhooks. |

**Confidence:** MEDIUM-HIGH - Railway/Render are common for early-stage SaaS. AWS/GCP viable alternatives with more complexity.

## Alternatives Considered

| Category | Recommended | Alternative | Why Not Alternative |
|----------|-------------|-------------|---------------------|
| **Framework** | Fastify | Express.js | Express is 3-4x slower (20K vs 70K req/sec). Fastify has better TypeScript support and built-in validation. |
| **Framework** | Fastify | NestJS | NestJS adds architectural overhead. Fastify + modules achieves same modularity with less abstraction. Better for small team. |
| **ORM** | Drizzle | Prisma | Prisma 6→7 migration churn, larger bundle size, less SQL transparency. Drizzle is the 2025-2026 trend for new projects. |
| **Testing** | Vitest | Jest | Jest is 10-20x slower in watch mode, worse ESM support, requires ts-jest for TypeScript. Vitest is Vite-ecosystem standard. |
| **LLM Framework** | LangChain | LlamaIndex | LlamaIndex is data-focused (RAG). LangChain better for agent orchestration (secretary skills). Combine if RAG needed later. |
| **Image API** | Replicate | Self-hosted SD | Self-hosting requires GPU management, model updates, scaling. API is pay-per-use with no ops burden. |
| **WhatsApp (prod)** | Business API | whatsapp-web.js | whatsapp-web.js is UNOFFICIAL, Meta bans accounts. Only for MVP. Production requires official API. |
| **Queue** | BullMQ | Agenda | Agenda is MongoDB-based, slower, less feature-complete. BullMQ is Redis-backed, industry standard since Bull deprecated. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **Official WhatsApp SDK** | Archived since June 2023, no longer maintained | Direct REST API calls to WhatsApp Cloud API or community SDKs |
| **ts-node** | Slower than tsx, poor ESM support, abandoned for 2025 workflows | tsx (4x faster, ESM-native, works with Node.js watch mode) |
| **Jest** | 10-20x slower than Vitest, complex ESM configuration, worse TypeScript DX | Vitest (Vite-native, faster, better TypeScript) |
| **Self-hosted Stable Diffusion** | GPU costs, model management, scaling complexity, updates burden | Replicate/Fal.ai APIs (pay-per-use, managed infrastructure) |
| **OpenAI DALL-E** | Limited character consistency, $0.04/image (10-20x Replicate cost) | Replicate + getimg.ai (consistent characters, $0.002-0.004/image) |
| **Mongoose (MongoDB)** | Multi-tenancy harder than PostgreSQL RLS, no pgvector for future semantic search | PostgreSQL + Drizzle ORM |
| **CommonJS (require)** | ESM is the 2025 standard, better tree-shaking, native browser compatibility | ES Modules (import/export) with "type": "module" in package.json |

## Installation

```bash
# Core Framework
npm install fastify@5 @fastify/cors @fastify/helmet
npm install drizzle-orm@0.36 postgres
npm install bullmq@5 ioredis@5

# LLM & AI
npm install langchain@0.3 @langchain/openai @langchain/anthropic
npm install @anthropic-ai/sdk@0.78
npm install zod@3

# Google Calendar Integration
npm install googleapis@140

# Validation & Config
npm install zod@3 dotenv@16

# Dependency Injection (Plugin System)
npm install awilix@10

# Logging
npm install pino@9 pino-pretty@11

# Dev Dependencies
npm install -D typescript@5 @types/node@20
npm install -D tsx@4 vitest@2
npm install -D drizzle-kit@0.27 # Database migrations
npm install -D @typescript-eslint/parser @typescript-eslint/eslint-plugin
npm install -D prettier eslint
```

## Stack Patterns by Variant

### For Serverless Deployment (Vercel/Cloudflare Workers)

**Modify:**
- Use Vercel AI SDK instead of LangChain (lighter bundle)
- Use edge-compatible Redis (Upstash) instead of ioredis
- Use connection pooling for PostgreSQL (PgBouncer)
- Webhooks → Edge functions, Jobs → separate service

**Why:** Serverless has cold start constraints. Vercel AI SDK is optimized for edge runtime. Standard stack assumes long-running server.

### For Self-Hosted VPS

**Add:**
- Docker + docker-compose for orchestration
- Nginx for reverse proxy
- PM2 for process management (or use Docker's restart policies)
- Letsencrypt for SSL

**Why:** VPS requires explicit process management and reverse proxy configuration.

### For Development/MVP

**Swap:**
- WhatsApp Business API → whatsapp-web.js (faster iteration, no approval)
- PostgreSQL → SQLite + Drizzle (simpler local setup)
- Redis → In-memory cache (eliminate dependency)

**Why:** Faster local development. Migrate to production stack before launch.

## Version Compatibility

| Package | Requires | Notes |
|---------|----------|-------|
| fastify@5 | Node 20+ | Uses native fetch, async hooks improvements |
| langchain@0.3 | Node 18+ | ESM-only, requires "type": "module" |
| drizzle-orm@0.36 | TypeScript 5+ | Uses latest TS features, satisfies operator |
| vitest@2 | Vite 5+ | Auto-installs Vite if not present |
| tsx@4 | Node 18.6+ | Uses native --loader (no ts-node compatibility) |
| bullmq@5 | Redis 6.2+ | Uses Redis streams, not available in older Redis |

## Configuration Best Practices

### Environment Variable Validation (Zod)

```typescript
// config/env.ts
import { z } from 'zod';

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']),
  PORT: z.string().transform(Number).pipe(z.number().positive()),
  DATABASE_URL: z.string().url(),
  REDIS_URL: z.string().url(),
  OPENROUTER_API_KEY: z.string().min(10),
  WHATSAPP_VERIFY_TOKEN: z.string(),
  WHATSAPP_ACCESS_TOKEN: z.string(),
  GOOGLE_CLIENT_ID: z.string(),
  GOOGLE_CLIENT_SECRET: z.string(),
});

export const env = envSchema.parse(process.env);
```

### Dependency Injection Container (Awilix)

```typescript
// container.ts
import { createContainer, asClass, asValue } from 'awilix';
import { LLMService } from './services/llm';
import { ImageService } from './services/image';
import { CalendarSkill } from './skills/calendar';

export const container = createContainer();

container.register({
  // Services (singletons)
  llmService: asClass(LLMService).singleton(),
  imageService: asClass(ImageService).singleton(),

  // Skills (modular plugins)
  calendarSkill: asClass(CalendarSkill).singleton(),

  // Config
  config: asValue(env),
});
```

### Plugin/Skill Interface

```typescript
// types/skill.ts
export interface Skill {
  name: string;
  description: string;
  tools: ToolDefinition[]; // LangChain tools
  execute(context: ConversationContext): Promise<SkillResult>;
}

// Skills register themselves in DI container
// New skills = new file + container registration
// No modifications to existing code
```

## TypeScript Configuration

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "lib": ["ES2022"],
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

## Docker Configuration

```dockerfile
# Multi-stage build for production
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:20-alpine AS runner

WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY package*.json ./

ENV NODE_ENV=production
EXPOSE 3000

CMD ["node", "dist/index.js"]
```

## Sources

### Official Documentation (HIGH Confidence)
- [WhatsApp Business Platform Node.js SDK](https://whatsapp.github.io/WhatsApp-Nodejs-SDK/) - Official SDK (archived 2023)
- [WhatsApp Cloud API Documentation](https://developers.facebook.com/docs/whatsapp/cloud-api) - Current official integration
- [Google Calendar API Node.js Quickstart](https://developers.google.com/workspace/calendar/api/quickstart/nodejs) - Official Google docs
- [Anthropic SDK npm](https://www.npmjs.com/package/@anthropic-ai/sdk) - Version 0.78.0
- [BullMQ Official Documentation](https://docs.bullmq.io/) - Queue implementation guide
- [Drizzle ORM Documentation](https://orm.drizzle.team/) - Official ORM docs
- [OpenRouter API Documentation](https://openrouter.ai/docs) - Unified LLM gateway

### Technical Comparisons & Benchmarks (MEDIUM-HIGH Confidence)
- [Drizzle vs Prisma 2026 Comparison](https://www.bytebase.com/blog/drizzle-vs-prisma/) - Detailed ORM comparison
- [Express vs Fastify vs NestJS Performance](https://www.index.dev/skill-vs-skill/backend-nestjs-vs-expressjs-vs-fastify) - 2026 benchmarks
- [Vitest vs Jest 2026 Migration Guide](https://www.sitepoint.com/vitest-vs-jest-2026-migration-benchmark/) - Performance data
- [LangChain vs LlamaIndex 2026](https://contabo.com/blog/llamaindex-vs-langchain-which-one-to-choose-in-2026/) - LLM framework comparison
- [Multi-tenant PostgreSQL Architecture](https://www.bytebase.com/blog/multi-tenant-database-architecture-patterns-explained/) - SaaS database patterns
- [Node.js in 2025: Modern Practices](https://medium.com/lets-code-future/node-js-in-2025-modern-practices-you-should-be-using-ae1890ca575b) - Current best practices

### Image Generation APIs (MEDIUM Confidence)
- [AI Image Model Pricing Comparison 2026](https://pricepertoken.com/image) - Replicate vs Fal.ai costs
- [Best AI Character Generator 2026](https://www.neolemon.com/blog/best-ai-character-generator-for-consistent-characters-2025/) - Consistent character solutions
- [Replicate Consistent Characters Guide](https://replicate.com/blog/generate-consistent-characters) - Implementation patterns
- [getimg.ai Features](https://getimg.ai/features/consistent-ai-characters) - Character reference system

### Integration Guides (MEDIUM Confidence)
- [WhatsApp Business API Integration 2025](https://javascript.plainenglish.io/mastering-whatsapp-business-api-integration-a-step-by-step-node-js-guide-2025-edition-1b604c8c83a5) - Step-by-step guide
- [whatsapp-web.js Guide](https://wwebjs.dev/guide/) - Unofficial library documentation
- [Claude API Integration 2025](https://collabnix.com/claude-api-integration-guide-2025-complete-developer-tutorial-with-code-examples/) - Anthropic integration
- [OpenRouter Practical Guide](https://medium.com/@milesk_33/a-practical-guide-to-openrouter-unified-llm-apis-model-routing-and-real-world-use-d3c4c07ed170) - Multi-model routing

### Development Tools & Practices (MEDIUM-HIGH Confidence)
- [JWT Authentication Best Practices 2025](https://medium.com/deno-the-complete-reference/5-jwt-authentication-best-practices-for-node-js-apps-f1aaceda3f81) - Security patterns
- [Zod Environment Variable Validation](https://creatures.dev/blog/env-type-safety-and-validation/) - Config validation
- [Docker + TypeScript Best Practices 2025](https://medium.com/@robinviktorsson/containerizing-a-typescript-node-js-application-with-docker-a-step-by-step-guide-be7fc87191f8) - Containerization
- [Dependency Injection in Node.js TypeScript](https://www.lodely.com/blog/dependency-injection-in-nodejs-typescript) - Plugin architecture patterns

### Community Resources (LOW-MEDIUM Confidence)
- [LLM Orchestration in 2026](https://research.aimultiple.com/llm-orchestration/) - Framework overview (requires verification for production use)
- [State Machine Chatbot Patterns](https://rogerjunior.medium.com/how-to-build-a-chatbot-from-scratch-with-javascript-using-state-machines-95597c436517) - Conversation flow architecture

---

*Stack research completed: 2026-02-23*
*Overall confidence: MEDIUM-HIGH - Core technologies HIGH confidence, image generation APIs MEDIUM confidence due to rapid market changes*
