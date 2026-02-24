"""
Web chat router — POST /chat and GET /chat/history.

Uses WebAdapter -> platform_router -> ChatService pipeline.
Logs both turns to messages table with channel='web' (Pitfall 3: never mix with 'whatsapp').
"""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.dependencies import get_current_user, get_authed_supabase
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
    user=Depends(get_current_user),
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
    return messages
