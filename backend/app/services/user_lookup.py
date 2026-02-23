from app.database import supabase_admin  # Service role client — bypasses RLS


async def lookup_user_by_phone(phone: str) -> dict | None:
    """
    Find user by linked WhatsApp phone number.

    Uses service role client (bypasses RLS) because this is a server-to-server
    operation — no user JWT exists in the webhook context.

    Args:
        phone: Phone number in E.164 format (+1234567890)

    Returns:
        Dict with user_id if found, None if no user has linked this number.
    """
    result = (
        supabase_admin
        .from_("user_preferences")
        .select("user_id")
        .eq("whatsapp_phone", phone)
        .single()
        .execute()
    )
    return result.data if result.data else None
