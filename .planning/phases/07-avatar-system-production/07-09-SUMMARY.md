---
phase: 07-avatar-system-production
plan: 09
subsystem: api
tags: [fastapi, backgroundtasks, polling, react, typescript, comfyui]

# Dependency graph
requires:
  - phase: 07-avatar-system-production
    provides: ComfyUI provider, watermark pipeline, Supabase storage upload, avatars router
  - phase: 07.1-switch-image-generation-to-comfyui-cloud
    provides: ComfyUIProvider with working 4-step flow returning image_bytes

provides:
  - POST /avatars/me/reference-image returns 202 immediately (fire-and-forget)
  - _generate_reference_image_task background function runs full ComfyUI pipeline asynchronously
  - triggerReferenceImage() fire-and-forget frontend helper
  - pollForReferenceImage() polling helper with 3s interval and 5-minute timeout
  - AvatarSetupPage with spinner, polling loop, timeout error, and Regenerate cancel logic

affects: [frontend-onboarding, avatar-setup-flow, comfyui-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - FastAPI BackgroundTasks for long-running jobs (fire-and-forget + client polls)
    - supabase_admin (service role) in background tasks -- no user JWT in background context
    - setInterval polling loop with cleanup function returned for React useEffect/useRef cancel

key-files:
  created: []
  modified:
    - backend/app/routers/avatars.py
    - frontend/src/api/avatars.ts
    - frontend/src/pages/AvatarSetupPage.tsx

key-decisions:
  - "BackgroundTasks parameter injected by FastAPI without Depends() -- no changes to main.py needed"
  - "status_code=202 on decorator -- FastAPI returns 202 Accepted for this endpoint"
  - "reference_image_url cleared to None before queuing task -- ensures frontend polling waits for new image and does not show stale previous URL"
  - "supabase_admin used in background task -- consistent with Phase 2 service role pattern; no user JWT available in background context"
  - "Background task exceptions caught and logged but not re-raised -- task failure must not crash the event loop; frontend times out via polling after 5 minutes"
  - "triggerReferenceImage replaces generateReferenceImage -- semantically: fires job, does not return URL"
  - "pollForReferenceImage returns cleanup function -- caller stores in useRef and cancels on Regenerate or unmount"

patterns-established:
  - "Fire-and-forget + poll pattern: POST returns 202 immediately; client polls GET until field is non-null"
  - "stopPollingRef pattern: useRef stores cleanup function to cancel active setInterval before starting a new one"

requirements-completed: [AVTR-05, INTM-03]

# Metrics
duration: 12min
completed: 2026-03-02
---

# Phase 7 Plan 9: GAP-3 Fix -- Reference Image Fire-and-Forget + Frontend Polling Summary

**FastAPI BackgroundTasks converts blocking 120s ComfyUI pipeline to 202 fire-and-forget; AvatarSetupPage polls GET /avatars/me every 3s with spinner, timeout, and Regenerate cancel logic**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-02T10:00:54Z
- **Completed:** 2026-03-02T10:12:10Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- POST /avatars/me/reference-image now returns 202 within ~100ms -- Nginx proxy_read_timeout (60s) can no longer kill the connection
- Full generate -> watermark -> upload -> sign -> write pipeline runs as FastAPI BackgroundTask using supabase_admin (service role)
- Frontend polls GET /avatars/me every 3s, shows "Generating your Ava..." spinner, stops when reference_image_url appears
- 5-minute polling timeout shows user-facing error "Generation timed out -- please try again"
- Regenerate cancels active poll via stopPollingRef, clears old image, fires new POST, restarts polling
- TypeScript build (npm run build) exits 0 -- no type errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Convert generate_reference_image to 202 + BackgroundTasks** - `a6c2856` (feat)
2. **Task 2: Add polling helpers to avatars.ts + rewrite AvatarSetupPage** - `c4d744b` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `backend/app/routers/avatars.py` - Added _generate_reference_image_task background function; endpoint now returns 202 + queues task; BackgroundTasks injected by FastAPI
- `frontend/src/api/avatars.ts` - Renamed generateReferenceImage to triggerReferenceImage (void return); added pollForReferenceImage() with setInterval loop, 3s interval, 5-minute timeout, cleanup function
- `frontend/src/pages/AvatarSetupPage.tsx` - Added useRef stopPollingRef, generating spinner with animate-spin, polling loop on form submit and Regenerate, timeout error state, Try again button

## Decisions Made

- BackgroundTasks parameter is injected by FastAPI automatically without Depends() -- no changes to main.py or any other file needed
- reference_image_url is explicitly set to None before queuing the background task -- this ensures the frontend polling loop waits for the newly generated image rather than immediately resolving with any stale URL
- supabase_admin (service role) used throughout the background task -- consistent with Phase 2 service-role-for-server-ops decision; no user JWT is available in background task context
- Background task exceptions are swallowed after logging -- the task must not crash the event loop; the frontend handles the "stuck" state via the 5-minute polling timeout

## Deviations from Plan

None -- plan executed exactly as written.

## Issues Encountered

- The Task 2 automated verification script used `console.assert(!api.includes('generateReferenceImage'), ...)` which fired a false positive because the comment `"NOTE: triggerReferenceImage replaces the old generateReferenceImage"` in avatars.ts contains the substring. The function export was correctly removed; grep confirmed no `export.*generateReferenceImage` exists. All 11 end-to-end checks passed.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- GAP-3 is resolved: reference image generation no longer blocks the HTTP connection
- All three Phase 7 GAPs are now fixed: GAP-1 (full-body prompt, 07-08), GAP-2 (ComfyUI history_v2 delivery, 07-07), GAP-3 (blocking timeout, 07-09)
- Phase 7 is complete pending human verification of the full onboarding flow: navigate to /avatar-setup, fill form, observe spinner, confirm image appears after 60-90s, Regenerate works, "Looks perfect" navigates to /chat

## Self-Check: PASSED

- FOUND: backend/app/routers/avatars.py
- FOUND: frontend/src/api/avatars.ts
- FOUND: frontend/src/pages/AvatarSetupPage.tsx
- FOUND: .planning/phases/07-avatar-system-production/07-09-SUMMARY.md
- Commit a6c2856: feat(07-09): convert generate_reference_image to 202 + BackgroundTasks
- Commit c4d744b: feat(07-09): add polling helpers to avatars.ts + rewrite AvatarSetupPage with polling loop

---
*Phase: 07-avatar-system-production*
*Completed: 2026-03-02*
