# Phase 2: Infrastructure & User Management - Context

**Gathered:** 2026-02-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Secure, multi-tenant database and WhatsApp integration with production-grade message handling.

Deliverables:
- Auth backend (email + password) with a minimal test UI (no styled web app — that's Phase 6)
- Supabase database with RLS enabled on all tables
- Core schema: users, avatars, messages, user preferences
- WhatsApp webhook wired up: a logged-in user who has linked their number can send a message and get an echo back

AI/LLM integration is NOT in scope — that's Phase 3. The WhatsApp bot just echoes in Phase 2.

</domain>

<decisions>
## Implementation Decisions

### Authentication & Identity
- **Web-first signup**: users create accounts on the web app, not via WhatsApp. WhatsApp is a delivery channel linked after signup — not the identity source.
- **Method**: email + password (no OAuth, no magic link in Phase 2)
- **Phase 2 UI**: backend + minimal barebones HTML form to prove auth works. No styling — that's Phase 6.
- **WhatsApp linking**: user enters their phone number in the app/settings. Backend stores it. When that number messages Ava on WhatsApp, the webhook looks it up and routes to their account. No SMS OTP verification in Phase 2.

### Database Schema

**avatars table** (one per user — enforced):
- `name` — avatar's name
- `age` — integer, minimum 20 enforced (hard CHECK constraint, per compliance decision from Phase 1)
- `personality` — enum / list of choices (not free text)
- `physical_description` — text
- `created_at`
- `user_id` FK (one avatar per user — unique constraint on user_id)

**messages table**:
- `user_id`, `avatar_id`, `channel` (enum: 'app' | 'whatsapp'), `role` (enum: 'user' | 'assistant'), `content`, `created_at`
- No session/conversation grouping in Phase 2 — flat message log, queryable by any combination

**User preferences** (Phase 2 scope only):
- WhatsApp phone number linkage — stored as a column on the users table or a simple user_preferences row
- Spice level, notification settings, UI preferences deferred to later phases

**RLS**: enabled on all tables, tested with multiple accounts to confirm isolation.

### Hosting & Deployment

**Architecture principle**: service-separated from day one. Each service is an independent module configured via URL/env var so any component can be swapped from local to cloud without code changes.

| Service | Dev (local) | Production |
|---------|-------------|------------|
| Database | Supabase cloud (free tier, used from day one) | Supabase cloud |
| Backend / webhook | Local machine (FastAPI) | VPS (DigitalOcean / Hetzner) |
| LLMs | Ollama on local machine | Remote GPU server (Phase 3 concern) |
| Image generation | N/A Phase 2 | ComfyUI cloud / GPU rental (Phase 5+ concern) |

**Backend**: Python + FastAPI
- Rationale: LangGraph (Phase 3+) is Python-first; local LLM tooling (Ollama, llama.cpp) has far better Python SDKs; user knows Python
- FastAPI handles webhooks and REST APIs as well as Express

**Config management**: `.env` file + `python-dotenv` for local dev; environment variables on VPS for production. All service URLs (Supabase, Ollama, future image gen API) are env vars — no hardcoded endpoints.

### Claude's Discretion
- Exact Supabase Auth integration pattern (Supabase Auth vs custom JWT — Claude to pick the cleanest approach given Python + FastAPI)
- Personality enum values (the list of choices for avatar personality — Claude defines reasonable defaults)
- WhatsApp webhook library choice (Twilio, Meta Cloud API direct, or similar — Claude picks based on Phase 2 needs)
- RLS policy specifics (Claude implements standard user-isolation policies)
- API endpoint structure and naming

</decisions>

<specifics>
## Specific Ideas

- "Everything should be separate and chosen" — modularity is a first-class constraint, not an afterthought. Even if everything runs locally during dev, the code must support swapping each service to a remote endpoint via config.
- Local dev environment: FastAPI server + Ollama on local machine, Supabase cloud for DB. One machine can handle all of this comfortably.
- The web app UI in Phase 2 is intentionally minimal — just enough to prove auth and account creation work. Don't invest in styling or UX yet.

</specifics>

<deferred>
## Deferred Ideas

- Full styled web app UI — Phase 6 (Web App & Multi-Platform)
- LLM/AI integration — Phase 3 (Core Intelligence & Mode Switching)
- Spice level and intimate mode user preferences — Phase 5 (Intimate Mode Text Foundation)
- Image generation infrastructure (ComfyUI cloud) — Phase 5+
- WhatsApp OTP verification for phone number linking — could be added in a later phase if security requires it
- Multiple avatars per user — deferred, schema supports it (user_id FK) but Phase 2 enforces one avatar per user

</deferred>

---

*Phase: 02-infrastructure-user-management*
*Context gathered: 2026-02-23*
