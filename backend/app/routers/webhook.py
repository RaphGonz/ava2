from fastapi import APIRouter, Request, HTTPException, Query
from app.config import settings
from app.services.whatsapp import send_whatsapp_message
from app.services.user_lookup import lookup_user_by_phone
from app.database import supabase_admin
import logging

router = APIRouter(prefix="/webhook", tags=["webhook"])
logger = logging.getLogger(__name__)


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
    """Process incoming WhatsApp webhook payload."""
    value = body["entry"][0]["changes"][0]["value"]

    if "messages" not in value:
        return  # Delivery receipt or status update — ignore

    message = value["messages"][0]
    sender_phone = message["from"]  # E.164 format: +1234567890
    message_type = message.get("type")

    if message_type != "text":
        return  # Only handle text messages in Phase 2

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

    # Phase 2: Echo the message back
    echo_text = f"[Echo] {incoming_text}"
    await send_whatsapp_message(
        phone_number_id=phone_number_id,
        to=sender_phone,
        text=echo_text,
    )

    # Log both incoming and outgoing messages to Supabase
    # Uses supabase_admin (service role) — webhook has no user JWT
    try:
        supabase_admin.from_("messages").insert([
            {
                "user_id": user["user_id"],
                "avatar_id": None,
                "channel": "whatsapp",
                "role": "user",
                "content": incoming_text,
            },
            {
                "user_id": user["user_id"],
                "avatar_id": None,
                "channel": "whatsapp",
                "role": "assistant",
                "content": echo_text,
            },
        ]).execute()
    except Exception as e:
        logger.error(f"Message logging failed for user {user['user_id']}: {e}")
        # DB failure does not prevent the echo from being sent — already sent above
