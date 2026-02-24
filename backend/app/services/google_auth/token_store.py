"""Per-user Google Calendar OAuth token storage in Supabase.

Tokens are stored server-side in the google_calendar_tokens table.
Uses supabase_admin (service role) because the webhook/skill pipeline
runs without a user JWT in scope.

IMPORTANT: Never store tokens in session memory — they must survive restarts.
"""
import logging
from datetime import datetime, timezone
from typing import Any
from app.database import supabase_admin

logger = logging.getLogger(__name__)

TABLE = "google_calendar_tokens"


async def get_calendar_tokens(user_id: str) -> dict[str, Any] | None:
    """Return stored token dict for user_id, or None if not connected."""
    try:
        result = (
            supabase_admin.table(TABLE)
            .select("access_token, refresh_token, token_expiry, scopes")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        return result.data if result.data else None
    except Exception as e:
        logger.error(f"Failed to fetch calendar tokens for {user_id}: {e}")
        return None


async def save_calendar_tokens(
    user_id: str,
    access_token: str,
    refresh_token: str,
    token_expiry: datetime | None,
    scopes: list[str],
) -> None:
    """Upsert OAuth tokens for user_id. Called after OAuth callback and after token refresh."""
    try:
        row = {
            "user_id": user_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_expiry": token_expiry.isoformat() if token_expiry else None,
            "scopes": scopes,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        supabase_admin.table(TABLE).upsert(row).execute()
    except Exception as e:
        logger.error(f"Failed to save calendar tokens for {user_id}: {e}")
        raise


async def delete_calendar_tokens(user_id: str) -> None:
    """Remove stored tokens (e.g., when token is revoked by user)."""
    try:
        supabase_admin.table(TABLE).delete().eq("user_id", user_id).execute()
    except Exception as e:
        logger.error(f"Failed to delete calendar tokens for {user_id}: {e}")
