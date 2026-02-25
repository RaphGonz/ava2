---
phase: 07-avatar-system-production
plan: 03
subsystem: infra
tags: [bullmq, redis, worker, queue, replicate, pillow, supabase-storage, watermark, photo-delivery]

# Dependency graph
requires:
  - phase: 07-01
    provides: ReplicateProvider, build_avatar_prompt, apply_watermark, ImageProvider Protocol
  - phase: 06-web-app-multi-platform
    provides: messages table (web channel), WhatsAppAdapter send pattern, supabase_admin

provides:
  - BullMQ Queue singleton (get_photo_queue) + enqueue_photo_job() with 3-attempt exponential backoff
  - process_photo_job() — full 8-step pipeline: build prompt -> Replicate -> download -> watermark -> Supabase upload -> signed URL -> audit log -> deliver
  - worker_main.py standalone Docker entry point (python worker_main.py, concurrency=3)
  - Web delivery via [PHOTO]url[/PHOTO] messages table insert
  - WhatsApp delivery via send_whatsapp_message() with phone lookup from user_preferences

affects: [07-04, docker-compose, photo-endpoint]

# Tech tracking
tech-stack:
  added: [bullmq==2.19.5, httpx (already present — used for Replicate CDN download)]
  patterns:
    - Queue-Worker separation: FastAPI imports Queue only; Worker is a separate process (no Worker import in web process)
    - Same connection dict format on both Queue and Worker to avoid job serialization mismatch
    - Deferred imports in worker_main.py main() for env var availability
    - Failure notification on all-retries-exhausted via same delivery channel as success

key-files:
  created:
    - backend/app/services/jobs/__init__.py
    - backend/app/services/jobs/queue.py
    - backend/app/services/jobs/processor.py
    - backend/worker_main.py
  modified:
    - backend/requirements.txt (added bullmq==2.19.5)
    - backend/app/config.py (added redis_url setting, default redis://redis:6379)

key-decisions:
  - "Queue singleton uses lazy init on first call — avoids Redis connection at import time (safe for FastAPI process)"
  - "Worker entry point uses asyncio.Future() to block forever — Docker stop signal kills process cleanly"
  - "Web delivery uses [PHOTO]url[/PHOTO] marker in messages table content — frontend ChatBubble renders as <img>"
  - "WhatsApp delivery fetches phone from user_preferences table via supabase_admin — decoupled from job data"
  - "redis_url added to Settings with default redis://redis:6379 — matches Docker Compose service name"

patterns-established:
  - "Queue-Worker isolation: only enqueue side lives in FastAPI; Worker is always a separate process/container"
  - "Failure notification pattern: attemptsMade >= max_attempts-1 check before notifying user"

requirements-completed: [INTM-03, ARCH-03]

# Metrics
duration: 8min
completed: 2026-02-25
---

# Phase 7 Plan 03: BullMQ Photo Worker Pipeline Summary

**BullMQ queue + 8-step photo pipeline (Replicate FLUX -> Pillow watermark -> Supabase Storage -> signed URL) with web and WhatsApp delivery routing and a standalone Docker worker entry point**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-25T09:33:50Z
- **Completed:** 2026-02-25T09:41:50Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- BullMQ queue singleton with enqueue_photo_job() — attempts=3, exponential backoff (2s/4s/8s), removeOnComplete/removeOnFail cleanup
- Full 8-step processor pipeline: build FLUX prompt -> Replicate generate -> httpx download (immediate, URL expires ~1h) -> Pillow watermark -> Supabase Storage upload (photos/{user_id}/{job_id}.jpg) -> 24h signed URL -> audit log -> channel delivery
- worker_main.py standalone Docker entry point: BullMQ Worker concurrency=3, parses REDIS_URL env var, blocks with asyncio.Future()

## Task Commits

Each task was committed atomically:

1. **Task 1: BullMQ queue singleton + photo job processor (full pipeline)** - `1366cf0` (feat)
2. **Task 2: BullMQ worker entry point (Docker CMD: python worker_main.py)** - `19cb2a3` (feat)

## Files Created/Modified

- `backend/app/services/jobs/__init__.py` - Package marker (empty)
- `backend/app/services/jobs/queue.py` - Queue singleton + enqueue_photo_job() with retry config
- `backend/app/services/jobs/processor.py` - Full 8-step pipeline processor with web/WhatsApp delivery
- `backend/worker_main.py` - Standalone Docker worker entry point, concurrency=3, blocks on asyncio.Future()
- `backend/requirements.txt` - Added bullmq==2.19.5
- `backend/app/config.py` - Added redis_url field (default: redis://redis:6379)

## Decisions Made

- Queue singleton uses lazy init on first call — avoids Redis connection at import time, safe for FastAPI process startup
- Worker entry point uses asyncio.Future() to block forever — Docker stop signal kills process cleanly with no busy-loop
- Web delivery uses [PHOTO]url[/PHOTO] marker inserted as assistant role message in messages table — frontend ChatBubble renders inline
- WhatsApp delivery fetches phone from user_preferences table via supabase_admin (not passed in job data) — decoupled and consistent with existing WhatsAppAdapter pattern
- redis_url added to Settings with default redis://redis:6379 (matches Docker Compose service name) rather than hardcoded in queue.py

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added redis_url to Settings**
- **Found during:** Task 1 (queue.py implementation)
- **Issue:** queue.py references settings.redis_url but the field was missing from Settings class — AttributeError at runtime
- **Fix:** Added redis_url: str = "redis://redis:6379" to Settings in backend/app/config.py
- **Files modified:** backend/app/config.py
- **Verification:** Import succeeds; settings.redis_url accessible
- **Committed in:** 1366cf0 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Essential for runtime correctness. No scope creep.

## Issues Encountered

- bullmq not installed in local dev environment — installed via pip for verification purposes; already added to requirements.txt for Docker deployment

## User Setup Required

None — Redis connection uses Docker Compose default. Worker runs as a separate Docker service.

## Next Phase Readiness

- Worker pipeline complete. Plan 04 can now add the send_photo LLM tool call that triggers enqueue_photo_job()
- Docker Compose worker service definition needed (separate container: python worker_main.py)
- Supabase Storage "photos" bucket must exist before worker processes first job (bucket creation is infra setup)

---
*Phase: 07-avatar-system-production*
*Completed: 2026-02-25*

## Self-Check: PASSED

- FOUND: backend/app/services/jobs/__init__.py
- FOUND: backend/app/services/jobs/queue.py
- FOUND: backend/app/services/jobs/processor.py
- FOUND: backend/worker_main.py
- FOUND: .planning/phases/07-avatar-system-production/07-03-SUMMARY.md
- FOUND: commit 1366cf0 (Task 1)
- FOUND: commit 19cb2a3 (Task 2)
