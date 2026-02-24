"""Google OAuth2 flow for Calendar access.

Uses Flow.from_client_config() — web server pattern, not InstalledAppFlow.
Scope: calendar.events only (least privilege — avoids full calendar management access).
"""
import asyncio
from datetime import datetime, timezone
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from app.config import settings
from app.services.google_auth.token_store import save_calendar_tokens

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

_CLIENT_CONFIG = {
    "web": {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}


def get_auth_url() -> str:
    """Return the Google OAuth consent URL. User must visit this in a browser."""
    flow = Flow.from_client_config(
        _CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=settings.google_oauth_redirect_uri,
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",     # required for refresh_token
        prompt="consent",          # always show consent to get refresh_token
        include_granted_scopes="true",
    )
    return auth_url


async def exchange_code_for_tokens(user_id: str, code: str) -> None:
    """Exchange authorization code for tokens and persist them for user_id.

    Runs Flow.fetch_token() in a thread pool — it makes synchronous HTTP calls.
    Raises on failure (caller should catch and show error to user).
    """
    flow = Flow.from_client_config(
        _CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=settings.google_oauth_redirect_uri,
    )
    # fetch_token is synchronous — run in executor to avoid blocking event loop
    await asyncio.to_thread(flow.fetch_token, code=code)

    creds = flow.credentials
    expiry = creds.expiry  # datetime or None
    if expiry and expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    await save_calendar_tokens(
        user_id=user_id,
        access_token=creds.token,
        refresh_token=creds.refresh_token or "",
        token_expiry=expiry,
        scopes=list(creds.scopes or SCOPES),
    )


async def get_credentials_for_user(user_id: str) -> Credentials | None:
    """Load and auto-refresh credentials for user_id.

    Returns None if user has not connected Google Calendar.
    Raises google.auth.exceptions.RefreshError if token was revoked — caller
    must catch this, delete tokens, and prompt re-authorization.
    """
    from app.services.google_auth.token_store import get_calendar_tokens

    tokens = await get_calendar_tokens(user_id)
    if not tokens:
        return None

    creds = Credentials(
        token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=tokens.get("scopes") or SCOPES,
    )

    if creds.expired and creds.refresh_token:
        await asyncio.to_thread(creds.refresh, Request())
        expiry = creds.expiry
        if expiry and expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        await save_calendar_tokens(
            user_id=user_id,
            access_token=creds.token,
            refresh_token=creds.refresh_token or "",
            token_expiry=expiry,
            scopes=list(creds.scopes or SCOPES),
        )

    return creds
