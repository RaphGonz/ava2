"""
Stripe Checkout session creation and webhook event verification.
stripe_price_id is read from settings — never hardcoded (BILL-02).
"""
import stripe
from app.config import settings

# Module-level API key (global pattern is fine at this scale per RESEARCH.md)
stripe.api_key = settings.stripe_secret_key


def create_checkout_session(user_id: str, email: str | None = None) -> str:
    """
    Create a Stripe Checkout Session for monthly subscription.
    Returns the checkout URL to redirect the user to.

    Config-driven (BILL-02): stripe_price_id comes from settings/env.
    """
    params: dict = {
        "mode": "subscription",
        "line_items": [{"price": settings.stripe_price_id, "quantity": 1}],
        "success_url": f"{settings.frontend_url}/chat?subscribed=1",
        "cancel_url": f"{settings.frontend_url}/subscribe?cancelled=1",
        "client_reference_id": user_id,
        "metadata": {"user_id": user_id},
    }
    if email:
        params["customer_email"] = email
    session = stripe.checkout.Session.create(**params)
    return session.url


def verify_webhook_event(raw_body: bytes, sig_header: str) -> stripe.Event:
    """
    Verify Stripe webhook signature and return the event.
    Raises stripe.error.SignatureVerificationError on mismatch.

    IMPORTANT: raw_body must be the original bytes from await request.body() —
    never pass a parsed JSON dict here (Pitfall 4 from RESEARCH.md).
    """
    return stripe.Webhook.construct_event(
        raw_body, sig_header, settings.stripe_webhook_secret
    )
