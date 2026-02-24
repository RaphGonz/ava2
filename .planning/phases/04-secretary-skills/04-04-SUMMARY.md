---
phase: 04-secretary-skills
plan: "04"
subsystem: api
tags: [tavily, research, asyncio, skill-registry, secretary]

# Dependency graph
requires:
  - phase: 04-secretary-skills
    plan: "01"
    provides: "Skill Protocol, ParsedIntent dataclass, skill registry (register/get/list_skills), config fields for Tavily"
provides:
  - "ResearchSkill class implementing Skill Protocol for 'research' intent (SECR-03)"
  - "Tavily API integration wrapped in asyncio.to_thread"
  - "Ambiguous query detection heuristic (< 3 words, no question word)"
  - "Graceful degradation: missing API key and API failures return user-friendly error messages"
  - "'research' skill registered in skill registry at import time"
affects: [05-reminder-delivery, future-skills]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "asyncio.to_thread wrapping synchronous third-party SDK calls to avoid blocking FastAPI event loop"
    - "Register at import time pattern: skill module self-registers via register() at module bottom"
    - "Graceful degradation via empty-string default credentials: missing key → error message, not startup crash"
    - "Tavily include_answer='advanced' for LLM-quality answer without extra OpenAI call"

key-files:
  created:
    - backend/app/services/skills/research_skill.py
  modified: []

key-decisions:
  - "Tavily include_answer='advanced' provides pre-formatted AI answer — no separate LLM summarization call needed"
  - "TavilyClient.search() is synchronous — always wrapped in asyncio.to_thread to avoid blocking the event loop"
  - "Ambiguity heuristic: fewer than 3 words with no recognized question starter is 'broad' — returns clarifying question"
  - "Answer format: paragraph text + blank line + 'Source: [url]' — no trailing offers or follow-ups per CONTEXT.md"

patterns-established:
  - "asyncio.to_thread wrapping pattern: all synchronous SDK calls (Tavily, Google Auth) go through to_thread"
  - "Module-level skill self-registration: _skill = SkillClass(); register('intent', _skill) at bottom of module"
  - "Graceful degradation chain: missing key → RESEARCH_ERROR_MSG; API failure → RESEARCH_ERROR_MSG; short answer → NO_ANSWER_MSG"

requirements-completed: [SECR-03]

# Metrics
duration: 6min
completed: 2026-02-24
---

# Phase 4 Plan 04: ResearchSkill Summary

**ResearchSkill using Tavily include_answer="advanced" for direct factual answers with one source link, asyncio.to_thread integration, and graceful degradation for missing keys and API failures**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-24T09:30:44Z
- **Completed:** 2026-02-24T09:37:46Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- ResearchSkill class implementing the Skill Protocol — handles 'research' intent end-to-end
- Tavily API integration using include_answer="advanced" — no extra LLM summarization call needed
- asyncio.to_thread wrapping TavilyClient.search() — synchronous SDK never blocks the event loop
- Ambiguity detection heuristic: queries under 3 words with no question word return a clarifying question
- Three-tier graceful degradation: missing API key, API failure, and too-short answer each return distinct friendly messages
- Registered at module import time — 'research' available in skill registry without any routing changes

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement ResearchSkill with Tavily API integration** - `0c48bac` (feat)

**Plan metadata:** `(pending)`

## Files Created/Modified
- `backend/app/services/skills/research_skill.py` - ResearchSkill implementing Skill Protocol, registered for 'research' intent

## Decisions Made
- Tavily include_answer="advanced" provides LLM-quality answer pre-formatted — no second OpenAI call needed; keeps research responses fast and cost-efficient
- asyncio.to_thread is the correct wrapper for any synchronous SDK (Tavily, Google Auth) used inside async FastAPI handlers
- Ambiguity heuristic kept simple: word-count + question-starter check handles both English and French queries per CONTEXT.md bilingual requirement
- Response format strictly follows CONTEXT.md locked decisions: one paragraph, one source link, no follow-up offers

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required beyond TAVILY_API_KEY in backend/.env (already documented in Phase 4 Plan 01).

## Next Phase Readiness

- 'research' skill registered and fully functional pending TAVILY_API_KEY credential in .env
- Skill registry now has 'research' available for routing from ChatService/intent classifier
- Plans 02 (Google Calendar OAuth) and 03 (CalendarSkill) remain independent of this plan
- All 20 Phase 3 tests still pass (verified during execution)

---
*Phase: 04-secretary-skills*
*Completed: 2026-02-24*
