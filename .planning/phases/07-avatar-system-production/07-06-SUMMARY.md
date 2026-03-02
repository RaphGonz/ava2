---
phase: 07-avatar-system-production
plan: 06
subsystem: testing
tags: [verification, avatar, image-generation, comfyui, prompt-builder, delivery]

# Dependency graph
requires:
  - phase: 07-avatar-system-production
    provides: Avatar system, billing, Docker Compose, worker pipeline, AvatarSetupPage
  - phase: 07.1-switch-image-generation-to-comfyui-cloud
    provides: ComfyUIProvider, 4-step history_v2 flow, seed randomization

provides:
  - 12 automated structural checks passing (Phase 7 structural integrity confirmed)
  - 2 implementation gaps identified for gap-closure cycle

affects: [gap-closure, 07.1-gap-closure, prompt-builder, comfyui-delivery]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Verification plan pattern: automated checks (Task 1) + human walkthrough (Task 2)"

key-files:
  created:
    - .planning/phases/07-avatar-system-production/07-06-SUMMARY.md
  modified: []

key-decisions:
  - "Plan 07-06 declared PARTIAL: Task 1 (automated) passed; Task 2 (human) revealed 2 blocking gaps — image quality and delivery"
  - "Gaps forwarded to gap-closure cycle rather than inline fix, to keep verification plan scope clean"

patterns-established:
  - "Gap-closure cycle: verification plan documents gaps; separate fix plans address each gap atomically"

requirements-completed: []

gaps_found:
  - id: GAP-1
    title: "Prompt builder generates portrait-only images, not full body"
    file: backend/app/services/image/prompt_builder.py
    severity: high
    description: >
      The generated reference image is portrait/head-and-shoulders only.
      The prompt_builder.py does not include composition directives to request
      a full-body shot. The avatar setup form collects gender, nationality, and
      appearance description — but the assembled prompt lacks framing instructions
      such as "full body", "standing", "full-length portrait".
    impact: >
      Avatar reference image does not represent the avatar's full appearance.
      Users cannot meaningfully evaluate the generated image before approving it.
      Downstream intimate-mode photo generation also inherits the wrong composition.
    fix_hint: >
      Add a composition suffix to the prompt returned by build_avatar_prompt()
      that always includes full-body framing (e.g., "full body, standing, full-length
      portrait, head to toe").

  - id: GAP-2
    title: "ComfyUI image delivery broken — result never returned to app; avatar stuck in pending state"
    file: backend/app/routers/avatars.py
    severity: critical
    description: >
      ComfyUI successfully generates the image (confirmed on the ComfyUI side),
      but the result is never delivered back to the application.
      The avatar record in the database remains in a generating/pending state indefinitely.
      The AvatarSetupPage becomes locked/stuck waiting for the avatar status to transition
      to complete — a transition that never occurs.
      Root cause is likely in the job completion callback or the polling/webhook path
      from the worker back to avatars.py (status update + reference_image_url write).
    impact: >
      Avatar onboarding is completely blocked. Users cannot complete setup, approve their
      reference image, or proceed to /chat. The entire Phase 7 avatar flow is non-functional.
    fix_hint: >
      Investigate the worker processor (backend/app/services/jobs/processor.py) and
      the avatars router (backend/app/routers/avatars.py) to confirm:
      (1) the worker writes the completed image URL back to the avatar row,
      (2) the avatar status is updated from "generating" to "complete",
      (3) the AvatarSetupPage polls or reacts to the status change correctly.

# Metrics
duration: partial
completed: 2026-03-02
---

# Phase 7 Plan 06: End-to-End Verification Summary

**12 automated structural checks passed; human walkthrough blocked by 2 critical implementation gaps in ComfyUI delivery and prompt composition**

## Performance

- **Duration:** partial (Task 1 complete, Task 2 blocked)
- **Started:** 2026-03-02
- **Completed:** 2026-03-02 (partial)
- **Tasks:** 1/2 (Task 1 automated — PASS; Task 2 human verify — PARTIAL, 2 gaps found)
- **Files modified:** 0 (verification-only plan)

## Accomplishments

- All 12 automated structural checks passed (Python imports, Protocol isinstance, model fields, config, billing routes, send_photo tool, full test suite, frontend build, Docker Compose config, migration SQL, .env.example completeness, worker_main.py syntax)
- 2 implementation gaps identified and documented for the gap-closure cycle
- Phase 7 structural integrity confirmed — gaps are behavioral/integration issues, not missing scaffolding

## Task Commits

1. **Task 1: Automated verification — 12 structural checks** - `db7afea` (chore: add REPLICATE_API_TOKEN to .env.example, all checks passing)
2. **Task 2: Human verification** - partial — gaps found, no approve commit

**Plan metadata:** (this commit)

## Files Created/Modified

- `.planning/phases/07-avatar-system-production/07-06-SUMMARY.md` - This summary with gap documentation

## Decisions Made

- Plan 07-06 declared PARTIAL: automated checks pass but human walkthrough exposed 2 blocking implementation gaps
- Gaps forwarded to gap-closure cycle; no inline fixes applied to keep verification plan scope clean
- Requirements AVTR-01 through AVTR-05, INTM-03, ARCH-03, BILL-01, BILL-02 cannot be marked complete until gaps are resolved

## Gaps Found

### GAP-1: Prompt builder generates portrait-only images (non-full-body)

- **Severity:** High
- **Found during:** Task 2 — Test 1 (Avatar onboarding)
- **File:** `backend/app/services/image/prompt_builder.py`
- **Issue:** `build_avatar_prompt()` assembles a prompt from the avatar fields (name, age, gender, nationality, appearance description, personality) but does not include any composition or framing directives. ComfyUI produces a head-and-shoulders / portrait crop rather than a full-body image.
- **Impact:** Avatar reference image is incomplete; users cannot evaluate full appearance. Downstream photo generation inherits wrong framing.
- **Proposed fix:** Append a composition suffix to the prompt: `"full body, standing, full-length portrait, head to toe"` — or an equivalent framing directive that the ComfyUI workflow responds to.

### GAP-2: ComfyUI image delivery broken — avatar stuck in pending state (CRITICAL)

- **Severity:** Critical
- **Found during:** Task 2 — Test 1 (Avatar onboarding)
- **Files:** `backend/app/services/jobs/processor.py`, `backend/app/routers/avatars.py`
- **Issue:** ComfyUI generates the image successfully (confirmed on ComfyUI dashboard), but the result is never written back to the application. The avatar database row remains in `generating` / `pending` status. The `AvatarSetupPage` polls for status change but receives no update — the page locks and the user cannot proceed.
- **Impact:** Avatar onboarding is completely blocked. No user can complete the setup flow. Tests 2-5 of the human walkthrough were not reachable due to this blocker.
- **Proposed fix:** Trace the callback/polling path in `processor.py`: confirm the worker (a) downloads the image, (b) stores it to Supabase Storage, (c) writes `reference_image_url` + status `"complete"` back to the avatar row. Also confirm `AvatarSetupPage` reacts to the status transition (polling interval, query invalidation, or WebSocket).

## Deviations from Plan

None — this is a verification plan; no code was written. Gaps found during human verification are documented above for gap-closure.

## Issues Encountered

- Tests 2-5 (subscription gate, ARCH-03 terminal check, Docker Compose, Sentry empty DSN) were not completed due to the blocker from GAP-2. These tests should be re-run after both gaps are resolved.

## Next Phase Readiness

**Blocked.** Phase 7 cannot be declared complete until:

1. GAP-2 (delivery) is fixed — avatar setup must complete end-to-end
2. GAP-1 (composition) is fixed — reference image must be full-body
3. Tests 2-5 of the human walkthrough are re-run and pass

Gap-closure plans should address GAP-2 first (critical — blocks everything) then GAP-1 (high — affects image quality).

---
*Phase: 07-avatar-system-production*
*Completed: 2026-03-02 (partial)*
