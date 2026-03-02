---
phase: 07-avatar-system-production
plan: 04
subsystem: ui, api
tags: [react, openai, bullmq, fastapi, typescript, replicate, supabase]

# Dependency graph
requires:
  - phase: 07-02
    provides: avatar model, AvatarCreate/AvatarResponse, POST /avatars, GET /avatars/me, PATCH /avatars/me/persona
  - phase: 07-03
    provides: BullMQ queue singleton, enqueue_photo_job(), photo generation pipeline processor

provides:
  - SEND_PHOTO_TOOL definition + intimate mode tool call detection in ChatService
  - enqueue_photo_job() wiring in handle_message() when finish_reason == "tool_calls"
  - PHOTO_PLACEHOLDER_MSG returned and appended to session history (not raw tool_calls — Pitfall 3)
  - POST /avatars/me/reference-image endpoint (generate + watermark + upload + signed URL)
  - frontend/src/api/avatars.ts with getMyAvatar/createAvatar/generateReferenceImage
  - AvatarSetupPage.tsx onboarding form with reference image preview + regenerate loop
  - App.tsx OnboardingGate redirecting to /avatar-setup when no avatar found

affects: [07-05, 07-06, chat, onboarding, intimate-mode, photo-pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Intimate mode LLM direct call: self._openai_client.chat.completions.create() with tools=[SEND_PHOTO_TOOL] instead of self._llm.complete()"
    - "OnboardingGate React component wraps protected routes, redirects on null avatar from useQuery"
    - "queryClient.invalidateQueries(['avatar']) on AvatarSetupPage completion prevents redirect loop"

key-files:
  created:
    - frontend/src/api/avatars.ts
    - frontend/src/pages/AvatarSetupPage.tsx
  modified:
    - backend/app/services/chat.py
    - backend/app/routers/avatars.py
    - frontend/src/App.tsx
    - backend/tests/test_secretary_skills.py

key-decisions:
  - "Intimate mode LLM calls use self._openai_client.chat.completions.create() directly with tools=[SEND_PHOTO_TOOL] — not self._llm.complete() — to enable tool_calls detection"
  - "PHOTO_PLACEHOLDER_MSG appended to session history (not the raw tool_calls message) to prevent OpenAI tool message ordering error (Pitfall 3)"
  - "channel defaults to 'web' in ChatService — WhatsApp channel override is a post-beta improvement when channel info is plumbed into handle_message()"
  - "No updateAvatar function in avatars.ts — avatar locked post-onboarding per user decision; only PATCH /avatars/me/persona (personality only) remains"
  - "OnboardingGate uses React Query queryKey ['avatar'] with 5min staleTime — AvatarSetupPage invalidates this key on approval to clear redirect loop"

patterns-established:
  - "Tool call detection pattern: check finish_reason == 'tool_calls' and choice.message.tool_calls before json.loads(tool_call.function.arguments)"
  - "Onboarding gate pattern: useQuery in a wrapper component, redirect to setup page when data === null, invalidate query on completion"

requirements-completed: [AVTR-01, AVTR-02, AVTR-03, AVTR-04, AVTR-05, INTM-03]

# Metrics
duration: 18min
completed: 2026-02-25
---

# Phase 7 Plan 04: LLM send_photo Tool Call + Avatar Onboarding Flow Summary

**Intimate mode ChatService now detects send_photo tool calls and enqueues BullMQ jobs; AvatarSetupPage onboarding form with reference image generation loop wired end-to-end via new POST /avatars/me/reference-image endpoint**

## Performance

- **Duration:** 18 min
- **Started:** 2026-02-25T10:01:48Z
- **Completed:** 2026-02-25T10:19:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- ChatService intimate mode now calls `self._openai_client.chat.completions.create()` with `tools=[SEND_PHOTO_TOOL]`; on `finish_reason == "tool_calls"` it calls `enqueue_photo_job()` and returns placeholder text (not the raw tool_calls message — avoids Pitfall 3)
- AvatarSetupPage.tsx: complete onboarding form with name, age (20+ enforced), gender, nationality, appearance, personality + reference image preview + approve/regenerate loop
- App.tsx OnboardingGate component wraps /chat and /settings; redirects to /avatar-setup when GET /avatars/me returns 404 (null from getMyAvatar)
- POST /avatars/me/reference-image backend endpoint: builds prompt, calls Replicate, downloads image, applies watermark, uploads to Supabase storage, returns 24h signed URL
- Frontend TypeScript build passes (zero errors); all 47 backend tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: ChatService send_photo tool call + BullMQ enqueue in intimate mode** - `188df70` (feat)
2. **Task 2: AvatarSetupPage + avatars API module + App.tsx OnboardingGate + POST /avatars/me/reference-image** - `7966e74` (feat)

**Plan metadata:** (docs commit — see final commit below)

## Files Created/Modified
- `backend/app/services/chat.py` - Added `import json`, `SEND_PHOTO_TOOL` dict, `PHOTO_PLACEHOLDER_MSG`, replaced LLM try/except with mode-aware branch
- `backend/app/routers/avatars.py` - Added `import logging`, `logger`, and `POST /me/reference-image` endpoint
- `frontend/src/api/avatars.ts` - New: `getMyAvatar`, `createAvatar`, `generateReferenceImage` (no updateAvatar)
- `frontend/src/pages/AvatarSetupPage.tsx` - New: full onboarding form + reference image preview + approve/regenerate loop
- `frontend/src/App.tsx` - Added `AvatarSetupPage` import, `OnboardingGate` component, `/avatar-setup` and `/subscribe` routes, wrapped `/chat` and `/settings` with OnboardingGate
- `backend/tests/test_secretary_skills.py` - Updated `test_intimate_mode_bypasses_intent_classifier` to mock `_openai_client.chat.completions.create` (intimate mode no longer calls `_llm.complete`)

## Decisions Made
- Intimate mode LLM calls use `self._openai_client.chat.completions.create()` directly with `tools=[SEND_PHOTO_TOOL]` to enable tool_calls detection; secretary mode still uses `self._llm.complete()` unchanged
- `PHOTO_PLACEHOLDER_MSG` appended to session history instead of the raw `tool_calls` message — prevents OpenAI API error on subsequent requests (Pitfall 3 from RESEARCH.md)
- `channel` defaults to `"web"` in `ChatService.handle_message()` — WhatsApp channel support is a post-beta improvement requiring channel plumbed into `handle_message()` signature
- No `updateAvatar` in `avatars.ts` — avatar locked after onboarding per user decision (only personality update via PATCH /avatars/me/persona)
- `OnboardingGate` uses `queryKey: ['avatar']` with 5-minute stale time; `AvatarSetupPage.handleApprove()` calls `queryClient.invalidateQueries({ queryKey: ['avatar'] })` before navigating to `/chat` to prevent redirect loop

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test_intimate_mode_bypasses_intent_classifier to mock correct code path**
- **Found during:** Task 1 verification (running full test suite)
- **Issue:** Test expected `mock_llm.complete` to be called in intimate mode and return "LLM response". After our change, intimate mode now calls `self._openai_client.chat.completions.create()` directly — the test's mock was not patching the new code path, causing the test to hit the real OpenAI API and get a 429 quota error
- **Fix:** Updated test to create a `mock_response` object with `choices[0].finish_reason = "stop"` and `choices[0].message.content = "LLM response"`, patched `service._openai_client.chat.completions.create`, and added assertion that `mock_llm.complete.assert_not_called()` to confirm the new behavior
- **Files modified:** `backend/tests/test_secretary_skills.py`
- **Verification:** Test passes (1 passed, 25 warnings); full suite 47 passed
- **Committed in:** `7966e74` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug)
**Impact on plan:** Auto-fix was necessary to keep tests aligned with the new intimate mode code path. No scope creep.

## Issues Encountered
- `App.tsx` had already been partially updated by Plan 05 (it already had `SubscribePage` imported and `/subscribe` route). The re-read before write caught this correctly; the final write replaced the file with the complete version including `OnboardingGate` and `AvatarSetupPage` alongside the existing `SubscribePage` import.
- `SubscribePage.tsx` already existed as a full implementation (from Plan 05 — plans ran out of order). No stub was needed.

## User Setup Required
None - no external service configuration required for these changes. The reference image generation endpoint requires Replicate and Supabase storage (configured in 07-01/07-02), already in `.env`.

## Next Phase Readiness
- Full onboarding flow complete: signup → avatar setup → reference image → chat
- Photo loop complete: intimate mode LLM tool call → BullMQ enqueue → worker processes (07-03)
- Ready for 07-05 (billing/Stripe integration) and 07-06 (production deployment)

## Self-Check: PASSED

- backend/app/services/chat.py: FOUND
- backend/app/routers/avatars.py: FOUND
- frontend/src/api/avatars.ts: FOUND
- frontend/src/pages/AvatarSetupPage.tsx: FOUND
- frontend/src/App.tsx: FOUND
- 07-04-SUMMARY.md: FOUND
- Commit 188df70 (Task 1): FOUND
- Commit 7966e74 (Task 2): FOUND
- Frontend build: PASSED (zero TypeScript errors)
- Backend tests: PASSED (47 passed, 0 failed)

---
*Phase: 07-avatar-system-production*
*Completed: 2026-02-25*
