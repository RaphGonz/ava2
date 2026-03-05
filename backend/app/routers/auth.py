"""
Auth router — account creation, sign-in, and auth helper endpoints.

POST /auth/signup          — Create account with email + password
POST /auth/signin          — Sign in with email + password
POST /auth/forgot-password — Request password reset link (no email enumeration)
POST /auth/send-email-hook — Supabase HTTPS hook for auth emails (signup welcome + password reset)
POST /auth/send-welcome    — Send welcome email for authenticated user (Google OAuth path)
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.config import settings
from app.database import supabase_admin, supabase_client
from app.dependencies import get_current_user
from app.models.auth import SignupRequest, SigninRequest, TokenResponse
from app.services.email.resend_client import (
    send_password_reset_email,
    send_welcome_email,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
async def signup(body: SignupRequest):
    """
    Create a new user account with email and password.

    IMPORTANT: Requires email confirmation disabled in Supabase Dashboard.
    Authentication > Providers > Email > uncheck 'Confirm email'.
    Otherwise session will be None and no token can be returned.
    """
    try:
        response = supabase_client.auth.sign_up({
            "email": body.email,
            "password": body.password,
        })
        if response.user is None:
            raise HTTPException(status_code=400, detail="Signup failed")
        if response.session is None:
            raise HTTPException(
                status_code=400,
                detail="Email confirmation required — disable it in Supabase Dashboard "
                       "(Authentication > Providers > Email > uncheck 'Confirm email')",
            )
        return TokenResponse(
            access_token=response.session.access_token,
            user_id=str(response.user.id),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/signin", response_model=TokenResponse)
async def signin(body: SigninRequest):
    """Sign in with email and password. Returns JWT access token."""
    try:
        response = supabase_client.auth.sign_in_with_password({
            "email": body.email,
            "password": body.password,
        })
        return TokenResponse(
            access_token=response.session.access_token,
            user_id=str(response.user.id),
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")


# ---------------------------------------------------------------------------
# Password reset (AUTH-02)
# ---------------------------------------------------------------------------

class _ForgotPasswordBody(BaseModel):
    email: str


@router.post("/forgot-password")
async def forgot_password(body: _ForgotPasswordBody):
    """
    Trigger a Supabase password reset email for the given address.

    SECURITY: Always returns the same 200 response — prevents email enumeration
    (CONTEXT.md locked decision). Supabase silently does nothing for unregistered
    emails, so no branch on user existence is needed.
    """
    try:
        supabase_client.auth.reset_password_for_email(
            body.email,
            options={"redirect_to": f"{settings.frontend_url}/reset-password"},
        )
    except Exception as exc:
        # Log but never expose whether the email exists (no enumeration)
        logger.warning("Password reset attempt for %s suppressed: %s", body.email, exc)

    return {"message": "If an account exists with this email, a reset link has been sent"}


# ---------------------------------------------------------------------------
# Supabase send-email hook (EMAI-02 + AUTH-02)
# ---------------------------------------------------------------------------

@router.post("/send-email-hook")
async def supabase_send_email_hook(request: Request):
    """
    HTTPS hook called by Supabase whenever it needs to send an auth email.

    Handles:
    - email_action_type == "recovery"  -> password reset email (AUTH-02)
    - email_action_type == "signup"    -> welcome email for email/password users (EMAI-02)

    Verification: standardwebhooks HMAC with supabase_hook_secret (strip v1,whsec_ prefix).
    Must return 200 {} on success; 401 on bad signature — per Supabase hook contract.

    NOTE: Read raw_body BEFORE any JSON parsing (critical — FastAPI won't let you re-read body).
    """
    raw_body = await request.body()
    headers = dict(request.headers)

    # Verify HMAC signature (strip v1,whsec_ prefix per RESEARCH.md Pitfall 3)
    if not settings.supabase_hook_secret:
        logger.error("SUPABASE_HOOK_SECRET not configured — rejecting hook call")
        raise HTTPException(status_code=401, detail="Hook not configured")

    from standardwebhooks.webhooks import Webhook
    hook_secret = settings.supabase_hook_secret.replace("v1,whsec_", "")
    wh = Webhook(hook_secret)
    try:
        payload = wh.verify(raw_body.decode(), headers)
    except Exception as exc:
        logger.warning("Hook signature verification failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid hook signature")

    user = payload.get("user", {})
    email_data = payload.get("email_data", {})
    action_type = email_data.get("email_action_type")
    user_email = user.get("email")

    if not user_email:
        return {}

    if action_type == "recovery":
        # Password reset: build the reset URL from token_hash (RESEARCH.md Pattern 2)
        token = email_data.get("token_hash") or email_data.get("token")
        site_url = email_data.get("site_url") or settings.frontend_url
        reset_url = f"{site_url}/reset-password?token={token}&type=recovery"
        await send_password_reset_email(user_email, reset_url)

    elif action_type == "signup":
        # email+password signup — send welcome email
        # Google OAuth users do NOT trigger this hook (they are auto-confirmed)
        full_name = user.get("user_metadata", {}).get("full_name", "")
        first_name = full_name.split()[0] if full_name else None
        await send_welcome_email(user_email, first_name)

    return {}


# ---------------------------------------------------------------------------
# Send welcome for Google OAuth signups (EMAI-02 — Google path)
# ---------------------------------------------------------------------------

@router.post("/send-welcome")
async def send_welcome(user=Depends(get_current_user)):
    """
    Send a welcome email for an authenticated user who signed up via Google OAuth.

    Google OAuth users are auto-confirmed and do NOT trigger the send-email hook
    (Pitfall 5 from RESEARCH.md). The frontend calls this immediately after detecting
    a new Google signup via onAuthStateChange.

    Idempotency: sets welcome_sent=true in user_metadata via supabase_admin to prevent
    duplicate welcome emails on page refreshes. Non-blocking — returns 200 regardless
    of email outcome.
    """
    user_id = str(user.id)
    metadata: dict = {}

    # Idempotency check — skip if welcome already sent
    try:
        user_data = supabase_admin.auth.admin.get_user_by_id(user_id)
        metadata = user_data.user.user_metadata or {}
        if metadata.get("welcome_sent"):
            return {"sent": False, "reason": "already_sent"}
    except Exception as exc:
        logger.warning("Could not check welcome_sent for %s: %s", user_id, exc)
        # Proceed — better to send a duplicate than silently skip

    # Send welcome email
    email = user.email
    if not email:
        return {"sent": False, "reason": "no_email"}

    # Best-effort first_name extraction from user_metadata
    user_meta = getattr(user, "user_metadata", None) or {}
    full_name = str(user_meta.get("full_name", ""))
    first_name = full_name.split()[0] if full_name else None

    await send_welcome_email(email, first_name)

    # Mark as sent (best-effort, non-blocking)
    try:
        supabase_admin.auth.admin.update_user_by_id(
            user_id,
            {"user_metadata": {**metadata, "welcome_sent": True}},
        )
    except Exception as exc:
        logger.warning("Could not set welcome_sent flag for %s: %s", user_id, exc)

    return {"sent": True}
