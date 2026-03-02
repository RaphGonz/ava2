# Phase 4: Secretary Skills - Research

**Researched:** 2026-02-24
**Domain:** Google Calendar API, Web Search/Research API, LLM Intent Classification, Skill Registry Pattern
**Confidence:** MEDIUM-HIGH (Google Calendar API well-documented; skill registry pattern is Claude's discretion; Tavily API verified via PyPI)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Confirmation & Response Style**
- After adding a meeting: structured summary format — "Added: [Title] · [Day] · [Time]"
- Schedule display: one event per line with bullet points — "• Tue 3pm — Team standup"
- Tone: efficient assistant — crisp, no filler words, no emojis, gets to the point
- Reminders: single daily digest (e.g., morning summary of the day's events) OR a session-start reminder — NOT per-meeting pings throughout the day; frequency should respect user preference (some users are busy and don't need reminders, others have sparse schedules and do)

**Research Response Format**
- Length: one sharp paragraph, 3–5 sentences max — covers the core answer concisely
- Sources: one source link appended at the end ("Source: [url]")
- Broad/ambiguous questions: ask one clarifying question before answering ("That's a big topic — are you thinking about X, Y, or Z?")
- Follow-up offers: none — give the answer and stop; user asks if they want more

**Conflict & Error Handling**
- Calendar conflict: warn and ask — "You already have [X] at that time. Add anyway?" — user confirms before overwriting
- Calendar API / auth error: plain error message — "Couldn't connect to Google Calendar. Check your account settings." — no retries, no technical details
- Research with no solid results: best-effort answer with caveat — "I'm not fully certain, but..." — never hard-refuse if something useful can be said
- Ambiguous intent (can't tell if user wants calendar, research, or general chat): ask one disambiguation question — "Did you want me to add that to your calendar, or look it up?"

**Natural Language Parsing**
- Date/time parsing: very flexible — "mardi à 3h", "next Tuesday at 3", "tomorrow morning", "in 2 hours" all work; bot infers as much as it can from context
- Missing required field (e.g., meeting with no time): ask for the single missing piece — "When should I schedule that?" — one follow-up per gap, not a form
- Intent detection: LLM intent classification — AI call classifies each message as calendar, research, or general chat before routing; handles nuanced and indirect phrasing better than keyword matching
- Time zone: single configured timezone per user stored in their profile; all calendar operations use it — no per-message timezone handling

### Claude's Discretion
- Exact wording of error messages (keep them practical and non-technical)
- Skill registry architecture / plugin pattern for adding new skills
- How to handle edge cases in date parsing (e.g., "next month" with no day)
- Reminder storage format and delivery scheduling mechanics

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SECR-01 | User can add a meeting to their Google Calendar via chat | Google Calendar API events.insert(), dateparser for NL date parsing, intent classification to detect "add meeting" requests |
| SECR-02 | User can view their upcoming schedule from Google Calendar via chat | Google Calendar API events.list() with timeMin/timeMax, formatting as bullet list |
| SECR-03 | User can ask the bot to research a topic and receive a concise answer | Tavily API with include_answer="advanced", LLM-post-processed to 3–5 sentence paragraph with source link |
| ARCH-01 | Modular skill system — new capabilities can be added as plugins | Skill registry using Python Protocol + dict-based registry; each skill is a module with a handle() async function; router selects skill by intent |
</phase_requirements>

---

## Summary

Phase 4 adds three concrete capabilities to the existing ChatService pipeline: Google Calendar management (add/view events), web research, and the modular skill registry that makes both extensible. The existing `ChatService.handle_message()` flow currently routes all non-mode-switch messages directly to the LLM. This phase intercepts that path in secretary mode to run LLM-based intent classification first, then dispatch to the appropriate skill.

The critical design challenge is the two-step OAuth flow required by Google Calendar API. Each user must independently authorize the bot to access their Google Calendar — this means a database table to store per-user OAuth tokens (access_token, refresh_token, token_expiry) and a FastAPI callback route to complete the OAuth handshake. The user experience requires a setup step ("Connect your Google Calendar") before SECR-01 and SECR-02 can work.

For research (SECR-03), Tavily API (version 0.7.21, released 2026-01-30) is the standard LLM-optimized search tool. It returns an AI-generated `answer` field plus source URLs, which maps perfectly to the required response format. The skill registry (ARCH-01) should be a simple Python Protocol + dictionary registry — no need for dynamic importlib loading at this scale; the registry maps intent strings to skill handler functions and is extensible by adding new entries.

**Primary recommendation:** Use `google-api-python-client` + `google-auth-oauthlib` for Calendar (HIGH confidence), `tavily-python` for research (HIGH confidence, verified on PyPI 0.7.21), `dateparser` for multilingual date parsing (HIGH confidence), and OpenAI structured outputs (Pydantic `response_format`) for intent classification (HIGH confidence).

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| google-api-python-client | >=2.0.0 | Google Calendar API client | Official Google library; used in all official docs |
| google-auth-oauthlib | >=1.0.0 | OAuth2 flow for user consent + token refresh | Official Google auth library for web apps |
| google-auth-httplib2 | >=0.2.0 | HTTP transport for google-auth | Required by google-api-python-client |
| tavily-python | 0.7.21 | LLM-optimized web search with AI-generated answers | Best-in-class for AI assistants; include_answer eliminates extra LLM call |
| dateparser | 1.3.0 | Multilingual NL date/time parsing (FR + EN) | 200+ languages; handles relative dates, French natively |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| openai (already installed) | >=1.0.0 | Intent classification via structured outputs | Intent classifier uses AsyncOpenAI with Pydantic response_format |
| pytz or zoneinfo (stdlib 3.9+) | stdlib | Timezone-aware datetime construction | Converting user's stored timezone into aware datetimes for Calendar API |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| tavily-python | SerpAPI | SerpAPI is faster (0.072s vs 2.3s) but returns raw SERP data — needs extra LLM call to summarize; Tavily's include_answer eliminates that step |
| tavily-python | Exa | Exa is semantic/neural search; good for research but less known; Tavily has better LLM-answer integration |
| dateparser | LLM-only parsing | LLM parsing is flexible but non-deterministic — dateparser gives a Python datetime object reliably; use both: LLM extracts the date string, dateparser converts it |
| google-api-python-client | gcsa (Google Calendar Simple API) | gcsa is a higher-level wrapper but adds a dependency; google-api-python-client is the official library with all features |

**Installation (add to requirements.txt):**
```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2 tavily-python dateparser
```

---

## Architecture Patterns

### Recommended Project Structure
```
backend/app/services/
├── chat.py                    # MODIFIED: add skill dispatch before LLM fallback
├── skills/
│   ├── __init__.py
│   ├── registry.py            # Skill registry: intent -> handler mapping
│   ├── intent_classifier.py   # LLM-based intent classification (structured output)
│   ├── calendar_skill.py      # SECR-01, SECR-02: Google Calendar operations
│   └── research_skill.py      # SECR-03: Tavily search + format response
├── google_auth/
│   ├── __init__.py
│   ├── flow.py                # OAuth2 flow initiation and callback handling
│   └── token_store.py         # Per-user token CRUD in Supabase
└── (existing: llm/, session/, mode_detection/, whatsapp.py, user_lookup.py)

backend/app/routers/
└── google_oauth.py            # NEW: /auth/google/connect and /auth/google/callback routes
```

### Pattern 1: Skill Registry (Protocol + Dict)
**What:** A dictionary mapping intent strings to async handler functions. Each skill is a module with a standardized async `handle(user_id, parsed_intent, user_tz) -> str` signature. The registry is a plain dict; adding a new skill is one line.

**When to use:** When new capabilities (Spotify, OCR, reminders) need to slot in without modifying routing logic.

**Example:**
```python
# Source: Claude's discretion — fits existing Protocol-based architecture (see llm/base.py)
from typing import Protocol, runtime_checkable
from dataclasses import dataclass

@dataclass
class ParsedIntent:
    skill: str          # "calendar_add" | "calendar_view" | "research" | "chat"
    raw_text: str       # original user message
    extracted_date: str | None  # for calendar intents
    extracted_title: str | None # for calendar intents
    query: str | None           # for research intents

@runtime_checkable
class Skill(Protocol):
    async def handle(self, user_id: str, intent: ParsedIntent, user_tz: str) -> str:
        ...

# registry.py
_REGISTRY: dict[str, Skill] = {}

def register(skill_name: str, skill: Skill) -> None:
    _REGISTRY[skill_name] = skill

def get(skill_name: str) -> Skill | None:
    return _REGISTRY.get(skill_name)
```

### Pattern 2: LLM Intent Classification (Structured Output)
**What:** A single fast LLM call before routing classifies the user's message into one of: `calendar_add`, `calendar_view`, `research`, `chat`. Uses OpenAI structured outputs with Pydantic model to guarantee a valid enum value — no JSON parsing errors.

**When to use:** Secretary mode only — intimate mode bypasses intent classification and goes straight to LLM.

**Example:**
```python
# Source: OpenAI Structured Outputs docs — https://platform.openai.com/docs/guides/structured-outputs
from pydantic import BaseModel
from typing import Literal
from openai import AsyncOpenAI

class IntentResult(BaseModel):
    intent: Literal["calendar_add", "calendar_view", "research", "chat"]
    extracted_date: str | None = None    # e.g. "mardi à 15h", "next Tuesday at 3pm"
    extracted_title: str | None = None  # e.g. "Team standup", "dentist"
    query: str | None = None            # for research intents

async def classify_intent(client: AsyncOpenAI, text: str, model: str) -> IntentResult:
    response = await client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": INTENT_CLASSIFIER_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format=IntentResult,
    )
    return response.choices[0].message.parsed
```

### Pattern 3: Google Calendar OAuth2 Per-User Token Storage
**What:** Each user goes through a one-time OAuth consent flow. The resulting tokens (access_token, refresh_token, token_expiry, scopes) are stored in a Supabase table (`google_calendar_tokens`). On each Calendar API call, tokens are loaded, refreshed if expired, and re-saved.

**When to use:** Any SECR-01 or SECR-02 operation.

**Example:**
```python
# Source: Official google-auth docs — https://google-auth.readthedocs.io/en/latest/
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Reconstructing credentials from stored tokens
creds = Credentials(
    token=stored_tokens["access_token"],
    refresh_token=stored_tokens["refresh_token"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    scopes=["https://www.googleapis.com/auth/calendar.events"],
)

if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    # Re-save updated tokens to Supabase

service = build("calendar", "v3", credentials=creds)
```

### Pattern 4: Bilingual Date Parsing (dateparser + LLM extraction)
**What:** The LLM intent classifier extracts the raw date string from the user message (e.g., "mardi à 15h", "next Tuesday at 3"). Then `dateparser.parse()` converts it to a Python datetime, applying the user's stored timezone and PREFER_DATES_FROM='future' so "Tuesday" means next Tuesday, not last Tuesday.

**Example:**
```python
# Source: dateparser docs — https://dateparser.readthedocs.io/en/latest/
import dateparser

def parse_user_date(date_string: str, user_tz: str) -> datetime | None:
    return dateparser.parse(
        date_string,
        languages=["fr", "en"],
        settings={
            "TIMEZONE": user_tz,           # e.g. "Europe/Paris"
            "RETURN_AS_TIMEZONE_AWARE": True,
            "PREFER_DATES_FROM": "future",  # "next Tuesday" = upcoming Tuesday
            "PREFER_DAY_OF_MONTH": "first", # "next month" = 1st of next month
        },
    )
```

### Anti-Patterns to Avoid
- **Blocking Google API calls:** `googleapiclient.discovery.build()` and `creds.refresh()` are synchronous — wrap them in `asyncio.get_event_loop().run_in_executor(None, ...)` or use a thread pool to avoid blocking FastAPI's event loop
- **Storing tokens in session memory:** Session is in-memory and per-process — tokens MUST go to Supabase so they survive restarts
- **Using `calendar` scope instead of `calendar.events`:** The `calendar` scope grants full calendar management (delete calendars, change sharing). Use `calendar.events` for events-only access — principle of least privilege
- **Hardcoded timezone assumptions:** Always read timezone from user's preferences table row; default to UTC if missing
- **Inline intent classification prompt:** Keep INTENT_CLASSIFIER_PROMPT as a module constant in intent_classifier.py — easy to tune without touching logic
- **Calling intent classifier in intimate mode:** Skill dispatch only applies in SECRETARY mode — ChatService must check `current_mode` before calling intent classifier

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Multilingual date parsing | Custom regex for French/English dates | dateparser 1.3.0 | 200+ locale support; handles relative dates, timezones, PREFER_DATES_FROM; regex fails on "dans 2 heures", "the day after tomorrow" |
| Web research with source | Custom scraper + summarizer LLM | tavily-python 0.7.21 | include_answer="advanced" returns AI-generated answer + URLs ready to use; building a scraper + summarizer is weeks of work for worse results |
| Google OAuth token refresh | Custom refresh logic | google-auth Credentials.refresh() | Edge cases: token revocation, concurrent refresh, 50-token limit per user/client — the SDK handles all of this |
| Intent JSON parsing | String matching / regex on user message | OpenAI structured outputs (Pydantic) | Structured outputs guarantee valid enum values; no try/except JSON parsing; handles nuanced indirect phrasing ("can you block my Tuesday afternoon?") |
| Google API async wrapping | asyncio.to_thread per call | wrap entire calendar service in a helper | run_in_executor ensures one wrapper pattern; individual call wrapping creates boilerplate |

**Key insight:** The Google Calendar SDK and google-auth library handle the hardest parts (token refresh, concurrent safety, HTTP transport). Don't replicate this logic — the 50 refresh-token-per-user limit and token revocation scenarios are traps for hand-rolled solutions.

---

## Common Pitfalls

### Pitfall 1: Blocking Event Loop with Synchronous Google API
**What goes wrong:** `service.events().insert(...).execute()` is synchronous — calling it directly in an async FastAPI handler blocks the event loop, stalling all concurrent requests.
**Why it happens:** `google-api-python-client` uses synchronous HTTP (`httplib2`) internally; it is not async-native.
**How to avoid:** Wrap all Google API calls with `asyncio.get_event_loop().run_in_executor(None, sync_fn)` or use `asyncio.to_thread(sync_fn)` (Python 3.9+). Create a thin async wrapper module.
**Warning signs:** Requests pile up, webhook processing slows, uvicorn logs show long response times.

### Pitfall 2: OAuth Consent Screen Not in Production Mode
**What goes wrong:** Google limits OAuth apps in "testing" mode to 100 users. Users not on the allowlist get a "This app isn't verified" error and cannot authorize.
**Why it happens:** New Google Cloud projects default to testing mode; production requires submitting for OAuth verification if using sensitive scopes.
**How to avoid:** For initial development, add test users explicitly in Google Cloud Console. Plan for OAuth verification if the app goes public. Consider using `calendar.events` scope (less sensitive, easier approval) vs `calendar` (full access, requires verification).
**Warning signs:** User reports "Google hasn't verified this app" during OAuth consent.

### Pitfall 3: Tavily API Rate Limits and Key Management
**What goes wrong:** Tavily free tier has 1,000 monthly API credits. A search with include_answer="advanced" costs more credits than basic. Production usage with multiple users exhausts the free tier quickly.
**Why it happens:** Each `TavilyClient.search()` call consumes credits based on search_depth and include_answer level.
**How to avoid:** Store `TAVILY_API_KEY` in settings (like `openai_api_key`). Handle `TavilyClient` exceptions gracefully — return a "couldn't research that right now" message on failure. Consider search_depth="basic" for most queries.
**Warning signs:** Tavily returns 429 or auth errors; research skill silently fails.

### Pitfall 4: dateparser Returns None for Ambiguous Dates
**What goes wrong:** `dateparser.parse("next month")` with `PREFER_DAY_OF_MONTH="first"` returns the 1st of next month, but `dateparser.parse("mardi")` with no year context may return None if dateparser cannot resolve relative reference without PREFER_DATES_FROM.
**Why it happens:** dateparser requires disambiguation settings for future-biased relative dates; without them it may return past dates or None.
**How to avoid:** Always pass `PREFER_DATES_FROM="future"` in settings. When dateparser returns None, ask the user: "When exactly should I schedule that?" — treat None as a missing required field.
**Warning signs:** Calendar events created in the past; events.insert() returns 400 for past datetimes.

### Pitfall 5: Google Calendar Token Revocation
**What goes wrong:** User revokes the app's access in their Google account settings. Subsequent API calls get 401 responses with "Token has been expired or revoked."
**Why it happens:** Google OAuth tokens can be revoked by the user at any time from their account settings.
**How to avoid:** Catch `google.auth.exceptions.RefreshError` — clear the stored tokens from Supabase and return the "Check your account settings" error message. Provide a re-connect flow.
**Warning signs:** Calendar operations return 401 despite seemingly valid stored tokens.

### Pitfall 6: Intent Classifier Fires in Intimate Mode
**What goes wrong:** A user in intimate mode says "let's add something to the agenda" — intent classifier routes it to calendar skill, breaking the intimate experience.
**Why it happens:** Intent classification runs before mode check if not guarded correctly.
**How to avoid:** In `ChatService.handle_message()`, only invoke intent classifier when `current_mode == ConversationMode.SECRETARY`. Intimate mode always goes straight to LLM.
**Warning signs:** User reports calendar-related responses during intimate conversations.

---

## Code Examples

Verified patterns from official sources:

### Listing Upcoming Events (Google Calendar API)
```python
# Source: https://developers.google.com/workspace/calendar/api/quickstart/python
import datetime
from googleapiclient.discovery import build

def list_upcoming_events(service, max_results: int = 10) -> list[dict]:
    now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return result.get("items", [])
```

### Creating an Event (Google Calendar API)
```python
# Source: https://developers.google.com/workspace/calendar/api/guides/create-events
def create_calendar_event(service, title: str, start_dt, end_dt, user_tz: str) -> dict:
    event = {
        "summary": title,
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": user_tz,
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": user_tz,
        },
    }
    return service.events().insert(calendarId="primary", body=event).execute()
```

### Research Skill via Tavily
```python
# Source: https://pypi.org/project/tavily-python/ (verified version 0.7.21)
from tavily import TavilyClient

async def research_topic(query: str, tavily_api_key: str) -> tuple[str, str]:
    """Returns (answer_text, source_url)."""
    client = TavilyClient(api_key=tavily_api_key)
    # run_in_executor since TavilyClient.search() is synchronous
    import asyncio
    response = await asyncio.to_thread(
        client.search,
        query,
        include_answer="advanced",
        max_results=3,
        search_depth="basic",
    )
    answer = response.get("answer", "I couldn't find a solid answer on that.")
    # First result URL as the source citation
    results = response.get("results", [])
    source_url = results[0]["url"] if results else ""
    return answer, source_url
```

### Supabase Migration — google_calendar_tokens table
```sql
-- Source: project pattern (see backend/migrations/001_initial_schema.sql style)
CREATE TABLE google_calendar_tokens (
    user_id     UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    access_token  TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    token_expiry  TIMESTAMPTZ,
    scopes        TEXT[],
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: users can only read/write their own token row
ALTER TABLE google_calendar_tokens ENABLE ROW LEVEL SECURITY;
CREATE POLICY "user owns token" ON google_calendar_tokens
    FOR ALL USING (auth.uid() = user_id);
```

### Intent Classifier Prompt (SECR approach)
```python
# Source: Claude's discretion — follows existing prompt pattern in prompts.py
INTENT_CLASSIFIER_PROMPT = """You are an intent classifier for a personal assistant bot.
Classify the user's message into exactly one of these intents:
- "calendar_add": user wants to add, schedule, or book a meeting/event/appointment
- "calendar_view": user wants to see their schedule, upcoming events, calendar, agenda
- "research": user wants to look up information, get a factual answer, learn about a topic
- "chat": general conversation, questions about you, everything else

For calendar_add: also extract the event title and the date/time string as stated by the user.
For research: also extract the core query to search for.
Be bilingual — handle English and French naturally.
Examples:
- "Add dentist appointment Tuesday at 2pm" → calendar_add, title="dentist appointment", date="Tuesday at 2pm"
- "Ajoute une réunion d'équipe mardi à 15h" → calendar_add, title="réunion d'équipe", date="mardi à 15h"
- "What's on my calendar?" → calendar_view
- "Qu'est-ce que la mécanique quantique?" → research, query="mécanique quantique"
- "How are you?" → chat"""
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Keyword matching for intent (e.g., "add" → calendar) | LLM structured output classification | 2023 (function calling) → 2024 (structured outputs) | Handles indirect phrasing: "block my afternoon" → calendar_add |
| InstalledAppFlow (desktop OAuth) | Web server OAuth2 flow with callback route | Standard for server apps | Users authenticate via browser link, tokens stored server-side |
| SerpAPI for web research | Tavily with include_answer | 2023-2024 | Eliminates separate summarization LLM call; answer pre-formatted for chat |
| Custom date parser / regex | dateparser library | Established | 200+ languages, relative dates, timezone-aware out of the box |
| google-auth json file storage | Database token storage (Supabase) | Required for multi-user server apps | Supports unlimited users, survives server restarts |

**Deprecated/outdated:**
- `InstalledAppFlow.run_local_server()`: Desktop-only; not usable in server context — use `Flow.from_client_secrets_file()` with `redirect_uri` for web callback
- `googleapiclient.discovery.build()` with token.json file: File-based, single-user — use database token storage for multi-user server

---

## Open Questions

1. **Google OAuth Consent Screen Verification**
   - What we know: Apps using `calendar.events` scope may require OAuth verification for public use. In testing mode (up to 100 test users), no verification needed.
   - What's unclear: Whether this app will exceed 100 users in the near term; whether the scope triggers "sensitive" designation requiring verification.
   - Recommendation: Start with testing mode (add specific user emails as test users in Google Cloud Console). Plan verification flow as a pre-launch task.

2. **Reminder Storage and Delivery (Claude's Discretion)**
   - What we know: User wants daily digest or session-start reminder (NOT per-event pings). Reminder delivery mechanics are deferred detail.
   - What's unclear: Whether reminders in Phase 4 are "stored for future delivery" (which requires a scheduler/cron job) or simply delivered when the session starts (simpler: just query Calendar at session start).
   - Recommendation: For Phase 4, implement as session-start reminder: on first message of a new day, query Calendar for today's events and prepend a brief agenda. This requires no scheduler infrastructure and satisfies the "morning digest" use case. Store a `last_briefing_date` in user preferences.

3. **Google Calendar Connection UX in WhatsApp**
   - What we know: OAuth requires a browser-based consent flow — the user must click a link.
   - What's unclear: How the user is directed to authorize from WhatsApp. The bot must send a URL message ("To connect your Google Calendar, tap: [link]") and the user completes auth in the browser.
   - Recommendation: When a calendar skill is triggered and no tokens exist for the user, return: "To use calendar features, connect your Google Calendar: [link]" where the link points to a FastAPI `/auth/google/connect?user_id=...` route.

4. **Conflict Detection Time Window**
   - What we know: CONTEXT.md specifies: detect conflicts and ask before adding. Google Calendar API's freebusy.query endpoint returns busy periods.
   - What's unclear: Exact window for conflict detection (e.g., does a 30-min event conflict with a 2-hour event that overlaps it? What about back-to-back events?).
   - Recommendation: Use `events.list` with timeMin/timeMax spanning the proposed event's start/end and check for any existing events in that window. Flag any overlap, not just exact conflicts.

---

## Sources

### Primary (HIGH confidence)
- `https://developers.google.com/workspace/calendar/api/quickstart/python` — Official Python quickstart; events.list() code verified
- `https://developers.google.com/workspace/calendar/api/guides/create-events` — events.insert() body format; only start+end required
- `https://developers.google.com/workspace/calendar/api/auth` — OAuth scopes: calendar.events vs calendar vs calendar.readonly (full scope list verified)
- `https://pypi.org/project/tavily-python/` — Version 0.7.21 (2026-01-30), MIT license, Python >=3.8 confirmed
- `https://docs.tavily.com/documentation/api-reference/endpoint/search` — include_answer parameter behavior, response structure with answer field verified
- `https://dateparser.readthedocs.io/en/latest/` — Version 1.3.0; PREFER_DATES_FROM, TIMEZONE, RETURN_AS_TIMEZONE_AWARE settings verified
- `https://platform.openai.com/docs/guides/structured-outputs` — Pydantic response_format pattern for intent classification verified
- `https://google-auth.readthedocs.io/en/latest/` — google.oauth2.credentials.Credentials, refresh() pattern verified

### Secondary (MEDIUM confidence)
- `https://joshuaakanetuk.com/blog/how-to-use-google-calendar-py/` — Multi-source verified Python Calendar API examples
- `https://endgrate.com/blog/how-to-create-calendar-events-with-the-google-calendar-api-in-python` — Verified against official docs
- `https://blog.tavily.com/getting-started-with-the-tavily-search-api/` — Tavily SDK basic usage examples

### Tertiary (LOW confidence)
- Community patterns for skill registry architecture — no single authoritative source; pattern derived from existing project conventions (Protocol in llm/base.py)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Google Calendar API and google-auth are official; tavily-python version verified on PyPI; dateparser version verified in docs
- Architecture: MEDIUM — Skill registry pattern is Claude's discretion area; recommended approach follows project conventions (Protocol pattern from Phase 3)
- Pitfalls: MEDIUM-HIGH — Google OAuth blocking I/O and token revocation are well-documented failure modes; some pitfalls (dateparser None returns) verified in docs

**Research date:** 2026-02-24
**Valid until:** 2026-03-24 (Google Calendar API: stable; Tavily: fast-moving — re-verify if > 2 weeks)
