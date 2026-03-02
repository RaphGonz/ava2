---
phase: 07-avatar-system-production
plan: 07
subsystem: api
tags: [comfyui, httpx, image-generation, async]

# Dependency graph
requires:
  - phase: 07.1-switch-image-generation-to-comfyui-cloud
    provides: ComfyUIProvider with 4-step generation flow (submit, poll, history_v2, view)
provides:
  - Fixed ComfyUIProvider._fetch_history_and_download — unwraps prompt_id key from history_v2 response
  - Fixed ComfyUIProvider._download_output — accepts pre-extracted outputs dict
  - Per-operation httpx timeouts (connect/read/write/pool) replacing single 60s timeout
affects: [avatar-onboarding, AvatarSetupPage, AVTR-05, INTM-03]

# Tech tracking
tech-stack:
  added: []
  patterns: [ComfyUI history_v2 response is prompt_id-keyed at root — always unwrap before reading outputs]

key-files:
  created: []
  modified:
    - backend/app/services/image/comfyui_provider.py

key-decisions:
  - "history_v2 response wrapped under prompt_id key — job_data = history_data.get(prompt_id, {}) before accessing outputs"
  - "_download_output now accepts pre-extracted outputs dict — no double .get('outputs') lookup"
  - "httpx.AsyncClient timeout changed from single 60s to per-operation: connect=10s, read=120s, write=30s, pool=10s — large image downloads need 120s read budget"
  - "Warning log includes raw history_data keys to surface key format surprises in future"

patterns-established:
  - "ComfyUI history_v2 unwrap pattern: job_data = history_data.get(prompt_id, {}); outputs = job_data.get('outputs', {})"

requirements-completed: [AVTR-05, INTM-03]

# Metrics
duration: 5min
completed: 2026-03-02
---

# Phase 7 Plan 07: ComfyUI history_v2 prompt_id unwrap fix Summary

**Fixed ComfyUIProvider to unwrap the prompt_id-keyed root of history_v2 response before reading outputs — unblocking avatar image delivery that was silently returning empty results and crashing with HTTP 500**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-02T07:56:32Z
- **Completed:** 2026-03-02T08:01:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Fixed critical GAP-2: `_fetch_history_and_download` now correctly reads `history_data[prompt_id]["outputs"]` instead of `history_data["outputs"]` (which was always `{}`)
- Fixed `_download_output` to accept the already-extracted `outputs` dict directly, eliminating the double `.get("outputs")` lookup that was a dead code path
- Replaced single 60s httpx timeout with per-operation timeouts (connect=10s, read=120s, write=30s, pool=10s) to handle large image downloads on cold ComfyUI starts
- Updated module docstring and warning log to accurately describe the history_v2 response format
- Error log now includes available output node keys to aid debugging of node key mismatches

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix _fetch_history_and_download — unwrap prompt_id key from history_v2 response** - `ce1834c` (fix)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified
- `backend/app/services/image/comfyui_provider.py` - Fixed history_v2 prompt_id unwrap, _download_output signature, httpx timeout, module docstring

## Decisions Made
- `history_data.get(prompt_id, {})` pattern used to unwrap the outer key — handles case where job_data is absent gracefully without crashing
- `_download_output` signature changed from `history_data: dict` to `outputs: dict` — caller now responsible for passing the pre-extracted outputs, keeping method focused on a single concern
- httpx read timeout raised to 120s — ComfyUI large image downloads (multi-MB PNG files) can exceed 60s on cold GPU starts
- Warning log now includes `Raw keys: {list(history_data.keys())}` — surfaces the actual top-level key format if it differs from the expected prompt_id pattern

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- GAP-2 (ComfyUI delivery broken) is now closed
- Avatar onboarding can complete end-to-end: ComfyUI generates image, history_v2 response is correctly parsed, image bytes returned, avatar row updated with reference_image_url
- GAP-1 (portrait-only prompt) addressed in 07-06 SUMMARY as separate gap-closure — prompt_builder.py fix
- Phase 7 gap-closure is complete; human verification of the full onboarding flow (07-06 Task 2 Tests 1-5) can now proceed

---
*Phase: 07-avatar-system-production*
*Completed: 2026-03-02*

## Self-Check: PASSED
- FOUND: backend/app/services/image/comfyui_provider.py
- FOUND: .planning/phases/07-avatar-system-production/07-07-SUMMARY.md
- FOUND: commit ce1834c (fix(07-07): unwrap prompt_id key from history_v2 response)
