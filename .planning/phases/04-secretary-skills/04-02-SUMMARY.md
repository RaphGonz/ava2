---
phase: 04-secretary-skills
plan: "02"
subsystem: auth
tags: [google-oauth, oauth2, calendar, supabase, rls, fastapi]

# Dependency graph
requires:
  - phase: 02-infrastructure-user-management
    provides: supabase_admin client (service role) and database.py pattern
  - phase: 03-core-intelligence-mode-switching
    provides: ChatService pipeline that calendar_skill.py will integrate with
provides:
  - google_calendar_tokens Supabase table with RLS (user owns their own token row)
  - token_store.py: get_calendar_tokens(), save_calendar_tokens(), delete_calendar_tokens()
  - flow.py: get_auth_url(), exchange_code_for_tokens(), get_credentials_for_user()
  - GET /auth/google/connect — returns OAuth consent URL for user to visit
  - GET /auth/google/callback — exchanges authorization code, persists tokens
affects: [04-secretary-skills]

# Tech tracking
tech-stack:
  added:
    - google-auth-oauthlib>=1.0.0
    - google-api-python-client>=2.0.0
    - google-auth-httplib2>=0.2.0
  patterns:
    - Flow.from_client_config() web server OAuth2 pattern (not InstalledAppFlow)
    - asyncio.to_thread() for synchronous Google Auth HTTP calls (non-blocking)
    - supabase_admin for server-side token storage (consistent with Phase 2 pattern)
    - state param carries user_id through OAuth round-trip

key-files:
  created:
    - backend/migrations/002_google_calendar_tokens.sql
    - backend/app/services/google_auth/__init__.py
    - backend/app/services/google_auth/token_store.py
    - backend/app/services/google_auth/flow.py
    - backend/app/routers/google_oauth.py
  modified:
    - backend/app/main.py

key-decisions:
  - "Flow.from_client_config() used instead of InstalledAppFlow — web server OAuth2 pattern is correct for server-side token exchange"
  - "asyncio.to_thread() wraps all synchronous Google Auth calls (fetch_token, creds.refresh) to avoid blocking the FastAPI event loop"
  - "supabase_admin (service role) used for token storage — webhook/skill pipeline runs without user JWT in scope, consistent with Phase 2 server-side op pattern"
  - "state param carries user_id through OAuth consent URL round-trip — security note added to connect route (should be signed in production)"
  - "calendar.events scope only (not full calendar) — least privilege per RESEARCH.md anti-patterns"
  - "google_client_id, google_client_secret, google_oauth_redirect_uri added to Settings with empty string defaults — missing credentials return 500 at OAuth call site, not at startup"

patterns-established:
  - "Google OAuth web server pattern: Flow.from_client_config() with redirect_uri, access_type=offline, prompt=consent"
  - "Blocking HTTP in async: always wrap synchronous google-auth calls in asyncio.to_thread()"
  - "Token persistence: upsert row keyed by user_id into google_calendar_tokens via supabase_admin"

requirements-completed: [SECR-01, SECR-02]

# Metrics
duration: 14min
completed: 2026-02-24
---

# Phase 4 Plan 02: Google OAuth Infrastructure Summary

**Google Calendar OAuth infrastructure: per-user token storage in Supabase, web server OAuth2 flow with google-auth-oauthlib, and FastAPI /auth/google routes.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-02-24T09:00:11Z
- **Completed:** 2026-02-24T09:14:09Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Created `002_google_calendar_tokens.sql` migration with RLS policy ensuring each user can only read/write their own token row
- Built `google_auth` service package with `token_store.py` (Supabase CRUD) and `flow.py` (OAuth2 web server flow with auto-refresh)
- Exposed `GET /auth/google/connect` and `GET /auth/google/callback` routes; all 20 existing Phase 3 tests continue to pass

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed google-auth-oauthlib and google-api-python-client**
- **Found during:** Task 2 verification setup
- **Issue:** `google_auth_oauthlib` and `google.oauth2.credentials` were not installed in the Python environment; flow.py would fail at import
- **Fix:** Ran `pip install google-auth-oauthlib google-auth google-api-python-client`; requirements.txt already contained these packages (pre-populated by the planner for Phase 4)
- **Files modified:** None (requirements.txt was already correct)
- **Commit:** N/A (pip install only, no code change)

## Task Commits

Each task was committed atomically:

1. **Task 1: DB migration for google_calendar_tokens and google_auth token store service** - `90627cf` (feat)
2. **Task 2: Google OAuth flow service and /auth/google router** - `601b8b3` (feat)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified

- `backend/migrations/002_google_calendar_tokens.sql` - CREATE TABLE google_calendar_tokens with UUID PK, RLS policy "user owns google token"
- `backend/app/services/google_auth/__init__.py` - Empty package marker for google_auth service module
- `backend/app/services/google_auth/token_store.py` - get_calendar_tokens(), save_calendar_tokens(), delete_calendar_tokens() using supabase_admin
- `backend/app/services/google_auth/flow.py` - get_auth_url(), exchange_code_for_tokens(), get_credentials_for_user() with asyncio.to_thread() wrapping
- `backend/app/routers/google_oauth.py` - GET /auth/google/connect and GET /auth/google/callback FastAPI routes
- `backend/app/main.py` - Added import and include_router for google_oauth

## Verification

All Phase 3 tests pass:
```
20 passed in 0.09s
```

Google OAuth routes confirmed registered:
```python
['/auth/google/connect', '/auth/google/callback']
```

## User Setup Required

The SQL in `002_google_calendar_tokens.sql` must be run against Supabase before the calendar skill can store tokens:
```sql
-- Run in Supabase Dashboard -> SQL Editor
-- Contents of backend/migrations/002_google_calendar_tokens.sql
```

Google OAuth credentials must be added to `backend/.env`:
```
GOOGLE_CLIENT_ID=<from Google Cloud Console>
GOOGLE_CLIENT_SECRET=<from Google Cloud Console>
GOOGLE_OAUTH_REDIRECT_URI=https://<your-domain>/auth/google/callback
```

## Self-Check: PASSED

- FOUND: backend/migrations/002_google_calendar_tokens.sql
- FOUND: backend/app/services/google_auth/token_store.py
- FOUND: backend/app/services/google_auth/flow.py
- FOUND: backend/app/routers/google_oauth.py
- FOUND: .planning/phases/04-secretary-skills/04-02-SUMMARY.md
- FOUND commit: 90627cf (feat: add google_calendar_tokens migration and token_store service)
- FOUND commit: 601b8b3 (feat: add Google OAuth flow service and /auth/google router)
