---
phase: 05-intimate-mode-text-foundation
plan: "01"
subsystem: api
tags: [llm, prompts, content-safety, crisis-detection, regex, python]

# Dependency graph
requires:
  - phase: 03-core-intelligence-mode-switching
    provides: ChatService, intimate_prompt() call site, SessionStore per-mode history
  - phase: 04-secretary-skills
    provides: ChatService handle_message() wiring pattern for pre-LLM gates
provides:
  - Per-persona intimate_prompt() dispatch with 6 factory functions (playful, dominant, shy, caring, intellectual, adventurous)
  - ContentGuard class with check_message() and module-level content_guard singleton
  - GuardResult dataclass and _REFUSAL_MESSAGES dict for 6 blocked categories
  - CrisisDetector class with two-layer check_message() and module-level crisis_detector singleton
  - CrisisResult dataclass and CRISIS_RESPONSE constant with 988 Lifeline
affects: [05-02-chatservice-wiring, 05-03-persona-endpoint, testing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-persona prompt dispatch: intimate_prompt() routes via dict.get(personality, fallback) to private factory functions"
    - "Dual-pass normalization for content guard: space-replace AND collapse-remove to catch obfuscation (ch!ld)"
    - "Two-layer crisis detection: Layer 1 immediate trigger on unambiguous phrases, Layer 2 context scoring requiring distress in message AND history"
    - "Module-level singletons pattern: content_guard and crisis_detector importable from their packages"

key-files:
  created:
    - backend/app/services/content_guard/__init__.py
    - backend/app/services/content_guard/guard.py
    - backend/app/services/crisis/__init__.py
    - backend/app/services/crisis/detector.py
  modified:
    - backend/app/services/llm/prompts.py

key-decisions:
  - "intimate_prompt() dispatch uses dict.get(personality, _intimate_caring) — unknown personas fall back to caring, never raise"
  - "ContentGuard dual-pass normalization: space-replace (standard) + collapse-remove (empty) — catches obfuscation like ch!ld which space-replace alone misses"
  - "Obfuscation pattern ch[^a-z]{0,2}ld added to minors regex — catches symbol-insertion variants beyond simple char collapse"
  - "'want to die' placed in Layer 2 context-boost (not Layer 1 immediate) — prevents false positive on 'want to die laughing'"
  - "ContentGuard is mode-agnostic pure function — mode gating lives in chat.py, not guard itself (Pitfall 6)"
  - "CrisisDetector runs in all modes — wiring in chat.py decides whether to route; detector has no mode awareness"
  - "Six persona factory functions added including intellectual and adventurous for full PersonalityType enum coverage"

patterns-established:
  - "Pattern 1: Per-persona prompt factory — each function has vocabulary-level anchors (specific phrase examples), not just adjective descriptors"
  - "Pattern 2: Content guard normalization before regex matching — always normalize input, never match raw text"
  - "Pattern 3: Crisis Layer 1 vs Layer 2 split — unambiguous phrases are immediate triggers; ambiguous phrases require context accumulation"

requirements-completed: [INTM-01, INTM-02]

# Metrics
duration: 12min
completed: 2026-02-24
---

# Phase 5 Plan 01: Per-Persona Prompts + ContentGuard + CrisisDetector Summary

**Per-persona intimate_prompt() dispatch (6 factories), ContentGuard with dual-pass normalization for 6 blocked categories, and two-layer CrisisDetector with 988 Lifeline response — all pure Python, zero new dependencies**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-24T12:01:20Z
- **Completed:** 2026-02-24T12:13:00Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- Replaced generic intimate_prompt() with dispatch routing to 6 per-persona factory functions, each with vocabulary-level anchors, anti-question-ending rule, and character protection
- Built ContentGuard service with dual-pass input normalization to catch obfuscation bypasses (ch!ld), 6 blocked categories, per-category refusal messages, and module-level singleton
- Built CrisisDetector service with Layer 1 immediate triggers and Layer 2 context scoring; "want to die" correctly placed in Layer 2 to avoid false positive on ironic phrases

## Task Commits

Each task was committed atomically:

1. **Task 1: Per-Persona Intimate System Prompts** - `bca9321` (feat)
2. **Task 2: ContentGuard Safety Service** - `d4a7147` (feat)
3. **Task 3: CrisisDetector Service** - `6190ec8` (feat)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified
- `backend/app/services/llm/prompts.py` - Replaced generic intimate_prompt() with per-persona dispatch to 6 factory functions
- `backend/app/services/content_guard/__init__.py` - Package marker (empty)
- `backend/app/services/content_guard/guard.py` - ContentGuard class, GuardResult, _REFUSAL_MESSAGES, content_guard singleton
- `backend/app/services/crisis/__init__.py` - Package marker (empty)
- `backend/app/services/crisis/detector.py` - CrisisDetector class, CrisisResult, CRISIS_RESPONSE, crisis_detector singleton

## Decisions Made
- **Dual-pass normalization in ContentGuard:** Space-replace alone fails to catch "ch!ld" (becomes "ch ld", word boundaries break match). Added collapse-remove (empty string) pass plus explicit obfuscation pattern `ch[^a-z]{0,2}ld` in the minors regex. Fixes Pitfall 2 from RESEARCH.md.
- **"want to die" in Layer 2 not Layer 1:** Per RESEARCH.md Pitfall 3, moving this phrase to context-required detection prevents false positives on ironic uses like "I want to die laughing". Verified by test.
- **Intellectual and adventurous personas added:** PersonalityType enum has these beyond the four primary ones. Added matching factory functions with appropriate vocabulary anchors rather than falling through to caring silently.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed obfuscation bypass in ContentGuard normalization**
- **Found during:** Task 2 (ContentGuard Safety Service) — verification test
- **Issue:** Plan specified `re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())` but "ch!ld" normalizes to "ch ld" (space breaks word boundary), not caught by regex
- **Fix:** Added second collapse-remove pass (`re.sub(r"[^a-zA-Z0-9\s]", "", lowered)`) AND added obfuscation-aware pattern `ch[^a-z]{0,2}ld` to the minors regex. Both passes are searched.
- **Files modified:** backend/app/services/content_guard/guard.py
- **Verification:** `ContentGuard().check_message('ch!ld roleplay')` returns `GuardResult(blocked=True, category='minors')`
- **Committed in:** d4a7147 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Necessary correctness fix — the plan's normalization approach had a gap for symbol-insertion obfuscation. No scope creep.

## Issues Encountered
None beyond the obfuscation bypass documented above.

## User Setup Required
None - no external service configuration required. All three modules are pure Python using stdlib only.

## Next Phase Readiness
- All three service modules are importable and fully unit-testable
- `intimate_prompt(avatar_name, personality)` signature unchanged — no call-site changes in chat.py needed
- ContentGuard and CrisisDetector are ready to be wired as pre-LLM gates in Plan 02 (ChatService wiring)
- Import pattern for Plan 02: `from app.services.content_guard.guard import content_guard, _REFUSAL_MESSAGES` and `from app.services.crisis.detector import crisis_detector, CRISIS_RESPONSE`

## Self-Check: PASSED

All files verified present:
- FOUND: backend/app/services/llm/prompts.py
- FOUND: backend/app/services/content_guard/__init__.py
- FOUND: backend/app/services/content_guard/guard.py
- FOUND: backend/app/services/crisis/__init__.py
- FOUND: backend/app/services/crisis/detector.py

All commits verified:
- FOUND: bca9321 (Task 1 — intimate prompt dispatch)
- FOUND: d4a7147 (Task 2 — ContentGuard)
- FOUND: 6190ec8 (Task 3 — CrisisDetector)

---
*Phase: 05-intimate-mode-text-foundation*
*Completed: 2026-02-24*
