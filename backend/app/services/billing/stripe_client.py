"""
Stripe Checkout session creation and webhook event verification.
Price IDs are read from settings (env) — never hardcoded (BILL-02).
"""
import stripe
from app.config import settings

# Module-level API key (global pattern is fine at this scale per RESEARCH.md)
stripe.api_key = settings.stripe_secret_key

PLAN_PRICE_IDS = {
    "basic": "stripe_price_id_basic",
    "premium": "stripe_price_id_premium",
    "elite": "stripe_price_id_elite",
}


def get_price_id(plan: str) -> str:
    """Return the Stripe price ID for the given plan slug. Raises ValueError if not configured."""
    attr = PLAN_PRICE_IDS.get(plan)
    if not attr:
        raise ValueError(f"Unknown plan: {plan}")
    price_id = getattr(settings, attr, "")
    if not price_id:
        raise ValueError(f"Price ID not configured for plan: {plan}")
    return price_id


def create_checkout_session(user_id: str, plan: str = "premium", email: str | None = None) -> str:
    """
    Create a Stripe Checkout Session for the given plan.
    Returns the checkout URL to redirect the user to.

    Config-driven (BILL-02): price IDs come from settings/env, never hardcoded.
    Defaults to "premium" — the base plan per product design.
    """
    price_id = get_price_id(plan)
    params: dict = {
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
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


def create_portal_session(stripe_customer_id: str, return_url: str) -> str:
    """
    Create a Stripe Customer Portal session and return the URL.
    NEVER cache this URL — portal sessions are single-use (Pitfall 4).
    Each call creates a fresh session.
    """
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=return_url,
    )
    return session.url


def cancel_subscription_at_period_end(stripe_subscription_id: str) -> dict:
    """
    Mark a subscription to cancel at the end of the current billing period.
    CRITICAL: Uses stripe.Subscription.modify(cancel_at_period_end=True) —
    user retains access until period_end (Pitfall 1, locked in STATE.md).
    Retrieves full subscription after modify to ensure all fields are present.
    """
    stripe.Subscription.modify(
        stripe_subscription_id,
        cancel_at_period_end=True,
    )
    subscription = stripe.Subscription.retrieve(stripe_subscription_id)
    sub_dict = subscription if isinstance(subscription, dict) else subscription.to_dict()
    return {
        "cancel_at_period_end": sub_dict.get("cancel_at_period_end", True),
        "current_period_end": sub_dict.get("current_period_end"),
    }
