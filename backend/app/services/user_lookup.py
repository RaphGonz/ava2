from app.database import supabase_admin
import logging

logger = logging.getLogger(__name__)


async def lookup_user_by_phone(phone: str) -> dict | None:
    """Find user by linked WhatsApp phone. Returns user_preferences row or None.

    Uses service role client (supabase_admin) — webhook is server-to-server,
    no user JWT exists in this context. RLS bypass is intentional here.
    """
    try:
        result = (
            supabase_admin
            .from_("user_preferences")
            .select("user_id")
            .eq("whatsapp_phone", phone)
            .single()
            .execute()
        )
        return result.data if result.data else None
    except Exception as e:
        logger.error(f"Phone lookup failed for {phone}: {e}")
        return None
