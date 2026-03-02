---
phase: 02-infrastructure-user-management
plan: 01
subsystem: infra
tags: [fastapi, supabase, postgresql, rls, pydantic-settings, uvicorn, httpx, whatsapp]

# Dependency graph
requires:
  - phase: 01-foundation-compliance
    provides: Avatar age floor decision (age >= 20) and compliance decisions used in CHECK constraint
provides:
  - FastAPI backend scaffold with all required project structure
  - Pydantic BaseSettings config loading all service URLs from env vars
  - Two Supabase client singletons (anon/RLS and service role)
  - Per-request authenticated Supabase client via get_authed_supabase dependency
  - Complete Supabase schema migration (enums, tables, RLS, indexes) in one transaction
affects: [02-02, 02-03, 02-04, 03-core-intelligence, all-backend-phases]

# Tech tracking
tech-stack:
  added:
    - supabase==2.28.0
    - fastapi>=0.115.0
    - uvicorn[standard]>=0.30.0
    - httpx>=0.27.0
    - python-dotenv>=1.0.0
    - pydantic-settings>=2.0.0
    - python-jose[cryptography]>=3.0.0
    - gunicorn>=22.0.0
  patterns:
    - Pydantic BaseSettings with SettingsConfigDict(env_file=".env") for all config
    - lru_cache on get_settings() for singleton Settings instance
    - Two Supabase client singletons: anon key (RLS enforced) and service role (admin bypass)
    - Per-query postgrest.auth(token) pattern for RLS context (avoids set_auth() thread-safety issues)
    - FastAPI Depends() for get_current_user and get_authed_supabase injection
    - RLS policies using (SELECT auth.uid()) wrapper for ~95% performance improvement
    - Partial index on whatsapp_phone WHERE NOT NULL for efficient webhook phone lookup

key-files:
  created:
    - backend/app/main.py
    - backend/app/config.py
    - backend/app/database.py
    - backend/app/dependencies.py
    - backend/app/routers/auth.py
    - backend/app/routers/avatars.py
    - backend/app/routers/preferences.py
    - backend/app/routers/webhook.py
    - backend/app/routers/health.py
    - backend/app/models/auth.py
    - backend/app/models/avatar.py
    - backend/app/models/message.py
    - backend/app/services/whatsapp.py
    - backend/app/services/user_lookup.py
    - backend/requirements.txt
    - backend/.env.example
    - backend/Makefile
    - backend/templates/auth.html
    - backend/migrations/001_initial_schema.sql
  modified: []

key-decisions:
  - "Used postgrest.auth(token) per-query pattern instead of set_auth() on singleton to avoid JWT context bleed between concurrent async requests"
  - "Avatar age CHECK constraint (age >= 20) at DB level mirrors Phase 1 compliance decision; also validated at application layer in AvatarCreate model"
  - "8 RLS policies (not 9 as stated in plan — plan had typo; RESEARCH.md schema correctly shows 3+3+2=8 policies)"
  - "service role client (supabase_admin) reserved exclusively for webhook phone lookup — never used for user-facing endpoints"
  - "Partial index on whatsapp_phone WHERE NOT NULL avoids full table scans on every incoming WhatsApp message"

patterns-established:
  - "Pattern: All env vars loaded via pydantic-settings BaseSettings — no hardcoded URLs or secrets anywhere"
  - "Pattern: Two Supabase clients — supabase_client (anon, RLS) for user ops; supabase_admin (service role) for server ops"
  - "Pattern: get_authed_supabase returns AuthedClient wrapper using postgrest.auth(token) per table operation"
  - "Pattern: Webhook always returns HTTP 200 to Meta — exceptions logged internally, never propagated to HTTP response"

requirements-completed: [ARCH-04, USER-02]

# Metrics
duration: 19min
completed: 2026-02-23
---

# Phase 2 Plan 01: FastAPI/Supabase Backend Scaffold Summary

**FastAPI backend scaffold with pydantic-settings config, dual Supabase clients (anon + service role), and complete Supabase schema migration (3 tables, 3 enums, 8 RLS policies, 5 indexes) in one transaction**

## Performance

- **Duration:** 19 min
- **Started:** 2026-02-23T12:59:05Z
- **Completed:** 2026-02-23T13:18:10Z
- **Tasks:** 2
- **Files modified:** 23 (all created new)

## Accomplishments

- Complete FastAPI backend project scaffold with all required directories and files
- Two Supabase client singletons: anon key client (user-facing, RLS enforced) and service role client (admin/webhook ops)
- Atomic Supabase schema migration wrapping all DDL in BEGIN/COMMIT: 3 enums, 3 tables with correct constraints, 8 RLS policies, 5 indexes including partial index on whatsapp_phone

## Task Commits

Each task was committed atomically:

1. **Task 1: Backend project scaffold** - `b36897e` (feat)
2. **Task 2: Supabase schema migration** - `2e4916a` (feat)

**Plan metadata:** (docs commit — pending)

## Files Created/Modified

- `backend/app/config.py` - Pydantic BaseSettings with 7 required env vars + lru_cache get_settings()
- `backend/app/database.py` - supabase_client (anon) and supabase_admin (service role) singletons
- `backend/app/dependencies.py` - get_current_user and get_authed_supabase (per-query postgrest.auth pattern)
- `backend/app/main.py` - FastAPI app with CORS, health route, all router mounts
- `backend/app/routers/auth.py` - POST /auth/signup, POST /auth/signin
- `backend/app/routers/avatars.py` - POST /avatars, GET /avatars/me
- `backend/app/routers/preferences.py` - PUT /preferences/whatsapp, GET /preferences/me
- `backend/app/routers/webhook.py` - GET /webhook (verify), POST /webhook (echo handler)
- `backend/app/routers/health.py` - GET /health
- `backend/app/models/auth.py` - SignupRequest, SigninRequest, TokenResponse
- `backend/app/models/avatar.py` - AvatarCreate (age >= 20 validator), AvatarResponse, PersonalityType enum
- `backend/app/models/message.py` - MessageCreate, MessageResponse, MessageChannel/Role enums
- `backend/app/services/whatsapp.py` - send_whatsapp_message() via Meta Graph API, parse_incoming_message()
- `backend/app/services/user_lookup.py` - lookup_user_by_phone() using supabase_admin
- `backend/requirements.txt` - 8 packages with pinned/minimum versions
- `backend/.env.example` - 7 env var templates with source comments
- `backend/Makefile` - dev, prod, install, ngrok targets
- `backend/templates/auth.html` - minimal Phase 2 test UI (no styling)
- `backend/migrations/001_initial_schema.sql` - complete schema: uuid-ossp, 3 enums, 3 tables, RLS, 5 indexes

## Decisions Made

- **postgrest.auth(token) over set_auth():** Used per-query JWT scoping via `supabase_client.postgrest.auth(token).from_(table)` instead of `set_auth()` on the singleton. This avoids the documented thread-safety risk in async contexts where concurrent requests could overwrite each other's JWT context.
- **Age validation at two layers:** CHECK (age >= 20) enforced at DB level (per Phase 1 compliance decision) AND validated in AvatarCreate Pydantic model. DB constraint is the source of truth; app validation provides early feedback.
- **8 RLS policies:** Plan specified "9" but RESEARCH.md schema correctly shows 8 (3+3+2 for user_preferences + avatars + messages). Implemented per RESEARCH.md exactly.

## Deviations from Plan

None - plan executed exactly as written. The "9 RLS policies" vs "8 actual" is a pre-existing typo in the plan document, not a deviation — the schema verbatim from RESEARCH.md Pattern 3 has 8 policies and was implemented as specified.

## Issues Encountered

None.

## User Setup Required

**External services require manual configuration before running the backend.**

1. **Create `.env` file** in `backend/` by copying `.env.example` and filling in real values:
   - `SUPABASE_URL` and keys from Supabase Dashboard > Settings > API
   - WhatsApp Cloud API credentials from Meta for Developers > App > WhatsApp > API Setup

2. **Apply the database migration** to Supabase:
   - Copy contents of `backend/migrations/001_initial_schema.sql`
   - Paste into Supabase Dashboard > SQL Editor > Run

3. **Disable email confirmation** in Supabase:
   - Dashboard > Authentication > Providers > Email > uncheck "Confirm email"
   - Required for Phase 2 immediate-token signup flow

4. **Install Python dependencies:**
   ```bash
   cd backend && pip install -r requirements.txt
   ```

5. **Start development server:**
   ```bash
   cd backend && make dev
   ```
   Visit http://localhost:8000/health — should return `{"status": "ok"}`

## Next Phase Readiness

- Backend scaffold ready for Phase 2 auth, avatar, and webhook feature implementations
- Schema migration ready to apply to Supabase cloud instance
- All router stubs in place for Plans 02-03 (auth endpoints), 02-04 (WhatsApp webhook)
- No blockers — all foundation code is in place

---
*Phase: 02-infrastructure-user-management*
*Completed: 2026-02-23*
