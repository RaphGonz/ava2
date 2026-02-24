from fastapi import APIRouter, Request, HTTPException, Query
from datetime import datetime, timezone
from app.config import settings
from app.services.user_lookup import lookup_user_by_phone
from app.services.session.store import get_session_store
from app.services.llm.openai_provider import OpenAIProvider
from app.services.chat import ChatService
from app.adapters.whatsapp_adapter import WhatsAppAdapter
from app.database import supabase_admin
import logging

router = APIRouter(prefix="/webhook", tags=["webhook"])
logger = logging.getLogger(__name__)

# Module-level singletons — instantiated once at import time
_llm_provider = OpenAIProvider(
    api_key=settings.openai_api_key,
    model=settings.llm_model,
)
_chat_service = ChatService(llm=_llm_provider, session_store=get_session_store())
_whatsapp_adapter = WhatsAppAdapter(
    chat_service=_chat_service,
    phone_number_id=settings.whatsapp_phone_number_id,
)


@router.get("")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Forbidden")


@router.post("")
async def handle_incoming(request: Request):
    """
    Meta delivers incoming WhatsApp messages here.
    Always returns HTTP 200 — non-200 causes Meta to retry (duplicate messages).
    """
    try:
        body = await request.json()
        await process_whatsapp_message(body)
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
    return {"status": "ok"}


async def process_whatsapp_message(body: dict) -> None:
    """Process incoming WhatsApp webhook payload via WhatsAppAdapter pipeline."""
    from app.adapters.base import NormalizedMessage

    value = body["entry"][0]["changes"][0]["value"]
    if "messages" not in value:
        return  # Delivery receipt or status update — ignore

    message = value["messages"][0]
    sender_phone = message["from"]
    message_type = message.get("type")

    if message_type != "text":
        return  # Text only in Phase 6

    incoming_text = message["text"]["body"]

    # Look up user by phone (service role — no user JWT in webhook context)
    user = await lookup_user_by_phone(sender_phone)

    if user is None:
        # Unlinked number — send registration instructions via direct API call
        from app.services.whatsapp import send_whatsapp_message
        phone_number_id = value["metadata"]["phone_number_id"]
        await send_whatsapp_message(
            phone_number_id=phone_number_id,
            to=sender_phone,
            text="Please create an account at ava.example.com and link your number",
        )
        return

    user_id = user["user_id"]

    msg = NormalizedMessage(
        user_id=user_id,
        text=incoming_text,
        platform="whatsapp",
        timestamp=datetime.now(timezone.utc),
    )

    # receive() -> platform_router -> ChatService -> returns reply text
    reply_text = await _whatsapp_adapter.receive(msg)

    # Send reply (adapter resolves user_id -> phone internally)
    await _whatsapp_adapter.send(user_id, reply_text)

    # Log both messages to Supabase (DB failure must not prevent reply — already sent)
    from app.services.user_lookup import get_avatar_for_user
    avatar = await get_avatar_for_user(user_id)
    try:
        supabase_admin.from_("messages").insert([
            {
                "user_id": user_id,
                "avatar_id": avatar["id"] if avatar else None,
                "channel": "whatsapp",
                "role": "user",
                "content": incoming_text,
            },
            {
                "user_id": user_id,
                "avatar_id": avatar["id"] if avatar else None,
                "channel": "whatsapp",
                "role": "assistant",
                "content": reply_text,
            },
        ]).execute()
    except Exception as e:
        logger.error(f"Message logging failed for user {user_id}: {e}")
