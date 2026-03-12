# Phase 16: Async Chat Architecture — Immediate User Bubble, Background AI Reply - Research

**Researched:** 2026-03-11
**Domain:** FastAPI BackgroundTasks, React Query v5 cache mutation, async message flow
**Confidence:** HIGH

## Summary

The current POST /chat endpoint runs synchronously: it calls the LLM (~2-10s), waits for the full reply, then inserts both the user message and assistant reply into the DB in a single batch, and finally returns `{ reply: string }`. This means the user's own message does not exist in the DB until the AI has finished. The frontend compensates with an `onMutate` optimistic update, but the 3-second polling interval clobbers that fake bubble with real DB data that doesn't yet contain the user message — causing the bubble to flash off and reappear.

The fix has two parts. On the backend: split the single synchronous operation into (1) insert user message immediately and return it as the HTTP response body, then (2) kick off the LLM + assistant-reply insert as a fire-and-forget async task. On the frontend: drop the `onMutate` hack entirely. The `onSuccess` callback receives the real user message row returned by the server and appends it to the React Query cache via `setQueryData`. The 3-second poll does the honest work of picking up the assistant reply when it lands.

The project already has a **confirmed bug** with FastAPI `BackgroundTasks` + CORSMiddleware: tasks tied to the request lifecycle are silently cancelled by `asyncio.CancelledError` when the HTTP connection closes. This was fixed in `avatars.py` (Phase 07) using `asyncio.ensure_future()`. The same pattern MUST be applied here. For the chat background task, the response is returned after inserting the user message (a fast synchronous DB write), and the long-running LLM call starts after. The risk of cancellation is real because CORS middleware closes the connection before the background task finishes — `asyncio.ensure_future()` is the proven fix in this codebase.

**Primary recommendation:** In POST /chat, insert user message synchronously and return it; schedule LLM + assistant insert with `asyncio.ensure_future()` (NOT FastAPI `BackgroundTasks`). In `useSendMessage`, remove `onMutate`, add `onSuccess` that calls `setQueryData` to append the returned user message row. No changes to GET /chat/history or polling interval.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CHAT-01 | POST /chat inserts the user message into DB immediately and returns the user message row (id, role, content, created_at) — not the AI reply | Backend split pattern: synchronous user-message insert + asyncio.ensure_future() for LLM task |
| CHAT-02 | AI reply is generated in a background task and inserted into DB when ready — polling picks it up on the next cycle | asyncio.ensure_future() pattern from avatars.py Phase 07 — decouples LLM latency from HTTP response |
| CHAT-03 | Frontend displays user bubble immediately on send (from onSuccess, not onMutate) and AI reply appears when poll retrieves it — no optimistic hack | React Query v5 setQueryData in onSuccess; drop onMutate entirely |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.131.0 (installed) | HTTP router, dependency injection | Already the project's web framework |
| asyncio | stdlib | `ensure_future()` for fire-and-forget tasks | Proven fix for CORSMiddleware task-cancellation bug in this codebase |
| @tanstack/react-query | ^5.90.21 (installed) | Server state, polling, cache mutation | Already the project's data-fetching library |
| supabase-py | 2.25.1 (installed) | DB insert for messages table | Already the project's DB client |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-jose / FastAPI Depends | already used | Auth dependency on POST /chat | Unchanged — `require_active_subscription` stays on POST /chat |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `asyncio.ensure_future()` | FastAPI `BackgroundTasks` | BackgroundTasks silently cancelled on connection close with CORSMiddleware present — KNOWN BUG in this codebase (avatars.py comment). Do NOT use. |
| `asyncio.ensure_future()` | `asyncio.create_task()` | `create_task()` is the modern equivalent and preferred in Python 3.10+; either works inside an async context. `ensure_future()` is what this codebase already uses. |
| polling | WebSockets / SSE | WebSockets/SSE add connection-state complexity; polling is already working at 3s interval and is sufficient |

**Installation:** No new packages required. All libraries already installed.

## Architecture Patterns

### Target Flow

```
POST /chat:
  1. Authenticate (require_active_subscription) — unchanged
  2. Fetch avatar — unchanged
  3. INSERT user message row into messages table (synchronous, fast ~10ms)
  4. asyncio.ensure_future(_run_llm_and_insert(user_id, text, avatar))
  5. Return the inserted user message row: {id, role, content, created_at}

_run_llm_and_insert(user_id, text, avatar):
  1. await _web_adapter.receive(msg)   # LLM call, 2-10s
  2. INSERT assistant reply into messages table
  (runs independently — NOT tied to request lifecycle)

GET /chat/history:
  No changes. Returns all messages for user ordered by created_at ASC.
  Poll at 3s picks up user message immediately after POST returns.
  Poll picks up assistant reply ~2-10s later when background task writes it.
```

### Pattern 1: asyncio.ensure_future for Fire-and-Forget LLM Task

**What:** Schedule an independent coroutine that is NOT a child of the current request Task. Immune to connection-close cancellation.
**When to use:** Any time a long-running async operation must survive after the HTTP response is sent, especially when CORSMiddleware is present (which it is in this project via `main.py`).
**Example:**
```python
# Source: avatars.py in this codebase (Phase 07 BUG FIX, confirmed working in production)
import asyncio

async def _run_llm_and_insert(user_id: str, text: str, avatar: dict | None) -> None:
    """
    Background task: call LLM, insert assistant reply into DB.
    Runs as an independent asyncio Task — not cancelled on connection close.
    All exceptions caught — never propagates to the event loop.
    """
    try:
        msg = NormalizedMessage(
            user_id=user_id,
            text=text,
            platform="web",
            timestamp=datetime.now(timezone.utc),
        )
        reply_text = await _web_adapter.receive(msg)
        # Insert assistant reply
        avatar_obj = avatar or await get_avatar_for_user(user_id)
        supabase_admin.from_("messages").insert({
            "user_id": user_id,
            "avatar_id": avatar_obj["id"] if avatar_obj else None,
            "channel": "web",
            "role": "assistant",
            "content": reply_text,
        }).execute()
    except Exception as e:
        logger.error(f"Background LLM task failed for user {user_id}: {e}")


@router.post("")
async def send_message(body: ChatRequest, user=Depends(require_active_subscription)):
    user_id = str(user.id)
    avatar = await get_avatar_for_user(user_id)

    # Step 1: Insert user message immediately
    result = supabase_admin.from_("messages").insert({
        "user_id": user_id,
        "avatar_id": avatar["id"] if avatar else None,
        "channel": "web",
        "role": "user",
        "content": body.text,
    }).execute()
    user_row = result.data[0]  # {id, role, content, created_at, ...}

    # Step 2: Fire LLM + assistant-reply insert as independent task
    asyncio.ensure_future(_run_llm_and_insert(user_id, body.text, avatar))

    # Step 3: Return the user message row — frontend appends it to cache immediately
    return {
        "id": user_row["id"],
        "role": user_row["role"],
        "content": user_row["content"],
        "created_at": user_row["created_at"],
    }
```

### Pattern 2: React Query v5 onSuccess with setQueryData (no onMutate)

**What:** `onSuccess` receives the real server response (the user message row). Append it to the local cache immediately. Poll does the rest — no optimistic hacks.
**When to use:** When the server returns real data on mutation success that should be injected into a list cache without triggering a full refetch.

```typescript
// Source: @tanstack/react-query v5 docs — queryClient.setQueryData with updater function
export function useSendMessage(token: string | null, options?: UseSendMessageOptions) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (text: string) =>
      fetch('/chat', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      }).then(async r => {
        if (!r.ok) {
          const body = await r.json().catch(() => ({ detail: 'Failed to send message' }))
          throw new ApiError(body.detail || 'Failed to send message', r.status)
        }
        return r.json() as Promise<ChatMessage>  // NOW returns ChatMessage, not { reply: string }
      }),
    // onMutate: REMOVED — no optimistic hack
    onSuccess: (userMessage: ChatMessage) => {
      // Append the real user message row to the cache immediately
      queryClient.setQueryData<ChatMessage[]>(['chat-history'], prev => [
        ...(prev ?? []),
        userMessage,
      ])
      // Do NOT invalidate — polling at 3s will pick up the assistant reply
    },
    onError: options?.onError,
  })
}
```

### Anti-Patterns to Avoid

- **Using FastAPI `BackgroundTasks`:** Silently cancelled by CORSMiddleware on connection close. The codebase already hit this bug in Phase 07 (`avatars.py` BUG FIX comment). Use `asyncio.ensure_future()` instead.
- **Keeping `onMutate` alongside the new `onSuccess`:** If both are present, the optimistic bubble (temp id `optimistic-${Date.now()}`) will coexist with the real row from `onSuccess`, causing a duplicate bubble until the next poll merges state. Drop `onMutate` entirely.
- **Calling `invalidateQueries` in `onSuccess`:** This triggers a full refetch immediately after the user message is appended. The refetch will include the user message but NOT the assistant reply yet (background task still running). This is a no-op improvement over the current state. Just use `setQueryData` to append the user message and let the 3s poll do the rest.
- **Inserting both messages in the background task:** The user message MUST be inserted synchronously before the response is returned. If the background task inserts the user message, there's a race: the poll at t+3s may fire before the background task writes it, causing a flash where the user sees no bubble for 3s.
- **Catching `BaseException` in the background task:** `asyncio.CancelledError` is a `BaseException` (not `Exception`). `except Exception` does NOT catch it. For `asyncio.ensure_future()` tasks, the task is an independent `Task` object that is not cancelled by connection close — so this is safe. But if there's any internal `await` that you want protected, use `except Exception` (not `except BaseException`) to avoid masking real cancellations.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Background LLM execution | Custom thread pool, queue, or subprocess | `asyncio.ensure_future()` | Single-process FastAPI + asyncio; no Redis/BullMQ overhead; LLM call is already async (AsyncOpenAI) |
| Frontend cache append | Manual DOM state / useReducer | `queryClient.setQueryData()` | React Query manages stale-time, deduplication, and poll merge automatically |
| Real-time assistant reply delivery | WebSockets, SSE, long-polling | Existing 3s `refetchInterval` poll | Already implemented; adding streaming would require significant infrastructure change |

**Key insight:** This is a surgical refactor of data flow, not a new architecture. The existing polling, DB schema, auth, and session management are all unchanged.

## Common Pitfalls

### Pitfall 1: FastAPI BackgroundTasks + CORSMiddleware Cancellation
**What goes wrong:** LLM call starts, HTTP connection closes after 202/200 response, Starlette propagates `asyncio.CancelledError` into the background task at the first `await`. Task dies silently. No assistant reply ever written to DB.
**Why it happens:** `BackgroundTasks` tasks are children of the request `Task`. CORSMiddleware (Starlette `HTTPMiddleware`) closes the connection, which cancels the parent Task tree.
**How to avoid:** Use `asyncio.ensure_future()` — creates an independent `Task` that is NOT a child of the request Task. Cannot be cancelled by connection close.
**Warning signs:** Assistant reply never appears in DB after a POST /chat that returned 200. No error logs (because `CancelledError` is `BaseException`, not caught by `except Exception`).

**This bug is CONFIRMED in this codebase** (avatars.py Phase 07 BUG FIX comment). Do not use `BackgroundTasks` for long-running async tasks.

### Pitfall 2: Duplicate User Bubble from Residual onMutate
**What goes wrong:** `onMutate` inserts an optimistic message with `id: "optimistic-${Date.now()}"`. `onSuccess` appends the real row. Poll returns the real row again. User sees two identical messages for 3 seconds.
**Why it happens:** The optimistic row and the real row have different IDs, so React's key reconciliation won't merge them. Poll data replaces the whole cache, dropping the optimistic row but the real row was already appended by `onSuccess`, so it stays.
**How to avoid:** Remove `onMutate` entirely when switching to server-driven bubble. The `onSuccess` handler is the only place that touches the cache.
**Warning signs:** User sees their message appear twice briefly after sending.

### Pitfall 3: Background Task Uses supabase_admin Synchronously — No Event Loop Issue
**What goes wrong (misconception):** Thinking `supabase_admin` sync client will block the event loop when called from a background task.
**Reality:** The background task is an asyncio coroutine (`async def`). The sync supabase client calls do run on the event loop thread, but they are fast (~10ms DB insert). The LLM call uses `AsyncOpenAI` which is truly async. This is the same pattern used in `web_chat.py` today — sync Supabase inserts inside async handlers. It's acceptable.
**If it becomes an issue:** Wrap sync DB calls in `asyncio.to_thread()` (pattern already established in Phase 04 for Google Auth).

### Pitfall 4: Supabase insert().execute() not returning id/created_at
**What goes wrong:** The `insert()` call returns data only if Supabase is configured to return it, and only the columns selected.
**Why it happens:** Supabase PostgREST returns the inserted row by default when called via the Python client with `.execute()`. The `messages` table has `DEFAULT uuid_generate_v4()` for `id` and `DEFAULT NOW()` for `created_at` — these are DB-generated, so the Python dict sent to insert does NOT have them. Supabase returns the full row.
**How to avoid:** Trust the PostgREST default (returning the inserted row). Access `result.data[0]` to get `{id, user_id, avatar_id, channel, role, content, created_at}`.
**Warning signs:** KeyError on `result.data[0]["id"]` — means insert failed or returned empty. Add error handling: `if not result.data: raise HTTPException(...)`.

### Pitfall 5: mutationFn return type mismatch
**What goes wrong:** `mutationFn` currently returns `Promise<{ reply: string }>`. After the backend change, it must return `Promise<ChatMessage>`. If the TypeScript type is not updated, `onSuccess(data)` will be typed as `{ reply: string }` and the `setQueryData` append will receive the wrong object.
**How to avoid:** Update the `mutationFn` return type in `useSendMessage` from `Promise<{ reply: string }>` to `Promise<ChatMessage>`. The `ChatMessage` interface already exists in `chat.ts`.
**Warning signs:** TypeScript compiler error on `onSuccess: (userMessage: ChatMessage)` — `data` has type `{ reply: string }` not `ChatMessage`.

## Code Examples

### Backend: send_message router (after refactor)
```python
# Source: this codebase, based on avatars.py asyncio.ensure_future() pattern
import asyncio
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.dependencies import get_current_user, get_authed_supabase, require_active_subscription
from app.adapters.base import NormalizedMessage
from app.adapters.web_adapter import WebAdapter
from app.services.user_lookup import get_avatar_for_user
from app.database import supabase_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])
from app.routers.webhook import _chat_service
_web_adapter = WebAdapter(chat_service=_chat_service)


class ChatRequest(BaseModel):
    text: str


async def _run_llm_and_insert(user_id: str, text: str, avatar: dict | None) -> None:
    """Independent asyncio Task — not cancelled by connection close."""
    try:
        msg = NormalizedMessage(
            user_id=user_id,
            text=text,
            platform="web",
            timestamp=datetime.now(timezone.utc),
        )
        reply_text = await _web_adapter.receive(msg)
        supabase_admin.from_("messages").insert({
            "user_id": user_id,
            "avatar_id": avatar["id"] if avatar else None,
            "channel": "web",
            "role": "assistant",
            "content": reply_text,
        }).execute()
    except Exception as e:
        logger.error(f"Background LLM task failed for user {user_id}: {e}")


@router.post("")
async def send_message(
    body: ChatRequest,
    user=Depends(require_active_subscription),
):
    user_id = str(user.id)
    avatar = await get_avatar_for_user(user_id)

    # Insert user message immediately — before LLM starts
    result = supabase_admin.from_("messages").insert({
        "user_id": user_id,
        "avatar_id": avatar["id"] if avatar else None,
        "channel": "web",
        "role": "user",
        "content": body.text,
    }).execute()

    if not result.data:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Failed to save message")

    user_row = result.data[0]

    # Fire LLM as independent task (immune to CORSMiddleware cancellation)
    asyncio.ensure_future(_run_llm_and_insert(user_id, body.text, avatar))

    # Return the user message row — frontend uses it to show bubble immediately
    return {
        "id": user_row["id"],
        "role": user_row["role"],
        "content": user_row["content"],
        "created_at": user_row["created_at"],
    }
```

### Frontend: useSendMessage (after refactor)
```typescript
// Source: @tanstack/react-query v5 API — queryClient.setQueryData with updater
// No onMutate — no optimistic hack
export function useSendMessage(token: string | null, options?: UseSendMessageOptions) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (text: string) =>
      fetch('/chat', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      }).then(async r => {
        if (!r.ok) {
          const body = await r.json().catch(() => ({ detail: 'Failed to send message' }))
          throw new ApiError(body.detail || 'Failed to send message', r.status)
        }
        return r.json() as Promise<ChatMessage>  // ChatMessage, not { reply: string }
      }),
    // onMutate: removed — no optimistic update needed
    onSuccess: (userMessage: ChatMessage) => {
      // Append real user row to cache — no full refetch needed
      queryClient.setQueryData<ChatMessage[]>(['chat-history'], prev => [
        ...(prev ?? []),
        userMessage,
      ])
      // Assistant reply arrives via 3s poll — no action needed here
    },
    onError: options?.onError,
  })
}
```

### Existing Pattern: asyncio.ensure_future in this codebase
```python
# Source: backend/app/routers/avatars.py (Phase 07 BUG FIX — confirmed in production)
# Schedule as an independent asyncio Task -- decoupled from request lifecycle.
# asyncio.ensure_future() creates a Task on the running event loop that is NOT
# a child of the current request Task and therefore cannot be cancelled on
# connection close (unlike FastAPI BackgroundTasks with CORSMiddleware present).
asyncio.ensure_future(_generate_reference_image_task(str(user.id)))
return {"status": "generating"}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Synchronous LLM in POST /chat — block until reply | Split: insert user msg → return → background LLM | Phase 16 | User sees their own bubble instantly; no wait for AI |
| Batch insert (user + AI in one call after LLM) | Two separate inserts (user before LLM, AI after) | Phase 16 | User message always in DB regardless of LLM outcome |
| `onMutate` optimistic hack with temp ID | `onSuccess` with real row from server | Phase 16 | No ID mismatch, no flash disappear/reappear |
| `{ reply: string }` POST /chat response | `{ id, role, content, created_at }` — ChatMessage row | Phase 16 | Frontend can use real ID for React key — no temp ID collision |

**Deprecated/outdated after this phase:**
- `onMutate` in `useSendMessage`: remove entirely
- `invalidateQueries` in `onSuccess` for chat: replace with `setQueryData` append
- Batch insert of both messages at the end of POST /chat: split into two separate inserts

## Open Questions

1. **Should the background task also handle the `_rewrite_photo_paths` logic for photos?**
   - What we know: `_rewrite_photo_paths` runs on `GET /chat/history` at read time — it rewrites `[PHOTO_PATH]` tokens on each poll. This is independent of the insert path.
   - What's unclear: When the background LLM task generates a photo (intimate mode), it currently enqueues a BullMQ job that writes the `[PHOTO_PATH]` token to the messages table. This existing flow is unchanged by Phase 16.
   - Recommendation: No changes needed. Photo path rewriting stays at read time in GET /chat/history.

2. **Is `asyncio.ensure_future()` safe in Uvicorn/Gunicorn multi-worker mode?**
   - What we know: The project uses Gunicorn with Uvicorn workers (`gunicorn[standard]` in requirements). `asyncio.ensure_future()` schedules on the running event loop of the current worker process.
   - What's unclear: If a request hits Worker A, `ensure_future()` runs in Worker A's event loop. The DB write goes to Supabase (shared). This is fine — each worker is an independent process with its own event loop.
   - Recommendation: No issue. Each Gunicorn worker has its own event loop; tasks are isolated per worker. The Supabase DB is the shared source of truth.

3. **Should `_web_adapter.receive()` in the background task still go through `platform_router` and `ChatService`?**
   - What we know: Yes. The existing `_web_adapter.receive()` call goes through `platform_router -> ChatService.handle_message()` which handles mode detection, session state, content guardrails, etc.
   - What's unclear: Nothing — this is unchanged. The background task calls the same code path as before, just decoupled from the HTTP request lifecycle.
   - Recommendation: Keep the exact same call chain. Only the timing and task scheduling change.

## Sources

### Primary (HIGH confidence)
- avatars.py in this codebase — `asyncio.ensure_future()` BUG FIX comment (Phase 07, confirmed working in production). Direct codebase evidence.
- backend/app/routers/web_chat.py — Current POST /chat implementation. Directly read.
- frontend/src/api/chat.ts — Current `useSendMessage` with `onMutate`. Directly read.
- backend/migrations/001_initial_schema.sql — `messages` table columns (id UUID DEFAULT uuid_generate_v4(), created_at TIMESTAMPTZ DEFAULT NOW()). Directly read.
- backend/requirements.txt — FastAPI 0.131.0, supabase 2.25.1, @tanstack/react-query ^5.90.21. Directly read.

### Secondary (MEDIUM confidence)
- FastAPI docs — BackgroundTasks lifecycle tied to request task (Starlette behavior): https://fastapi.tiangolo.com/tutorial/background-tasks/
- TanStack Query v5 docs — `queryClient.setQueryData` updater function: https://tanstack.com/query/v5/docs/reference/QueryClient#queryclientsetquerydata

### Tertiary (LOW confidence)
- None — all critical claims are verified by direct codebase evidence.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries are already installed and in use in the project
- Architecture: HIGH — asyncio.ensure_future() pattern is proven in this exact codebase (avatars.py); React Query setQueryData pattern is the standard v5 API
- Pitfalls: HIGH — FastAPI BackgroundTasks cancellation bug is confirmed and documented in the codebase (not theoretical)

**Research date:** 2026-03-11
**Valid until:** 2026-04-10 (stable patterns — no fast-moving dependencies)
