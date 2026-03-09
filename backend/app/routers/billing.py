"""
Billing router — Stripe Checkout and webhook handler.

POST /billing/checkout        — create Stripe Checkout Session (requires auth)
POST /billing/webhook         — Stripe webhook endpoint (no auth — uses signature verification)
GET  /billing/subscription    — current subscription state from local DB (Phase 11)
GET  /billing/invoices        — up to 12 recent Stripe invoices (Phase 11)
POST /billing/portal-session  — create Stripe Customer Portal URL (Phase 11)
POST /billing/cancel          — cancel at period end + emit survey usage event (Phase 11)

Transactional emails added in Phase 9:
- checkout.session.completed  -> receipt email    (EMAI-03)
- customer.subscription.deleted -> cancellation email (EMAI-04)
"""
import logging
from datetime import datetime, timezone

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.database import supabase_admin
from app.dependencies import get_current_user
from app.services.billing.stripe_client import (
    cancel_subscription_at_period_end,
    create_checkout_session,
    create_portal_session,
    verify_webhook_event,
)
from app.services.billing.subscription import (
    activate_subscription,
    deactivate_subscription,
    get_customer_invoices,
    get_subscription_detail,
    get_user_email_by_subscription_id,
    update_subscription_cancel_state,
)
from app.services.email.resend_client import send_cancellation_email, send_receipt_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


class CancelRequest(BaseModel):
    q1: str = ""  # "What did you like most about Ava?" — optional, can be empty
    q2: str = ""  # "Why are you leaving?" — optional, can be empty


@router.get("/subscription")
async def get_subscription(user=Depends(get_current_user)):
    """
    Return current subscription state from local DB (not a live Stripe call).
    Use get_current_user only — NOT require_active_subscription (Pitfall 7).
    """
    detail = await get_subscription_detail(str(user.id))
    if detail is None:
        return {"status": "none"}
    return detail


@router.get("/invoices")
async def list_invoices(user=Depends(get_current_user)):
    """
    Return up to 12 most recent Stripe invoices for the user.
    Calls Stripe API (not cached) — used only on explicit billing page load.
    stripe_customer_id may be None for users who never subscribed — returns [].
    """
    detail = await get_subscription_detail(str(user.id))
    if detail is None or not detail.get("stripe_customer_id"):
        return []
    try:
        invoices = get_customer_invoices(detail["stripe_customer_id"])
        return invoices
    except Exception as e:
        logger.error(f"Invoice list failed for user {user.id}: {e}")
        return []


@router.post("/portal-session")
async def create_billing_portal_session(user=Depends(get_current_user)):
    """
    Create a Stripe Customer Portal session and return the URL.
    Frontend opens URL in new tab. Never cache this URL — portal sessions are single-use.
    """
    from app.config import settings
    detail = await get_subscription_detail(str(user.id))
    if detail is None or not detail.get("stripe_customer_id"):
        raise HTTPException(status_code=404, detail="No subscription found")
    try:
        return_url = f"{settings.frontend_url}/billing"
        portal_url = create_portal_session(
            stripe_customer_id=detail["stripe_customer_id"],
            return_url=return_url,
        )
        return {"portal_url": portal_url}
    except Exception as e:
        logger.error(f"Portal session creation failed for user {user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create billing portal session")


@router.post("/cancel")
async def cancel_subscription(body: CancelRequest, user=Depends(get_current_user)):
    """
    Set cancel_at_period_end=True on the Stripe subscription.
    CRITICAL: Uses stripe.Subscription.modify() — user retains access until period end.
    Survey responses stored in usage_events as metadata (SUBS-04 + ADMN-02).
    """
    detail = await get_subscription_detail(str(user.id))
    if detail is None or not detail.get("stripe_subscription_id"):
        raise HTTPException(status_code=404, detail="No active subscription found")
    try:
        result = cancel_subscription_at_period_end(detail["stripe_subscription_id"])
    except Exception as e:
        logger.error(f"Stripe cancel failed for user {user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")

    # Emit usage event with survey responses as metadata (SUBS-04 + ADMN-02)
    try:
        supabase_admin.from_("usage_events").insert({
            "user_id": str(user.id),
            "event_type": "subscription_cancelled",
            "metadata": {"q1": body.q1, "q2": body.q2},
        }).execute()
    except Exception as exc:
        logger.error("Failed to emit subscription_cancelled usage event: %s", exc)

    return {
        "cancel_at_period_end": result["cancel_at_period_end"],
        "current_period_end": result["current_period_end"],
    }


@router.post("/checkout")
async def create_checkout(user=Depends(get_current_user)):
    """
    Create a Stripe Checkout Session and return the redirect URL.
    Frontend redirects user to checkout_url.
    """
    from app.config import settings
    if not settings.stripe_price_id:
        raise HTTPException(status_code=503, detail="Billing not configured")
    try:
        url = create_checkout_session(user_id=str(user.id))
        return {"checkout_url": url}
    except Exception as e:
        logger.error(f"Checkout session creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Stripe webhook — verifies signature then handles:
    - checkout.session.completed -> activate subscription + send receipt email (EMAI-03)
    - invoice.payment_failed -> deactivate subscription (past_due)
    - customer.subscription.deleted -> cancel subscription + send cancellation email (EMAI-04)

    CRITICAL: await request.body() BEFORE any JSON parsing (Pitfall 4 from RESEARCH.md).
    Email failures never raise — they are logged and the webhook returns 200 regardless.
    """
    raw_body = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = verify_webhook_event(raw_body, sig_header)
    except stripe.error.SignatureVerificationError:
        logger.warning("Stripe webhook signature verification failed")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        raise HTTPException(status_code=400, detail="Webhook processing failed")

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        user_id = data.get("metadata", {}).get("user_id")
        if user_id:
            await activate_subscription(
                user_id=user_id,
                customer_id=data.get("customer", ""),
                subscription_id=data.get("subscription", ""),
            )

            # EMAI-03: receipt email — non-blocking, log-only on failure
            try:
                user_email = (data.get("customer_details") or {}).get("email")
                amount_cents = data.get("amount_total") or 0
                amount_usd = amount_cents / 100.0

                # next_billing_date: not in checkout session directly; use "next month" as fallback
                # Phase 11 will display the actual date from the subscriptions table
                next_billing = "your next billing date"

                if user_email:
                    await send_receipt_email(user_email, amount_usd, next_billing)
                else:
                    logger.warning("No customer email in checkout.session.completed — receipt not sent")
            except Exception as exc:
                logger.error("Receipt email failed (non-blocking): %s", exc)

    elif event_type in ("invoice.payment_failed",):
        sub_id = data.get("subscription")
        if sub_id:
            await deactivate_subscription(sub_id, new_status="past_due")

    elif event_type == "customer.subscription.updated":
        sub_id = data.get("id")
        if sub_id:
            cancel_at_period_end = data.get("cancel_at_period_end", False)
            current_period_end_ts = data.get("current_period_end")
            try:
                await update_subscription_cancel_state(
                    subscription_id=sub_id,
                    cancel_at_period_end=cancel_at_period_end,
                    current_period_end_ts=current_period_end_ts,
                )
            except Exception as exc:
                logger.error("Failed to update cancel_at_period_end for sub %s: %s", sub_id, exc)

    elif event_type == "customer.subscription.deleted":
        sub_id = data.get("id")
        if sub_id:
            await deactivate_subscription(sub_id, new_status="canceled")

            # EMAI-04: cancellation email — non-blocking, log-only on failure
            try:
                user_email = await get_user_email_by_subscription_id(sub_id)
                period_end_ts = data.get("current_period_end")
                if period_end_ts:
                    access_until = datetime.fromtimestamp(
                        period_end_ts, tz=timezone.utc
                    ).strftime("%B %d, %Y")
                else:
                    access_until = "the end of your current billing period"

                if user_email:
                    await send_cancellation_email(user_email, access_until)
                else:
                    logger.warning("Could not resolve email for sub %s — cancellation email not sent", sub_id)
            except Exception as exc:
                logger.error("Cancellation email failed (non-blocking): %s", exc)

    return {"received": True}
