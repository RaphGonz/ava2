# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-23)

**Core value:** A single AI companion that seamlessly switches between getting things done (secretary) and personal connection (intimate partner), all inside the messaging app the user already uses.
**Current focus:** Phase 4 - Secretary Skills

## Current Position

Phase: 4 of 7 (Secretary Skills)
Plan: 1 of 5 in current phase
Status: In progress
Last activity: 2026-02-24 — Completed 04-01 (Skill registry foundation: Skill Protocol + ParsedIntent + registry dict + OpenAI structured-output intent classifier + config fields for Google/Tavily + new packages installed)

Progress: [███████░░░] 72%

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

### Pending Todos

- Register webhook URL in Meta Developer Console after starting ngrok
- Submit WhatsApp Business Account verification (takes 2-15 business days)
- Add WhatsApp credentials to backend/.env when they arrive

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-02-24
Stopped at: Completed 04-01-PLAN.md — Skill registry foundation complete (Skill Protocol + ParsedIntent + classify_intent() + config fields + new packages)
Resume file: None
