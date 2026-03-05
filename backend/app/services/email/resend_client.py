"""
Resend email service — async wrapper over the synchronous Resend Python SDK.

Uses asyncio.to_thread() (established codebase pattern from Phase 4) because
resend.Emails.send() is synchronous and would block the FastAPI event loop.

Email failures never propagate to callers — one automatic retry after 3s,
then log and return False (CONTEXT.md decision: email must not block auth/payment).
"""
import asyncio
import logging

import resend

from app.config import settings

logger = logging.getLogger(__name__)


def _sync_send(params: dict) -> dict:
    """Synchronous Resend call — runs in a thread via asyncio.to_thread."""
    resend.api_key = settings.resend_api_key
    return resend.Emails.send(params)


async def send_email(to: str, subject: str, html: str, retry: bool = True) -> bool:
    """
    Send a transactional email via Resend.

    Returns True on success. On failure: retries once after 3s (CONTEXT.md: exact
    retry delay is Claude's discretion), then logs and returns False.
    Never raises — callers must not block on email outcome.
    """
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not configured — email not sent to %s", to)
        return False

    params = {
        "from": settings.resend_from_address,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    try:
        await asyncio.to_thread(_sync_send, params)
        logger.info("Email sent to %s: %s", to, subject)
        return True
    except Exception as exc:
        logger.error("Email send failed for %s (%s): %s", to, subject, exc)
        if retry:
            await asyncio.sleep(3)
            return await send_email(to, subject, html, retry=False)
        return False


# ---------------------------------------------------------------------------
# Email template helpers
# Each returns (subject, html) tuple — keeps templates co-located with sender.
# Tone: warm but concise, first-name greeting, no corporate jargon (CONTEXT.md).
# ---------------------------------------------------------------------------

def _base_html(title: str, body_html: str) -> str:
    """Minimal brand-consistent email shell — logo wordmark, brand colors, clean layout."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;background:#f9fafb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;padding:40px 16px;">
    <tr><td align="center">
      <table width="480" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;border:1px solid #e5e7eb;overflow:hidden;">
        <!-- Header -->
        <tr><td style="background:#111827;padding:24px 32px;">
          <span style="color:#ffffff;font-size:22px;font-weight:700;letter-spacing:-0.5px;">Ava</span>
        </td></tr>
        <!-- Body -->
        <tr><td style="padding:32px;">
          {body_html}
        </td></tr>
        <!-- Footer -->
        <tr><td style="padding:16px 32px;border-top:1px solid #f3f4f6;">
          <p style="margin:0;font-size:12px;color:#9ca3af;text-align:center;">
            Ava &mdash; Your AI companion &bull; <a href="{settings.frontend_url}" style="color:#9ca3af;">avasecret.org</a>
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _cta_button(label: str, href: str) -> str:
    return (
        f'<a href="{href}" style="display:inline-block;background:#111827;color:#ffffff;'
        f'text-decoration:none;padding:12px 24px;border-radius:8px;font-size:14px;'
        f'font-weight:600;margin-top:24px;">{label}</a>'
    )


async def send_welcome_email(to: str, first_name: str | None = None) -> bool:
    """Welcome email — triggered on new account creation (email/password AND Google)."""
    name = first_name or "there"
    body = f"""
      <h2 style="margin:0 0 8px;font-size:20px;color:#111827;">Hey {name}, welcome to Ava.</h2>
      <p style="margin:0 0 16px;font-size:15px;color:#374151;line-height:1.6;">
        Your AI companion is ready. Start a conversation, switch modes, explore what Ava can do.
      </p>
      <p style="margin:0;font-size:15px;color:#374151;line-height:1.6;">
        We're glad you're here.
      </p>
      {_cta_button("Start chatting", f"{settings.frontend_url}/chat")}
    """
    return await send_email(to, "Welcome to Ava", _base_html("Welcome to Ava", body))


async def send_password_reset_email(to: str, reset_url: str) -> bool:
    """Password reset email — link is valid for 5 minutes (Supabase enforced)."""
    body = f"""
      <h2 style="margin:0 0 8px;font-size:20px;color:#111827;">Reset your password</h2>
      <p style="margin:0 0 16px;font-size:15px;color:#374151;line-height:1.6;">
        We received a request to reset the password for your Ava account.
        Click the button below to choose a new one.
      </p>
      <p style="margin:0;font-size:13px;color:#6b7280;">
        This link expires in 5 minutes. If you didn't request this, you can safely ignore it.
      </p>
      {_cta_button("Reset password", reset_url)}
    """
    return await send_email(to, "Reset your Ava password", _base_html("Reset password", body))


async def send_receipt_email(
    to: str,
    amount_usd: float,
    next_billing_date: str,
) -> bool:
    """Subscription receipt — sent on checkout.session.completed (EMAI-03)."""
    body = f"""
      <h2 style="margin:0 0 8px;font-size:20px;color:#111827;">Subscription confirmed</h2>
      <p style="margin:0 0 16px;font-size:15px;color:#374151;line-height:1.6;">
        Thanks for subscribing to Ava. Here's your receipt.
      </p>
      <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;margin-bottom:16px;">
        <tr style="background:#f9fafb;">
          <td style="padding:10px 16px;font-size:13px;color:#6b7280;">Amount charged</td>
          <td style="padding:10px 16px;font-size:13px;color:#111827;text-align:right;font-weight:600;">${amount_usd:.2f} USD</td>
        </tr>
        <tr>
          <td style="padding:10px 16px;font-size:13px;color:#6b7280;">Next billing date</td>
          <td style="padding:10px 16px;font-size:13px;color:#111827;text-align:right;">{next_billing_date}</td>
        </tr>
      </table>
      {_cta_button("Manage billing", f"{settings.frontend_url}/settings")}
    """
    return await send_email(to, "Your Ava subscription is active", _base_html("Receipt", body))


async def send_cancellation_email(to: str, access_until: str) -> bool:
    """Cancellation confirmation — sent on customer.subscription.deleted (EMAI-04)."""
    body = f"""
      <h2 style="margin:0 0 8px;font-size:20px;color:#111827;">Your subscription has been cancelled</h2>
      <p style="margin:0 0 16px;font-size:15px;color:#374151;line-height:1.6;">
        We've cancelled your Ava subscription. You'll continue to have full access until
        <strong>{access_until}</strong>.
      </p>
      <p style="margin:0 0 16px;font-size:15px;color:#374151;line-height:1.6;">
        If you change your mind, you can re-subscribe at any time and pick up right where you left off.
      </p>
      {_cta_button("Re-subscribe", f"{settings.frontend_url}/subscribe")}
    """
    return await send_email(
        to,
        "Your Ava subscription has been cancelled",
        _base_html("Subscription cancelled", body),
    )
