---
phase: 07-avatar-system-production
plan: 01
subsystem: database, image-generation
tags: [replicate, flux, pillow, watermark, protocol, postgres, rls, stripe]

# Dependency graph
requires:
  - phase: 06-web-app-multi-platform
    provides: preferences schema, platform router, LLMProvider Protocol pattern
  - phase: 03-core-intelligence-mode-switching
    provides: LLMProvider structural typing pattern (mirrored for ImageProvider)
provides:
  - DB migration 004 — avatars.gender, avatars.nationality columns; subscriptions table with RLS
  - ImageProvider Protocol (ARCH-03) — runtime_checkable, mirrors LLMProvider
  - GeneratedImage dataclass with url/model/prompt fields
  - ReplicateProvider — FLUX 1.1 Pro via replicate.async_run()
  - build_avatar_prompt() — combines avatar fields + scene_description into FLUX prompt
  - apply_watermark() — Pillow alpha_composite watermark; returns JPEG bytes
affects: [07-02-chat-service, 07-03-billing, 07-04-storage-photos, 07-05-production]

# Tech tracking
tech-stack:
  added: [replicate, Pillow>=10.0.0]
  patterns:
    - ImageProvider Protocol using structural typing (runtime_checkable) — mirrors LLMProvider from Phase 3
    - Lazy import of replicate inside generate() — defers Python version compatibility issue to call time
    - IF NOT EXISTS guards on all DDL — idempotent migration safe to re-run

key-files:
  created:
    - backend/migrations/004_phase7_avatar_fields.sql
    - backend/app/services/image/__init__.py
    - backend/app/services/image/base.py
    - backend/app/services/image/replicate_provider.py
    - backend/app/services/image/prompt_builder.py
    - backend/app/services/image/watermark.py
  modified:
    - backend/requirements.txt

key-decisions:
  - "ImageProvider Protocol uses structural typing (runtime_checkable) — identical pattern to LLMProvider from Phase 3; swapping providers requires only config change + new concrete class, no inheritance"
  - "replicate module imported lazily inside generate() — defers pydantic v1/Python 3.14 incompatibility to call time; local dev environment (Python 3.14) can import and Protocol-check without running generate()"
  - "subscriptions table uses stripe_price_id column (config-driven) — no hardcoded amounts; supports BILL-02 config-driven pricing"
  - "subscriptions RLS: SELECT own row only; all writes via service role (webhook) — user cannot self-modify subscription status"
  - "apply_watermark() falls back to ImageFont.load_default() if DejaVu font missing — works in all environments including local dev without font installed"

patterns-established:
  - "Lazy SDK import pattern: import heavy/version-sensitive SDKs inside methods not at module top level"
  - "Prompt builder as pure function (no class) — testable without any DB or HTTP dependency"
  - "IF NOT EXISTS + CONSTRAINT IF NOT EXISTS guards on all DDL for idempotent migrations"

requirements-completed: [AVTR-05, ARCH-03]

# Metrics
duration: 8min
completed: 2026-02-25
---

# Phase 7 Plan 01: DB Schema Extensions + ImageProvider Layer Summary

**Idempotent DB migration adding avatar gender/nationality and subscriptions table; swappable ImageProvider Protocol (ARCH-03) with FLUX 1.1 Pro via Replicate, prompt builder combining all avatar fields, and Pillow watermark helper**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-25T09:07:59Z
- **Completed:** 2026-02-25T09:16:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- DB migration 004 ready to apply: adds `gender` and `nationality` columns to `avatars`, creates `subscriptions` table with Stripe fields and RLS (user reads own row; service role writes via webhook)
- `ImageProvider` Protocol (ARCH-03) with `GeneratedImage` dataclass — structural typing mirrors Phase 3 `LLMProvider`, no inheritance required, swappable via config
- `ReplicateProvider` calls `replicate.async_run()` with FLUX 1.1 Pro, returns CDN URL wrapped in `GeneratedImage`
- `build_avatar_prompt()` pure function combines name/age/gender/nationality/physical_description + scene_description with photorealism anchors
- `apply_watermark()` uses Pillow `alpha_composite` for semi-transparent watermark at bottom-right; degrades gracefully when DejaVu font unavailable

## Task Commits

Each task was committed atomically:

1. **Task 1: DB migration — avatar new columns + subscriptions table** - `093c79b` (feat)
2. **Task 2: ImageProvider Protocol + Replicate provider + prompt builder + watermark** - `747f1a5` (feat)

## Files Created/Modified
- `backend/migrations/004_phase7_avatar_fields.sql` — Idempotent migration: ALTER TABLE avatars ADD gender/nationality; CREATE TABLE subscriptions with RLS
- `backend/app/services/image/__init__.py` — Package marker (empty)
- `backend/app/services/image/base.py` — ImageProvider Protocol (runtime_checkable) + GeneratedImage dataclass
- `backend/app/services/image/replicate_provider.py` — ReplicateProvider: FLUX 1.1 Pro via replicate.async_run()
- `backend/app/services/image/prompt_builder.py` — build_avatar_prompt() pure function
- `backend/app/services/image/watermark.py` — apply_watermark() Pillow alpha_composite with font fallback
- `backend/requirements.txt` — Added replicate and Pillow>=10.0.0

## Decisions Made
- `replicate` imported lazily inside `generate()` (not at module top-level) — the local environment runs Python 3.14 which triggers a pydantic v1 incompatibility in the replicate package at import time. Lazy import defers this to actual API call time; all Protocol checks and import verification pass without issue. Production Docker will use Python 3.11/3.12 where replicate installs cleanly.
- `subscriptions` table stores `stripe_price_id` (no amounts) — BILL-02 config-driven pricing requirement.
- RLS on subscriptions: user can only SELECT own row; INSERT/UPDATE happens only via service role in Stripe webhook handler.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Lazy import of replicate to fix Python 3.14 pydantic v1 incompatibility**
- **Found during:** Task 2 (ImageProvider verification)
- **Issue:** `import replicate` at module top-level crashes on Python 3.14 (local env) because `replicate` uses `pydantic.v1` which is incompatible with Python 3.14. The verification command `from app.services.image.replicate_provider import ReplicateProvider` failed with `pydantic.v1.errors.ConfigError`.
- **Fix:** Moved `import replicate` from module top-level into the `generate()` method body — defers the import to actual API call time. All import checks, Protocol isinstance checks, and build_avatar_prompt tests pass without needing replicate to be importable.
- **Files modified:** `backend/app/services/image/replicate_provider.py`
- **Verification:** All verification checks pass: imports OK, Protocol isinstance OK, prompt builder OK
- **Committed in:** `747f1a5` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking — environment compatibility)
**Impact on plan:** Lazy import is a standard Python pattern; no behavior change in production. All success criteria met.

## Issues Encountered
- Python 3.14 local environment incompatible with `replicate` package's use of `pydantic.v1`. Resolved via lazy import (Rule 3). Production environment (Python 3.11/3.12 in Docker) unaffected.

## User Setup Required

The DB migration must be applied manually in the Supabase Dashboard SQL editor:

1. Navigate to Supabase Dashboard → Project → SQL Editor → New query
2. Paste the full contents of `backend/migrations/004_phase7_avatar_fields.sql`
3. Click "Run"

Verify with:
```sql
SELECT column_name FROM information_schema.columns
WHERE table_name = 'avatars' AND column_name IN ('gender', 'nationality');
-- Should return 2 rows

SELECT table_name FROM information_schema.tables
WHERE table_name = 'subscriptions';
-- Should return 1 row
```

## Next Phase Readiness
- DB schema ready: gender/nationality on avatars, subscriptions table — billing (07-03) and avatar model (07-02) can proceed
- ImageProvider layer complete: ReplicateProvider, prompt builder, watermark — photo job worker (07-04) can use these directly
- `replicate` and `Pillow` added to requirements.txt — Docker build will install them automatically

---
*Phase: 07-avatar-system-production*
*Completed: 2026-02-25*

## Self-Check: PASSED

- FOUND: backend/migrations/004_phase7_avatar_fields.sql
- FOUND: backend/app/services/image/base.py
- FOUND: backend/app/services/image/replicate_provider.py
- FOUND: backend/app/services/image/prompt_builder.py
- FOUND: backend/app/services/image/watermark.py
- FOUND: .planning/phases/07-avatar-system-production/07-01-SUMMARY.md
- FOUND: commit 093c79b (Task 1)
- FOUND: commit 747f1a5 (Task 2)
