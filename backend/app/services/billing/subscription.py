"""
Subscription status persistence — reads/writes the subscriptions table in Supabase.
Uses supabase_admin (service role) because Stripe webhooks run without user JWT.
"""
import logging
from datetime import datetime
from app.database import supabase_admin

logger = logging.getLogger(__name__)


async def activate_subscription(
    user_id: str,
    customer_id: str,
    subscription_id: str,
    price_id: str | None = None,
    period_end: datetime | None = None,
) -> None:
    """Upsert subscription row to active status. Called on checkout.session.completed."""
    data: dict = {
        "user_id": user_id,
        "stripe_customer_id": customer_id,
        "stripe_subscription_id": subscription_id,
        "status": "active",
        "updated_at": "now()",
    }
    if price_id:
        data["stripe_price_id"] = price_id
    if period_end:
        data["current_period_end"] = period_end.isoformat()

    try:
        supabase_admin.from_("subscriptions").upsert(
            data, on_conflict="user_id"
        ).execute()
        logger.info(f"Subscription activated for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to activate subscription for user {user_id}: {e}")
        raise


async def deactivate_subscription(subscription_id: str, new_status: str = "inactive") -> None:
    """Set subscription status to inactive/past_due/canceled. Called on payment failure/cancel."""
    try:
        supabase_admin.from_("subscriptions").update({
            "status": new_status,
            "updated_at": "now()",
        }).eq("stripe_subscription_id", subscription_id).execute()
        logger.info(f"Subscription {subscription_id} set to {new_status}")
    except Exception as e:
        logger.error(f"Failed to deactivate subscription {subscription_id}: {e}")
        raise


def get_subscription_status(user_id: str) -> str | None:
    """
    Synchronous check — returns subscription status string or None if no row.
    Returns 'active', 'inactive', 'past_due', 'canceled', or None.
    Used by require_active_subscription FastAPI dependency.
    """
    result = (
        supabase_admin.from_("subscriptions")
        .select("status")
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    return result.data.get("status") if result.data else None
