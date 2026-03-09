"""
Subscription status persistence — reads/writes the subscriptions table in Supabase.
Uses supabase_admin (service role) because Stripe webhooks run without user JWT.
"""
import logging
import stripe
from datetime import datetime, timezone
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
        .limit(1)
        .execute()
    )
    return result.data[0]["status"] if result.data else None


async def get_subscription_detail(user_id: str) -> dict | None:
    """
    Return subscription detail from local DB (no live Stripe call).
    Returns None if the user has no subscription row.
    Hard-codes plan_name as "Ava Monthly" — single-product MVP.
    """
    try:
        result = (
            supabase_admin.from_("subscriptions")
            .select("status, current_period_end, cancel_at_period_end, stripe_customer_id, stripe_subscription_id")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        row = result.data[0]
        return {
            "plan_name": "Ava Monthly",
            "status": row["status"],
            "current_period_end": row["current_period_end"],
            "cancel_at_period_end": row.get("cancel_at_period_end", False),
            "stripe_customer_id": row["stripe_customer_id"],
            "stripe_subscription_id": row["stripe_subscription_id"],
        }
    except Exception as e:
        logger.error(f"Failed to get subscription detail for user {user_id}: {e}")
        return None


def get_customer_invoices(stripe_customer_id: str) -> list[dict]:
    """
    Return up to 12 most recent Stripe invoices for the given customer.
    Synchronous — stripe SDK is synchronous.
    Returns [] on any error.
    """
    try:
        invoices = stripe.Invoice.list(customer=stripe_customer_id, limit=12)
        return [
            {
                "date": inv.created,
                "amount_paid": inv.amount_paid,
                "status": inv.status,
                "invoice_pdf": inv.invoice_pdf,
            }
            for inv in invoices.data
        ]
    except Exception as e:
        logger.error(f"Failed to list invoices for customer {stripe_customer_id}: {e}")
        return []


async def update_subscription_cancel_state(
    subscription_id: str,
    cancel_at_period_end: bool,
    current_period_end_ts: int | None,
) -> None:
    """
    Persist cancel_at_period_end (and optionally current_period_end) for a subscription row.
    Called from the customer.subscription.updated webhook branch — non-fatal on failure.
    """
    try:
        update_data: dict = {
            "cancel_at_period_end": cancel_at_period_end,
            "updated_at": "now()",
        }
        if current_period_end_ts is not None:
            update_data["current_period_end"] = datetime.fromtimestamp(
                current_period_end_ts, tz=timezone.utc
            ).isoformat()

        supabase_admin.from_("subscriptions").update(update_data).eq(
            "stripe_subscription_id", subscription_id
        ).execute()
        logger.info(
            "Updated cancel_at_period_end=%s for subscription %s",
            cancel_at_period_end,
            subscription_id,
        )
    except Exception as e:
        logger.error(
            "Failed to update cancel_at_period_end for subscription %s: %s",
            subscription_id,
            e,
        )


async def get_user_email_by_subscription_id(subscription_id: str) -> str | None:
    """
    Look up the user's email address for a given Stripe subscription ID.

    Used by the cancellation email flow because `customer.subscription.deleted`
    Stripe events do not reliably include the customer email directly in the payload
    (Pitfall 7 from RESEARCH.md).

    Strategy:
    1. Look up user_id from local subscriptions table by stripe_subscription_id
    2. Fetch user record from Supabase auth via supabase_admin.auth.admin.get_user_by_id()
    3. Return email or None (caller must handle None gracefully — email failure non-blocking)
    """
    try:
        result = (
            supabase_admin.from_("subscriptions")
            .select("user_id")
            .eq("stripe_subscription_id", subscription_id)
            .limit(1)
            .execute()
        )
        if not result.data:
            logger.warning("No subscription row found for stripe_subscription_id=%s", subscription_id)
            return None

        user_id = result.data[0]["user_id"]
        user_record = supabase_admin.auth.admin.get_user_by_id(user_id)
        return user_record.user.email if user_record and user_record.user else None
    except Exception as exc:
        logger.error("Failed to look up email for subscription %s: %s", subscription_id, exc)
        return None
