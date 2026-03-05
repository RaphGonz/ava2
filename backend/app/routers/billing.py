"""
Billing router — Stripe Checkout and webhook handler.

POST /billing/checkout  — create Stripe Checkout Session (requires auth)
POST /billing/webhook   — Stripe webhook endpoint (no auth — uses signature verification)

Transactional emails added in Phase 9:
- checkout.session.completed  -> receipt email    (EMAI-03)
- customer.subscription.deleted -> cancellation email (EMAI-04)
"""
import logging
from datetime import datetime, timezone

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request

from app.dependencies import get_current_user
from app.services.billing.stripe_client import create_checkout_session, verify_webhook_event
from app.services.billing.subscription import (
    activate_subscription,
    deactivate_subscription,
    get_user_email_by_subscription_id,
)
from app.services.email.resend_client import send_cancellation_email, send_receipt_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


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
