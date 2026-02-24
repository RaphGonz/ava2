"""
Platform router — checks user's preferred_platform before dispatching to ChatService.

Called by both WhatsAppAdapter and WebAdapter. Keeps preferred_platform enforcement
in one place (not duplicated across adapters — per research anti-patterns section).

Decision: preferred_platform lookup uses supabase_admin (service role) because
WhatsApp adapter runs in webhook context without a user JWT (Pitfall 5 in RESEARCH.md).
"""
import logging
from app.database import supabase_admin
from app.adapters.base import NormalizedMessage
from app.services.chat import ChatService

logger = logging.getLogger(__name__)

# In-character warm redirect message (per CONTEXT.md decisions)
_REDIRECT_TEMPLATE = (
    "Hey 😊 I mostly hang out on {preferred} — come find me there! "
    "(You can change this in settings)"
)
_PLATFORM_LABELS = {
    "whatsapp": "WhatsApp",
    "web": "the web app",
}


async def route(
    chat_service: ChatService,
    user_id: str,
    incoming_platform: str,
    message: NormalizedMessage,
    avatar: dict | None,
) -> str:
    """
    Check preferred_platform. If mismatch, return in-character redirect.
    If match (or no preference set), dispatch to ChatService.handle_message().

    Args:
        chat_service: Module-level ChatService singleton.
        user_id: Authenticated user UUID.
        incoming_platform: Platform this message arrived on ("whatsapp" or "web").
        message: Normalized message envelope.
        avatar: Avatar row from DB (name, personality) or None if not set up.

    Returns:
        Reply text to deliver back via the adapter's send().
    """
    try:
        result = (
            supabase_admin
            .from_("user_preferences")
            .select("preferred_platform")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        preferred = (result.data or {}).get("preferred_platform")
    except Exception as e:
        logger.error(f"preferred_platform lookup failed for user {user_id}: {e}")
        preferred = None  # Default: allow message through

    # If user has a preference AND the incoming platform doesn't match -> redirect
    if preferred and preferred != incoming_platform:
        label = _PLATFORM_LABELS.get(preferred, preferred)
        return _REDIRECT_TEMPLATE.format(preferred=label)

    # No preference set, or preference matches -> dispatch to core pipeline
    return await chat_service.handle_message(
        user_id=user_id,
        incoming_text=message.text,
        avatar=avatar,
    )
