---
phase: 03-core-intelligence-mode-switching
plan: 01
subsystem: api
tags: [openai, llm, python, protocol, pydantic-settings, asyncio]

# Dependency graph
requires:
  - phase: 02-infrastructure-user-management
    provides: config.py Settings class with pydantic-settings, backend/app/services/ package structure
provides:
  - LLMProvider Protocol (structural interface, runtime_checkable) for ARCH-02 swappability
  - OpenAIProvider concrete implementation using AsyncOpenAI with max_retries=1
  - secretary_prompt() and intimate_prompt() template functions
  - Settings.llm_provider, Settings.llm_model, Settings.openai_api_key config fields
affects: [03-02-mode-switching, 03-03-conversation-orchestrator, 03-04-message-routing, 05-avatar-personality]

# Tech tracking
tech-stack:
  added: [openai>=1.0.0, rapidfuzz>=3.0.0]
  patterns: [Python Protocol structural typing, AsyncOpenAI non-blocking client, runtime_checkable provider interface]

key-files:
  created:
    - backend/app/services/llm/__init__.py
    - backend/app/services/llm/base.py
    - backend/app/services/llm/openai_provider.py
    - backend/app/services/llm/prompts.py
  modified:
    - backend/requirements.txt
    - backend/app/config.py

key-decisions:
  - "LLMProvider uses Python Protocol (structural typing) not ABC — any class with async complete() satisfies it without inheritance"
  - "AsyncOpenAI with max_retries=1 delegates retry logic to SDK, except block returns user-friendly fallback message"
  - "System prompt templates are pure functions accepting avatar_name and personality at runtime — no hardcoded strings"
  - "openai_api_key defaults to empty string in Settings — missing key silently returns fallback, not 500 error"

patterns-established:
  - "Protocol pattern: LLM provider interface defined as @runtime_checkable Protocol — future providers implement the same signature, set llm_provider in config"
  - "Prompt template pattern: secretary_prompt(avatar_name, personality) and intimate_prompt(avatar_name, personality) called with DB row values at request time"
  - "Async client pattern: AsyncOpenAI used throughout — never synchronous OpenAI() which blocks uvicorn event loop"

requirements-completed: [ARCH-02, CHAT-01]

# Metrics
duration: 9min
completed: 2026-02-23
---

# Phase 3 Plan 01: LLM Service Abstraction Layer Summary

**OpenAI-backed LLM service with swappable Protocol interface, AsyncOpenAI client, and per-mode system prompt templates for secretary and intimate avatar personalities**

## Performance

- **Duration:** 9 min
- **Started:** 2026-02-23T20:15:28Z
- **Completed:** 2026-02-23T20:24:48Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- LLMProvider Protocol defined with @runtime_checkable decorator — any class with async complete(messages, system_prompt) satisfies the interface without inheritance (ARCH-02 swappability)
- OpenAIProvider backed by AsyncOpenAI with max_retries=1 SDK retry and user-friendly fallback message on exception
- secretary_prompt() and intimate_prompt() functions accepting avatar_name and personality at runtime, with anti-leak instructions per RESEARCH.md Pitfall 3
- config.py Settings extended with llm_provider, llm_model, openai_api_key loaded from .env automatically

## Task Commits

Each task was committed atomically:

1. **Task 1: Add LLM dependencies to requirements.txt and extend config.py** - `2d48776` (chore)
2. **Task 2: Create LLM service package — Protocol, OpenAI provider, and system prompt templates** - `3aa33d7` (feat)

**Plan metadata:** _(docs commit follows)_

## Files Created/Modified
- `backend/app/services/llm/__init__.py` - Empty package marker
- `backend/app/services/llm/base.py` - LLMProvider Protocol and Message type alias
- `backend/app/services/llm/openai_provider.py` - Concrete OpenAI implementation using AsyncOpenAI
- `backend/app/services/llm/prompts.py` - secretary_prompt() and intimate_prompt() template functions
- `backend/requirements.txt` - Added openai>=1.0.0 and rapidfuzz>=3.0.0
- `backend/app/config.py` - Added llm_provider, llm_model, openai_api_key to Settings class

## Decisions Made
- Used Python Protocol (not ABC) for LLMProvider — structural typing means a future provider just needs the right method signature, no base class coupling
- AsyncOpenAI client is required for FastAPI/uvicorn async context; synchronous OpenAI() would block the event loop
- max_retries=1 in AsyncOpenAI() delegates retry to the SDK, which handles transient errors and rate limits; the except block covers SDK-exhausted retries with a user-friendly message
- openai_api_key defaults to empty string so the Settings class can be instantiated without a key (returns fallback message rather than crashing at startup)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
OpenAI API key required before LLM calls will succeed. Add to `backend/.env`:

```
OPENAI_API_KEY=sk-...
```

Get key from: OpenAI Dashboard -> API Keys -> Create new secret key.
Without this key, the system will start but return the fallback message "I'm having trouble thinking right now — try again in a moment." for all LLM requests.

## Next Phase Readiness
- LLM service layer complete and ready for use by 03-02 (mode switching), 03-03 (conversation orchestrator)
- LLMProvider Protocol provides clean seam — call sites import from base.py, swap provider via config
- No blockers

---
*Phase: 03-core-intelligence-mode-switching*
*Completed: 2026-02-23*
