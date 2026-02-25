# Phase 7: Avatar System & Production - Research

**Researched:** 2026-02-25
**Domain:** Image generation pipeline (Replicate/FLUX), background jobs (BullMQ), Stripe billing, Sentry, Docker Compose production deployment, Pillow watermarking, C2PA metadata, avatar setup UX
**Confidence:** MEDIUM-HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Avatar Setup Flow**
- Avatar configuration form appears during signup, before anything else (before first chat)
- Form fields: gender, age (20+ enforced), nationality/race, free-text appearance description (all four AVTR-01 through AVTR-04)
- After form submission: generate a reference image immediately, show it to the user, offer to regenerate until satisfied
- Avatar editable at any time post-signup via web settings; editing triggers a new reference image generation

**Image Generation Pipeline**
- Trigger: LLM decides when to send a photo — uses a `send_photo` tool call with scene/prompt description embedded in the call
- Image provider: Replicate API (FLUX or SDXL models), swappable via modular provider interface (ARCH-03)
- Pipeline: LLM tool call → backend enqueues BullMQ job → Replicate generates image → result delivered to user
- Delivery on web app: photo displayed inline in chat conversation
- Delivery on WhatsApp: secure authenticated link to web portal (per PLAT-03, no inline NSFW images on WhatsApp)

**Billing Model**
- Monthly subscription, single tier at beta launch
- Architecture must support adding more tiers later without rework (configuration-driven, per BILL-02)
- Integration scope: Stripe Checkout for payment + webhooks to update subscription status in DB + backend enforces access behind active subscription
- No Stripe Billing Portal for beta (can add later)
- Immediate paywall: user must subscribe to start chatting, no free trial

**Production Readiness**
- Monitoring: Sentry for error tracking + UptimeRobot for uptime alerts — no full observability stack needed for beta
- BullMQ failure strategy: retry 3x with exponential backoff → move to dead-letter queue → notify user that photo failed after all retries exhausted
- Compliance baseline: audit log every image generation request (user, prompt, timestamp, result URL) + visible watermark + C2PA metadata on all outputs
- Deployment: Docker Compose for fast, reproducible deployment on any server — speed to market is the priority
- Secrets: .env file on server, never committed to git; .env.example in repo documents required keys

### Claude's Discretion
- Reference image generation prompt construction from avatar fields
- Exact BullMQ queue configuration (concurrency, job TTL)
- Watermarking implementation details (library choice, watermark position/opacity)
- Sentry SDK integration specifics
- Docker Compose service layout (nginx, backend, worker, frontend)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AVTR-01 | User can select avatar gender | Avatar form field; stored in DB alongside physical_description; fed into image generation prompt |
| AVTR-02 | User can select avatar age (20+ enforced, hard floor) | Existing AvatarCreate model has `age: int = Field(..., ge=20)`; DB CHECK age >= 20; form validation needed |
| AVTR-03 | User can select avatar nationality/race | New avatar field; stored in DB; fed into image generation prompt |
| AVTR-04 | User can describe avatar appearance in free text | Existing `physical_description` column covers this; already in AvatarCreate model |
| AVTR-05 | Avatar definition feeds into image generation for consistent character photos | Prompt construction from avatar fields + Replicate FLUX API call pattern |
| INTM-03 | Bot sends AI-generated photos during intimate conversations | LLM tool call (`send_photo`) → BullMQ job → Replicate → Supabase storage → signed URL delivery |
| ARCH-03 | Modular image generation — image API provider is swappable without changing photo flow | ImageProvider Protocol (mirrors LLMProvider pattern from Phase 3); config-driven provider selection |
| BILL-01 | Flexible billing infrastructure that supports multiple pricing models | Stripe Checkout + webhook handler + subscription status in DB; config-driven tier table |
| BILL-02 | Billing model is customizable without code changes (configuration-driven) | Stripe Price IDs in config/env; plan table in DB; no hardcoded amounts |
</phase_requirements>

---

## Summary

Phase 7 is the final phase and the most architecturally broad — it adds avatar customization fields, an LLM-driven image generation pipeline, Stripe billing, production monitoring, and Docker Compose deployment. The codebase entering Phase 7 is already well-structured: an `AvatarCreate` model exists with `physical_description` but lacks `gender` and `nationality` fields; a `photo.py` router with signed-URL delivery already exists from Phase 6; and the `LLMProvider` Protocol pattern (structural typing, no inheritance) provides the template for the new `ImageProvider` Protocol required by ARCH-03.

The image generation pipeline is the most technically complex component. The flow is: (1) intimate mode LLM call includes a `send_photo` tool definition, (2) LLM decides to trigger it and returns a tool call, (3) ChatService detects the tool call and enqueues a BullMQ job, (4) a separate BullMQ worker process calls Replicate's FLUX API, (5) the worker downloads the image, adds a Pillow watermark and C2PA metadata, uploads to Supabase Storage, generates a signed URL, and delivers it to the user. BullMQ Python (v2.19.5) is actively maintained and uses Redis as a backing store — Redis must be added to the Docker Compose stack. Stripe integration is straightforward: `stripe.checkout.Session.create(mode="subscription")` + webhook handler for `checkout.session.completed` and `invoice.payment_failed` events.

The avatar DB schema needs two new columns (`gender TEXT` and `nationality TEXT`) in a migration `004_phase7_avatar_fields.sql`. The `AvatarCreate` Pydantic model needs matching fields. The frontend needs: (a) an `AvatarSetupPage` shown once after signup (onboarding gate), (b) an avatar edit section in `SettingsPage`, (c) a reference image preview flow with regenerate option, (d) a `SubscribePage` for Stripe Checkout redirect, and (e) a paywall gate that blocks chat access until subscription is active. Sentry SDK integrates automatically with FastAPI via `sentry_sdk.init()` called at startup.

**Primary recommendation:** Build in this order: (1) DB migration + AvatarCreate model update, (2) ImageProvider Protocol + Replicate provider, (3) BullMQ worker + Redis in Docker Compose, (4) LLM tool call integration in intimate mode, (5) Stripe billing + subscription gate, (6) Avatar setup UX (frontend onboarding), (7) Sentry + Docker Compose production config.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `replicate` | latest (PyPI) | Replicate API Python client | Official SDK; supports `async_run()` and webhook callbacks; FLUX models live here |
| `bullmq` | 2.19.5 (PyPI) | Redis-backed job queue (Python) | Active maintenance (Feb 2026 release); BullMQ Python is the only Redis-native queue that shares protocol with Node workers |
| `redis` | latest | BullMQ backing store | Required by BullMQ Python; run as Docker service |
| `stripe` | latest | Stripe payments | Official Stripe SDK; `stripe.checkout.Session.create()` + webhook verify |
| `sentry-sdk` | latest | Error tracking | Official SDK; FastAPI auto-detected when both are installed |
| `Pillow` | >=10.0.0 (already implicit) | Image watermarking | Standard Python image library; alpha composite for text watermarks |
| `c2pa-python` | latest | C2PA metadata embedding | Official C2PA tooling; requires Python 3.10+; MIT/Apache dual license |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `httpx` | >=0.27.0 (already in reqs) | Download image from Replicate URL | Already in requirements; async-capable |
| `python-multipart` | already in reqs | File upload handling | Already present |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| BullMQ Python | Celery + Redis | Celery is more mature but doesn't share queue format with Node.js; BullMQ is the spec choice |
| BullMQ Python | arq (Python async) | arq has no Python-to-Node interop; BullMQ chosen per CONTEXT.md |
| Replicate FLUX | Stability AI SDXL direct | SDXL on Replicate also supported; swappable via ARCH-03 provider interface |
| c2pa-python | Manual EXIF XMP metadata | c2pa-python is the standards-compliant path; manual XMP embedding is fragile |
| Pillow watermark | Invisible steganographic watermark | Visible watermark is compliance decision per CONTEXT.md |

**Installation (new packages only):**
```bash
# Backend
pip install replicate bullmq stripe sentry-sdk c2pa-python

# Redis (Docker service — no pip install needed)
```

---

## Architecture Patterns

### Recommended Project Structure

New files this phase adds to the existing backend:

```
backend/app/
├── services/
│   ├── image/                   # NEW: image generation domain
│   │   ├── __init__.py
│   │   ├── base.py              # ImageProvider Protocol (mirrors llm/base.py)
│   │   ├── replicate_provider.py  # Concrete Replicate implementation
│   │   ├── prompt_builder.py    # Construct FLUX prompt from avatar fields
│   │   └── watermark.py         # Pillow watermark + C2PA metadata helpers
│   ├── jobs/                    # NEW: BullMQ worker
│   │   ├── __init__.py
│   │   ├── queue.py             # Queue singleton (enqueue jobs)
│   │   └── worker.py            # Worker entry point (run as separate process)
│   └── billing/                 # NEW: Stripe billing
│       ├── __init__.py
│       ├── stripe_client.py     # Stripe session create + webhook verify
│       └── subscription.py      # DB read/write for subscription status
├── routers/
│   ├── billing.py               # NEW: POST /billing/checkout, POST /billing/webhook
│   └── photo.py                 # EXISTING: extend with bucket creation
├── models/
│   └── avatar.py                # EXTEND: add gender, nationality fields
├── migrations/
│   └── 004_phase7_avatar_fields.sql  # NEW
└── worker_main.py               # NEW: Docker entry point for BullMQ worker

frontend/src/
├── pages/
│   ├── AvatarSetupPage.tsx      # NEW: onboarding form + reference image preview
│   └── SubscribePage.tsx        # NEW: Stripe Checkout redirect trigger
├── App.tsx                      # EXTEND: add /avatar-setup route + paywall gate
└── api/
    ├── avatars.ts               # NEW: createAvatar, updateAvatar, generateReferenceImage
    └── billing.ts               # NEW: createCheckoutSession
```

**Docker Compose services:**
```
docker-compose.yml (root)
├── nginx       — reverse proxy, serves built frontend static files, proxy /api → backend
├── backend     — FastAPI (uvicorn + gunicorn)
├── worker      — BullMQ Python worker (same image as backend, different CMD)
├── redis       — Redis 7 Alpine (BullMQ backing store)
└── (Supabase cloud — external, no Docker service needed)
```

### Pattern 1: ImageProvider Protocol (ARCH-03)

**What:** A Python Protocol (structural typing, same as LLMProvider) that any image provider must satisfy. Concrete providers (Replicate, future) implement it without inheritance.

**When to use:** All image generation calls go through this protocol. ChatService never imports Replicate directly.

```python
# backend/app/services/image/base.py
from typing import Protocol, runtime_checkable
from dataclasses import dataclass

@dataclass
class GeneratedImage:
    url: str           # Replicate output URL (temporary, ~1 hour TTL)
    model: str         # e.g. "black-forest-labs/flux-1.1-pro"
    prompt: str        # Full prompt used

@runtime_checkable
class ImageProvider(Protocol):
    """
    Structural interface for image generation providers (ARCH-03).
    Any class with async generate() satisfies this Protocol.
    """
    async def generate(
        self,
        prompt: str,
        aspect_ratio: str = "2:3",  # portrait default for avatar photos
    ) -> GeneratedImage:
        ...
```

### Pattern 2: LLM Tool Call for send_photo

**What:** In intimate mode, the LLM call includes a `send_photo` tool definition. When the LLM decides a photo is appropriate, it returns a `tool_calls` response instead of plain text. ChatService detects this, enqueues a BullMQ job, and returns a placeholder message to the user.

**When to use:** Only in `ConversationMode.INTIMATE`. Tool definition added to the `chat.completions.create()` call.

```python
# Pattern for extending openai_provider.py or adding to ChatService intimate path

SEND_PHOTO_TOOL = {
    "type": "function",
    "function": {
        "name": "send_photo",
        "description": (
            "Send an AI-generated photo of yourself to the user. "
            "Use when the conversation calls for a visual moment — "
            "the user asks for a photo, or you decide the moment is right. "
            "Describe the scene/pose/setting in detail."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "scene_description": {
                    "type": "string",
                    "description": (
                        "Detailed description of the photo scene: "
                        "setting, lighting, pose, mood, what avatar is wearing/doing."
                    ),
                },
            },
            "required": ["scene_description"],
        },
    },
}

# In intimate mode LLM call:
response = await client.chat.completions.create(
    model=model,
    messages=full_messages,
    tools=[SEND_PHOTO_TOOL],
    tool_choice="auto",
)

# Check for tool call:
choice = response.choices[0]
if choice.finish_reason == "tool_calls":
    tool_call = choice.message.tool_calls[0]
    if tool_call.function.name == "send_photo":
        import json
        args = json.loads(tool_call.function.arguments)
        scene = args["scene_description"]
        # Enqueue BullMQ job, return placeholder text to user
```

### Pattern 3: BullMQ Job Enqueue and Worker

**What:** The main FastAPI process enqueues photo jobs to Redis via BullMQ Queue. A separate worker process consumes them.

```python
# backend/app/services/jobs/queue.py
from bullmq import Queue

_photo_queue: Queue | None = None

def get_photo_queue() -> Queue:
    global _photo_queue
    if _photo_queue is None:
        _photo_queue = Queue(
            "photo_generation",
            {"connection": {"host": "redis", "port": 6379}},
        )
    return _photo_queue

async def enqueue_photo_job(
    user_id: str,
    scene_description: str,
    avatar: dict,
    channel: str,  # "web" or "whatsapp"
) -> None:
    queue = get_photo_queue()
    await queue.add(
        "generate_photo",
        {
            "user_id": user_id,
            "scene_description": scene_description,
            "avatar": avatar,
            "channel": channel,
        },
        {
            "attempts": 3,
            "backoff": {"type": "exponential", "delay": 2000},
            "removeOnComplete": 100,  # keep last 100 completed jobs
            "removeOnFail": 200,      # keep last 200 failed jobs for inspection
        },
    )
```

```python
# backend/worker_main.py  (Docker CMD: python worker_main.py)
import asyncio
import logging
from bullmq import Worker
from app.services.jobs.processor import process_photo_job

logging.basicConfig(level=logging.INFO)

async def main():
    worker = Worker(
        "photo_generation",
        process_photo_job,
        {
            "connection": {"host": "redis", "port": 6379},
            "concurrency": 3,  # Claude's discretion: 3 concurrent image jobs
        },
    )
    # Worker runs until process exits
    await asyncio.Future()  # block forever

if __name__ == "__main__":
    asyncio.run(main())
```

### Pattern 4: Stripe Checkout Session + Webhook

**What:** Single endpoint creates Stripe Checkout Session in `subscription` mode. Webhook endpoint verifies signature and updates subscription status in DB.

```python
# backend/app/routers/billing.py

import stripe
from fastapi import APIRouter, Depends, Request, HTTPException
from app.config import settings
from app.dependencies import get_current_user

router = APIRouter(prefix="/billing", tags=["billing"])
stripe.api_key = settings.stripe_secret_key

@router.post("/checkout")
async def create_checkout_session(user=Depends(get_current_user)):
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{
            "price": settings.stripe_price_id,  # from env — config-driven (BILL-02)
            "quantity": 1,
        }],
        success_url=f"{settings.frontend_url}/chat?subscribed=1",
        cancel_url=f"{settings.frontend_url}/subscribe?cancelled=1",
        client_reference_id=str(user.id),  # link Stripe session to our user
        metadata={"user_id": str(user.id)},
    )
    return {"checkout_url": session.url}

@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"]["user_id"]
        customer_id = session["customer"]
        subscription_id = session["subscription"]
        # Write to subscriptions table in DB
        await _activate_subscription(user_id, customer_id, subscription_id)

    elif event["type"] == "invoice.payment_failed":
        subscription_id = event["data"]["object"]["subscription"]
        await _deactivate_subscription(subscription_id)

    return {"received": True}
```

### Pattern 5: Pillow Watermark

**What:** Download image bytes from Replicate output URL, apply visible text watermark at bottom-right with semi-transparency, save as JPEG.

```python
# backend/app/services/image/watermark.py
from PIL import Image, ImageDraw, ImageFont
import io

def apply_watermark(image_bytes: bytes, text: str = "© Ava") -> bytes:
    """Apply semi-transparent text watermark. Returns JPEG bytes."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Position: bottom-right margin
    font_size = max(img.width // 40, 14)  # scale with image
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    margin = font_size
    x = img.width - text_w - margin
    y = img.height - text_h - margin

    draw.text((x, y), text, font=font, fill=(255, 255, 255, 180))  # 180/255 opacity
    watermarked = Image.alpha_composite(img, overlay).convert("RGB")

    output = io.BytesIO()
    watermarked.save(output, format="JPEG", quality=90)
    return output.getvalue()
```

### Pattern 6: Subscription Gate (FastAPI Dependency)

**What:** A FastAPI dependency that checks if the current user has an active subscription. Used on chat endpoints.

```python
# backend/app/dependencies.py (extend existing file)
from fastapi import Depends, HTTPException
from app.database import supabase_admin

async def require_active_subscription(user=Depends(get_current_user)):
    """Raises 402 if the user has no active subscription."""
    result = (
        supabase_admin.from_("subscriptions")
        .select("status")
        .eq("user_id", str(user.id))
        .maybe_single()
        .execute()
    )
    sub = result.data
    if not sub or sub.get("status") != "active":
        raise HTTPException(
            status_code=402,
            detail="Subscription required. Visit /subscribe to activate.",
        )
    return user
```

### Anti-Patterns to Avoid

- **Calling Replicate synchronously from FastAPI request handler:** Blocks the event loop for 10-30 seconds during image generation. Always enqueue a BullMQ job and return immediately.
- **Hardcoding Stripe Price IDs:** Violates BILL-02. Always read from `settings.stripe_price_id` (env var).
- **Storing Replicate output URLs as permanent photo links:** Replicate URLs expire after ~1 hour. Always download, watermark, upload to Supabase Storage, and use the Supabase signed URL.
- **Running BullMQ worker inside the FastAPI process:** Worker is CPU/IO-bound during image generation. Run as a separate Docker service with its own container.
- **Importing Redis/BullMQ in main FastAPI app:** Only the worker process needs BullMQ Worker; the web process only needs BullMQ Queue (enqueue side).
- **Checking subscription status on every message via DB call:** Cache subscription status in session store or use short-lived JWT claims if performance becomes an issue.
- **Verifying Stripe webhooks without the raw body:** `stripe.Webhook.construct_event()` requires the raw bytes. FastAPI must read `await request.body()` BEFORE any JSON parsing.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Job queue with retries | Custom asyncio queue with retry loop | BullMQ Python + Redis | Exponential backoff, dead-letter queue, job TTL, concurrency — all built-in |
| Stripe webhook signature verification | Custom HMAC comparison | `stripe.Webhook.construct_event()` | Handles timing attacks, encoding edge cases, replay prevention |
| Image watermarking | Custom PNG/JPEG bit manipulation | Pillow `alpha_composite` | Standard library; handles all pixel formats, color modes, EXIF |
| C2PA metadata | Custom XMP/EXIF editing | `c2pa-python` library | Standards-compliant; required for actual C2PA verification tools to recognize metadata |
| Subscription state machine | Custom status tracking | Stripe webhooks + `subscriptions` table | Stripe handles payment retry logic, dunning, failed payment recovery |
| Replicate polling | Custom HTTP polling loop | `replicate.predictions.create(webhook=...)` | Replicate pushes completion via webhook; polling wastes resources and has race conditions |

**Key insight:** Every component in this phase has a battle-tested external solution. The phase's value is wiring them together correctly, not building infrastructure.

---

## Common Pitfalls

### Pitfall 1: Replicate Output URL Expiry
**What goes wrong:** Worker stores the direct Replicate output URL in the DB and sends it to the user. URL expires after ~1 hour. User gets a broken image link.
**Why it happens:** Replicate returns a temporary CDN URL, not a permanent storage URL.
**How to avoid:** Worker downloads image bytes with `httpx`, applies watermark, uploads to Supabase Storage `photos` bucket, generates Supabase signed URL (24h). Store the Supabase path in DB, generate signed URL on demand.
**Warning signs:** Photo visible immediately after generation but broken 2 hours later.

### Pitfall 2: Missing Supabase Storage Bucket
**What goes wrong:** `photo.py` signed URL endpoint returns 500 because the `photos` bucket doesn't exist. This was noted in STATE.md from Phase 6.
**Why it happens:** Supabase Storage buckets must be created manually or via API before upload. The bucket was deferred to Phase 7.
**How to avoid:** First task in Phase 7 is creating the `photos` private bucket in Supabase Dashboard (or via `supabase_admin.storage.create_bucket()`).
**Warning signs:** `StorageApiError: The resource was not found` on upload or signed URL calls.

### Pitfall 3: LLM Tool Call in Intimate Mode Breaking Existing History
**What goes wrong:** After adding `tools=[SEND_PHOTO_TOOL]` to the intimate mode LLM call, previous conversation history that has `tool_calls` in assistant messages causes OpenAI to return errors on replay.
**Why it happens:** OpenAI requires that if a message with `tool_calls` exists in history, the next message must be a `tool` role message with the result. Session history only stores `user`/`assistant` text messages.
**How to avoid:** When the LLM returns a `tool_calls` response, do NOT append the raw `tool_calls` message to session history. Instead, append a synthetic `assistant` text message (the placeholder "I'm sending you a photo...") to maintain clean history.

### Pitfall 4: Stripe Webhook Raw Body Consumed by FastAPI
**What goes wrong:** `stripe.Webhook.construct_event()` fails with a signature error even when the secret is correct.
**Why it happens:** If any FastAPI middleware or dependency reads and parses the body as JSON before the webhook handler runs, the raw bytes are consumed. Stripe signature verification requires the original raw bytes.
**How to avoid:** Webhook endpoint uses `Request` directly and calls `await request.body()` as the first statement. No JSON middleware on this route. Add `content_type` check: only accept `application/json` with raw body.

### Pitfall 5: BullMQ Python Worker Not Seeing Jobs
**What goes wrong:** Jobs are added to the queue but the worker never processes them.
**Why it happens:** BullMQ Python defaults to `decode_responses=False` on the Redis connection. If the enqueue side uses different serialization, jobs appear with different key formats.
**How to avoid:** Use the same connection options on both Queue (enqueue) and Worker. Pass `{"connection": {"host": "redis", "port": 6379}}` as a dict (not a Redis client instance) to both.

### Pitfall 6: Avatar Fields Missing from Image Prompt
**What goes wrong:** Generated photos don't look consistent with the avatar definition. Gender, nationality, and appearance description are set but not used in the FLUX prompt.
**Why it happens:** `prompt_builder.py` wasn't wired into the worker's Replicate call, or the avatar dict fetched by the worker is incomplete.
**How to avoid:** Worker receives the full `avatar` dict (including all new fields) as part of the job payload. `prompt_builder.py` constructs the full FLUX prompt before calling Replicate.

### Pitfall 7: Onboarding Gate Redirect Loop
**What goes wrong:** User hits `/chat`, gets redirected to `/avatar-setup`, completes setup, but gets sent back to `/avatar-setup` again.
**Why it happens:** The frontend onboarding gate checks avatar existence via API but the response is stale (React Query cache not invalidated after avatar creation).
**How to avoid:** After successful avatar creation + reference image approval, call `queryClient.invalidateQueries({ queryKey: ['avatar'] })` before navigating to `/chat`.

### Pitfall 8: `avatar` Table Missing `gender` and `nationality` Columns
**What goes wrong:** Phase 7 starts using `avatar.gender` and `avatar.nationality` but the DB schema has neither. Inserts fail silently or raise 500 errors.
**Why it happens:** Migration 004 hasn't been applied, or `AvatarCreate` Pydantic model wasn't updated to match.
**How to avoid:** First backend task: write and apply `004_phase7_avatar_fields.sql` adding `gender TEXT` and `nationality TEXT` columns to `avatars` table. Update `AvatarCreate`, `AvatarResponse` models simultaneously.

---

## Code Examples

Verified patterns from official sources and existing codebase:

### FLUX Image Generation via Replicate (async)
```python
# Source: github.com/replicate/replicate-python README
import replicate

async def generate_image(prompt: str) -> str:
    """Returns the Replicate output URL (temporary — download immediately)."""
    output = await replicate.async_run(
        "black-forest-labs/flux-1.1-pro",
        input={
            "prompt": prompt,
            "aspect_ratio": "2:3",   # portrait for avatar photos
            "output_format": "jpeg",
            "output_quality": 90,
        },
    )
    # output is a FileOutput object in replicate v1.0+
    # output.url gives the CDN URL
    return str(output)
```

### Avatar Prompt Construction
```python
# backend/app/services/image/prompt_builder.py
def build_avatar_prompt(avatar: dict, scene_description: str) -> str:
    """
    Construct FLUX prompt from avatar fields + scene description.
    Called by the BullMQ worker before Replicate API call.
    """
    name = avatar.get("name", "woman")
    gender = avatar.get("gender", "woman")
    age = avatar.get("age", 25)
    nationality = avatar.get("nationality", "")
    appearance = avatar.get("physical_description", "")

    # Base character description (consistent anchor)
    character_parts = [
        f"Photo of {name},",
        f"a {age}-year-old {nationality} {gender}," if nationality else f"a {age}-year-old {gender},",
    ]
    if appearance:
        character_parts.append(appearance + ",")

    # Scene from LLM tool call
    character_parts.append(scene_description)

    # Quality anchors for photorealism
    character_parts.extend([
        "photorealistic, professional photography,",
        "high detail, natural lighting",
    ])

    return " ".join(character_parts)
```

### Stripe Checkout Session (Python SDK)
```python
# Source: docs.stripe.com/api/checkout/sessions/create
import stripe

session = stripe.checkout.Session.create(
    mode="subscription",
    line_items=[{"price": price_id, "quantity": 1}],
    success_url="https://example.com/chat?subscribed=1",
    cancel_url="https://example.com/subscribe",
    client_reference_id=user_id,
    metadata={"user_id": user_id},
)
# session.url is the Stripe-hosted checkout page URL
```

### Stripe Webhook Verification
```python
# Source: docs.stripe.com/webhooks
event = stripe.Webhook.construct_event(
    payload=raw_body_bytes,
    sig_header=request.headers.get("stripe-signature"),
    secret=settings.stripe_webhook_secret,
)
# event["type"] is e.g. "checkout.session.completed"
```

### Sentry FastAPI Setup
```python
# Source: docs.sentry.io/platforms/python/integrations/fastapi/
# backend/app/main.py — call before app = FastAPI()
import sentry_sdk

sentry_sdk.init(
    dsn=settings.sentry_dsn,       # from env, empty string = disabled in dev
    environment=settings.app_env,  # "development" | "production"
    traces_sample_rate=0.1,        # 10% of requests for performance monitoring
)
# FastAPI integration activates automatically — no explicit FastApiIntegration() needed
# unless custom transaction_style is required
```

### DB Migration: Avatar Fields
```sql
-- backend/migrations/004_phase7_avatar_fields.sql
BEGIN;

ALTER TABLE public.avatars
  ADD COLUMN IF NOT EXISTS gender      TEXT,
  ADD COLUMN IF NOT EXISTS nationality TEXT;

-- Note: both nullable — existing avatars (from Phase 2 testing) keep their rows
-- Phase 7 avatar setup form collects these fields; they're required in the form
-- but nullable in DB to avoid breaking existing data

COMMIT;
```

### Docker Compose (production layout)
```yaml
# docker-compose.yml (root)
version: "3.9"
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
    depends_on:
      - backend

  backend:
    build: ./backend
    env_file: ./backend/.env
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    restart: unless-stopped

  worker:
    build: ./backend
    command: python worker_main.py
    env_file: ./backend/.env
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    # No port exposure needed — only internal services connect
```

### BullMQ Python: Enqueue with Retry Config
```python
# Source: docs.bullmq.io/python/introduction + CONTEXT.md decisions
await queue.add(
    "generate_photo",
    job_data,
    {
        "attempts": 3,
        "backoff": {"type": "exponential", "delay": 2000},  # 2s, 4s, 8s
        "removeOnComplete": 100,
        "removeOnFail": 200,
    },
)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Stripe direct charge API | Stripe Checkout (hosted UI) | ~2020 | Stripe handles PCI compliance, 3DS, card UI — no custom payment form needed |
| Replicate polling loop | Replicate webhook callback OR `async_run()` | 2023 | No busy-waiting; fire-and-forget with callback |
| SDXL for avatar photos | FLUX 1.1 Pro | Late 2024 | FLUX produces more photorealistic results; 6x faster than predecessor |
| Replicate client returns URL strings | Returns `FileOutput` objects | v1.0.0 | Must call `str(output)` or `await output.aread()` to get URL/bytes |
| sentry-sdk manual FastAPI middleware | Auto-detection when both packages installed | 2023 | Just `sentry_sdk.init(dsn=...)` is sufficient |

**Deprecated/outdated:**
- `replicate.run()` (synchronous): use `replicate.async_run()` in FastAPI async context to avoid blocking the event loop.
- Stripe `stripe.api_key = key` global + `stripe.checkout.Session.create()`: still works but Stripe now also offers `StripeClient(api_key)` instance pattern — global is fine for this scale.

---

## Open Questions

1. **Replicate FLUX model ID for NSFW content**
   - What we know: `black-forest-labs/flux-1.1-pro` is the standard model. Replicate has NSFW-capable models but they may require explicit account approval.
   - What's unclear: Whether the Replicate account needs special verification for adult content; which specific model ID to use.
   - Recommendation: Start with `flux-1.1-pro`; if content is rejected by Replicate's safety filters, investigate `black-forest-labs/flux-1.1-pro-ultra` or SDXL alternatives. The ImageProvider abstraction (ARCH-03) makes swapping trivial.

2. **C2PA signing certificate requirement**
   - What we know: `c2pa-python` can embed C2PA manifests. Creating a *valid, verifiable* C2PA manifest requires a signing certificate (X.509).
   - What's unclear: Whether the CONTEXT.md compliance requirement means "embed metadata fields" (no cert needed) or "create cryptographically signed manifests" (requires CA cert).
   - Recommendation: For beta, embed C2PA-formatted metadata without a trusted CA signature (self-signed or unsigned manifest). Document this as a known limitation. Full CA-signed C2PA is a post-beta hardening task.

3. **BullMQ Python worker process stability on Windows dev vs Linux prod**
   - What we know: BullMQ Python uses asyncio; the worker runs as a long-lived process.
   - What's unclear: The dev environment is Windows (per env context); BullMQ Python may behave differently on Windows event loops.
   - Recommendation: Do all BullMQ worker testing inside Docker (Linux container) even during local development. Document this in .env.example and docker-compose.

4. **Subscription gate: when to check (per-request vs. cached)**
   - What we know: The subscription dependency reads from DB on every request. At beta scale this is fine.
   - What's unclear: If subscription check adds 50ms+ per request, it may degrade UX.
   - Recommendation: Simple DB check via supabase_admin for beta. Cache in session store if latency becomes observable. Flag for optimization post-beta.

---

## Sources

### Primary (HIGH confidence)
- github.com/replicate/replicate-python README — async_run(), FileOutput, webhook patterns, v1.0.0 breaking changes
- docs.bullmq.io/python/introduction — Queue, Worker, Python API basics
- docs.bullmq.io/python/changelog — v2.19.5 (latest, Feb 11 2026)
- docs.stripe.com/api/checkout/sessions/create — Session.create() Python code, subscription mode
- docs.stripe.com/webhooks — construct_event() signature verification
- docs.sentry.io/platforms/python/integrations/fastapi/ — auto-detection, minimal init pattern
- supabase.com/docs/reference/python/storage-from-upload — upload() API, path format, file_options
- opensource.contentauthenticity.org/docs/c2pa-python/ — install command, capabilities

### Secondary (MEDIUM confidence)
- replicate.com/docs/topics/predictions/create-a-prediction — async mode + webhook pattern (partially verified via official docs)
- Pillow alpha_composite watermark pattern — verified across multiple official and tutorial sources
- Docker Compose FastAPI + Redis + worker pattern — verified against official FastAPI Docker docs

### Tertiary (LOW confidence)
- Replicate FLUX model ID `black-forest-labs/flux-1.1-pro` — seen on replicate.com but exact input params (aspect_ratio, output_format) not fully verified from official API reference; validate during implementation
- C2PA unsigned manifest approach for beta — project-specific interpretation; validate with compliance requirements

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified via official docs/PyPI/changelogs
- Architecture: MEDIUM-HIGH — patterns derived from official docs + existing codebase conventions; LLM tool call pattern for send_photo is training knowledge (verified against OpenAI function calling docs conceptually)
- Pitfalls: HIGH — most derived from STATE.md notes (Replicate URL expiry, missing bucket noted explicitly), plus verified library-specific gotchas

**Research date:** 2026-02-25
**Valid until:** 2026-03-25 (30 days — Replicate model IDs and Stripe API are stable; BullMQ Python fast-moving but major patterns stable)
