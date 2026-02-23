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


async def get_avatar_for_user(user_id: str) -> dict | None:
    """Fetch the avatar row for a given user_id. Returns dict or None if no avatar.

    Uses supabase_admin (service role) — webhook context has no user JWT.
    Returns keys: id, user_id, name, age, personality, physical_description.
    """
    try:
        result = (
            supabase_admin
            .from_("avatars")
            .select("id, user_id, name, age, personality, physical_description")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        return result.data if result.data else None
    except Exception as e:
        logger.error(f"Avatar lookup failed for user {user_id}: {e}")
        return None
