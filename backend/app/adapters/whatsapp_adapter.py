"""
WhatsApp platform adapter — satisfies PlatformAdapter Protocol without inheritance.

Wraps existing webhook send/receive logic extracted from webhook.py.
receive() -> platform_router -> ChatService
send() -> send_whatsapp_message() via Meta Graph API
"""
import logging
from datetime import datetime, timezone
from app.adapters.base import NormalizedMessage
from app.services.user_lookup import get_avatar_for_user
from app.services.whatsapp import send_whatsapp_message
from app.services.platform_router import route
from app.database import supabase_admin

logger = logging.getLogger(__name__)


class WhatsAppAdapter:
    """
    Concrete WhatsApp adapter. Satisfies PlatformAdapter Protocol — no imports
    of PlatformAdapter needed in this file. The Protocol check is structural.
    """

    def __init__(self, chat_service, phone_number_id: str):
        self._chat_service = chat_service
        self._phone_number_id = phone_number_id

    async def receive(self, message: NormalizedMessage) -> str:
        """Route inbound WhatsApp message through platform_router -> ChatService."""
        avatar = await get_avatar_for_user(message.user_id)
        return await route(
            chat_service=self._chat_service,
            user_id=message.user_id,
            incoming_platform="whatsapp",
            message=message,
            avatar=avatar,
        )

    async def send(self, user_id: str, text: str) -> None:
        """Deliver reply to WhatsApp by resolving user_id -> phone -> Meta API."""
        try:
            result = (
                supabase_admin
                .from_("user_preferences")
                .select("whatsapp_phone")
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
            )
            phone = (result.data or {}).get("whatsapp_phone")
            if not phone:
                logger.warning(f"No WhatsApp phone for user {user_id} — cannot deliver reply")
                return
            await send_whatsapp_message(
                phone_number_id=self._phone_number_id,
                to=phone,
                text=text,
            )
        except Exception as e:
            logger.error(f"WhatsApp send failed for user {user_id}: {e}")
