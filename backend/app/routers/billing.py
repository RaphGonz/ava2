"""
Billing router — Stripe Checkout and webhook handler.

POST /billing/checkout  — create Stripe Checkout Session (requires auth)
POST /billing/webhook   — Stripe webhook endpoint (no auth — uses signature verification)
"""
import logging
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from app.dependencies import get_current_user
from app.services.billing.stripe_client import create_checkout_session, verify_webhook_event
from app.services.billing.subscription import activate_subscription, deactivate_subscription

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
    - checkout.session.completed → activate subscription
    - invoice.payment_failed → deactivate subscription
    - customer.subscription.deleted → cancel subscription

    CRITICAL: await request.body() BEFORE any JSON parsing (Pitfall 4 from RESEARCH.md).
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

    elif event_type in ("invoice.payment_failed",):
        sub_id = data.get("subscription")
        if sub_id:
            await deactivate_subscription(sub_id, new_status="past_due")

    elif event_type == "customer.subscription.deleted":
        sub_id = data.get("id")
        if sub_id:
            await deactivate_subscription(sub_id, new_status="canceled")

    return {"received": True}
