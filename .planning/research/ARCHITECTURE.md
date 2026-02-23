# Architecture Research

**Domain:** Dual-mode AI companion chatbot delivered via messaging platforms
**Researched:** 2026-02-23
**Confidence:** HIGH

## Standard Architecture

### System Overview

Modern AI chatbot systems in 2026 have shifted from rule-based intent mapping to **tool-calling orchestration architectures**. The dominant pattern is a layered, modular system where components communicate via well-defined interfaces, enabling independent scaling and evolution of individual subsystems.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MESSAGING ADAPTER LAYER                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │WhatsApp  │  │Telegram  │  │Discord   │  │  Email   │            │
│  │ Adapter  │  │ Adapter  │  │ Adapter  │  │ Adapter  │            │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘            │
│       │             │              │             │                  │
│       └─────────────┴──────────────┴─────────────┘                  │
│                            ↓                                         │
├─────────────────────────────────────────────────────────────────────┤
│                       ORCHESTRATION LAYER                            │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │          Conversation Orchestrator                       │        │
│  │  - System instructions & mode management                 │        │
│  │  - Turn routing & tool coordination                      │        │
│  │  - Safety policies & content moderation                  │        │
│  └──────────────┬──────────────────────────────────┬────────┘        │
│                 ↓                                   ↓                │
│    ┌───────────────────┐                ┌──────────────────┐        │
│    │   Agent Router    │                │  Context Manager │        │
│    │ (mode detection)  │                │  (RAG, chunking) │        │
│    └─────────┬─────────┘                └────────┬─────────┘        │
├──────────────┼──────────────────────────────────┼──────────────────┤
│              ↓                                   ↓                  │
│         SKILL/TOOL LAYER                  MEMORY LAYER              │
│  ┌─────────────────────┐           ┌──────────────────────┐        │
│  │   Tool Registry     │           │  Short-term Memory   │        │
│  │  ┌──────────────┐   │           │  (conversation buf)  │        │
│  │  │ Calendar     │   │           └──────────────────────┘        │
│  │  │ Skill        │   │           ┌──────────────────────┐        │
│  │  ├──────────────┤   │           │  Long-term Memory    │        │
│  │  │ Reminder     │   │           │  (vector DB + RAG)   │        │
│  │  │ Skill        │   │           └──────────────────────┘        │
│  │  ├──────────────┤   │           ┌──────────────────────┐        │
│  │  │ Research     │   │           │  Working Memory      │        │
│  │  │ Skill        │   │           │  (Redis cache)       │        │
│  │  ├──────────────┤   │           └──────────────────────┘        │
│  │  │ Image Gen    │   │                                            │
│  │  │ Skill        │   │                                            │
│  │  └──────────────┘   │                                            │
│  └─────────────────────┘                                            │
├─────────────────────────────────────────────────────────────────────┤
│                        PROVIDER LAYER                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │  LLM     │  │  Image   │  │ External │  │  User    │            │
│  │ Provider │  │ Provider │  │   APIs   │  │   DB     │            │
│  │ Abstraction││Abstraction││(Calendar)│  │ (Postgres)│            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Messaging Adapter** | Normalizes platform-specific events (WhatsApp, Telegram, etc.) into unified message schema. Handles webhook management, retry logic, idempotency. | Express.js webhook endpoints, platform SDK wrappers, event normalization middleware |
| **Conversation Orchestrator** | Core engine that manages conversation turns, routes requests based on mode, enforces safety policies, coordinates tool calls. | State machine or flow-based orchestration (LangGraph-style), maintains conversation context |
| **Agent Router** | Detects user intent to switch modes (secretary ↔ intimate), routes messages to appropriate conversation flows, handles fuzzy intent matching. | NLU-based classification or LLM-powered intent detection with function calling |
| **Tool Registry** | Catalog of available skills exposed as callable functions. Dynamically discovers and loads skills at runtime. Uses MCP (Model Context Protocol) pattern. | JSON schema registry, plugin manifest loader, dynamic function registration |
| **Context Manager** | Handles RAG retrieval, conversation summarization, chunking for long documents. Manages what enters the LLM context window. | Vector similarity search, summarization pipeline, context window optimizer |
| **Memory System** | Multi-tiered memory: short-term (conversation buffer), long-term (user preferences/history in vector DB), working (inter-agent cache). | Redis for working memory, Pinecone/Weaviate/Qdrant for vector store, conversation history in Postgres |
| **Skill Modules** | Encapsulated capabilities (calendar, reminders, research, image generation). Each is independently deployable with defined input/output contracts. | Microservice or plugin with standard interface: `execute(params) → result` |
| **LLM Provider Abstraction** | Unified interface across multiple LLM providers (OpenAI, Anthropic, open-source). Handles routing, failover, cost optimization. | LiteLLM, Portkey AI, or custom abstraction layer with retry/circuit breaker logic |
| **Image Provider Abstraction** | Unified interface for image generation backends (Stable Diffusion, DALL-E, Midjourney API). Manages prompt templates, escalation logic, content safety. | Abstract factory pattern with provider-specific implementations |
| **User DB** | Stores user accounts, avatar configurations, persona selections, billing state. Multi-tenant data isolation. | PostgreSQL with row-level security or MongoDB with tenant scoping |
| **Audit Log** | Records all agent decisions, tool invocations, mode switches, content generation for compliance, debugging, improvement. | Append-only event log (DynamoDB, EventStore), structured JSON logging |

## Recommended Project Structure

```
src/
├── adapters/                # Messaging platform adapters
│   ├── base/
│   │   └── MessageAdapter.ts      # Abstract base class
│   ├── whatsapp/
│   │   ├── WhatsAppAdapter.ts     # WhatsApp Business API integration
│   │   ├── webhookHandler.ts      # Webhook endpoint logic
│   │   └── normalizer.ts          # Event normalization to common schema
│   ├── telegram/                  # Future: Telegram adapter
│   └── registry.ts                # Adapter factory/registry
│
├── orchestration/           # Core conversation engine
│   ├── ConversationOrchestrator.ts  # Main orchestration logic
│   ├── AgentRouter.ts               # Mode detection & routing
│   ├── modes/
│   │   ├── SecretaryMode.ts         # Secretary conversation flow
│   │   └── IntimateMode.ts          # Intimate conversation flow
│   └── SafetyPolicy.ts              # Content moderation & safety checks
│
├── skills/                  # Pluggable skill modules
│   ├── base/
│   │   └── Skill.ts                 # Abstract skill interface
│   ├── calendar/
│   │   ├── CalendarSkill.ts         # Google Calendar integration
│   │   └── schema.json              # Function declaration schema
│   ├── reminders/
│   │   ├── ReminderSkill.ts
│   │   └── schema.json
│   ├── research/
│   │   ├── ResearchSkill.ts         # Web search/knowledge lookup
│   │   └── schema.json
│   ├── imageGeneration/
│   │   ├── ImageGenerationSkill.ts  # Avatar photo generation
│   │   ├── escalationLogic.ts       # Content intensity progression
│   │   └── schema.json
│   └── SkillRegistry.ts             # Dynamic skill loader
│
├── providers/               # Provider abstraction layers
│   ├── llm/
│   │   ├── LLMProvider.ts           # Abstract LLM interface
│   │   ├── OpenAIProvider.ts
│   │   ├── AnthropicProvider.ts
│   │   ├── router.ts                # Intelligent routing logic
│   │   └── fallback.ts              # Failover handling
│   ├── image/
│   │   ├── ImageProvider.ts         # Abstract image gen interface
│   │   ├── StableDiffusionProvider.ts
│   │   ├── DALLEProvider.ts
│   │   └── promptBuilder.ts         # Prompt template engine
│   └── external/
│       └── GoogleCalendarAPI.ts     # External API clients
│
├── memory/                  # Multi-tiered memory system
│   ├── ShortTermMemory.ts           # Conversation buffer (in-memory/Redis)
│   ├── LongTermMemory.ts            # User history (vector DB)
│   ├── WorkingMemory.ts             # Inter-agent state (Redis)
│   └── ContextManager.ts            # RAG retrieval & context optimization
│
├── data/                    # Data access layer
│   ├── models/
│   │   ├── User.ts                  # User entity
│   │   ├── Avatar.ts                # Avatar configuration
│   │   ├── Conversation.ts          # Conversation history
│   │   └── AuditLog.ts              # Event log
│   ├── repositories/
│   │   ├── UserRepository.ts
│   │   ├── AvatarRepository.ts
│   │   └── ConversationRepository.ts
│   └── database.ts                  # Database connection & migration
│
├── events/                  # Event-driven communication
│   ├── EventBus.ts                  # Internal event bus
│   ├── handlers/
│   │   ├── MessageReceivedHandler.ts
│   │   ├── ModeChangedHandler.ts
│   │   └── SkillCompletedHandler.ts
│   └── queue.ts                     # Message queue integration (BullMQ/SQS)
│
├── api/                     # HTTP API layer
│   ├── routes/
│   │   ├── webhooks.ts              # Platform webhooks
│   │   ├── users.ts                 # User management
│   │   └── health.ts                # Health checks
│   ├── middleware/
│   │   ├── authentication.ts
│   │   ├── rateLimiting.ts
│   │   └── errorHandler.ts
│   └── server.ts                    # Express app setup
│
├── utils/                   # Shared utilities
│   ├── logger.ts                    # Structured logging
│   ├── validation.ts                # Input validation
│   ├── retry.ts                     # Retry logic with backoff
│   └── idempotency.ts               # Duplicate prevention
│
└── main.ts                  # Application entry point
```

### Structure Rationale

- **adapters/**: Messaging platforms are isolated adapters implementing a common interface. Adding Telegram means creating `adapters/telegram/` without touching core logic.
- **orchestration/**: The brain of the system. Single responsibility: manage conversation flow, route to appropriate handlers, enforce policies.
- **skills/**: Each skill is a self-contained module with its own schema. The registry dynamically loads skills, enabling runtime extensibility.
- **providers/**: Abstract all external dependencies (LLMs, image APIs, external services). Swap providers by changing configuration, not code.
- **memory/**: Separates short-term (ephemeral), long-term (persistent), and working (cache) memory concerns.
- **data/**: Clean data access layer with repository pattern for testability and database portability.
- **events/**: Enables asynchronous, decoupled processing. Webhook receives → acknowledge immediately → queue for processing.
- **api/**: Thin HTTP layer. Webhooks translate platform events to internal events and hand off to orchestrator.

## Architectural Patterns

### Pattern 1: Adapter Pattern for Messaging Platforms

**What:** Channel adapter standardizes inputs from different messaging platforms (WhatsApp, Telegram, Discord) into a unified internal message schema.

**When to use:** Any system needing multi-platform support where each platform has different APIs, event formats, and delivery semantics.

**Trade-offs:**
- **Pro:** Core logic is platform-agnostic. Adding platforms is additive, not invasive.
- **Pro:** Testing is easier—mock the adapter interface, not each platform SDK.
- **Con:** Some platform-specific features may not map cleanly to common schema (requires extension points).
- **Con:** Slight performance overhead from normalization layer.

**Example:**
```typescript
// Base adapter interface
interface IMessageAdapter {
  normalize(platformEvent: any): UnifiedMessage;
  send(conversationId: string, message: OutgoingMessage): Promise<void>;
  acknowledge(eventId: string): Promise<void>;
}

// WhatsApp-specific implementation
class WhatsAppAdapter implements IMessageAdapter {
  normalize(whatsappWebhook: WhatsAppEvent): UnifiedMessage {
    return {
      conversationId: whatsappWebhook.entry[0].id,
      userId: whatsappWebhook.entry[0].changes[0].value.contacts[0].wa_id,
      text: whatsappWebhook.entry[0].changes[0].value.messages[0].text.body,
      timestamp: new Date(whatsappWebhook.entry[0].changes[0].value.messages[0].timestamp),
      platform: 'whatsapp',
      metadata: { /* platform-specific */ }
    };
  }

  async send(conversationId: string, message: OutgoingMessage): Promise<void> {
    await this.whatsappClient.sendMessage({
      messaging_product: "whatsapp",
      to: conversationId,
      text: { body: message.text }
    });
  }

  async acknowledge(eventId: string): Promise<void> {
    // WhatsApp requires immediate 200 OK to prevent retries
    // (handled at webhook endpoint level)
  }
}

// Telegram adapter would implement the same interface
class TelegramAdapter implements IMessageAdapter {
  // Different implementation, same interface
}

// Adapter registry for dynamic resolution
class AdapterRegistry {
  private adapters = new Map<string, IMessageAdapter>();

  register(platform: string, adapter: IMessageAdapter) {
    this.adapters.set(platform, adapter);
  }

  get(platform: string): IMessageAdapter {
    const adapter = this.adapters.get(platform);
    if (!adapter) throw new Error(`No adapter for platform: ${platform}`);
    return adapter;
  }
}
```

### Pattern 2: Tool Registry with Dynamic Skill Loading

**What:** Skills are discovered and loaded at runtime based on user intent. Uses MCP (Model Context Protocol) pattern where skills expose JSON schemas that LLMs can invoke.

**When to use:** Systems requiring extensibility without redeployment. Chatbots with growing capability sets, plugin ecosystems.

**Trade-offs:**
- **Pro:** Zero-downtime feature additions. Drop a new skill module in, it's automatically available.
- **Pro:** LLM learns to use new tools without retraining—just provide the schema.
- **Con:** Dynamic loading increases complexity (schema validation, error handling, security sandboxing).
- **Con:** Harder to trace execution paths statically.

**Example:**
```typescript
// Skill interface with declarative schema
interface ISkill {
  name: string;
  description: string;
  schema: JSONSchema; // OpenAI function calling schema
  execute(params: Record<string, any>): Promise<SkillResult>;
}

// Example: Calendar skill
class CalendarSkill implements ISkill {
  name = "add_calendar_event";
  description = "Adds an event to the user's Google Calendar";
  schema = {
    type: "object",
    properties: {
      title: { type: "string", description: "Event title" },
      start: { type: "string", format: "date-time" },
      end: { type: "string", format: "date-time" },
      description: { type: "string" }
    },
    required: ["title", "start", "end"]
  };

  async execute(params: { title: string; start: string; end: string; description?: string }) {
    const event = await this.googleCalendar.events.insert({
      calendarId: 'primary',
      requestBody: {
        summary: params.title,
        start: { dateTime: params.start },
        end: { dateTime: params.end },
        description: params.description
      }
    });

    return {
      success: true,
      data: { eventId: event.data.id, link: event.data.htmlLink }
    };
  }
}

// Skill registry with auto-discovery
class SkillRegistry {
  private skills = new Map<string, ISkill>();

  register(skill: ISkill) {
    this.skills.set(skill.name, skill);
  }

  // Returns schemas for LLM function calling
  getFunctionDeclarations(): OpenAIFunctionDeclaration[] {
    return Array.from(this.skills.values()).map(skill => ({
      name: skill.name,
      description: skill.description,
      parameters: skill.schema
    }));
  }

  async execute(skillName: string, params: any): Promise<SkillResult> {
    const skill = this.skills.get(skillName);
    if (!skill) throw new Error(`Unknown skill: ${skillName}`);
    return await skill.execute(params);
  }
}

// Orchestrator invokes skills via LLM tool calls
class ConversationOrchestrator {
  async processTurn(userMessage: string) {
    const functions = this.skillRegistry.getFunctionDeclarations();

    const response = await this.llm.chat({
      messages: [{ role: "user", content: userMessage }],
      functions, // LLM can call any registered skill
      function_call: "auto"
    });

    // If LLM decided to call a function
    if (response.function_call) {
      const result = await this.skillRegistry.execute(
        response.function_call.name,
        JSON.parse(response.function_call.arguments)
      );

      // Feed result back to LLM for final response
      return await this.llm.chat({
        messages: [
          { role: "user", content: userMessage },
          { role: "assistant", content: null, function_call: response.function_call },
          { role: "function", name: response.function_call.name, content: JSON.stringify(result) }
        ]
      });
    }

    return response;
  }
}
```

### Pattern 3: Multi-Provider Abstraction with Intelligent Routing

**What:** Unified interface across multiple LLM and image generation providers. Routes requests based on cost, latency, and capability requirements. Automatic failover on provider errors.

**When to use:** Production systems requiring high availability, cost optimization, and vendor independence.

**Trade-offs:**
- **Pro:** No vendor lock-in. Swap providers via config change.
- **Pro:** Cost optimization—route simple tasks to cheaper models, complex reasoning to premium models.
- **Pro:** Resilience—automatic failover maintains uptime when providers have outages.
- **Con:** Abstraction layer hides provider-specific features (must use lowest common denominator or extension mechanism).
- **Con:** Added complexity in routing logic and configuration management.

**Example:**
```typescript
// Abstract LLM provider interface
interface ILLMProvider {
  name: string;
  chat(request: ChatRequest): Promise<ChatResponse>;
  supportsStreaming: boolean;
  costPerToken: number;
}

// Provider implementations
class OpenAIProvider implements ILLMProvider {
  name = "openai";
  supportsStreaming = true;
  costPerToken = 0.00002; // GPT-4o pricing

  async chat(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.openai.chat.completions.create({
      model: "gpt-4o",
      messages: request.messages,
      functions: request.functions
    });
    return this.normalize(response);
  }

  private normalize(raw: OpenAI.ChatCompletion): ChatResponse {
    // Transform to unified schema
  }
}

class AnthropicProvider implements ILLMProvider {
  name = "anthropic";
  supportsStreaming = true;
  costPerToken = 0.000015; // Claude 3.5 Sonnet pricing

  async chat(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.anthropic.messages.create({
      model: "claude-3-5-sonnet-20241022",
      messages: request.messages,
      tools: request.functions // Different terminology, same concept
    });
    return this.normalize(response);
  }

  private normalize(raw: Anthropic.Message): ChatResponse {
    // Transform to unified schema
  }
}

// Intelligent router
class LLMRouter {
  private providers: ILLMProvider[];
  private primaryProvider: string;
  private fallbackProviders: string[];

  async chat(request: ChatRequest, options?: { preferCheap?: boolean }): Promise<ChatResponse> {
    // Route simple requests to cheaper models
    if (options?.preferCheap && this.isSimpleRequest(request)) {
      return this.routeToCheapest(request);
    }

    // Try primary provider with exponential backoff
    try {
      const provider = this.getProvider(this.primaryProvider);
      return await this.withRetry(() => provider.chat(request));
    } catch (error) {
      // Failover to backup providers
      return this.failover(request, error);
    }
  }

  private async failover(request: ChatRequest, originalError: Error): Promise<ChatResponse> {
    for (const fallbackName of this.fallbackProviders) {
      try {
        const provider = this.getProvider(fallbackName);
        logger.warn(`Failing over to ${fallbackName} after error: ${originalError.message}`);
        return await provider.chat(request);
      } catch (e) {
        // Continue to next fallback
      }
    }
    throw new Error("All LLM providers failed");
  }

  private isSimpleRequest(request: ChatRequest): boolean {
    // Heuristic: short messages, no function calls, no complex context
    return request.messages.length < 5 && !request.functions;
  }

  private routeToCheapest(request: ChatRequest): Promise<ChatResponse> {
    const cheapest = this.providers.reduce((min, p) =>
      p.costPerToken < min.costPerToken ? p : min
    );
    return cheapest.chat(request);
  }
}
```

### Pattern 4: Event-Driven Webhook Architecture

**What:** Webhook endpoints acknowledge immediately (200 OK), then queue events for asynchronous processing. Prevents platform retries and enables horizontal scaling.

**When to use:** High-throughput messaging integrations where immediate response is required but processing is complex/slow.

**Trade-offs:**
- **Pro:** Horizontal scalability—multiple workers process queue independently.
- **Pro:** Resilience—temporary downstream failures don't lose data (messages stay in queue).
- **Pro:** Platform compliance—immediate acknowledgment prevents retry storms.
- **Con:** Eventually consistent—slight delay between webhook receipt and processing completion.
- **Con:** Requires message queue infrastructure (Redis, RabbitMQ, SQS).

**Example:**
```typescript
// Webhook endpoint (thin, fast, acknowledgment-focused)
app.post('/webhooks/whatsapp', async (req, res) => {
  const event = req.body;

  // Verify webhook signature (platform-specific)
  if (!verifyWhatsAppSignature(req.headers, req.body)) {
    return res.status(401).send('Unauthorized');
  }

  // Idempotency check—prevent duplicate processing
  const eventId = event.entry[0].id;
  if (await redis.exists(`processed:${eventId}`)) {
    logger.info(`Duplicate event ${eventId}, skipping`);
    return res.sendStatus(200); // Already processed
  }

  // Queue for processing (non-blocking)
  await messageQueue.add('whatsapp-message', {
    eventId,
    event,
    receivedAt: Date.now()
  });

  // Immediate acknowledgment to WhatsApp
  res.sendStatus(200);
});

// Asynchronous worker (complex processing)
messageQueue.process('whatsapp-message', async (job) => {
  const { eventId, event } = job.data;

  try {
    // Normalize platform event
    const adapter = adapterRegistry.get('whatsapp');
    const message = adapter.normalize(event);

    // Process through orchestrator
    const response = await orchestrator.processTurn(message);

    // Send response back to user
    await adapter.send(message.conversationId, response);

    // Mark as processed (idempotency)
    await redis.setex(`processed:${eventId}`, 86400, '1'); // 24hr TTL

  } catch (error) {
    logger.error(`Failed to process event ${eventId}:`, error);
    throw error; // Will retry based on queue configuration
  }
});
```

### Pattern 5: Multi-Tiered Memory Architecture

**What:** Separate short-term (conversation buffer), long-term (user history/preferences), and working (inter-agent cache) memory layers. Context manager selectively loads relevant information into LLM context window.

**When to use:** Conversational systems requiring history awareness without exhausting token limits. Systems with personalization needs.

**Trade-offs:**
- **Pro:** Scalable context—store unlimited history, load only what's relevant.
- **Pro:** Cost efficiency—don't pay for tokens on irrelevant old messages.
- **Pro:** Personalization—recall user preferences from months ago.
- **Con:** Complexity in retrieval strategy (what's "relevant"?).
- **Con:** Eventually consistent—long-term memory writes may lag.

**Example:**
```typescript
// Context manager orchestrates memory layers
class ContextManager {
  constructor(
    private shortTerm: ShortTermMemory,  // In-memory/Redis, last ~10 turns
    private longTerm: LongTermMemory,    // Vector DB, entire history
    private working: WorkingMemory       // Redis, inter-skill cache
  ) {}

  async buildContext(userId: string, currentMessage: string): Promise<Message[]> {
    const context: Message[] = [];

    // Always include recent conversation (short-term)
    const recentTurns = await this.shortTerm.getRecent(userId, 10);
    context.push(...recentTurns);

    // Retrieve relevant long-term memories via RAG
    const relevantHistory = await this.longTerm.retrieve(userId, currentMessage, {
      limit: 5,
      similarityThreshold: 0.7
    });

    if (relevantHistory.length > 0) {
      // Insert as system message for context
      context.unshift({
        role: "system",
        content: `Relevant past interactions:\n${relevantHistory.map(m => m.content).join('\n')}`
      });
    }

    // Include user preferences from working memory (fast cache)
    const userPrefs = await this.working.get(`user:${userId}:preferences`);
    if (userPrefs) {
      context.unshift({
        role: "system",
        content: `User preferences: ${JSON.stringify(userPrefs)}`
      });
    }

    return context;
  }

  async storeInteraction(userId: string, messages: Message[]) {
    // Immediate: Add to short-term buffer
    await this.shortTerm.append(userId, messages);

    // Async: Embed and store in long-term vector DB
    await this.longTerm.store(userId, messages);

    // Extract and cache updated preferences
    const extractedPrefs = this.extractPreferences(messages);
    if (extractedPrefs) {
      await this.working.set(`user:${userId}:preferences`, extractedPrefs);
    }
  }
}

// Long-term memory with vector similarity
class LongTermMemory {
  async retrieve(userId: string, query: string, options: RetrievalOptions): Promise<Message[]> {
    // Embed query
    const queryEmbedding = await this.embeddings.embed(query);

    // Vector similarity search
    const results = await this.vectorDB.query({
      vector: queryEmbedding,
      filter: { userId },
      topK: options.limit,
      scoreThreshold: options.similarityThreshold
    });

    return results.map(r => r.metadata.message);
  }

  async store(userId: string, messages: Message[]) {
    for (const message of messages) {
      const embedding = await this.embeddings.embed(message.content);
      await this.vectorDB.upsert({
        id: `${userId}:${message.timestamp}`,
        vector: embedding,
        metadata: { userId, message, timestamp: message.timestamp }
      });
    }
  }
}
```

## Data Flow

### Request Flow (Webhook → Response)

```
[WhatsApp Message]
    ↓
[Webhook Endpoint] → Verify signature, check idempotency
    ↓
[Message Queue] → Acknowledge immediately (200 OK)
    ↓
[Async Worker] → Dequeue for processing
    ↓
[Message Adapter] → Normalize to UnifiedMessage
    ↓
[Conversation Orchestrator] → Load context, determine mode
    ↓
[Agent Router] → Detect intent (secretary vs. intimate)
    ↓
┌───────────────────────────┐
│   Secretary Mode          │   Intimate Mode
│   ↓                       │   ↓
│ [Skill Selection]         │ [Personality Selection]
│   ↓                       │   ↓
│ [Tool Invocation]         │ [Conversation Gen]
│ - Calendar skill          │ - LLM chat (persona-based)
│ - Reminder skill          │ - Image generation (if triggered)
│ - Research skill          │   ↓
│   ↓                       │ [Content Escalation Check]
│ [Function Result]         │   ↓
│   ↓                       │ [Image Provider] (if needed)
└───────────────┬───────────┴───┬──────────
                ↓               ↓
        [LLM Provider] → Generate final response
                ↓
        [Memory System] → Store interaction
                ↓
        [Message Adapter] → Format for platform
                ↓
        [WhatsApp API] → Send response
```

### State Management Flow

```
[Conversation Start]
    ↓
[Short-term Memory] ← Load last 10 turns from Redis
    ↓
[Context Manager] ← Retrieve relevant long-term memories (RAG)
    ↓
[User Preferences] ← Load from working memory cache
    ↓
[LLM Context Window] ← Assemble: system prompt + preferences + history + current
    ↓
[LLM Response]
    ↓
[Memory Storage]
    ├→ [Short-term] ← Append immediately (Redis)
    ├→ [Long-term] ← Embed & store asynchronously (Vector DB)
    └→ [Working] ← Update preferences cache (Redis)
```

### Skill Invocation Flow

```
[User Message: "Schedule meeting tomorrow 2pm"]
    ↓
[Orchestrator] → Pass to LLM with function declarations
    ↓
[LLM] → Decides to call `add_calendar_event` function
    ↓ (function_call response)
[Orchestrator] → Looks up skill in registry
    ↓
[Skill Registry] → Returns CalendarSkill instance
    ↓
[CalendarSkill.execute()] → Calls Google Calendar API
    ↓
[Google Calendar API] → Returns event ID & link
    ↓
[Orchestrator] → Passes result back to LLM as function result
    ↓
[LLM] → Generates user-friendly response: "Done! Meeting scheduled..."
    ↓
[Message Adapter] → Sends response to user
```

### Key Data Flows

1. **Webhook Ingestion (Event-Driven):** Webhook receives event → immediate ack → queue → async worker → processing. This decouples receipt from processing, enabling horizontal scaling and fault tolerance.

2. **Mode Switching:** User message → Agent Router (NLU or LLM-based) → detects switch intent ("I'm alone" → intimate mode) → updates conversation state → routes to appropriate mode handler.

3. **Tool Calling (MCP Pattern):** LLM receives function schemas → decides which to invoke → orchestrator executes skill → result returns to LLM → final response generated.

4. **Image Generation Escalation:** Intimate mode conversation → Context Manager analyzes conversation intensity → determines photo escalation level (mild/moderate/explicit) → passes to Image Provider with appropriate prompt → Avatar-consistent image generated → sent to user.

5. **Multi-Provider Failover:** Request → LLM Router → attempts primary provider → on failure, exponential backoff → failover to backup provider → eventual success or exhaustion → audit log records all attempts.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| **0-1k users** | Monolith is fine. Single Node.js process, Redis for memory, PostgreSQL for users. WhatsApp webhook → in-process orchestrator → response. Focus on feature development, not premature optimization. |
| **1k-10k users** | Add message queue (BullMQ with Redis) to decouple webhook acknowledgment from processing. Horizontal scaling: multiple worker processes behind load balancer. Consider managed vector DB (Pinecone, Qdrant Cloud). Monitor LLM costs—start routing simple queries to cheaper models. |
| **10k-100k users** | Microservices for independent scaling: separate orchestrator, skill workers, image generation workers. Use SQS/RabbitMQ for inter-service messaging. Implement caching layers (Redis for hot data, CDN for generated images). Database sharding or read replicas for user data. Observability critical: distributed tracing (OpenTelemetry), centralized logging, LLM usage dashboards. |
| **100k+ users** | Full microservices architecture with service mesh. Separate LLM gateway (Portkey, LiteLLM) for cost optimization and rate limiting. Multi-region deployment for latency. Event sourcing for conversation history (rebuild state from event log). Consider managed platforms (AWS Bedrock, Azure OpenAI) for enterprise SLAs. Auto-scaling worker pools based on queue depth. |

### Scaling Priorities

1. **First bottleneck (10k users):** **LLM token costs.** As users grow, naive "send everything to GPT-4" becomes prohibitively expensive. **Fix:** Implement intelligent routing—simple queries to cheaper models (GPT-3.5, Claude Haiku), complex reasoning to premium models. Use prompt caching where providers support it (Anthropic, OpenAI). Summarize conversation history to reduce context window size.

2. **Second bottleneck (50k users):** **Webhook processing latency.** Single-threaded webhook handler can't keep up with message volume, leading to timeouts and retries. **Fix:** Event-driven architecture with message queue. Webhook acknowledges immediately, workers process asynchronously. Horizontal scaling of worker pool based on queue depth.

3. **Third bottleneck (100k users):** **Database write contention.** Heavy conversation logging creates write hotspots in PostgreSQL. **Fix:** Event sourcing pattern—append-only event log (DynamoDB, EventStore) for conversation history. Rebuild state from events on demand. Separate read models (CQRS) for analytics and reporting.

4. **Fourth bottleneck (500k users):** **Vector DB query latency.** Long-term memory retrieval becomes slow as embeddings accumulate. **Fix:** User-based sharding in vector DB. Implement hybrid search (vector + metadata filters). Pre-fetch likely needed memories asynchronously. Consider local approximate nearest neighbor (HNSW) for hot users.

## Anti-Patterns

### Anti-Pattern 1: Tight Coupling to LLM Provider

**What people do:** Directly call OpenAI SDK throughout codebase. `await openai.chat.completions.create(...)` in orchestrator, skills, and handlers.

**Why it's wrong:**
- Vendor lock-in—switching providers requires rewriting scattered calls.
- No failover—single provider outage breaks entire system.
- Cost optimization impossible—can't route different requests to different models.
- Testing is hard—must mock OpenAI SDK everywhere.

**Do this instead:** Create an abstraction layer (`ILLMProvider` interface) with provider-specific implementations. Route all LLM calls through a single `LLMRouter` that handles provider selection, failover, and cost optimization. Dependency inject the provider interface for testability.

```typescript
// WRONG: Direct coupling
class Orchestrator {
  async process(message: string) {
    const response = await openai.chat.completions.create({ /* ... */ });
    // Now you're stuck with OpenAI
  }
}

// RIGHT: Abstraction
class Orchestrator {
  constructor(private llm: ILLMProvider) {}

  async process(message: string) {
    const response = await this.llm.chat({ /* ... */ });
    // Can swap provider via DI
  }
}
```

### Anti-Pattern 2: Synchronous Webhook Processing

**What people do:** Webhook endpoint receives event → processes conversation → calls LLM → generates image → stores in DB → sends response → returns 200. All synchronous.

**Why it's wrong:**
- Violates platform timeout requirements (WhatsApp requires <20s, but LLM calls can take 30s+).
- Platform retries on timeout, causing duplicate processing.
- Cannot horizontally scale—webhook handler blocks on slow operations.
- Single slow request (e.g., image generation) blocks all other users.

**Do this instead:** Acknowledge immediately (200 OK), queue for async processing. Webhook handler's only job: validate, deduplicate, enqueue. Workers process the queue independently.

```typescript
// WRONG: Synchronous
app.post('/webhook', async (req, res) => {
  const message = normalize(req.body);
  const response = await orchestrator.process(message); // BLOCKS!
  await send(response);
  res.sendStatus(200); // Too late, platform already timed out
});

// RIGHT: Async
app.post('/webhook', async (req, res) => {
  await queue.add('message', req.body);
  res.sendStatus(200); // Immediate
});

queue.process('message', async (job) => {
  const message = normalize(job.data);
  const response = await orchestrator.process(message);
  await send(response);
});
```

### Anti-Pattern 3: God Object Orchestrator

**What people do:** Single `ConversationOrchestrator` class that handles mode detection, skill selection, LLM calls, memory management, safety checks, billing, and response formatting. 2000+ line class.

**Why it's wrong:**
- Violates Single Responsibility Principle—impossible to reason about.
- Testing nightmare—must mock every dependency.
- Cannot independently scale components (e.g., memory retrieval is slow but mode detection is fast).
- Changes to one concern (e.g., billing logic) risk breaking others.

**Do this instead:** Decompose into focused components. Orchestrator coordinates, but delegates to specialists: `AgentRouter` for mode detection, `ContextManager` for memory, `SkillRegistry` for tool invocation, `SafetyPolicy` for content checks. Each component has a clear interface and responsibility.

```typescript
// WRONG: God object
class ConversationOrchestrator {
  async process(message: string) {
    // Mode detection
    if (message.includes("alone")) this.mode = "intimate";
    // Memory management
    const history = await this.getHistory();
    // Skill selection
    const skill = this.selectSkill(message);
    // LLM call
    const response = await this.llm.chat(...);
    // Safety check
    if (this.containsUnsafeContent(response)) { /* ... */ }
    // Billing
    await this.recordUsage();
    // ... 100 more responsibilities
  }
}

// RIGHT: Composed
class ConversationOrchestrator {
  constructor(
    private router: AgentRouter,
    private contextMgr: ContextManager,
    private skillRegistry: SkillRegistry,
    private safety: SafetyPolicy,
    private llm: ILLMProvider
  ) {}

  async process(message: string) {
    const mode = await this.router.detectMode(message);
    const context = await this.contextMgr.buildContext(message);
    const response = await this.llm.chat(context);

    if (response.function_call) {
      const result = await this.skillRegistry.execute(response.function_call);
      return this.llm.chat([...context, result]);
    }

    await this.safety.check(response);
    return response;
  }
}
```

### Anti-Pattern 4: Missing Idempotency

**What people do:** Process every webhook event as-is, without checking if it was already handled. Platforms retry on network errors or timeouts, causing duplicate messages.

**Why it's wrong:**
- User receives duplicate responses ("Meeting scheduled" sent twice).
- Double-charges for LLM API calls and external actions (calendar event created twice).
- State corruption if operations aren't naturally idempotent.

**Do this instead:** Use event IDs to track processed events. Before processing, check if event was already handled. Store processed IDs in Redis with TTL (24-48 hours is typical).

```typescript
// WRONG: No idempotency
app.post('/webhook', async (req, res) => {
  await queue.add('message', req.body);
  res.sendStatus(200);
});

// RIGHT: Idempotency check
app.post('/webhook', async (req, res) => {
  const eventId = extractEventId(req.body);

  if (await redis.exists(`processed:${eventId}`)) {
    logger.info(`Duplicate event ${eventId}, skipping`);
    return res.sendStatus(200);
  }

  await queue.add('message', { eventId, ...req.body });
  res.sendStatus(200);
});

// In worker
queue.process('message', async (job) => {
  const { eventId } = job.data;

  // ... process ...

  // Mark as processed
  await redis.setex(`processed:${eventId}`, 86400, '1'); // 24hr TTL
});
```

### Anti-Pattern 5: Hardcoded Skill Logic

**What people do:** Mode handlers contain `if (message.includes("calendar"))` checks to manually route to calendar functionality. Adding new skills means modifying orchestrator code.

**Why it's wrong:**
- Not extensible—every new capability requires code changes.
- Cannot leverage LLM's understanding—forced to maintain manual keyword matching.
- Brittle—"add meeting" works but "schedule appointment" doesn't unless explicitly coded.

**Do this instead:** Use tool calling (function calling) pattern. Expose skills as JSON schemas to LLM. Let LLM decide which skill to invoke based on semantic understanding, not keyword matching.

```typescript
// WRONG: Hardcoded
class SecretaryMode {
  async handle(message: string) {
    if (message.includes("calendar") || message.includes("meeting")) {
      return this.calendarSkill.execute(message);
    } else if (message.includes("remind")) {
      return this.reminderSkill.execute(message);
    }
    // ... endless if/else
  }
}

// RIGHT: Tool calling
class SecretaryMode {
  async handle(message: string) {
    const functions = this.skillRegistry.getFunctionDeclarations();

    const response = await this.llm.chat({
      messages: [{ role: "user", content: message }],
      functions // LLM decides which skill to call
    });

    if (response.function_call) {
      return this.skillRegistry.execute(
        response.function_call.name,
        JSON.parse(response.function_call.arguments)
      );
    }
  }
}
```

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **WhatsApp Business API** | Webhook + REST API. Receive events via webhook (POST endpoint), send messages via Cloud API REST calls. | Must verify webhook signatures. Immediate ack required (<20s). Supports media, templates, interactive buttons. Requires Meta Business verification. |
| **Google Calendar API** | OAuth 2.0 + REST API. Users authorize via OAuth flow, server calls API with refresh tokens. | Requires OAuth consent screen setup. Handle token refresh. Consider service account for backend-initiated events (limits apply). |
| **OpenAI API** | REST API with API key. POST to `/v1/chat/completions` for chat, `/v1/images/generations` for DALL-E. | Rate limits by tier. Use streaming for responsive UX. Monitor token usage for cost control. Function calling for tool integration. |
| **Anthropic API** | REST API with API key. POST to `/v1/messages` for chat. | Different message format than OpenAI (system separate from messages). Tool use (not "function calling"). Prompt caching for cost savings. |
| **Stable Diffusion (via Replicate/RunPod)** | REST API or Python SDK. Submit generation job, poll for completion or use webhook callback. | Async by nature—expect 5-30s latency. NSFW filter configurable. Custom model loading for consistent character (LoRA/DreamBooth). |
| **Vector Database (Pinecone/Qdrant/Weaviate)** | REST API or native SDK. Upsert embeddings, query by vector similarity. | Choose based on scale: Pinecone (managed, expensive), Qdrant (self-hosted or cloud, fast), Weaviate (open-source, GraphQL). Filter by metadata (userId) for multi-tenancy. |
| **Redis** | In-process client (ioredis/node-redis). Use for short-term memory, working memory cache, idempotency tracking, message queue (BullMQ). | Choose Redis Stack for vector search if you want single DB. Set appropriate TTLs to prevent memory bloat. Consider persistence (AOF/RDB) for durability. |
| **PostgreSQL** | ORM (Prisma, TypeORM) or query builder (Knex). Store users, avatars, conversation metadata, billing records. | Use row-level security for multi-tenancy. Index userId fields. Consider partitioning by date for conversation history. Connection pooling essential (pg-pool). |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **Webhook Handler ↔ Orchestrator** | Message queue (BullMQ/SQS) | Async, decoupled. Webhook enqueues, orchestrator dequeues. Enables horizontal scaling of workers. Queue provides retry on failure. |
| **Orchestrator ↔ Skills** | Direct function call (in-process) or RPC (if microservices) | For monolith: Direct calls via Skill Registry. For microservices: gRPC or HTTP API. Skills must be stateless for horizontal scaling. |
| **Orchestrator ↔ LLM Provider** | HTTP REST (via abstraction layer) | Always abstract—never call provider SDK directly. Router handles provider selection. Implement circuit breaker for resilience. |
| **Orchestrator ↔ Memory System** | Direct calls (in-process) | Context Manager orchestrates short/long/working memory. Async writes to long-term (vector DB) to not block response. |
| **Image Skill ↔ Image Provider** | HTTP REST (async) | Image generation is slow (5-30s). Use job queue pattern: submit job, poll or webhook callback. Cache generated images in CDN/S3. |
| **Message Adapter ↔ Platform APIs** | Platform-specific SDK or HTTP | Adapter normalizes inbound (platform → unified schema) and denormalizes outbound (unified → platform format). Handles retries with exponential backoff. |
| **All Components ↔ Audit Log** | Event bus or direct write | Use structured logging (Winston, Pino) with JSON output. Centralized logging (CloudWatch, Datadog) for observability. Async writes to not block critical path. |

## Build Order Recommendations

Based on component dependencies, suggested implementation order:

### Phase 1: Foundation (Week 1-2)
1. **Database setup** (PostgreSQL + Redis) — Core data layer must exist first.
2. **User management** — User CRUD, authentication (simple API key or JWT for MVP).
3. **Message adapter base** — Abstract interface + single implementation (WhatsApp).
4. **Basic orchestrator** — Minimal: receive message → echo back (validates webhook flow).

**Why this order:** Establishes data persistence and basic message flow. Validates WhatsApp webhook integration early (can be tricky with signatures/verification).

### Phase 2: Core Intelligence (Week 3-4)
5. **LLM provider abstraction** — Start with single provider (OpenAI or Anthropic), but use interface.
6. **Simple conversation** — Basic chat without tools (validates LLM integration).
7. **Memory system (short-term only)** — Conversation buffer in Redis.
8. **Mode detection** — Agent Router with fuzzy intent matching for secretary ↔ intimate switching.

**Why this order:** Gets conversational AI working end-to-end. Mode switching validates core product differentiator early.

### Phase 3: Skills (Week 5-6)
9. **Skill Registry** — Dynamic skill loading with MCP pattern.
10. **First skill: Reminders** — Simpler than calendar (no OAuth), validates tool calling.
11. **Second skill: Calendar** — OAuth flow + Google Calendar API integration.
12. **Third skill: Research** — Web search or knowledge base lookup.

**Why this order:** Reminders are self-contained (no external auth), so they validate skill pattern without OAuth complexity. Calendar adds OAuth which is reusable for other Google services. Research skill demonstrates extensibility.

### Phase 4: Intimate Mode (Week 7-8)
13. **Personality system** — Preset personas as system prompt templates.
14. **Image provider abstraction** — Interface for image generation backends.
15. **Image generation skill** — Implement with Stable Diffusion or DALL-E.
16. **Content escalation logic** — Conversation analysis → determine photo intensity level.
17. **Avatar consistency** — Prompt templating with user's avatar config (gender, age, appearance).

**Why this order:** Personality comes first (simplest—just prompt engineering). Image generation is complex (async, slow, caching needed), so it's last in intimate mode. Escalation logic depends on conversation history (memory system), so it comes after image provider works.

### Phase 5: Production Hardening (Week 9-10)
18. **Message queue integration** — BullMQ for async webhook processing.
19. **Idempotency** — Prevent duplicate processing.
20. **Long-term memory** — Vector DB for conversation history RAG.
21. **Multi-provider failover** — LLM Router with fallback logic.
22. **Observability** — Structured logging, metrics, tracing.
23. **Billing tracking** — Record LLM/image API usage per user.

**Why this order:** Production concerns come after features work. Message queue enables scaling. Idempotency prevents bugs in production. Long-term memory is optimization (short-term works for MVP). Failover reduces single-point-of-failure risk. Observability is essential before launch. Billing last (must work but not blocking for beta).

### Dependencies Diagram

```
Database ────────┬──→ User Management
                 │
                 ├──→ Message Adapter ──→ Orchestrator (echo) ──→ LLM Provider
                 │                              │
                 │                              ↓
                 │                         Short-term Memory
                 │                              │
                 │                              ↓
                 │                         Mode Detection ──→ Skill Registry
                 │                              │                   │
                 │                              │                   ↓
                 │                              │              Skills (Reminders, Calendar, Research)
                 │                              │
                 │                              ↓
                 │                         Personality System
                 │                              │
                 │                              ↓
                 │                         Image Provider ──→ Image Skill
                 │                              │
                 │                              ↓
                 │                         Content Escalation
                 │
                 └──→ Message Queue ──→ Idempotency ──→ Long-term Memory ──→ Observability
```

**Critical path:** Database → Message Adapter → Orchestrator → LLM Provider → Mode Detection → Skills. Everything else can be added incrementally.

**Parallelizable:** Once orchestrator works, skills can be developed independently (calendar team, reminders team, image team). Message queue and observability can be added in parallel to feature development.

## Sources

### HIGH Confidence (Official Documentation & Recent Articles)

- [Designing a Chatbot System in 2026](https://bhavaniravi.com/blog/GenAI/designing-chatbot-system-in-2026/) - Production architecture patterns, MCP integration, multi-layered memory
- [How to Build a Chatbot: Components & Architecture 2026](https://research.aimultiple.com/chatbot-architecture/) - Component breakdown, NLP/NLU/NLG pipeline, modern patterns
- [Building a Scalable Webhook Architecture for Custom WhatsApp Solutions](https://www.chatarchitect.com/news/building-a-scalable-webhook-architecture-for-custom-whatsapp-solutions) - Event-driven patterns, message queues, idempotency
- [LLM Orchestration in 2026: Top 22 frameworks and gateways](https://research.aimultiple.com/llm-orchestration/) - Multi-provider abstraction, routing strategies, failover
- [Dynamic Skillset Reference Architecture | ChatBotKit](https://chatbotkit.com/examples/dynamic-skillset-reference-architecture) - Runtime skill discovery and loading patterns

### MEDIUM Confidence (Industry Sources, Multiple Corroborating Articles)

- [The Best Chatbot Builders in 2026](https://www.flowhunt.io/blog/best-chatbot-builders-2026/) - Modern platform capabilities, plugin architectures
- [Why modular architecture is best for AI chatbot development](https://telnyx.com/resources/architecture-chatbot-development) - Modularity benefits, component isolation
- [Multi-Agent Multi-LLM Systems Guide 2026](https://dasroot.net/posts/2026/02/multi-agent-multi-llm-systems-future-ai-architecture-guide-2026/) - Agent coordination patterns
- [Context Window Management for AI Agents](https://www.getmaxim.ai/articles/context-window-management-strategies-for-long-context-ai-agents-and-chatbots/) - Memory architecture strategies
- [Microservices Architecture for AI Applications](https://medium.com/@meeran03/microservices-architecture-for-ai-applications-scalable-patterns-and-2025-trends-5ac273eac232) - Microservices patterns for AI
- [Event-Driven Architecture Patterns](https://solace.com/event-driven-architecture-patterns/) - Message queue patterns, pub/sub vs. queues
- [Ultimate TypeScript Project Structure 2026](https://medium.com/@mernstackdevbykevin/an-ultimate-typescript-project-structure-2026-edition-4a2d02faf2e0) - Feature-first architecture, modern Node.js structure

### Framework-Specific Documentation

- [Orchestral AI Framework](https://arxiv.org/abs/2601.02577) - Unified LLM provider interface research
- [WhatsApp Cloud API Integration 2026](https://medium.com/@aktyagihp/whatsapp-cloud-api-integration-in-2026-0493dd05d644) - WhatsApp-specific patterns
- [AI SDK UI: Chatbot Message Persistence](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-message-persistence) - State management patterns

---
*Architecture research for: Dual-mode AI companion chatbot (Ava)*
*Researched: 2026-02-23*
*Confidence: HIGH for core patterns, MEDIUM for specific framework choices*
