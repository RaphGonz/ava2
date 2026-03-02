---
phase: 07-avatar-system-production
plan: 08
subsystem: api
tags: [comfyui, prompt-engineering, image-generation, avatar]

# Dependency graph
requires:
  - phase: 07-07-avatar-system-production
    provides: ComfyUI delivery fix (GAP-2) — history_v2 prompt_id unwrap

provides:
  - Full-body composition directive in build_avatar_prompt() (GAP-1 fix)
  - Portrait bias removed from prompt prefix
  - Reference-image endpoint passes full-body scene_description

affects: [processor.py, all ComfyUI image generation calls]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Full-body composition directive appended in build_avatar_prompt() before quality anchors — always active regardless of caller's scene_description"

key-files:
  created: []
  modified:
    - backend/app/services/image/prompt_builder.py
    - backend/app/routers/avatars.py

key-decisions:
  - "Full-body directive appended in build_avatar_prompt() (not in callers) — ensures processor.py LLM intimate-mode photos also get full-body framing without any changes to processor.py"
  - "Safety prefix changed from 'Professional portrait photograph' to 'Professional photograph' — 'portrait' word was priming ComfyUI for face-crop framing"
  - "scene_description in generate_reference_image() changed from 'full face' to 'full body visible, standing' — removes explicit portrait-crop request"

patterns-established:
  - "Composition constraints belong in the prompt builder, not in callers — callers only supply scene context"

requirements-completed: [AVTR-05]

# Metrics
duration: 8min
completed: 2026-03-02
---

# Phase 7 Plan 08: Full-Body Prompt Composition Fix Summary

**Removed portrait/face-crop bias from ComfyUI prompt builder by adding "full body, standing, full-length portrait, head to toe" directive and updating reference-image scene_description from "full face" to "full body visible, standing"**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-02T08:17:10Z
- **Completed:** 2026-03-02T08:24:37Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments

- Removed "portrait photograph" from the safety prefix in prompt_builder.py — word was priming ComfyUI for face-crop framing
- Added `"full body, standing, full-length portrait, head to toe,"` before quality anchors — directive is always appended regardless of caller, so processor.py intimate-mode photos also benefit without any changes
- Updated generate_reference_image() in avatars.py to pass `"neutral background, natural light, full body visible, standing"` instead of `"portrait photo, neutral background, natural light, full face"` — removes the explicit portrait crop request
- All automated assertions pass: full-body directive present, no portrait bias in prefix, avatar fields included, scene_description included

## Task Commits

Each task was committed atomically:

1. **Task 1: Add full-body composition directive to build_avatar_prompt() and fix scene_description in avatars.py** - `93fc6a5` (feat)

## Files Created/Modified

- `backend/app/services/image/prompt_builder.py` - Updated module docstring to reference ComfyUI; replaced "portrait photograph" prefix with "photograph"; added full-body composition directive before quality anchors
- `backend/app/routers/avatars.py` - Updated generate_reference_image() scene_description from "full face" to "full body visible, standing"

## Decisions Made

- Full-body directive placed in build_avatar_prompt() (not callers) so processor.py LLM intimate-mode photos automatically get full-body framing without any changes to processor.py
- "Portrait photograph" word removed from prefix because it was priming the model for portrait/face framing even before the scene_description was evaluated

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- GAP-1 (full-body prompt fix) and GAP-2 (ComfyUI delivery fix from 07-07) are both resolved
- Phase 7 is ready for human verification: generate a new reference image via /avatar-setup and confirm the avatar appears head-to-toe on a neutral background
- Requirements AVTR-01 through AVTR-05, INTM-03, ARCH-03, BILL-01, BILL-02 can be marked complete once human verify passes

---
*Phase: 07-avatar-system-production*
*Completed: 2026-03-02*
