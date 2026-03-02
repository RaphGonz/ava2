# Phase 6: Web App & Multi-Platform - Research

**Researched:** 2026-02-24
**Domain:** Web frontend (React/Vite), platform adapter abstraction (Python Protocol/ABC), secure photo delivery (Supabase Storage signed URLs), phone-based web auth (Supabase OTP)
**Confidence:** MEDIUM-HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Web chat UI:**
- Visual style: minimal chat bubble layout (familiar messaging-app feel)
- Authentication: phone verification — user links their WhatsApp number to get web access (no separate credential system)
- Conversation history: web-only — web app tracks its own messages separately from WhatsApp history
- Feature scope: web app is the full settings hub, differentiating it from WhatsApp with:
  - **Persona selector** — visual UI to choose/change Ava's persona
  - **Spiciness ceiling** — content intensity slider (flirty → explicit); Ava will not escalate beyond the user's chosen level
  - **Mode-switch phrase** — user-configurable phrase that triggers switching between secretary and intimate mode (stored in profile, ChatService checks it during message dispatch)
  - **Notification preferences** — control WhatsApp notification behavior from the web
  - **Account & billing** — subscription status, credits, payment method management

**Photo delivery:**
- When a photo is ready, Ava sends a rich WhatsApp message in her persona: e.g., "here's what you asked for ❤" + a secure URL. Tone must be in-character, not system-generated.
- Link expiry: 24 hours
- Access model: token-based URL — no login required to view. The token itself is the auth. Anyone with the link can view for 24h.
- What the link opens: the photo embedded in the web app's chat view (not a standalone photo viewer; opens in full web app context)

**Platform switching & preference:**
- User declares their preferred platform (WhatsApp or web app) via a toggle in the settings panel
- Ava replies ONLY on the user's preferred platform — not on both simultaneously
- When a user messages from their non-preferred platform, Ava sends an in-character warm redirect that also mentions they can change their preference in settings.
- When a user switches preferred platform: full context carries over — current mode (secretary/intimate), persona, and recent message history are all available on the new platform

**Adapter contract & extensibility:**
- Adapter interface: inbound + outbound only. Core handles everything else.
  - `receive(message: NormalizedMessage) → None` — feeds into core pipeline
  - `send(user_id: str, text: str) → None` — delivers response to platform
- Abstraction mechanism: Python ABC or Protocol — type-checked, enforced at dev time
- Normalized message envelope: `user_id + text + platform + timestamp` (minimal; no platform-specific metadata)
- Phase 6 scope: WhatsApp adapter (refactor existing webhook handler) + Web adapter. No additional platforms.

### Claude's Discretion

- Exact web UI framework choice (React, Vue, HTMX, etc.)
- JWT vs. session cookie for web app auth
- Exact spiciness level names/thresholds (e.g., "Mild / Spicy / Hot" vs. a numeric scale)
- Platform preference enforcement implementation (middleware vs. adapter-level check)
- Photo token generation and storage mechanism

### Deferred Ideas (OUT OF SCOPE)

- Telegram adapter — natural third platform, but deferred to post-Phase 6
- Safe-word behavior (stop/de-escalate signal on special phrase) — distinct from mode-switch phrase, would require ChatService changes; note for backlog
- Per-user topic blocklist (things Ava never brings up) — personal guardrails on top of system guardrails; note for backlog
- Consent/age-verification records in settings panel — was discussed but not included in this phase's settings scope; note for backlog
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PLAT-02 | User can chat via a web app with direct photo display | React/Vite frontend with chat UI + photo embed; FastAPI `/chat` router; web message channel in DB |
| PLAT-03 | NSFW photos on WhatsApp are delivered via secure authenticated web links (not inline) | Supabase Storage `create_signed_url()` with 24h expiry; photo viewer page in web app identified by token |
| PLAT-04 | User chooses whether to use WhatsApp or the web app as their primary interface | `preferred_platform` column in `user_preferences`; platform check in WhatsApp adapter before routing to ChatService |
| PLAT-05 | Messaging layer is modular — new platforms can be added as adapters without changing core logic | Python Protocol `PlatformAdapter` with `receive()` and `send()` methods; `NormalizedMessage` dataclass; refactor `webhook.py` and new `web_chat.py` router as concrete adapters |
</phase_requirements>

---

## Summary

Phase 6 has four interlocking deliverables: (1) a React/Vite web frontend with chat UI and settings panel, (2) a platform adapter abstraction layer using Python Protocol, (3) secure 24-hour photo delivery via Supabase Storage signed URLs, and (4) phone-OTP-based web authentication that ties into the existing Supabase email account. The backend work (adapter refactor, new API endpoints, DB migration) is the critical path — the frontend depends on stable API contracts.

The existing project is well-positioned: the backend already uses Python Protocol for `LLMProvider` (structural typing, same pattern applies to adapters), Supabase for auth and storage, FastAPI for routing, and the `user_preferences` table is the natural home for `preferred_platform`, `spiciness_level`, `mode_switch_phrase`, and `notification_prefs`. The web auth flow requires a new OTP endpoint (`POST /auth/verify-phone`) because the current auth model is email/password — phone OTP becomes a second-factor link, not a standalone account type.

The photo delivery decision (token = auth, no login required, 24h expiry) maps cleanly to Supabase Storage signed URLs: `create_signed_url(path, 86400)` returns a URL with a signed token that expires in 86400 seconds. The token is the URL itself — no separate token table needed. The web app needs a route (`/photo/:encodedUrl` or the raw signed URL direct-links to a viewer page) that fetches and renders the image.

**Primary recommendation:** Use React 19 + Vite + Tailwind CSS for the frontend (consistent with the FastAPI official full-stack template and the existing CORS setup in `main.py`). Use Python Protocol for the adapter interface (already the project's established pattern — see `LLMProvider`). Use Supabase Storage signed URLs for photo tokens. Store all new user preferences as new columns in the existing `user_preferences` table via a `003_phase6_preferences.sql` migration.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 19.x | UI framework for chat + settings | Project CORS is already configured for localhost:3000; FastAPI official template uses React |
| Vite | 6.x | Build tool & dev server | Industry standard for React 2025; fast HMR, TypeScript out of box |
| Tailwind CSS | 4.x | Styling | Minimal setup matches "minimal chat bubble" requirement; FastAPI official template uses Tailwind |
| Zustand | 5.x | Client-side state (auth token, messages, settings) | Lightweight, minimal boilerplate, excellent TypeScript support; well-suited for chat state |
| TanStack Query | 5.x | Server state management for API calls | Handles loading/error/refetch lifecycle; avoids hand-rolling fetch state |
| supabase-js | 2.x | Supabase client for frontend OTP auth | Official Supabase JS SDK |
| Python `typing.Protocol` | stdlib | Adapter interface definition | Already used in project for `LLMProvider` — consistent pattern |
| Supabase Storage | hosted | Signed URL photo delivery | Already provisioned; `create_signed_url()` handles expiry natively |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| shadcn/ui | latest | Accessible UI components (slider, toggle, button) | Settings panel spiciness slider and platform toggle |
| react-router-dom | 6.x | Client-side routing (chat view, settings, photo viewer) | SPA routing for `/chat`, `/settings`, `/photo/:token` |
| python-jose | >=3.0.0 | JWT signing for photo view page | Already in requirements.txt; alternative if not using Supabase Storage signed URLs |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| React + Vite | HTMX + Jinja2 | HTMX is simpler but lacks the reactive state needed for real-time chat updates, settings sliders, and the persona selector UI. Also, full SPA is better for the standalone web app experience. React is the right choice for this feature scope. |
| Zustand | React Context API | Context causes excessive re-renders in chat (new message appends). Zustand's subscription model is better for list-appending chat state. |
| Supabase Storage signed URLs | Custom HMAC token table | Supabase Storage signed URLs are a first-class feature with no extra infrastructure. Custom HMAC requires a DB table, token expiry cron job, and comparison logic. Use Supabase Storage. |
| Python Protocol | Python ABC | Project already uses Protocol for `LLMProvider`. Protocol has no inheritance requirement — adapters don't need to import or extend a base class, making them easier to test in isolation. Use Protocol for consistency. |
| TanStack Query | Supabase Realtime WebSocket | Supabase Realtime requires enabling replication on the messages table and managing WebSocket subscriptions. TanStack Query polling (refetchInterval) is simpler and sufficient for this non-latency-critical chat flow. Can upgrade to Realtime if needed post-launch. |

**Installation:**
```bash
# Frontend (new frontend/ directory)
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install react-router-dom @tanstack/react-query zustand @supabase/supabase-js
npm install -D tailwindcss @tailwindcss/vite
npm install @radix-ui/react-slider @radix-ui/react-switch  # via shadcn/ui

# Backend additions (backend/requirements.txt)
# No new packages needed — python-jose already present for JWT; supabase SDK already present
```

---

## Architecture Patterns

### Recommended Project Structure

```
frontend/                       # New Vite + React app
├── src/
│   ├── api/                    # API client functions (fetch wrappers for FastAPI)
│   │   ├── auth.ts             # signIn, verifyOtp, linkPhone
│   │   ├── chat.ts             # sendMessage, fetchMessages
│   │   └── preferences.ts     # getPreferences, updatePreferences
│   ├── components/
│   │   ├── ChatBubble.tsx
│   │   ├── ChatInput.tsx
│   │   ├── MessageList.tsx
│   │   └── PhotoViewer.tsx     # Renders signed photo URL embedded in chat view
│   ├── pages/
│   │   ├── ChatPage.tsx
│   │   ├── SettingsPage.tsx
│   │   └── PhotoPage.tsx       # Opened by WhatsApp link; displays photo in web app context
│   ├── store/
│   │   └── useAuthStore.ts     # Zustand store: JWT token, user_id, preferred_platform
│   └── App.tsx
├── index.html
└── vite.config.ts

backend/app/
├── adapters/                   # NEW: platform adapter layer
│   ├── __init__.py
│   ├── base.py                 # PlatformAdapter Protocol + NormalizedMessage dataclass
│   ├── whatsapp_adapter.py     # Wraps existing webhook.py send/receive logic
│   └── web_adapter.py          # Web chat adapter (receives from HTTP, sends via response)
├── routers/
│   ├── web_chat.py             # NEW: POST /chat, GET /chat/history
│   ├── preferences.py          # EXTENDED: add spiciness, mode_switch_phrase, preferred_platform
│   └── photo.py                # NEW: POST /photos/signed-url (admin signs URL; returns it)
├── services/
│   └── platform_router.py      # NEW: checks preferred_platform, dispatches or redirects
└── migrations/
    └── 003_phase6_preferences.sql  # NEW: columns on user_preferences + photo_tokens table

```

### Pattern 1: Python Protocol Adapter Interface

**What:** Define `PlatformAdapter` as a `typing.Protocol` — any class with `receive()` and `send()` satisfies it without inheritance. This is the same pattern as `LLMProvider` in `backend/app/services/llm/base.py`.

**When to use:** When you need a typed contract across multiple concrete implementations without forcing a class hierarchy.

```python
# backend/app/adapters/base.py
from typing import Protocol, runtime_checkable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class NormalizedMessage:
    user_id: str
    text: str
    platform: str          # "whatsapp" | "web"
    timestamp: datetime


@runtime_checkable
class PlatformAdapter(Protocol):
    """
    Structural interface for platform adapters (PLAT-05).

    Any class with receive() and send() satisfies this Protocol.
    To add a new platform: implement a class with this signature — no imports of base.py needed.
    """

    async def receive(self, message: NormalizedMessage) -> str:
        """Feed normalized message into core pipeline. Returns reply text."""
        ...

    async def send(self, user_id: str, text: str) -> None:
        """Deliver reply text to the platform."""
        ...
```

**Source:** Mirrors `backend/app/services/llm/base.py` (Phase 3 decision: Python Protocol, not ABC — project convention).

### Pattern 2: Platform Preference Enforcement

**What:** Before routing a message to ChatService, check the user's `preferred_platform` from their preferences. If the incoming message is on a non-preferred platform, return the in-character warm redirect instead of calling ChatService.

**When to use:** In the adapter `receive()` method or a shared `platform_router.py` service called by both adapters.

**Recommendation:** A shared `platform_router.py` service keeps the check in one place (not duplicated in both adapters). Each adapter calls `platform_router.route(user_id, platform, message)` which either dispatches to ChatService or returns a redirect text.

```python
# backend/app/services/platform_router.py
from app.database import supabase_admin
from app.adapters.base import NormalizedMessage
from app.services.chat import ChatService

REDIRECT_MSG_TEMPLATE = (
    "Hey 😊 I mostly hang out on {preferred} — come find me there! "
    "(You can change this in settings)"
)

async def route(
    chat_service: ChatService,
    user_id: str,
    incoming_platform: str,
    message: NormalizedMessage,
    avatar: dict | None,
) -> str:
    """
    Check preferred_platform. If mismatch, return in-character redirect.
    If match (or no preference set), dispatch to ChatService.
    """
    prefs = supabase_admin.from_("user_preferences") \
        .select("preferred_platform") \
        .eq("user_id", user_id) \
        .maybe_single() \
        .execute()

    preferred = (prefs.data or {}).get("preferred_platform")
    if preferred and preferred != incoming_platform:
        platform_label = "WhatsApp" if preferred == "whatsapp" else "the web app"
        return REDIRECT_MSG_TEMPLATE.format(preferred=platform_label)

    return await chat_service.handle_message(
        user_id=user_id,
        incoming_text=message.text,
        avatar=avatar,
    )
```

### Pattern 3: Supabase Storage Signed URL for Photo Delivery

**What:** When a photo is ready, store it in Supabase Storage (private bucket), generate a 24-hour signed URL, then send that URL via WhatsApp in an in-character message.

**When to use:** Whenever a photo needs to be delivered via WhatsApp (PLAT-03).

```python
# backend/app/routers/photo.py (or inline in photo generation service)
# Source: https://supabase.com/docs/reference/python/storage-from-createsignedurl

def generate_photo_signed_url(bucket: str, path: str) -> str:
    """
    Generate a 24-hour signed URL for a photo stored in Supabase Storage.
    The signed URL IS the auth token — no separate token table needed.
    """
    TWENTY_FOUR_HOURS = 86400
    response = supabase_admin.storage \
        .from_(bucket) \
        .create_signed_url(path, TWENTY_FOUR_HOURS)
    return response["signedURL"]
```

The WhatsApp message sent is in-persona: `f"here's what you asked for ❤ {signed_url}"` — the URL opens to a page in the web app (`/photo?url=...`) that embeds the image in the full web app context.

### Pattern 4: Web Chat API Router

**What:** New FastAPI router `POST /chat` accepts text from the web app frontend, runs it through the platform router, and returns the reply. `GET /chat/history` returns recent messages for the web channel.

```python
# backend/app/routers/web_chat.py
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user, get_authed_supabase
from app.adapters.base import NormalizedMessage
from app.services.platform_router import route
from datetime import datetime, timezone

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    text: str

@router.post("")
async def send_message(
    body: ChatRequest,
    user=Depends(get_current_user),
):
    user_id = str(user.id)
    msg = NormalizedMessage(
        user_id=user_id,
        text=body.text,
        platform="web",
        timestamp=datetime.now(timezone.utc),
    )
    reply = await route(
        chat_service=_chat_service,
        user_id=user_id,
        incoming_platform="web",
        message=msg,
        avatar=await get_avatar_for_user(user_id),
    )
    # Log both turns to messages table with channel="web"
    # Return reply
    return {"reply": reply}
```

### Pattern 5: Web App Phone Auth Flow

**What:** The web app uses phone OTP to link the user's WhatsApp number to their existing email account. It is NOT a separate account system. The flow is: user signs in with email/password (existing `/auth/signin` endpoint) → user goes to Settings → enters phone → backend calls Supabase OTP → user enters 6-digit code → backend verifies and stores the phone in `user_preferences`.

**Why this approach:** This avoids creating a second auth system. The user already has a Supabase email account. Phone verification is a supplemental step that writes to `user_preferences.whatsapp_phone` (already existing column) and confirms ownership. The JWT from email/password login is used for all web app API calls.

```python
# backend/app/routers/auth.py — new endpoint
@router.post("/phone/send-otp")
async def send_phone_otp(body: PhoneOTPRequest, user=Depends(get_current_user)):
    """Send OTP to phone number. User must be authenticated (email session active)."""
    # supabase_admin.auth.admin.generate_link is one approach;
    # alternatively use Twilio directly if Supabase phone auth requires Twilio setup.
    ...

@router.post("/phone/verify-otp")
async def verify_phone_otp(body: VerifyOTPRequest, user=Depends(get_current_user)):
    """Verify OTP, confirm phone ownership, store in user_preferences."""
    ...
```

**IMPORTANT caveat:** Supabase phone OTP requires configuring an SMS provider (Twilio) at the Supabase project level. This is infrastructure setup, not just code. See Open Questions.

### Pattern 6: DB Migration for Phase 6 Preferences

**What:** Add new columns to `user_preferences` for Phase 6 features. Do NOT create a new table — all user settings live in `user_preferences`.

```sql
-- backend/migrations/003_phase6_preferences.sql
ALTER TABLE public.user_preferences
  ADD COLUMN IF NOT EXISTS preferred_platform   TEXT DEFAULT 'whatsapp',  -- 'whatsapp' | 'web'
  ADD COLUMN IF NOT EXISTS spiciness_level      TEXT DEFAULT 'mild',      -- 'mild' | 'spicy' | 'explicit'
  ADD COLUMN IF NOT EXISTS mode_switch_phrase   TEXT,                     -- user-configurable, nullable
  ADD COLUMN IF NOT EXISTS notif_prefs          JSONB DEFAULT '{}';       -- flexible notification settings

-- photo_tokens table: tracks issued photo tokens for audit/revocation
-- NOTE: If using Supabase Storage signed URLs, this table may not be needed.
-- Only create if token revocation (before 24h expiry) is required.
-- DEFER this table unless revocation is explicitly needed.
```

**Spiciness level names (Claude's discretion recommendation):** Three-tier named scale — `mild` (flirty, no explicit), `spicy` (suggestive), `explicit` (full adult content). Named tiers are clearer than numeric and map naturally to UI radio buttons / a 3-step slider.

### Anti-Patterns to Avoid

- **Separate auth system for web:** Do NOT create new user accounts for the web app. Users sign in with their existing email/password. Phone OTP is a verification step only.
- **Duplicating ChatService logic in adapters:** Adapters must only handle transport (receive/send). All business logic stays in ChatService via `platform_router.py`. Never check mode, content guardrails, or crisis detection inside an adapter.
- **Cross-platform session bleed:** The web and WhatsApp channels write to the `messages` table with `channel='web'` or `channel='whatsapp'` respectively. History returned to the web app should filter to `channel='web'` only (per the locked decision: "web-only conversation history").
- **Blocking the event loop in adapters:** Adapters are async. Any synchronous SDK call must be wrapped with `asyncio.to_thread()` (established pattern from Phase 4).
- **Using `supabase_client` (anon) for signed URL generation:** Signed URLs for private buckets require the service role key. Use `supabase_admin` for `create_signed_url()` calls.
- **Hardcoding redirect message in both adapters:** The redirect message must live in `platform_router.py`, not duplicated in both adapters.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Photo URL expiry | Custom HMAC token table with cron-job cleanup | Supabase Storage `create_signed_url(path, 86400)` | First-class feature: expiry enforced by Supabase, no token table, no cron job, no comparison logic |
| Phone OTP sending | Custom SMS integration | Supabase Auth phone OTP (backed by Twilio) | Supabase manages rate limiting, delivery, and 6-digit code verification |
| Chat UI state management | Custom React context + useReducer | Zustand | useReducer causes the full component tree to re-render on message append; Zustand subscriptions do not |
| Settings form validation | Custom validation logic | Pydantic on backend + HTML5 constraints on frontend | Pydantic already validates `PhoneLinkRequest`; extend the same pattern for new settings |
| Platform adapter registry | Custom factory with string dispatch | Simple `if platform == "whatsapp"` in `platform_router.py` | With two platforms (WhatsApp + web), a registry pattern adds complexity without benefit. Keep it simple. |
| Frontend routing | Server-side routing / Jinja2 | React Router DOM | Phase 6 is a true SPA (chat, settings, photo pages all need client-side state) |

**Key insight:** The photo delivery requirement ("no login required, token is the auth") is solved entirely by Supabase Storage signed URLs. The URL itself encodes the expiry signature. Do not build a custom token system.

---

## Common Pitfalls

### Pitfall 1: Supabase Phone OTP Requires Twilio at Infrastructure Level

**What goes wrong:** Developer writes the frontend OTP flow but hits "Phone provider not configured" errors from Supabase. No amount of code fixes this.
**Why it happens:** Supabase phone OTP requires linking a Twilio account in the Supabase Dashboard (Authentication > Providers > Phone). This is a one-time infrastructure setup step, not a code step.
**How to avoid:** Treat Twilio+Supabase phone provider setup as a Wave 0 infrastructure task, not an implementation task.
**Warning signs:** `signInWithOtp({ phone: ... })` returns an error about phone provider not being enabled.

### Pitfall 2: CORS — Frontend Must Be Listed in Backend

**What goes wrong:** Web app running at `localhost:3000` gets CORS errors when calling FastAPI at `localhost:8000`.
**Why it happens:** The backend already allows `localhost:3000` in development (see `main.py`), but production origins are not configured. When deployed, the web app's production URL must be added to `allow_origins`.
**How to avoid:** Add a `FRONTEND_URL` config variable to `Settings` class with an env override. Update `main.py` CORS to include it. Add production URL to `.env` before deployment.
**Warning signs:** Browser console shows `Access-Control-Allow-Origin` missing in response.

### Pitfall 3: Web Channel History Isolation

**What goes wrong:** Web app shows WhatsApp messages mixed with web messages.
**Why it happens:** `GET /chat/history` fetches from `messages` table without filtering by `channel`.
**How to avoid:** `GET /chat/history` must always filter: `.eq("channel", "web")`. The ChatService message logging for web calls must write `channel="web"`. The existing WhatsApp flow writes `channel="whatsapp"`.
**Warning signs:** WhatsApp messages appearing in web app chat window.

### Pitfall 4: SessionStore is Platform-Agnostic (Good) But Must Not Be Confused With DB History

**What goes wrong:** Developer tries to load DB message history into SessionStore on web startup, or assumes in-memory session history is persisted across server restarts.
**Why it happens:** The in-memory `SessionStore` is for LLM context window management only — it is ephemeral. DB messages are for display history only.
**How to avoid:** On web app load, `GET /chat/history` fetches display messages from DB. The ChatService fills its in-memory session from the first web message onward (stateless between server restarts — this is the existing behavior, unchanged).
**Warning signs:** Old messages showing up in LLM context after server restart.

### Pitfall 5: Platform Preference Check Must Use `supabase_admin` (Service Role)

**What goes wrong:** `platform_router.py` calls Supabase with the user's JWT (anon client) — but the WhatsApp adapter doesn't have the user's JWT (it's a webhook, no user JWT in the request).
**Why it happens:** WhatsApp webhook runs without user authentication — it's Meta calling us. The existing pattern already uses `supabase_admin` for `lookup_user_by_phone`. The `preferred_platform` fetch must follow the same pattern.
**How to avoid:** `platform_router.py` must use `supabase_admin` (service role) for the `preferred_platform` lookup. Only user-facing API endpoints use the authed client.
**Warning signs:** 401 errors in webhook logs when looking up preferences.

### Pitfall 6: Photo Signed URL — Private Bucket Required

**What goes wrong:** Photos are readable by anyone who guesses the storage path (no auth required to access public bucket files).
**Why it happens:** Supabase Storage buckets are public by default. Signed URLs are only meaningful on private buckets.
**How to avoid:** Create the photos bucket as private. Only `supabase_admin` can generate signed URLs for private buckets.
**Warning signs:** Photos accessible via direct path URL without a signed token.

### Pitfall 7: Spiciness Level Not Enforced in ChatService

**What goes wrong:** User sets spiciness to "mild" but Ava still responds with explicit content because ChatService doesn't check the user's spiciness ceiling.
**Why it happens:** The `spiciness_level` preference is stored in DB but never loaded into ChatService's pipeline.
**How to avoid:** ChatService's `handle_message()` must read `avatar` (already passed in) or the preferences row for the `spiciness_level` and pass it to the intimate prompt generator. The intimate prompt should include the ceiling in the system prompt instruction.
**Warning signs:** User sets mild, Ava escalates anyway.

### Pitfall 8: Mode-Switch Phrase Conflicts With Existing Fuzzy Detection

**What goes wrong:** User sets a mode-switch phrase that is also a common word, causing false positives in every message.
**Why it happens:** The user-configured phrase is checked before (or in parallel with) the existing `detect_mode_switch()` fuzzy detector. Ordering and priority matter.
**How to avoid:** Check the user-configured `mode_switch_phrase` FIRST in ChatService (exact match, case-insensitive, stripped) — if it matches, switch mode. Only fall through to the fuzzy detector if no custom phrase match. Document that custom phrases should be distinct (UI hint: "choose something you wouldn't normally say").
**Warning signs:** Users reporting accidental mode switches.

---

## Code Examples

Verified patterns from official sources and existing project code:

### Supabase Storage: Create 24-Hour Signed URL
```python
# Source: https://supabase.com/docs/reference/python/storage-from-createsignedurl
# Uses supabase_admin (service role) — private bucket requires admin access

TWENTY_FOUR_HOURS = 86400

def get_photo_signed_url(photo_path: str) -> str:
    """
    Generate a 24-hour signed URL for a photo in the private 'photos' bucket.
    The returned URL is self-contained auth — no token table needed.
    """
    response = supabase_admin.storage \
        .from_("photos") \
        .create_signed_url(photo_path, TWENTY_FOUR_HOURS)
    return response["signedURL"]
```

### Python Protocol Adapter (follows project LLMProvider pattern)
```python
# Source: mirrors backend/app/services/llm/base.py — established project pattern

from typing import Protocol, runtime_checkable
from dataclasses import dataclass
from datetime import datetime

@dataclass
class NormalizedMessage:
    user_id: str
    text: str
    platform: str   # "whatsapp" | "web"
    timestamp: datetime

@runtime_checkable
class PlatformAdapter(Protocol):
    async def receive(self, message: NormalizedMessage) -> str: ...
    async def send(self, user_id: str, text: str) -> None: ...
```

### WhatsApp Adapter (refactors existing webhook.py)
```python
# backend/app/adapters/whatsapp_adapter.py
from app.adapters.base import NormalizedMessage, PlatformAdapter
from app.services.whatsapp import send_whatsapp_message
from app.services.platform_router import route

class WhatsAppAdapter:
    """Satisfies PlatformAdapter Protocol — no inheritance required."""

    def __init__(self, chat_service, phone_number_id: str):
        self._chat_service = chat_service
        self._phone_number_id = phone_number_id

    async def receive(self, message: NormalizedMessage) -> str:
        avatar = await get_avatar_for_user(message.user_id)
        return await route(self._chat_service, message.user_id, "whatsapp", message, avatar)

    async def send(self, user_id: str, text: str) -> None:
        # Need to resolve phone from user_id for WhatsApp delivery
        prefs = supabase_admin.from_("user_preferences") \
            .select("whatsapp_phone") \
            .eq("user_id", user_id) \
            .maybe_single() \
            .execute()
        phone = prefs.data["whatsapp_phone"]
        await send_whatsapp_message(self._phone_number_id, phone, text)
```

### TanStack Query: Fetch Chat Messages with Polling
```typescript
// frontend/src/api/chat.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useChatHistory(token: string) {
  return useQuery({
    queryKey: ['chat-history'],
    queryFn: () =>
      fetch('/chat/history', {
        headers: { Authorization: `Bearer ${token}` },
      }).then(r => r.json()),
    refetchInterval: 3000,  // Poll every 3s for new messages (simple, sufficient)
  });
}

export function useSendMessage(token: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (text: string) =>
      fetch('/chat', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      }).then(r => r.json()),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['chat-history'] }),
  });
}
```

### Zustand Auth Store
```typescript
// frontend/src/store/useAuthStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  token: string | null;
  userId: string | null;
  setAuth: (token: string, userId: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      userId: null,
      setAuth: (token, userId) => set({ token, userId }),
      clearAuth: () => set({ token: null, userId: null }),
    }),
    { name: 'ava-auth' }  // persisted to localStorage
  )
);
```

### Phase 6 DB Migration
```sql
-- backend/migrations/003_phase6_preferences.sql
ALTER TABLE public.user_preferences
  ADD COLUMN IF NOT EXISTS preferred_platform  TEXT    DEFAULT 'whatsapp',
  ADD COLUMN IF NOT EXISTS spiciness_level     TEXT    DEFAULT 'mild',
  ADD COLUMN IF NOT EXISTS mode_switch_phrase  TEXT,
  ADD COLUMN IF NOT EXISTS notif_prefs         JSONB   DEFAULT '{}';

-- Constraint: only valid platform values
ALTER TABLE public.user_preferences
  ADD CONSTRAINT chk_preferred_platform
  CHECK (preferred_platform IN ('whatsapp', 'web'));

-- Constraint: only valid spiciness values
ALTER TABLE public.user_preferences
  ADD CONSTRAINT chk_spiciness_level
  CHECK (spiciness_level IN ('mild', 'spicy', 'explicit'));
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Create React App | Vite | 2022-2023 | Create React App is deprecated (React docs no longer recommend it). Use `npm create vite@latest`. |
| Redux for all state | Zustand for client state + TanStack Query for server state | 2023-2024 | Redux is overkill for this use case. Zustand handles UI/auth state; TanStack Query handles API data. |
| Tailwind v3 config via `tailwind.config.js` | Tailwind v4 config via CSS `@import` and `@tailwindcss/vite` plugin | 2024-2025 | v4 eliminates the JS config file. Install: `npm install -D tailwindcss @tailwindcss/vite`. |
| `supabase_client.auth.set_auth(token)` for RLS | `supabase_client.postgrest.auth(token).from_(...)` per-query | Phase 2 decision | Already established: per-query auth avoids JWT context bleed in async. |

**Deprecated/outdated:**
- `Create React App (CRA)`: Officially deprecated. Use Vite.
- `python-jose` for JWT signing of photo URLs: Unnecessary when Supabase Storage signed URLs handle the same problem with zero extra code.

---

## Open Questions

1. **Supabase Phone OTP Infrastructure — Twilio Required**
   - What we know: Supabase phone OTP requires a Twilio account linked in the Supabase Dashboard. This is documented and confirmed.
   - What's unclear: Whether the project already has Twilio configured (STATE.md shows "WhatsApp credentials not yet configured"). Twilio for WhatsApp and Twilio for SMS OTP use the same Twilio account but are configured separately.
   - Recommendation: Treat "Supabase phone provider setup with Twilio" as a Wave 0 infrastructure task (like "register webhook in Meta console"). If Twilio SMS is unavailable or too complex for Phase 6, the fallback is: skip OTP verification entirely — user enters their phone number in settings and it's stored without verification (relying on the WhatsApp webhook linkage as proof of phone ownership). This is a weaker security model but simpler to implement.

2. **Photo Delivery is Phase 7 Scope (INTM-03), Not Phase 6**
   - What we know: `PLAT-03` ("NSFW photos on WhatsApp delivered via secure authenticated web links") is listed as Phase 6 in REQUIREMENTS.md, but photo GENERATION (`INTM-03`) is Phase 7. Phase 6 needs the photo DELIVERY infrastructure (signed URLs, photo viewer page) even though photos won't be generated yet.
   - What's unclear: Should Phase 6 build a fully functional photo viewer page with a signed URL, or just the backend signed URL endpoint as a stub for Phase 7 to wire up?
   - Recommendation: Build the full photo delivery infrastructure in Phase 6 (signed URL endpoint, photo viewer page, in-character WhatsApp message template). Phase 7 will call the already-built endpoint when photos are generated. This avoids splitting the delivery infrastructure across two phases.

3. **Frontend Deployment: Static Hosting vs. FastAPI Static Mount**
   - What we know: The existing `main.py` already has a commented pattern for serving static files via FastAPI. The CORS middleware already allows localhost:3000 for development. For production, Vite builds to a `dist/` folder.
   - What's unclear: Will the frontend be served from the same VPS as the FastAPI backend (FastAPI serves static files), or hosted separately (Vercel/Netlify)?
   - Recommendation: For Phase 6, serve the Vite `dist/` build from FastAPI using `StaticFiles` (already in `main.py` as a commented template). This simplifies deployment — one server, no CORS issues in production. In a later phase, move to Vercel if needed.

4. **Mode-Switch Phrase: Custom Phrase + Existing Fuzzy Detector Priority**
   - What we know: The user-configured `mode_switch_phrase` must be checked by ChatService. The existing `detect_mode_switch()` fuzzy detector is already in ChatService.
   - What's unclear: Exact priority ordering — should custom phrase override fuzzy, or supplement it?
   - Recommendation: Custom phrase is an exact-match check (case-insensitive, stripped) that runs FIRST in ChatService, before `detect_mode_switch()`. If custom phrase matches → switch mode. If not → fall through to existing fuzzy detection. This prevents the custom phrase from being caught or degraded by the fuzzy algorithm.

---

## Sources

### Primary (HIGH confidence)
- [Supabase Python Storage: create_signed_url](https://supabase.com/docs/reference/python/storage-from-createsignedurl) — signed URL generation, expiry parameter, Python SDK usage
- [Supabase Phone Login docs](https://supabase.com/docs/guides/auth/phone-login) — OTP flow, Twilio provider requirement, rate limiting
- [Python typing.Protocol (python.org)](https://docs.python.org/3/library/abc.html) — Protocol vs ABC for structural typing
- `backend/app/services/llm/base.py` — project's existing Protocol pattern (LLMProvider), directly applied to PlatformAdapter
- `backend/app/main.py` — CORS already allows localhost:3000; Phase 6 comment already present
- `backend/migrations/001_initial_schema.sql` — `user_preferences` table schema; `message_channel` enum with 'app' and 'whatsapp' values (needs 'web' added)
- `backend/app/services/chat.py` — ChatService structure, gate ordering, avatar handling (directly informs what Phase 6 must extend)

### Secondary (MEDIUM confidence)
- [FastAPI Official Full-Stack Template](https://fastapi.tiangolo.com/project-generation/) — React + Vite + Tailwind CSS is the FastAPI project's own recommendation
- [TanStack Query React docs](https://tanstack.com/query/latest/docs/framework/react/overview) — refetchInterval polling pattern for chat
- [Supabase JWT auth guide](https://supabase.com/docs/guides/auth/jwts) — Bearer token vs cookie; Bearer is correct for this SPA + API architecture
- [React State Management 2025 — Zustand](https://dev.to/cristiansifuentes/react-state-management-in-2025-context-api-vs-zustand-385m) — Zustand vs Context API; Zustand wins for chat state

### Tertiary (LOW confidence — flag for validation)
- [HTMX vs React for FastAPI (DEV.to)](https://dev.to/jaydevm/fastapi-and-htmx-a-modern-approach-to-full-stack-bma) — HTMX considered and rejected (see Alternatives Considered)
- Spiciness level names ("mild / spicy / explicit") — Claude's discretion; no authoritative source; reasonable naming for the domain

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — React/Vite/Tailwind is FastAPI's own recommendation; Protocol pattern mirrors existing project code
- Architecture patterns: HIGH — Platform router and adapter patterns derived from existing project structure and LLMProvider precedent
- Photo delivery: HIGH — Supabase Storage signed URLs verified against official docs
- Phone auth OTP: MEDIUM — Flow understood but Twilio infrastructure dependency flagged as open question
- Frontend implementation: MEDIUM — Standard React/TanStack Query patterns, well-documented but not verified in this exact project configuration

**Research date:** 2026-02-24
**Valid until:** 2026-03-24 (30 days — stable ecosystem; Supabase SDK and React are not fast-moving for these APIs)
