"""
Web chat router — POST /chat and GET /chat/history.

Uses WebAdapter -> platform_router -> ChatService pipeline.
Logs both turns to messages table with channel='web' (Pitfall 3: never mix with 'whatsapp').
"""
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


@router.post("")
async def send_message(
    body: ChatRequest,
    user=Depends(require_active_subscription),  # was: get_current_user
):
    """
    Send a message via the web chat interface.
    Runs through WebAdapter -> platform_router -> ChatService.
    Returns {"reply": <Ava's response>}.
    """
    user_id = str(user.id)
    msg = NormalizedMessage(
        user_id=user_id,
        text=body.text,
        platform="web",
        timestamp=datetime.now(timezone.utc),
    )

    reply_text = await _web_adapter.receive(msg)

    # Log both turns to messages table with channel='web'
    # send() is a no-op for WebAdapter — reply returned in HTTP response
    avatar = await get_avatar_for_user(user_id)
    try:
        supabase_admin.from_("messages").insert([
            {
                "user_id": user_id,
                "avatar_id": avatar["id"] if avatar else None,
                "channel": "web",
                "role": "user",
                "content": body.text,
            },
            {
                "user_id": user_id,
                "avatar_id": avatar["id"] if avatar else None,
                "channel": "web",
                "role": "assistant",
                "content": reply_text,
            },
        ]).execute()
    except Exception as e:
        logger.error(f"Web message logging failed for user {user_id}: {e}")

    return {"reply": reply_text}


_PHOTO_PATH_OPEN = "[PHOTO_PATH]"
_PHOTO_PATH_CLOSE = "[/PHOTO_PATH]"
_PHOTO_SIGNED_URL_TTL = 3600  # 1-hour signed URL generated fresh at each history fetch


def _rewrite_photo_paths(messages: list[dict]) -> list[dict]:
    """
    Replace [PHOTO_PATH]{path}[/PHOTO_PATH] tokens in message content with
    fresh 1-hour Supabase Storage signed URLs.

    This is called at read time so photos remain accessible permanently.
    The storage path persists in the DB forever; signed URLs are ephemeral
    and regenerated on each GET /chat/history call.
    """
    rewritten = []
    for msg in messages:
        content: str = msg.get("content", "")
        if _PHOTO_PATH_OPEN in content:
            start = content.find(_PHOTO_PATH_OPEN) + len(_PHOTO_PATH_OPEN)
            end = content.find(_PHOTO_PATH_CLOSE)
            if end > start:
                storage_path = content[start:end]
                try:
                    sign_response = (
                        supabase_admin.storage
                        .from_("photos")
                        .create_signed_url(storage_path, _PHOTO_SIGNED_URL_TTL)
                    )
                    fresh_url = (
                        sign_response.get("signedURL")
                        or sign_response.get("signedUrl")
                        or sign_response.get("signed_url")
                    )
                    if fresh_url:
                        # Replace [PHOTO_PATH] token with [PHOTO] + signed URL for frontend
                        new_content = (
                            content[: content.find(_PHOTO_PATH_OPEN)]
                            + f"[PHOTO]{fresh_url}[/PHOTO]"
                            + content[end + len(_PHOTO_PATH_CLOSE):]
                        )
                        msg = {**msg, "content": new_content}
                    else:
                        logger.error(
                            f"_rewrite_photo_paths: failed to sign path {storage_path!r} "
                            f"— sign_response={sign_response}"
                        )
                except Exception as sign_err:
                    logger.error(
                        f"_rewrite_photo_paths: error signing path {storage_path!r}: {sign_err}"
                    )
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
