from fastapi import APIRouter, Request, HTTPException, Query
from app.config import settings
from app.services.whatsapp import send_whatsapp_message
from app.services.user_lookup import lookup_user_by_phone, get_avatar_for_user
from app.services.session.store import get_session_store
from app.services.llm.openai_provider import OpenAIProvider
from app.services.chat import ChatService
from app.database import supabase_admin
import logging

router = APIRouter(prefix="/webhook", tags=["webhook"])
logger = logging.getLogger(__name__)

# Module-level singletons — instantiated once per process at import time
# OpenAIProvider uses AsyncOpenAI (non-blocking); safe to share across requests
_llm_provider = OpenAIProvider(
    api_key=settings.openai_api_key,
    model=settings.llm_model,
)
_chat_service = ChatService(llm=_llm_provider, session_store=get_session_store())


@router.get("")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """
    Meta calls this GET endpoint when you register the webhook URL.
    Returns the challenge value to confirm ownership.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Forbidden")


@router.post("")
async def handle_incoming(request: Request):
    """
    Meta delivers incoming WhatsApp messages here.

    Always returns HTTP 200 — non-200 causes Meta to retry delivery,
    resulting in duplicate messages. Errors are logged internally.
    """
    try:
        body = await request.json()
        await process_whatsapp_message(body)
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        # Still return 200 — Meta doesn't need to know about internal errors

    return {"status": "ok"}


async def process_whatsapp_message(body: dict) -> None:
    """Process incoming WhatsApp webhook payload through the AI pipeline."""
    value = body["entry"][0]["changes"][0]["value"]

    if "messages" not in value:
        return  # Delivery receipt or status update — ignore

    message = value["messages"][0]
    sender_phone = message["from"]  # E.164 format: +1234567890
    message_type = message.get("type")

    if message_type != "text":
        return  # Only handle text messages in Phase 3

    incoming_text = message["text"]["body"]
    phone_number_id = value["metadata"]["phone_number_id"]

    # Look up user by phone number (service role client — bypasses RLS)
    user = await lookup_user_by_phone(sender_phone)

    if user is None:
        # Unlinked number — send registration instructions
        await send_whatsapp_message(
            phone_number_id=phone_number_id,
            to=sender_phone,
            text="Please create an account at ava.example.com and link your number",
        )
        return

    user_id = user["user_id"]

    # Fetch avatar (cached in session after first call — see ChatService)
    avatar = await get_avatar_for_user(user_id)

    # Run through AI pipeline — returns reply text
    reply_text = await _chat_service.handle_message(
        user_id=user_id,
        incoming_text=incoming_text,
        avatar=avatar,
    )

    # Send reply via WhatsApp
    await send_whatsapp_message(
        phone_number_id=phone_number_id,
        to=sender_phone,
        text=reply_text,
    )

    # Log both messages to Supabase (DB failure must not prevent reply — already sent above)
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
        # DB failure does not prevent the reply — already sent above
