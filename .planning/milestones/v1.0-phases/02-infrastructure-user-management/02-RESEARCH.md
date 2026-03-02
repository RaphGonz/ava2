# Phase 2: Infrastructure & User Management - Research

**Researched:** 2026-02-23
**Domain:** Supabase Auth + PostgreSQL RLS, FastAPI backend, Meta WhatsApp Cloud API webhook integration
**Confidence:** HIGH

## Summary

Phase 2 builds the real working infrastructure: a Python/FastAPI backend with Supabase for auth and database, full RLS-enforced multi-tenant data isolation, and a WhatsApp webhook that echoes messages back to prove end-to-end connectivity. This phase establishes the data schema (users, avatars, messages, preferences) and the service-separated architecture that all later phases extend.

The stack is well-understood and well-documented. Supabase Python SDK (supabase-py v2.28+) handles auth and database operations against Supabase cloud. The WhatsApp integration uses Meta Cloud API directly (no third-party intermediary), handled via FastAPI webhooks and httpx for outbound message sending. The key architectural challenge is the per-request JWT context: the Supabase Python client must pass the user's access token on every database operation so RLS policies enforce correctly.

The biggest non-code risk is the WhatsApp Business Account verification process, which takes 2-15 business days. This must be initiated on day one of the phase. Development proceeds in parallel using a test phone number (Meta provides a free test number for Cloud API apps) so webhook work is never blocked.

**Primary recommendation:** Use supabase-py with a singleton async client + per-request `set_auth()` for RLS-correct database access. Use Meta Cloud API direct (no Twilio, no intermediary). Use ngrok for local webhook development. Submit WhatsApp Business Verification on day one.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Authentication & Identity:**
- Web-first signup: users create accounts on the web app, not via WhatsApp
- Method: email + password only (no OAuth, no magic link in Phase 2)
- Phase 2 UI: backend + minimal barebones HTML form to prove auth works — no styling (Phase 6)
- WhatsApp linking: user enters phone number in app/settings; backend stores it; webhook looks it up on incoming message; no SMS OTP verification in Phase 2

**Database Schema:**

avatars table (one per user, enforced):
- `name` — avatar's name
- `age` — integer, minimum 20 enforced (hard CHECK constraint per compliance decision from Phase 1)
- `personality` — enum / list of choices (not free text)
- `physical_description` — text
- `created_at`
- `user_id` FK (one avatar per user — unique constraint on user_id)

messages table:
- `user_id`, `avatar_id`, `channel` (enum: 'app' | 'whatsapp'), `role` (enum: 'user' | 'assistant'), `content`, `created_at`
- No session/conversation grouping in Phase 2 — flat message log

User preferences (Phase 2 scope only):
- WhatsApp phone number linkage — stored as column on users table or simple user_preferences row

RLS: enabled on all tables, tested with multiple accounts to confirm isolation.

**Hosting & Deployment:**

| Service | Dev (local) | Production |
|---------|-------------|------------|
| Database | Supabase cloud (free tier, from day one) | Supabase cloud |
| Backend / webhook | Local machine (FastAPI) | VPS (DigitalOcean / Hetzner) |
| LLMs | N/A in Phase 2 | N/A in Phase 2 |

Backend: Python + FastAPI
Config management: `.env` file + `python-dotenv` for local dev; environment variables on VPS for production. All service URLs are env vars — no hardcoded endpoints.

### Claude's Discretion
- Exact Supabase Auth integration pattern (Supabase Auth vs custom JWT — pick cleanest approach given Python + FastAPI)
- Personality enum values (the list of choices for avatar personality — define reasonable defaults)
- WhatsApp webhook library choice (Twilio, Meta Cloud API direct, or similar — pick based on Phase 2 needs)
- RLS policy specifics (implement standard user-isolation policies)
- API endpoint structure and naming

### Deferred Ideas (OUT OF SCOPE)
- Full styled web app UI — Phase 6
- LLM/AI integration — Phase 3
- Spice level and intimate mode user preferences — Phase 5
- Image generation infrastructure — Phase 5+
- WhatsApp OTP verification for phone number linking — later phase
- Multiple avatars per user — deferred; schema supports it but Phase 2 enforces one per user
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| USER-01 | User can create an account | Supabase Auth sign_up + email/password flow (§ Standard Stack, § Code Examples) |
| USER-02 | User data is fully isolated from other users | RLS policies with auth.uid() = user_id on all tables (§ Architecture Patterns, § Code Examples) |
| USER-03 | User can configure their avatar and persona during onboarding | avatars table schema + avatar creation endpoint (§ Architecture Patterns, § Code Examples) |
| PLAT-01 | User can chat via WhatsApp (WhatsApp Business API integration) | Meta Cloud API webhook + echo response (§ Standard Stack, § Architecture Patterns, § Code Examples) |
| ARCH-04 | Cloud-hosted on VPS/AWS, always-on for message handling | FastAPI + uvicorn on VPS; service-separated config via env vars (§ Architecture Patterns) |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| supabase-py | 2.28.0 (Feb 2026) | Supabase client: auth + database + RLS | Official Supabase Python SDK; PyPI verified; latest stable as of Feb 10, 2026 |
| fastapi | 0.115+ | HTTP framework for API routes and webhook endpoints | Python-first, async-native, excellent Pydantic integration; standard for Python APIs |
| uvicorn | 0.30+ | ASGI server for FastAPI | De facto ASGI server for FastAPI; supports --reload for dev |
| httpx | 0.27+ | Async HTTP client for calling Meta Graph API | Used by supabase-py internally; async; preferred over requests for FastAPI |
| python-dotenv | 1.0+ | Load .env files for local config | Standard for dev environment management |
| pydantic-settings | 2.x | Type-safe settings from env vars | Best practice for FastAPI config management; BaseSettings reads .env |
| psycopg2-binary | 2.9+ | PostgreSQL adapter (if direct DB access needed) | Standard Postgres driver for Python |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-jose | 3.x | JWT decoding/verification | Verifying Supabase JWTs in FastAPI dependency; alternative: PyJWT |
| ngrok | Latest CLI | HTTPS tunnel for local webhook development | Required during dev — Meta Cloud API needs public HTTPS for webhook registration |
| gunicorn | 22.x | Production WSGI/ASGI server | Production deployment on VPS: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Meta Cloud API direct | Twilio WhatsApp | Twilio adds cost and abstraction layer; Meta Cloud API is free (pay per message at scale), direct, and has better latency. Claude's recommendation: Meta Cloud API direct. |
| supabase-py | Direct psycopg2 + custom auth | supabase-py handles Auth, RLS context, and PostgREST — much less code. Direct psycopg2 loses RLS benefits and requires custom auth logic. |
| pydantic-settings | python-dotenv alone | pydantic-settings provides type validation + IDE support + test override capability. Strictly better than raw dotenv. |

**Installation:**
```bash
pip install supabase==2.28.0 fastapi uvicorn[standard] httpx python-dotenv pydantic-settings python-jose[cryptography] gunicorn
```

## Architecture Patterns

### Recommended Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app creation, router mounting
│   ├── config.py            # Pydantic BaseSettings (reads .env)
│   ├── dependencies.py      # get_current_user, get_supabase_client
│   ├── database.py          # Supabase client singleton
│   ├── routers/
│   │   ├── auth.py          # POST /auth/signup, POST /auth/signin
│   │   ├── avatars.py       # POST /avatars, GET /avatars/me
│   │   ├── messages.py      # GET /messages (history)
│   │   └── webhook.py       # GET /webhook (verify), POST /webhook (messages)
│   ├── models/
│   │   ├── auth.py          # SignupRequest, SigninRequest, TokenResponse
│   │   ├── avatar.py        # AvatarCreate, AvatarResponse
│   │   └── message.py       # MessageCreate, MessageResponse
│   └── services/
│       ├── whatsapp.py      # send_whatsapp_message(), parse_incoming()
│       └── user_lookup.py   # lookup_user_by_phone()
├── .env                     # Local secrets (not committed)
├── .env.example             # Template for env vars (committed)
├── requirements.txt
└── Makefile                 # dev, prod, ngrok targets
```

### Pattern 1: Supabase Auth — Email/Password Signup and Sign-In

**What:** Users create accounts and receive JWT access tokens. All subsequent requests include the Bearer token. FastAPI validates it via dependency injection.

**Signup flow:**

```python
# app/routers/auth.py
from fastapi import APIRouter, HTTPException
from app.database import supabase_client  # anon key client
from app.models.auth import SignupRequest, SigninRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=TokenResponse)
async def signup(body: SignupRequest):
    try:
        response = supabase_client.auth.sign_up({
            "email": body.email,
            "password": body.password,
        })
        if response.user is None:
            raise HTTPException(400, "Signup failed")
        # session is None if email confirmation enabled
        # For Phase 2: disable email confirmation in Supabase dashboard
        return TokenResponse(
            access_token=response.session.access_token,
            user_id=str(response.user.id)
        )
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/signin", response_model=TokenResponse)
async def signin(body: SigninRequest):
    try:
        response = supabase_client.auth.sign_in_with_password({
            "email": body.email,
            "password": body.password,
        })
        return TokenResponse(
            access_token=response.session.access_token,
            user_id=str(response.user.id)
        )
    except Exception as e:
        raise HTTPException(401, "Invalid credentials")
```

**IMPORTANT:** Disable email confirmation in the Supabase Dashboard under Authentication > Providers > Email > "Confirm email" toggle. Otherwise sign_up returns session=None and cannot return a token immediately.

### Pattern 2: Per-Request RLS via set_auth / Authorization Header

**What:** The Supabase client must know which user is making each request so RLS policies fire correctly. The pattern: one global client, per-request auth header override.

**Dependency injection:**

```python
# app/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import supabase_client

bearer_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    """Validates Supabase JWT and returns the user object."""
    token = credentials.credentials
    try:
        user_response = supabase_client.auth.get_user(token)
        if user_response.user is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_response.user
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

async def get_authed_supabase(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    """Returns Supabase client with user context set — RLS will enforce correctly."""
    token = credentials.credentials
    # set_auth scopes the client to the user's JWT for this operation
    supabase_client.auth.set_session(token, "")
    return supabase_client
```

**CRITICAL RLS PITFALL:** When using the service role key, RLS is bypassed entirely. For user-facing data operations, always use the anon key client + set_auth with the user's JWT. Reserve the service role for admin operations only (e.g., looking up user by phone number in the webhook handler).

### Pattern 3: Database Schema with RLS

**Full schema (matches CONTEXT.md exactly):**

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Personality enum (Claude's discretion: reasonable Phase 2 defaults)
CREATE TYPE personality_type AS ENUM (
  'playful',
  'dominant',
  'shy',
  'caring',
  'intellectual',
  'adventurous'
);

-- Channel and role enums for messages
CREATE TYPE message_channel AS ENUM ('app', 'whatsapp');
CREATE TYPE message_role AS ENUM ('user', 'assistant');

-- User preferences table (stores WhatsApp phone linkage in Phase 2)
CREATE TABLE public.user_preferences (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  whatsapp_phone TEXT,              -- E.164 format: +1234567890
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(user_id)                   -- One preferences row per user
);

-- Avatars table (one per user, enforced via UNIQUE on user_id)
CREATE TABLE public.avatars (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  age INTEGER NOT NULL CHECK (age >= 20),   -- Hard floor from Phase 1 compliance decision
  personality personality_type NOT NULL,
  physical_description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(user_id)                           -- Enforce one avatar per user
);

-- Messages table (flat log, no session grouping in Phase 2)
CREATE TABLE public.messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  avatar_id UUID REFERENCES public.avatars(id) ON DELETE SET NULL,
  channel message_channel NOT NULL,
  role message_role NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------
-- Row Level Security
-- -----------------------------------------------

ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.avatars ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- user_preferences policies
CREATE POLICY "Users can read own preferences"
  ON public.user_preferences FOR SELECT
  TO authenticated
  USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can insert own preferences"
  ON public.user_preferences FOR INSERT
  TO authenticated
  WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update own preferences"
  ON public.user_preferences FOR UPDATE
  TO authenticated
  USING ((SELECT auth.uid()) = user_id)
  WITH CHECK ((SELECT auth.uid()) = user_id);

-- avatars policies
CREATE POLICY "Users can read own avatar"
  ON public.avatars FOR SELECT
  TO authenticated
  USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can create own avatar"
  ON public.avatars FOR INSERT
  TO authenticated
  WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update own avatar"
  ON public.avatars FOR UPDATE
  TO authenticated
  USING ((SELECT auth.uid()) = user_id)
  WITH CHECK ((SELECT auth.uid()) = user_id);

-- messages policies
CREATE POLICY "Users can read own messages"
  ON public.messages FOR SELECT
  TO authenticated
  USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can insert own messages"
  ON public.messages FOR INSERT
  TO authenticated
  WITH CHECK ((SELECT auth.uid()) = user_id);

-- -----------------------------------------------
-- Performance Indexes (required for RLS policy performance)
-- -----------------------------------------------

CREATE INDEX idx_user_preferences_user_id ON public.user_preferences (user_id);
CREATE INDEX idx_avatars_user_id ON public.avatars (user_id);
CREATE INDEX idx_messages_user_id ON public.messages (user_id);
CREATE INDEX idx_messages_user_created ON public.messages (user_id, created_at DESC);
CREATE INDEX idx_user_preferences_phone ON public.user_preferences (whatsapp_phone)
  WHERE whatsapp_phone IS NOT NULL;  -- Partial index for phone lookup
```

**CRITICAL:** Use `(SELECT auth.uid())` not bare `auth.uid()` in policies. The SELECT wrapper allows Postgres to cache the result per statement, improving RLS performance ~95% on tables with many rows.

### Pattern 4: WhatsApp Webhook — Verification and Echo

**What:** Meta Cloud API delivers incoming messages to a registered HTTPS webhook. The server must handle GET (verification challenge) and POST (incoming messages).

**Webhook verification (GET):**

```python
# app/routers/webhook.py
from fastapi import APIRouter, Request, HTTPException, Query
from app.config import settings
import httpx

router = APIRouter(prefix="/webhook", tags=["webhook"])

@router.get("")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """Meta calls this GET endpoint when you register the webhook URL."""
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return int(hub_challenge)  # Must return challenge as integer
    raise HTTPException(status_code=403, detail="Forbidden")
```

**Message receipt and echo (POST):**

```python
@router.post("")
async def handle_incoming(request: Request):
    """Meta delivers incoming WhatsApp messages here."""
    body = await request.json()

    try:
        # Navigate the webhook payload structure
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" not in value:
            return {"status": "ok"}  # Delivery receipt or status update — ignore

        message = value["messages"][0]
        sender_phone = message["from"]          # E.164 format: "+1234567890"
        message_type = message.get("type")

        if message_type != "text":
            return {"status": "ok"}  # Only handle text in Phase 2

        incoming_text = message["text"]["body"]
        phone_number_id = value["metadata"]["phone_number_id"]

        # Look up user by phone number (service role client — bypasses RLS)
        user = await lookup_user_by_phone(sender_phone)

        if user is None:
            # Unlinked number — send instructions
            await send_whatsapp_message(
                phone_number_id=phone_number_id,
                to=sender_phone,
                text="Hi! Please create an account at ava.example.com and link your number to start chatting."
            )
            return {"status": "ok"}

        # Phase 2: Echo the message back
        echo_text = f"[Echo] {incoming_text}"
        await send_whatsapp_message(
            phone_number_id=phone_number_id,
            to=sender_phone,
            text=echo_text
        )

        # Log message to database (service role — user not authenticated here)
        await log_whatsapp_message(user_id=user.id, avatar_id=None,
                                    incoming=incoming_text, echo=echo_text)

    except (KeyError, IndexError):
        pass  # Malformed payload — return 200 to prevent Meta retries

    return {"status": "ok"}  # Always return 200 to Meta
```

**Sending messages via Meta Graph API:**

```python
# app/services/whatsapp.py
import httpx
from app.config import settings

async def send_whatsapp_message(phone_number_id: str, to: str, text: str) -> None:
    """Send a text message via Meta Cloud API."""
    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
```

### Pattern 5: Config with Pydantic BaseSettings

**What:** All service endpoints and secrets are env vars. No hardcoded URLs. Swapping from local to cloud requires only .env changes.

```python
# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # WhatsApp Cloud API
    whatsapp_access_token: str
    whatsapp_phone_number_id: str
    whatsapp_verify_token: str     # Any secret string you choose

    # App
    app_env: str = "development"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

**.env.example (committed to repo):**

```
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxx
WHATSAPP_PHONE_NUMBER_ID=123456789
WHATSAPP_VERIFY_TOKEN=my_secret_verify_token
APP_ENV=development
```

### Pattern 6: Phone Number Lookup for Webhook Routing

**What:** When a WhatsApp message arrives, the webhook must map the sender's phone number to a user account.

```python
# app/services/user_lookup.py
from app.database import supabase_admin  # Service role client — bypasses RLS

async def lookup_user_by_phone(phone: str):
    """Find user by linked WhatsApp phone. Returns None if not found."""
    # Normalize to E.164 if needed
    result = (
        supabase_admin
        .from_("user_preferences")
        .select("user_id")
        .eq("whatsapp_phone", phone)
        .single()
        .execute()
    )
    return result.data if result.data else None
```

**Note:** This uses the service role client (bypasses RLS), which is correct here — the webhook is server-to-server and no user JWT exists in this context.

### Anti-Patterns to Avoid

- **Using service_role key for user-facing endpoints:** Service role bypasses RLS entirely. User data isolation breaks silently. Always use anon key + user JWT for user operations.
- **Creating a new Supabase client per request:** Client initialization costs 5+ seconds. Create one global singleton client and use `set_auth()` per request.
- **Not returning HTTP 200 to Meta webhook POST:** If the webhook returns non-200, Meta retries the message. Return 200 always, even on errors. Log errors internally.
- **Storing phone numbers without normalization:** Store all phone numbers in E.164 format (+countrycode+number). Meta sends them in E.164. Inconsistent formats break user lookup.
- **Not disabling email confirmation in Supabase:** With email confirmation enabled, sign_up returns session=None, breaking the immediate-token flow needed for the minimal Phase 2 UI.
- **Indexing after RLS is live:** Deploy indexes with the schema migration, not as an afterthought. Missing index on user_id in policies causes full-table scans — performance degrades 100x+ on large tables.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JWT token creation and signing | Custom JWT library | Supabase Auth (supabase-py) | Supabase generates JWTs with correct claims (sub, aud, role) that RLS functions expect. Custom JWTs won't contain auth.uid() and will break RLS. |
| WhatsApp message sending | Direct HTTP calls without abstraction | `send_whatsapp_message()` service function + httpx | Meta Graph API has version pinning (v19.0), payload structure requirements, and error handling nuances. Wrap it once, use everywhere. |
| User authentication middleware | Manual token parsing in every route | FastAPI `Depends(get_current_user)` dependency | Dependency injection provides automatic 401 on invalid tokens, DRY auth logic, and testability. |
| Phone number normalization | Regex from scratch | E.164 format convention + validation on input | Meta always sends E.164. Accept E.164 only; validate on input; store normalized. No custom normalization needed. |
| Database migrations | Manual ALTER TABLE statements | SQL migration files (schema.sql + numbered migrations) | Supabase cloud applies migrations in order. Hand-editing live schema without migrations breaks team workflow and loses history. |

**Key insight:** The webhook routing (phone → user lookup) is a critical path that runs on every WhatsApp message. Keep it simple: one indexed DB lookup. Don't add caching in Phase 2 — premature optimization with no measurable load yet.

## Common Pitfalls

### Pitfall 1: Supabase Client RLS Context Lost Between Requests

**What goes wrong:** Using a single global Supabase client initialized with the service role key (or anon key without set_auth) for all requests. RLS policies see no authenticated user — all queries return empty or bypass isolation.

**Why it happens:** Developers initialize the client once at startup and forget that RLS requires per-request user context.

**How to avoid:**
- Two clients: one service role (admin ops), one anon + set_auth per user request
- FastAPI dependency `get_authed_supabase` sets user JWT before each database call
- Test isolation: create two users, insert data as user A, verify user B gets empty results

**Warning signs:** Queries returning data from all users or returning nothing when data exists.

### Pitfall 2: WhatsApp Webhook Returns Non-200

**What goes wrong:** Webhook handler raises an exception (bad payload, DB error). FastAPI returns 500. Meta retries the message 5+ times. User receives echo 5 times.

**Why it happens:** Not wrapping message processing in try/except, or letting DB errors propagate to HTTP response.

**How to avoid:**
```python
@router.post("")
async def handle_incoming(request: Request):
    try:
        body = await request.json()
        await process_whatsapp_message(body)  # All processing here
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        # Still return 200 — Meta doesn't need to know about internal errors
    return {"status": "ok"}
```

**Warning signs:** User receives duplicate messages; Meta dashboard shows webhook delivery failures.

### Pitfall 3: WhatsApp Business Verification Delay Blocks Phase

**What goes wrong:** WhatsApp Business Account verification takes 2-15 business days. Starting verification at end of development means the team waits idle with working code.

**Why it happens:** Verification feels like a "last step" but is actually gating.

**How to avoid:**
- Submit Meta Business Manager verification and WhatsApp Business Account setup on day one
- During development: use the test phone number Meta provides in Cloud API apps (free, no verification required)
- Test number limitation: can send to max 5 recipient numbers — sufficient for development/testing
- Webhook works fully with the test number; production number is a config swap (WHATSAPP_PHONE_NUMBER_ID env var)

**Warning signs:** Phase 2 code complete but WhatsApp success criterion blocked on pending verification.

### Pitfall 4: Avatar Age CHECK Constraint Not Enforced on Update

**What goes wrong:** The CHECK (age >= 20) constraint is applied at insert but someone adds an UPDATE endpoint that bypasses it by setting age via raw SQL or an admin bypass.

**Why it happens:** DB constraints only fire on INSERT/UPDATE through the RDBMS — they're correct by default. The pitfall is writing application-level validation that contradicts DB constraints.

**How to avoid:** Rely on the DB constraint as the source of truth. Application-level validation should mirror it but never weaken it. Never run age updates through service role unless absolutely required.

**Warning signs:** Application allows age < 20 to be set via PUT endpoint but DB silently rejects it (returns error not caught by app).

### Pitfall 5: Missing Partial Index on whatsapp_phone

**What goes wrong:** Every WhatsApp message causes a full-table scan of user_preferences to find the user. Performance degrades as user count grows.

**Why it happens:** The phone lookup is only for WhatsApp routing — most rows have NULL. A standard btree index on a mostly-NULL column is wasteful.

**How to avoid:**
```sql
CREATE INDEX idx_user_preferences_phone
  ON public.user_preferences (whatsapp_phone)
  WHERE whatsapp_phone IS NOT NULL;
```
Partial index — only indexes non-null phone rows. Fast lookup for webhook routing without wasted index space.

**Warning signs:** Slow webhook response times as user count grows; explain plan shows sequential scans.

### Pitfall 6: Supabase Free Tier Inactivity Pause

**What goes wrong:** Supabase free tier pauses projects after 1 week of inactivity. During development with gaps between sessions, the database becomes unavailable.

**Why it happens:** Free tier restriction; project is automatically paused.

**How to avoid:**
- Keep development active (daily queries prevent pause)
- Know the restore procedure: visit Supabase dashboard and click "Restore" — takes ~1-2 minutes
- Free tier limits that matter for Phase 2: 500MB DB storage, 50K monthly active users — well within Phase 2 scope

**Warning signs:** Connection timeouts when resuming development after a few days of inactivity.

## Code Examples

Verified patterns from official sources and research:

### Supabase Client Initialization (Singleton)

```python
# app/database.py
from supabase import create_client, Client
from app.config import settings

# Anon key client — for user-facing operations with RLS
supabase_client: Client = create_client(
    settings.supabase_url,
    settings.supabase_anon_key
)

# Service role client — for admin operations (webhook user lookup, etc.)
supabase_admin: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_role_key
)
```

### Avatar Creation Endpoint

```python
# app/routers/avatars.py
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user, get_authed_supabase
from app.models.avatar import AvatarCreate, AvatarResponse

router = APIRouter(prefix="/avatars", tags=["avatars"])

@router.post("", response_model=AvatarResponse)
async def create_avatar(
    body: AvatarCreate,
    user=Depends(get_current_user),
    db=Depends(get_authed_supabase),
):
    # Check if user already has an avatar (UNIQUE constraint will also catch this)
    existing = db.from_("avatars").select("id").eq("user_id", str(user.id)).execute()
    if existing.data:
        raise HTTPException(400, "Avatar already exists. One avatar per user in Phase 2.")

    result = db.from_("avatars").insert({
        "user_id": str(user.id),
        "name": body.name,
        "age": body.age,
        "personality": body.personality,
        "physical_description": body.physical_description,
    }).execute()

    return result.data[0]
```

### Phone Linking Endpoint

```python
# app/routers/preferences.py
@router.put("/preferences/whatsapp")
async def link_whatsapp(
    phone: str,
    user=Depends(get_current_user),
    db=Depends(get_authed_supabase),
):
    """Store user's WhatsApp phone number for message routing."""
    # Validate E.164 format
    if not phone.startswith("+") or not phone[1:].isdigit():
        raise HTTPException(400, "Phone must be in E.164 format: +1234567890")

    result = db.from_("user_preferences").upsert({
        "user_id": str(user.id),
        "whatsapp_phone": phone,
    }).execute()
    return {"status": "linked", "phone": phone}
```

### Minimal Auth Test UI (HTML form — no styling)

```html
<!-- templates/auth.html — barebones form to prove auth works -->
<!DOCTYPE html>
<html>
<head><title>Ava - Dev Auth</title></head>
<body>
  <h2>Sign Up</h2>
  <form id="signup">
    <input type="email" id="su-email" placeholder="Email" required>
    <input type="password" id="su-password" placeholder="Password" required>
    <button type="submit">Create Account</button>
  </form>

  <h2>Sign In</h2>
  <form id="signin">
    <input type="email" id="si-email" placeholder="Email" required>
    <input type="password" id="si-password" placeholder="Password" required>
    <button type="submit">Sign In</button>
  </form>

  <p id="result"></p>

  <script>
    document.getElementById('signup').onsubmit = async (e) => {
      e.preventDefault();
      const r = await fetch('/auth/signup', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email: su_email.value, password: su_password.value})
      });
      const data = await r.json();
      document.getElementById('result').textContent = r.ok
        ? `Signed up! Token: ${data.access_token.substring(0, 20)}...`
        : `Error: ${JSON.stringify(data)}`;
    };
  </script>
</body>
</html>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Twilio WhatsApp API (third-party) | Meta Cloud API direct | Meta opened Cloud API 2022; now standard | Eliminates Twilio cost and latency; Meta provides free test numbers; direct API control |
| On-premise WhatsApp Business API | Meta Cloud API | Meta deprecated on-premise 2022-2023 | Must use Cloud API for all new integrations; on-premise no longer supported for new accounts |
| Manual JWT creation for Supabase | supabase-py set_auth() | supabase-py v2+ | SDK handles JWT lifecycle; set_auth() provides clean per-request context |
| Global service role client for all ops | Anon client + per-request JWT | Supabase guidance evolving 2024-2025 | Critical security distinction: service role bypasses RLS; anon + JWT enforces it |
| pydantic v1 BaseSettings | pydantic-settings v2 (separate package) | Pydantic v2 release 2023 | Must pip install pydantic-settings separately; not bundled with pydantic v2+ |

**Deprecated/outdated:**
- **Flask for WhatsApp webhooks:** FastAPI is now the standard for Python async webhook handlers. Flask synchronous handlers cause blocking on I/O.
- **Twilio for WhatsApp:** Third-party intermediary adds cost and latency. Meta Cloud API is the direct path and is free at development scale.
- **On-premise WhatsApp Business API:** Meta stopped new account creation for on-premise. Cloud API is the only option.

## Open Questions

1. **Supabase `set_auth()` vs creating user-scoped client**
   - What we know: `set_auth()` is available in supabase-py; passing Authorization header per-operation is also documented. Both enforce RLS.
   - What's unclear: Thread safety of `set_auth()` on a singleton client in an async context — could one request's auth bleed into another?
   - Recommendation: Use `supabase_client.postgrest.auth(token)` for individual query authorization rather than `set_auth()` on the global client. This is the safest pattern for async contexts. Verify in Phase 2 implementation.

2. **WhatsApp Test Number Limitations**
   - What we know: Meta provides a free test phone number for Cloud API apps; limited to 5 recipient numbers.
   - What's unclear: Whether webhook delivery works identically with the test number vs. a verified business number.
   - Recommendation: Start with the test number; document any differences discovered during development.

3. **Supabase Free Tier — Phone Index + Inactivity**
   - What we know: Free tier pauses after 1 week inactivity; 500MB storage limit.
   - What's unclear: Whether the partial index on whatsapp_phone counts against storage limits meaningfully.
   - Recommendation: Negligible for Phase 2 scale. Monitor storage in Supabase dashboard.

## Sources

### Primary (HIGH confidence)

- [supabase-py PyPI](https://pypi.org/project/supabase/) — v2.28.0 release date verified (Feb 10, 2026)
- [Supabase Python Auth Reference](https://supabase.com/docs/reference/python/auth-api) — sign_up, sign_in_with_password method signatures
- [Supabase RLS Documentation](https://supabase.com/docs/guides/database/postgres/row-level-security) — Policy syntax, auth.uid() patterns, performance optimization
- [Supabase User Management](https://supabase.com/docs/guides/auth/managing-user-data) — auth.users reference table pattern, ON DELETE CASCADE, auto-trigger
- [Supabase Auth FastAPI Discussion #33811](https://github.com/orgs/supabase/discussions/33811) — Per-request JWT context, singleton client, set_auth pattern
- [Supabase Auth FastAPI Integration (grokipedia)](https://grokipedia.com/page/Supabase_Auth_and_FastAPI_Integration) — get_current_user dependency pattern with HTTPBearer
- [FastAPI Settings Documentation](https://fastapi.tiangolo.com/advanced/settings/) — pydantic-settings BaseSettings, lru_cache pattern
- [WhatsApp Cloud API Starter (GitHub)](https://github.com/ibrahimpelumi6142/whatsapp-cloud-api-starter) — Webhook verification and message sending structure, env vars
- [Meta WhatsApp FastAPI Guide (Lorenzo Uriel)](https://medium.com/@lorenzouriel/start-guide-to-build-a-meta-whatsapp-bot-with-python-and-fastapi-aee1edfd4132) — Complete FastAPI webhook implementation
- [ngrok + WhatsApp Integration](https://ngrok.com/partners/whatsapp) — Local webhook development pattern

### Secondary (MEDIUM confidence)

- [WhatsApp Business API Approval Timeline (Interakt)](https://www.interakt.shop/whatsapp-business-api/account-approval/) — 2-15 business day verification timeline
- [Supabase RLS Complete Guide 2026 (DesignRevision)](https://designrevision.com/blog/supabase-row-level-security) — Policy structure rules (SELECT/INSERT/UPDATE/DELETE)
- [Supabase Pricing 2026 (UIBakery)](https://uibakery.io/blog/supabase-pricing) — Free tier limits verified: 500MB DB, 50K MAU, 1 week inactivity pause
- [RLS Discussion #3479 (Supabase)](https://github.com/orgs/supabase/discussions/3479) — Python RLS user context via JWT

### Tertiary (LOW confidence — flagged for validation)

- Thread safety of `set_auth()` on singleton async client — not found in official docs; requires empirical testing in Phase 2

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — supabase-py version verified on PyPI; FastAPI patterns from official docs; Meta Cloud API is the documented standard
- Architecture: HIGH — RLS policies from official Supabase docs; FastAPI dependency injection pattern verified; webhook structure from multiple working GitHub repos
- Pitfalls: HIGH — RLS bypass via service role is documented; Meta retry behavior on non-200 is documented; Supabase free tier pause is verified in pricing docs
- WhatsApp verification timeline: MEDIUM — Multiple sources agree on 2-15 days; Meta doesn't publish an official SLA

**Research date:** 2026-02-23
**Valid until:** ~90 days (May 2026) — Supabase and Meta Cloud API are stable; supabase-py releases frequently but this phase's APIs are stable
