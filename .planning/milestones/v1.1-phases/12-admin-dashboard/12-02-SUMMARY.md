---
phase: 12-admin-dashboard
plan: 02
subsystem: api
tags: [supabase, usage-events, analytics, admin, stripe, chat, image-generation]

# Dependency graph
requires:
  - phase: 08-infrastructure-deployment
    provides: usage_events table with RLS enabled (admin reads via service role)
  - phase: 11-subscription-management-churn
    provides: billing.py cancel endpoint with existing subscription_cancelled emit pattern
provides:
  - message_sent emission in chat.py (normal LLM/skill flow end)
  - mode_switch emission in chat.py (3 actual switch paths only)
  - photo_generated emission in processor.py (alongside audit_log)
  - subscription_created emission in billing.py checkout.session.completed
  - 7 pytest tests in test_admin_events.py verifying all 4 emission paths
affects: [12-admin-dashboard, 13-smoke-test]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "fire-and-forget usage_events insert: try/except wraps each supabase_admin.from_('usage_events').insert().execute(), errors logged not raised, user flow never blocked"
    - "supabase_admin used for usage_events writes (no user JWT in webhook/worker context)"
    - "source inspection tests (inspect.getsource) for verifying emit wiring without live DB"

key-files:
  created:
    - backend/tests/test_admin_events.py
  modified:
    - backend/app/services/chat.py
    - backend/app/services/jobs/processor.py
    - backend/app/routers/billing.py

key-decisions:
  - "mode_switch emit placed after switch_mode() call but BEFORE return — all 3 actual switch paths (pending clarification, custom phrase, exact/fuzzy detect) wired; already-in-mode paths explicitly excluded"
  - "message_sent emit placed between final append_message and return reply — only fires on normal LLM/skill flow, not on early returns (crisis, guardrail, mode switch)"
  - "processor.py keeps BOTH audit_log (compliance) and usage_events (admin dashboard) — Step 7b is additive, not a replacement"
  - "backend/.env STRIPE_PRICE_ID -> STRIPE_PRICE_ID_BASIC/PREMIUM/ELITE (Rule 3 auto-fix: pre-existing env mismatch blocked test imports)"

patterns-established:
  - "Emit pattern: try: supabase_admin.from_('usage_events').insert({user_id, event_type, metadata}).execute() except Exception as exc: logger.error(...)"
  - "Fire-and-forget writes: never raise, never block caller, log-only on failure"

requirements-completed: [ADMN-02]

# Metrics
duration: 16min
completed: 2026-03-10
---

# Phase 12 Plan 02: Usage Event Emission Wiring Summary

**4 usage_events emission points wired across chat.py, processor.py, and billing.py using fire-and-forget try/except pattern, enabling admin dashboard real data (ADMN-02)**

## Performance

- **Duration:** 16 min
- **Started:** 2026-03-10T07:17:30Z
- **Completed:** 2026-03-10T07:33:30Z
- **Tasks:** 2
- **Files modified:** 3 + 1 created (test_admin_events.py)

## Accomplishments
- Wired `message_sent` emission at the end of the normal LLM/skill flow in `chat.py` — fires once per non-early-return reply
- Wired `mode_switch` emission at all 3 actual switch paths in `chat.py` — pending clarification, custom phrase match, and exact/fuzzy detection — intentionally excluded from already-in-mode returns
- Wired `photo_generated` emission in `processor.py` Step 7b immediately after the existing `audit_log` write — both writes preserved independently (compliance + analytics)
- Wired `subscription_created` emission in `billing.py` `checkout.session.completed` handler after `activate_subscription()` completes
- Created `test_admin_events.py` with 7 source-inspection tests — all GREEN without live DB

## Task Commits

1. **Task 1: Wire message_sent and mode_switch emissions in chat.py** - `dcc7df7` (feat)
2. **Task 2: Wire photo_generated, subscription_created + tests** - `ce25291` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `backend/app/services/chat.py` - Added 3 mode_switch emit blocks (one per actual switch path) and 1 message_sent emit block before final return
- `backend/app/services/jobs/processor.py` - Added Step 7b photo_generated emit after existing audit_log try/except (both writes kept)
- `backend/app/routers/billing.py` - Added subscription_created emit in checkout.session.completed after activate_subscription()
- `backend/tests/test_admin_events.py` - 7 source-inspection tests verifying all 4 event types are wired

## Decisions Made

- `mode_switch` emit placed after `switch_mode()` but before `return` in each of the 3 actual switch paths. Already-in-mode returns (`ALREADY_INTIMATE_MSG`/`ALREADY_SECRETARY_MSG`) are inside the `if target == session.mode:` guard and never reach the emit code.
- `message_sent` emit only fires at the single terminal `return reply` at the bottom of `handle_message()`. All early returns (crisis, guardrail, mode switch, skill dispatch) do not reach this point.
- `processor.py` Step 7 (audit_log) kept entirely — Step 7b is additive. Comment explicitly notes both writes are independent.
- Source inspection tests (via `inspect.getsource`) chosen over behavior-level mocks — lightweight, no DB required, verify the wiring exists in the code itself.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed backend/.env STRIPE_PRICE_ID field mismatch**
- **Found during:** Task 2 (running test_admin_events.py)
- **Issue:** `.env` had `STRIPE_PRICE_ID=price_...` (old Phase 7 field) but Settings model now requires `STRIPE_PRICE_ID_BASIC/PREMIUM/ELITE` (added in Phase 11). Pydantic raised `extra_forbidden` ValidationError, blocking all module imports and preventing tests from running.
- **Fix:** Replaced `STRIPE_PRICE_ID=price_...` with `STRIPE_PRICE_ID_BASIC=`, `STRIPE_PRICE_ID_PREMIUM=price_1T7Y6yGzFiJv4RfGhYAwGZM7`, `STRIPE_PRICE_ID_ELITE=` in `backend/.env`
- **Files modified:** `backend/.env` (gitignored, not committed)
- **Verification:** All 7 tests in test_admin_events.py pass; 58 other tests pass
- **Committed in:** ce25291 (Task 2 commit — .env excluded by .gitignore)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Auto-fix necessary for test execution. No scope creep. The .env fix corrects a pre-existing configuration drift from Phase 11 schema changes.

## Issues Encountered

- `test_comfyui_provider.py::test_t2i_generate_returns_image_bytes` fails with pre-existing mock structure issue (history_v2 outputs unwrapping). This failure pre-dates this plan and is unrelated to usage_events wiring. Excluded from regression scope.

## Next Phase Readiness

- All 4 event types now emit to `usage_events` in real user flows
- Admin dashboard (Phase 12 Plan 03+) can query the table and see real data
- 58 tests pass with no new regressions introduced

---
*Phase: 12-admin-dashboard*
*Completed: 2026-03-10*
