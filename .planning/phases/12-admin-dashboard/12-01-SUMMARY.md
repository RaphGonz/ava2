---
phase: 12-admin-dashboard
plan: "01"
subsystem: backend
tags: [admin, access-control, metrics, fastapi, supabase]
dependency_graph:
  requires: [billing-router, dependencies-get_current_user, database-supabase_admin, usage_events-table]
  provides: [admin-router, require_admin-dependency, GET-admin-metrics]
  affects: [main.py-router-registration, plan-03-admin-frontend]
tech_stack:
  added: []
  patterns: [FastAPI-Depends-chaining, service-role-bypass-RLS, user_metadata-admin-flag]
key_files:
  created:
    - backend/app/routers/admin.py
    - backend/tests/test_admin_access.py
  modified:
    - backend/app/main.py
decisions:
  - "require_admin reads user_metadata.is_admin (not app_metadata) — locked decision from CONTEXT.md"
  - "require_admin is defined in admin.py not dependencies.py — avoids global dependency anti-pattern"
  - "active_subscriptions d7/d30 filters by both status=active AND created_at >= cutoff — not a historical snapshot"
  - "active_users counts users with last_sign_in_at; new users who never signed in counted at creation time"
  - "Pagination deferred for >1000 users — TODO comment in _get_user_metrics"
metrics:
  duration_minutes: 29
  tasks_completed: 2
  files_created: 2
  files_modified: 1
  completed_date: "2026-03-10"
---

# Phase 12 Plan 01: Admin Backend API Summary

**One-liner:** FastAPI admin router with `require_admin` dependency (reads `user_metadata.is_admin`) and `GET /admin/metrics` returning 5 metrics (active_users, messages_sent, photos_generated, active_subscriptions, new_signups) across 3 time windows.

## What Was Built

### backend/app/routers/admin.py

- `require_admin(user=Depends(get_current_user))` — async FastAPI dependency that raises HTTP 403 if `(user.user_metadata or {}).get("is_admin", False)` is falsy. Reads `user_metadata` (not `app_metadata`) per locked decision.
- `GET /admin/metrics` — operator-only endpoint returning 5 product health metrics.

### backend/tests/test_admin_access.py

4 pytest tests for `require_admin`:
1. `test_require_admin_allows_admin_true` — `{"is_admin": True}` returns user object
2. `test_require_admin_blocks_non_admin` — empty `{}` metadata raises 403
3. `test_require_admin_blocks_admin_false` — `{"is_admin": False}` raises 403
4. `test_require_admin_handles_null_metadata` — `None` metadata raises 403 (handled via `or {}`)

### backend/app/main.py

Added:
```python
from app.routers import admin
...
app.include_router(admin.router)
```

## API Response Shape for /admin/metrics (Plan 03 Reference)

```json
{
  "active_users":         {"d7": 0, "d30": 0, "all": 0},
  "messages_sent":        {"d7": 0, "d30": 0, "all": 0},
  "photos_generated":     {"d7": 0, "d30": 0, "all": 0},
  "active_subscriptions": {"d7": 0, "d30": 0, "all": 0},
  "new_signups":          {"d7": 0, "d30": 0, "all": 0},
  "fetched_at": "2026-03-10T07:46:00.000000+00:00"
}
```

**Data sources:**
- `active_users` + `new_signups`: `supabase_admin.auth.admin.list_users()` — counts by `last_sign_in_at` / `created_at`
- `messages_sent` + `photos_generated`: `usage_events` table filtered by `event_type` and `created_at >= cutoff`
- `active_subscriptions`: `subscriptions` table filtered by `status='active'` (+ `created_at` for d7/d30)

**Access control:**
- 401 Unauthorized — no/invalid JWT (from `get_current_user`)
- 403 Forbidden — valid JWT but no `user_metadata.is_admin: true`
- 200 OK — admin user

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Settings crash due to stale STRIPE_PRICE_ID in .env (initially)**

- **Found during:** Task 1 first test run
- **Issue:** Test collection failed with `pydantic_core.ValidationError: stripe_price_id Extra inputs are not permitted`. The `.env` template line `STRIPE_PRICE_ID=price_...` was being parsed by pydantic-settings as a real value.
- **Resolution:** Investigation revealed the `.env` file was already updated by Plan 11 to use the 3-tier fields (`STRIPE_PRICE_ID_BASIC`, `STRIPE_PRICE_ID_PREMIUM`, `STRIPE_PRICE_ID_ELITE`). The apparent crash was a git stash operation side-effect during diagnosis. `config.py` required no permanent change — `extra="ignore"` was NOT added (the `.env` was already clean).
- **Files modified:** None permanently
- **Commit:** N/A (reverted during investigation)

## Verification Results

```
# Admin access tests
cd backend && python -m pytest tests/test_admin_access.py -x -q
4 passed, 23 warnings in 2.04s

# Admin router import
python -c "from app.routers.admin import router, require_admin; print('admin.py imports OK')"
admin.py imports OK

# Admin router registered
grep "admin" backend/app/main.py | grep include_router
app.include_router(admin.router)

# Full test suite (comfyui test pre-existing failure excluded)
cd backend && python -m pytest tests/ --ignore=tests/test_comfyui_provider.py -q
58 passed, 25 warnings in 14.14s
```

**Pre-existing failure:** `tests/test_comfyui_provider.py::test_t2i_generate_returns_image_bytes` — confirmed failing before this plan via `git stash` check. Out of scope.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | bb52515 | test(12-01): add require_admin access control tests |
| Task 2 | 3b62864 | feat(12-01): create admin router with require_admin dependency and /admin/metrics endpoint |

## Self-Check: PASSED

All files present: backend/app/routers/admin.py, backend/tests/test_admin_access.py, 12-01-SUMMARY.md
All commits verified: bb52515 (test), 3b62864 (feat)
