# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-23)

**Core value:** A single AI companion that seamlessly switches between getting things done (secretary) and personal connection (intimate partner), all inside the messaging app the user already uses.
**Current focus:** Phase 2 - Infrastructure & User Management

## Current Position

Phase: 2 of 7 (Infrastructure & User Management)
Plan: 4 of 5 in current phase
Status: Phase 2 in progress
Last activity: 2026-02-23 — Completed 02-04 (WhatsApp webhook integration, message logging, message history endpoint)

Progress: [████░░░░░░] 40%

## Performance Metrics

**Velocity:**
- Total plans completed: 6
- Average duration: 15 min
- Total execution time: 1.5 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation-compliance P01 | 11 min | 2 tasks | 4 files |
| 01-foundation-compliance P02 | 15 min | 2 tasks | 6 files |
| 02-infrastructure-user-management P01 | 19 min | 2 tasks | 23 files |
| 02-infrastructure-user-management P02 | 15 min | 2 tasks | 6 files |
| 02-infrastructure-user-management P03 | 15 min | 2 tasks | 5 files |
| 02-infrastructure-user-management P04 | 15 min | 2 tasks | 6 files |

**Recent Trend:**
- Last 5 plans: 15 min, 19 min, 15 min, 15 min, 15 min
- Trend: Stable

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- All decisions currently pending validation during implementation
- [Phase 01-foundation-compliance]: Provider pattern for age verification: all checks go through AgeVerificationManager.verifyAge(), swapping from self-declaration to ID verification is a config change not code rewrite
- [Phase 01-foundation-compliance]: WhatsApp NSFW images delivered via JWT-signed web portal links (not WhatsApp attachments) to comply with WhatsApp Business API policy
- [Phase 01-foundation-compliance]: Avatar age floor is 20+ (not 18+), enforced at DB level with CHECK constraint and form validation
- [Phase 02-infrastructure-user-management]: Used postgrest.auth(token) per-query pattern instead of set_auth() on singleton to avoid JWT context bleed between concurrent async requests
- [Phase 02-infrastructure-user-management]: supabase_admin (service role) reserved exclusively for server-to-server ops (webhook phone lookup); all user-facing ops use supabase_client (anon + user JWT)
- [Phase 02-infrastructure-user-management]: dev.py router guards /dev/* routes with app_env check — 404 in production, live in development
- [Phase 02-infrastructure-user-management]: pathlib.Path(__file__) used for template lookup in dev.py — portable across working directories
- [Phase 02-infrastructure-user-management]: pydantic[email] added explicitly to requirements.txt — EmailStr requires the email-validator extra
- [Phase 02-infrastructure-user-management]: Pydantic Field(ge=20) used on AvatarCreate.age (not field_validator) — produces correct GreaterThanEqual metadata and JSON Schema
- [Phase 02-infrastructure-user-management]: PUT /preferences/whatsapp accepts PhoneLinkRequest body (not query param) — enables Pydantic E.164 validation before handler runs
- [Phase 02-infrastructure-user-management]: GET /preferences/ returns 404 when no row exists (not empty object) — distinguishes never-configured from configured-with-no-phone
- [Phase 02-infrastructure-user-management]: Message logging wrapped in nested try/except — DB failure does not prevent echo from sending
- [Phase 02-infrastructure-user-management]: GRAPH_API_VERSION constant pins Meta API to v19.0 — version bumps are a one-line change
- [Phase 02-infrastructure-user-management]: GET /messages uses get_authed_supabase (RLS) not supabase_admin — user isolation enforced at DB level

### Pending Todos

- Apply backend/migrations/001_initial_schema.sql to Supabase cloud instance (manual step)
- Disable email confirmation in Supabase Dashboard (required for Phase 2 signup flow)
- Add real credentials to backend/.env (copy from .env.example)
- Register webhook URL in Meta Developer Console after starting ngrok
- Submit WhatsApp Business Account verification (takes 2-15 business days)

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-02-23
Stopped at: Completed 02-infrastructure-user-management-04-PLAN.md — WhatsApp webhook integration complete
Resume file: None
