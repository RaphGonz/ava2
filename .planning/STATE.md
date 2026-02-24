# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-23)

**Core value:** A single AI companion that seamlessly switches between getting things done (secretary) and personal connection (intimate partner), all inside the messaging app the user already uses.
**Current focus:** Phase 5 - Intimate Mode Text Foundation

## Current Position

Phase: 5 of 7 (Intimate Mode Text Foundation)
Plan: 3 of 4 in current phase
Status: In Progress
Last activity: 2026-02-24 — Completed 05-03 (PersonaUpdateRequest model, PATCH /avatars/me/persona endpoint, SessionStore.clear_avatar_cache() for immediate persona invalidation)

Progress: [████████░░] 80%

## Performance Metrics

**Velocity:**
- Total plans completed: 11
- Average duration: 12 min
- Total execution time: 2.3 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation-compliance P01 | 11 min | 2 tasks | 4 files |
| 01-foundation-compliance P02 | 15 min | 2 tasks | 6 files |
| 02-infrastructure-user-management P01 | 19 min | 2 tasks | 23 files |
| 02-infrastructure-user-management P02 | 15 min | 2 tasks | 6 files |
| 02-infrastructure-user-management P03 | 15 min | 2 tasks | 5 files |
| 02-infrastructure-user-management P04 | 15 min | 2 tasks | 6 files |
| 02-infrastructure-user-management P05 | 15 min | 2 tasks | 0 files |
| 03-core-intelligence-mode-switching P01 | 9 min | 2 tasks | 6 files |
| 03-core-intelligence-mode-switching P02 | 8 min | 2 tasks | 9 files |
| 03-core-intelligence-mode-switching P03 | 12 min | 2 tasks | 3 files |
| 03-core-intelligence-mode-switching P04 | 5 min | 2 tasks | 0 files |
| 04-secretary-skills P01 | 10 min | 2 tasks | 5 files |

**Recent Trend:**
- Last 5 plans: 9 min, 8 min, 12 min, 5 min, 10 min
- Trend: Stable

*Updated after each plan completion*
| Phase 04-secretary-skills P02 | 14 | 2 tasks | 6 files |
| Phase 04-secretary-skills P04 | 6 | 1 tasks | 1 files |
| Phase 04-secretary-skills P03 | 8 | 2 tasks | 2 files |
| Phase 04-secretary-skills P05 | 13 | 2 tasks | 3 files |
| Phase 05-01 P01 | 12 | 3 tasks | 5 files |
| Phase 05-intimate-mode-text-foundation P03 | 12 | 2 tasks | 3 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- All decisions currently pending validation during implementation
- [Phase 03-core-intelligence-mode-switching]: LLMProvider uses Python Protocol (structural typing) not ABC — any class with async complete() satisfies it without inheritance
- [Phase 03-core-intelligence-mode-switching]: AsyncOpenAI with max_retries=1 delegates retry logic to SDK; except block returns user-friendly fallback message
- [Phase 03-core-intelligence-mode-switching]: System prompt templates are pure functions accepting avatar_name and personality at runtime — no hardcoded strings
- [Phase 03-core-intelligence-mode-switching]: openai_api_key defaults to empty string in Settings — missing key returns fallback message, not 500 error at startup
- [Phase 01-foundation-compliance]: Provider pattern for age verification: all checks go through AgeVerificationManager.verifyAge(), swapping from self-declaration to ID verification is a config change not code rewrite
- [Phase 01-foundation-compliance]: WhatsApp NSFW images delivered via JWT-signed web portal links (not WhatsApp attachments) to comply with WhatsApp Business API policy
- [Phase 01-foundation-compliance]: Avatar age floor is 20+ (not 18+), enforced at DB level with CHECK constraint and form validation
- [Phase 02-infrastructure-user-management]: Used postgrest.auth(token) per-query pattern instead of set_auth() on singleton to avoid JWT context bleed between concurrent async requests
- [Phase 02-infrastructure-user-management]: supabase_admin (service role) reserved exclusively for server-to-server ops (webhook phone lookup); all user-facing ops use supabase_client (anon + user JWT)
- [Phase 02-infrastructure-user-management]: dev.py router guards /dev/* routes with app_env check — 404 in production, live in development
- [Phase 02-infrastructure-user-management]: pathlib.Path(__file__) used for template lookup in dev.py — portable across working directories
- [Phase 02-infrastructure-user-management]: pydantic[email] added explicitly to requirements.txt — EmailStr requires the email-validator extra
- [Phase 02-infrastructure-user-management]: Pydantic Field(ge=20) used on AvatarCreate.age (not field_validator) — produces correct GreaterThanEqual metadata and JSON Schema
- [Phase 02-infrastructure-user-management]: PUT /preferences/whatsapp accepts PhoneLinkRequest body (not query param) — enables Pydantic E.164 validation before handler runs
- [Phase 02-infrastructure-user-management]: GET /preferences/ returns 404 when no row exists (not empty object) — distinguishes never-configured from configured-with-no-phone
- [Phase 02-infrastructure-user-management]: Message logging wrapped in nested try/except — DB failure does not prevent echo from sending
- [Phase 02-infrastructure-user-management]: GRAPH_API_VERSION constant pins Meta API to v19.0 — version bumps are a one-line change
- [Phase 02-infrastructure-user-management]: GET /messages uses get_authed_supabase (RLS) not supabase_admin — user isolation enforced at DB level
- [Phase 02-infrastructure-user-management]: WhatsApp echo test deferred — credentials not configured; Tests 1-3 and 5 sufficient per plan to declare Phase 2 complete
- [Phase 02-infrastructure-user-management]: RLS isolation (USER-02) confirmed via two real Supabase accounts: User B GET /avatars/me returned 404, User A avatar never exposed
- [Phase 03-core-intelligence-mode-switching]: MAX_WORDS_FOR_FUZZY=10 guard prevents long sentences from triggering mode switch — only slash commands match for inputs over 10 words
- [Phase 03-core-intelligence-mode-switching]: Session history stored as two separate lists per ConversationMode in SessionState.history dict — never merged — prevents cross-mode prompt injection
- [Phase 03-core-intelligence-mode-switching]: asyncio.Lock on all SessionStore mutations ensures safety under concurrent Meta webhook deliveries to same user
- [Phase 03-core-intelligence-mode-switching]: ChatService is a stateless orchestrator — all mutable state lives in SessionStore; designed as module-level singleton in webhook.py
- [Phase 03-core-intelligence-mode-switching]: Avatar fetched in webhook.py and passed into handle_message() — keeps ChatService testable without DB dependency
- [Phase 03-core-intelligence-mode-switching]: send_whatsapp_message() called before Supabase logging — DB failure cannot block reply delivery
- [Phase 03-core-intelligence-mode-switching]: avatar_id now populated from avatar["id"] in message logging (was hardcoded None in Phase 2 echo)
- [Phase 03-core-intelligence-mode-switching]: Phase 3 declared complete after human approval — Option B verification (unit tests + grep) accepted without live OPENAI_API_KEY; live LLM testing deferred pending credential configuration
- [Phase 04-secretary-skills]: Skill registry uses module-level dict (not class-based) — consistent with Python module singleton pattern, simpler than dependency injection
- [Phase 04-secretary-skills]: classify_intent() accepts AsyncOpenAI client and model as arguments (not imported from config) — keeps classifier testable without config coupling
- [Phase 04-secretary-skills]: All new config fields default to empty string — missing credentials return graceful error messages, not startup crashes (same pattern as openai_api_key)
- [Phase 04-secretary-skills]: IntentResult (Pydantic BaseModel for LLM response) is separate from ParsedIntent (dataclass for domain routing) — clean separation between LLM schema and application domain object
- [Phase 04-secretary-skills]: Flow.from_client_config() used for web server OAuth2 — not InstalledAppFlow
- [Phase 04-secretary-skills]: asyncio.to_thread() wraps synchronous Google Auth calls to avoid blocking FastAPI event loop
- [Phase 04-secretary-skills]: supabase_admin used for google_calendar_tokens storage — webhook/skill pipeline runs without user JWT
- [Phase 04-secretary-skills]: calendar.events scope only (least privilege) — avoids full calendar management access
- [Phase 04-secretary-skills]: Tavily include_answer='advanced' provides pre-formatted AI answer — no separate LLM summarization call needed
- [Phase 04-secretary-skills]: asyncio.to_thread wrapping pattern established for all synchronous SDK calls inside async FastAPI handlers
- [Phase 04-secretary-skills]: pending_calendar_add typed as Any | None in store.py to avoid circular import between store and calendar_skill
- [Phase 04-secretary-skills]: CONFLICT_CONFIRM_KEYWORDS not in calendar_skill.py — lives in chat.py (Plan 05) so confirmation check runs before intent classification
- [Phase 04-secretary-skills]: CalendarSkill.handle() accepts optional session kwarg to store PendingCalendarAdd on conflict detection while keeping Skill Protocol stable
- [Phase 04-secretary-skills]: pending_calendar_add gate runs BEFORE mode switch detection to catch yes/oui as conflict confirmation instead of chat intent
- [Phase 04-secretary-skills]: ConversationMode.SECRETARY guard mandatory before classify_intent — intimate mode must never call intent classifier
- [Phase 04-secretary-skills]: Skill dispatch errors fall through to LLM silently via try/except — chat service never breaks on skill failure
- [Phase 05-intimate-mode-text-foundation]: intimate_prompt() dispatch uses dict.get(personality, _intimate_caring) — unknown personas fall back to caring, never raise
- [Phase 05-intimate-mode-text-foundation]: ContentGuard dual-pass normalization: space-replace + collapse-remove catches ch\!ld obfuscation that space-replace alone misses
- [Phase 05-intimate-mode-text-foundation]: 'want to die' placed in Layer 2 context-boost (not Layer 1 immediate) — prevents false positive on 'want to die laughing'
- [Phase 05-intimate-mode-text-foundation]: body.personality.value (string) written to supabase DB instead of enum member to avoid serialization inconsistency
- [Phase 05-intimate-mode-text-foundation]: object.__setattr__ used in clear_avatar_cache to reset dynamically-attached _avatar_cache attribute on SessionState dataclass
- [Phase 05-intimate-mode-text-foundation]: clear_avatar_cache is no-op for non-existent sessions — persona change before first message handled naturally by DB fetch on first message

### Pending Todos

- Register webhook URL in Meta Developer Console after starting ngrok
- Submit WhatsApp Business Account verification (takes 2-15 business days)
- Add WhatsApp credentials to backend/.env when they arrive

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-02-24
Stopped at: Completed 05-03-PLAN.md — PersonaUpdateRequest Pydantic model, PATCH /avatars/me/persona endpoint with 404/422 handling and DB write using .value, SessionStore.clear_avatar_cache() with object.__setattr__ and asyncio.Lock, PERS-01 satisfied
Resume file: None
