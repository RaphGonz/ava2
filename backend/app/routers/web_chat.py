"""
Web chat router — POST /chat and GET /chat/history.

Uses WebAdapter -> platform_router -> ChatService pipeline.
POST /chat: synchronous user-message insert → asyncio.ensure_future LLM task → return user row.
GET /chat/history: returns web-channel messages (RLS-filtered).
Pitfall 3: never mix channel='web' with 'whatsapp'.
"""
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

# Module-level singletons shared with webhook (same ChatService instance ensures shared session)
# Import from webhook to reuse — avoids creating a second ChatService with a different SessionStore
from app.routers.webhook import _chat_service

_web_adapter = WebAdapter(chat_service=_chat_service)


class ChatRequest(BaseModel):
    text: str


async def _run_llm_and_insert(user_id: str, text: str, avatar: dict | None) -> None:
    """
    Independent asyncio Task — not cancelled by connection close.
    Runs LLM call and inserts assistant reply into DB.
    Uses asyncio.ensure_future() (NOT FastAPI BackgroundTasks) because
    CORSMiddleware cancels BackgroundTasks on connection close — confirmed
    codebase bug fixed in avatars.py (Phase 07).
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
    """
    Send a message via the web chat interface.
    Step 1: Insert user message into DB immediately (fast ~10ms).
    Step 2: Schedule LLM + assistant insert as independent asyncio Task.
    Step 3: Return the inserted user message row — frontend appends it to cache instantly.
    GET /chat/history polling at 3s picks up the assistant reply when it lands.
    """
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

    # Fire LLM + assistant-reply insert as independent task.
    # asyncio.ensure_future() creates a Task NOT tied to this request — immune to
    # CORSMiddleware cancellation (same pattern as avatars.py Phase 07 BUG FIX).
    asyncio.ensure_future(_run_llm_and_insert(user_id, body.text, avatar))

    # Return the user message row — frontend uses it to show bubble immediately
    return {
        "id": user_row["id"],
        "role": user_row["role"],
        "content": user_row["content"],
        "created_at": user_row["created_at"],
    }


_PHOTO_PATH_OPEN = "[PHOTO_PATH]"
_PHOTO_PATH_CLOSE = "[/PHOTO_PATH]"
_PHOTO_SIGNED_URL_TTL = 3600        # signed URL lifetime: 1 hour
_PHOTO_CACHE_REFRESH_BEFORE = 600   # regenerate when less than 10 min remain

# Cache: storage_path -> (signed_url, generated_at unix timestamp)
_signed_url_cache: dict[str, tuple[str, float]] = {}


def _get_signed_url(storage_path: str) -> str | None:
    """Return a cached signed URL, regenerating only when close to expiry."""
    import time
    cached = _signed_url_cache.get(storage_path)
    if cached:
        url, generated_at = cached
        age = time.time() - generated_at
        if age < _PHOTO_SIGNED_URL_TTL - _PHOTO_CACHE_REFRESH_BEFORE:
            return url  # still fresh — reuse

    # Generate a new signed URL
    try:
        sign_response = (
            supabase_admin.storage
            .from_("photos")
            .create_signed_url(storage_path, _PHOTO_SIGNED_URL_TTL)
        )
        url = (
            sign_response.get("signedURL")
            or sign_response.get("signedUrl")
            or sign_response.get("signed_url")
        )
        if url:
            import time as _time
            _signed_url_cache[storage_path] = (url, _time.time())
            return url
        logger.error(f"_get_signed_url: no URL in response for {storage_path!r}: {sign_response}")
    except Exception as e:
        logger.error(f"_get_signed_url: error signing {storage_path!r}: {e}")
    return None


def _rewrite_photo_paths(messages: list[dict]) -> list[dict]:
    """
    Replace [PHOTO_PATH]{path}[/PHOTO_PATH] tokens in message content with
    signed URLs. URLs are cached for ~50 minutes to prevent flicker on polling.
    """
    rewritten = []
    for msg in messages:
        content: str = msg.get("content", "")
        if _PHOTO_PATH_OPEN in content:
            start = content.find(_PHOTO_PATH_OPEN) + len(_PHOTO_PATH_OPEN)
            end = content.find(_PHOTO_PATH_CLOSE)
            if end > start:
                storage_path = content[start:end]
                url = _get_signed_url(storage_path)
                if url:
                    new_content = (
                        content[: content.find(_PHOTO_PATH_OPEN)]
                        + f"[PHOTO]{url}[/PHOTO]"
                        + content[end + len(_PHOTO_PATH_CLOSE):]
                    )
                    msg = {**msg, "content": new_content}
        rewritten.append(msg)
    return rewritten


@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    user=Depends(get_current_user),
    db=Depends(get_authed_supabase),
):
    """
    Return recent web-channel messages for the authenticated user.
    Filters to channel='web' only — never returns WhatsApp messages (Pitfall 3).
    Returns newest-first, limit defaults to 50.

    Any message content containing a [PHOTO_PATH] storage path token is rewritten
    to a fresh 1-hour signed URL before returning, ensuring photos remain accessible
    permanently regardless of when the message was originally created.
    """
    result = (
        db.from_("messages")
        .select("id, role, content, created_at")
        .eq("channel", "web")
        .order("created_at", desc=True)
        .limit(min(limit, 200))
        .execute()
    )
    # Return in chronological order for display (reverse the newest-first fetch)
    messages = list(reversed(result.data or []))
    # Rewrite any [PHOTO_PATH] tokens to fresh signed URLs
    messages = _rewrite_photo_paths(messages)
    return messages
