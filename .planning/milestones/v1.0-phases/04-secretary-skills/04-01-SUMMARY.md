---
phase: 04-secretary-skills
plan: "01"
subsystem: api
tags: [openai, pydantic, python-protocol, registry-pattern, intent-classification, google-calendar, tavily]

# Dependency graph
requires:
  - phase: 03-core-intelligence-mode-switching
    provides: LLMProvider Protocol pattern (structural typing) and OpenAI AsyncOpenAI client used as foundation
provides:
  - Skill Protocol (runtime_checkable) with handle(user_id, intent, user_tz) -> str interface
  - ParsedIntent dataclass (skill, raw_text, extracted_date, extracted_title, query)
  - Module-level skill registry with register(), get(), list_skills() functions
  - classify_intent() async function using OpenAI structured outputs and IntentResult Pydantic model
  - config.py fields for google_client_id, google_client_secret, google_oauth_redirect_uri, tavily_api_key
  - requirements.txt entries for google-api-python-client, google-auth-oauthlib, google-auth-httplib2, tavily-python, dateparser
affects:
  - 04-02 (calendar_add skill — will call register() and implement Skill Protocol)
  - 04-03 (calendar_view skill — will call register() and implement Skill Protocol)
  - 04-04 (research skill — uses tavily_api_key from config)
  - 04-05 (ChatService integration — will call classify_intent() in secretary mode)

# Tech tracking
tech-stack:
  added: [tavily-python==0.7.21, dateparser==1.3.0, google-api-python-client>=2.0.0, google-auth-oauthlib>=1.0.0, google-auth-httplib2>=0.2.0]
  patterns:
    - "Plugin registry: skills self-register at import time via register(), ChatService dispatches via get() — no routing logic changes needed for new skills"
    - "OpenAI structured outputs with Pydantic response_format for guaranteed valid enum — no JSON parsing errors"
    - "Graceful fallback: classify_intent() catches all exceptions and returns ParsedIntent(skill='chat') — messages always handled"

key-files:
  created:
    - backend/app/services/skills/__init__.py
    - backend/app/services/skills/registry.py
    - backend/app/services/skills/intent_classifier.py
  modified:
    - backend/app/config.py
    - backend/requirements.txt

key-decisions:
  - "Skill registry uses module-level dict (not class-based) — consistent with Python module singleton pattern, simpler than dependency injection"
  - "classify_intent() accepts AsyncOpenAI client and model as arguments (not imported from config) — keeps classifier testable without config coupling"
  - "All new config fields default to empty string — missing credentials return graceful error messages, not startup crashes (same pattern as openai_api_key)"
  - "IntentResult is a separate Pydantic model from ParsedIntent — IntentResult is the LLM response shape, ParsedIntent is the domain object passed to skills"

patterns-established:
  - "Skill Plugin Pattern: implement handle() -> register() at module import time -> no routing changes needed"
  - "Structural typing for skill interface: Skill Protocol (runtime_checkable) matches LLMProvider pattern from Phase 3"
  - "Bilingual classifier: INTENT_CLASSIFIER_PROMPT includes FR+EN examples for both calendar and research intents"

requirements-completed: [ARCH-01, SECR-03]

# Metrics
duration: 10min
completed: 2026-02-24
---

# Phase 4 Plan 01: Skill Registry Foundation and Intent Classifier Summary

**Plugin-style skill registry with Skill Protocol + ParsedIntent dataclass and OpenAI structured-output intent classifier routing secretary messages to calendar_add, calendar_view, research, or chat**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-24T08:59:01Z
- **Completed:** 2026-02-24T09:09:05Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Created backend/app/services/skills/ package with Skill Protocol (runtime_checkable), ParsedIntent dataclass, and module-level registry (register/get/list_skills)
- Created intent_classifier.py with classify_intent() using OpenAI structured outputs (response_format=IntentResult), bilingual EN/FR system prompt, and chat fallback on error
- Updated config.py with google_client_id, google_client_secret, google_oauth_redirect_uri, tavily_api_key (all defaulting to empty string, no startup crash)
- Added 5 new packages to requirements.txt (google API client stack, tavily-python, dateparser) — all installed successfully
- All 20 Phase 3 regression tests still pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Create skill registry package with Skill Protocol, ParsedIntent, and registry dict** - `65bd76d` (feat)
2. **Task 2: Create intent classifier and update config + requirements** - `7d8887c` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `backend/app/services/skills/__init__.py` - Package marker (empty)
- `backend/app/services/skills/registry.py` - Skill Protocol, ParsedIntent dataclass, _REGISTRY dict, register/get/list_skills functions
- `backend/app/services/skills/intent_classifier.py` - classify_intent() async function, IntentResult Pydantic model, INTENT_CLASSIFIER_PROMPT (bilingual)
- `backend/app/config.py` - Added google_client_id, google_client_secret, google_oauth_redirect_uri, tavily_api_key fields
- `backend/requirements.txt` - Added google-api-python-client, google-auth-oauthlib, google-auth-httplib2, tavily-python, dateparser

## Decisions Made

- classify_intent() accepts AsyncOpenAI client and model as parameters (not importing from config directly) — keeps the function testable without config coupling, consistent with how ChatService was designed in Phase 3
- IntentResult (Pydantic BaseModel for LLM response) is separate from ParsedIntent (dataclass for domain routing) — clean separation between LLM schema and application domain object
- All new config fields default to empty string — graceful degradation, no crash on startup if secrets not configured (established pattern from openai_api_key)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

New environment variables will be needed when implementing calendar and research skills:
- `GOOGLE_CLIENT_ID` — from Google Cloud Console OAuth credentials
- `GOOGLE_CLIENT_SECRET` — from Google Cloud Console OAuth credentials
- `TAVILY_API_KEY` — from https://tavily.com

These are not required to start the server (defaults to empty string). They will be needed in Plans 04-02 through 04-04.

## Next Phase Readiness

- Skill registry ready: Plans 04-02, 04-03, 04-04 can implement Skill Protocol and call register() at import time
- Intent classifier ready: Plan 04-05 can call classify_intent() in ChatService secretary mode branch
- Config fields in place: google and tavily credentials just need to be set in .env when services are integrated
- All Phase 3 tests green — no regressions from new package additions

---
*Phase: 04-secretary-skills*
*Completed: 2026-02-24*

## Self-Check: PASSED

- FOUND: backend/app/services/skills/__init__.py
- FOUND: backend/app/services/skills/registry.py
- FOUND: backend/app/services/skills/intent_classifier.py
- FOUND: .planning/phases/04-secretary-skills/04-01-SUMMARY.md
- FOUND commit: 65bd76d (Task 1)
- FOUND commit: 7d8887c (Task 2)
